"""Spending rules of protocol v2.3 (Sections 10.3, 12.3 to 12.5, 16.4 and 16.5), shared by the answering runner
(src/run_models.py) and the judging runner (src/run_judges_v23.py).

One ledger for the whole study (results/logs/spend_ledger.jsonl), read strictly, and one lock file
(results/logs/spend.lock) taken by the runner before it reads the ledger. Lines written under these rules:

  call              a paid attempt: model_key, block, role (respondent | judge), item (an item of the holds file),
                    final (true when the attempt ended the call), reserved_usd, spent_usd (>= 0)
  block_complete    a block, or the part of one role (respondent | judge) in it, is closed after its runner counted
                    every planned call (the PI runs it). 'models' closes the part of some models only (for example
                    the calls of models 22 and 23 in block 5, which must end before block 6, Section 12.3)
  block_abandon     the PI's dated decision to stop or abandon the rest of a block, for some models; reason
  freeze            the freeze commit is registered: tag. Blocks 2 to 7 need it
  cut               cut n of Section 12.4: the calls of its items that are not yet sent are removed
  overrun           a call settled above its reservation: no further paid call until overrun_resolved
  overrun_resolved  the cause was found and recorded (reason)
  provider_stop     Section 16.5: every call to an account (and, through a router, to a serving host) stops
  provider_resume   the PI's dated decision to resume after the provider answered in writing
  credit_fee        a fee or tax on a credit purchase: spent_usd counts against the cap
  registration      the PI registered the protocol before the pilot (tag). Code reads answer files only after it
  preflight         the endpoint check of a model reached through OpenRouter (spent_usd 0)
  availability_call the harmless test call of a hosted model on the day of the freeze (Section 10.4, decision D13;
                    src/run_models.py --availability-check): spent_usd counts against the cap; it belongs to no block

Holds (Section 12.5). config/stage_holds.json lists, per block of Section 12.3, the paid calls planned for each
model and part, with the pessimistic cost of one call (scripts/holds_v23.py, from the manifest). A call of block B
is sent only if  spent + reservations in flight + holds of every unfinished block before B + its own bound
<= cap. The holds are counted from the calls that remain: planned calls minus calls with a final attempt.

Reservation bound (Section 12.5): UTF-8 bytes of the messages as sent, plus a fixed allowance per message and per
request, times the larger of the input and cache-write prices, plus the output cap times the output price.

Cuts (Section 12.4): before every block of the commercial main run (4, 6 and 7) the pessimistic cost of all
unfinished work is compared with what is left under the cap; cuts 1 to 4 are applied in order until it fits. A
block that does not fit after the four cuts does not start.

Command line (the PI's records; none of them sends a call):
  python -I src/spend_v23.py status
  python -I src/spend_v23.py register --tag TAG      (the pilot registration, Section 14)
  python -I src/spend_v23.py freeze --tag TAG
  python -I src/spend_v23.py fee --usd 1.25 --account openrouter --note "card fee of the 11/11 purchase"
  python -I src/spend_v23.py stop --account openrouter [--host Parasail] --reason "warning e-mail of DATE"
  python -I src/spend_v23.py resume --account openrouter [--host Parasail] --reason "provider's written answer"
  python -I src/spend_v23.py resolve-overrun --reason "cause found: ..."
  python -I src/spend_v23.py abandon --block 6 --models a,b --reason "..."
Blocks are closed by the runner that knows their plan: run_models.py --complete-block N (answers) and
run_judges_v23.py --complete-block N (verdicts).

Standard library only.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import pathlib
import sys
import threading
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
LEDGER = ROOT / "results" / "logs" / "spend_ledger.jsonl"
SPEND_LOCK = ROOT / "results" / "logs" / "spend.lock"
HOLDS = ROOT / "config" / "stage_holds.json"
MODELS = ROOT / "config" / "models.json"
STUDY_CAP_DEFAULT = 128.0          # Section 12.4 (decision D14, 11 November 2026)
BLOCKS = ("1", "2", "3", "4", "5", "6", "7")
BLOCK_NAMES = {"1": "pilot", "2": "missing answers of the primary panel",
               "3": "primary panel on the harmful frame (screen, then judging)",
               "4": "answers of the commercial models, their screen and the label sample",
               "5": "primary panel, the rest", "6": "commercial judges",
               "7": "commercial judges, challenge set"}
NEEDS_FREEZE = ("2", "3", "4", "5", "6", "7")
COMMERCIAL_MAIN = ("4", "6", "7")
CUTS = (1, 2, 3, 4)
ROLES = {"1": ("respondent", "judge"), "2": ("respondent",), "3": ("judge",), "4": ("respondent",),
         "5": ("judge",), "6": ("judge",), "7": ("judge",)}
PREREQ = {"3": ("2",), "4": ("3",), "5": ("4",), "6": ("4",), "7": ("6",)}      # Section 12.3: block order
PAID_FIRST = {"6": ("5",), "7": ("5",)}     # the paid calls of block 5 (models 22 and 23) end before these start
MESSAGE_ALLOWANCE = 32             # tokens per message: role markers and separators of the provider's wrapping
REQUEST_ALLOWANCE = 64             # tokens per request: begin marker, generation prompt, provider-side framing
ZDR_URL = "https://openrouter.ai/api/v1/endpoints/zdr"
USER_AGENT = "agentsControl-preflight/2.3"
EPS = 1e-9


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


# ---- ledger file -----------------------------------------------------------------------------------------------

def registered(path=None):
    """The pilot registration is recorded in the ledger (spend_v23.py register)."""
    return any(e.get("kind") == "registration" for e in read_ledger(path))


def read_ledger(path=None):
    """Every line of the ledger. An unreadable line stops the run: skipping it would drop money from the books."""
    path = pathlib.Path(path or LEDGER)
    if not path.exists():
        return []
    rows = []
    with open(path, encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    sys.exit(f"{path.name} line {n} is unreadable (interrupted write): repair it before any paid or "
                             f"bookkeeping run")
    return rows


def append_line(path, obj, durable=True):
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size:
        with open(path, "rb") as f:
            f.seek(-1, os.SEEK_END)
            last = f.read(1)
        if last != b"\n":
            with open(path, "ab") as f:
                f.write(b"\n")
    with open(path, "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")
        if durable:
            f.flush()
            os.fsync(f.fileno())


def acquire_lock(run, lock=None):
    lock = pathlib.Path(lock or SPEND_LOCK)
    lock.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        sys.exit(f"another paid process holds {lock.name}; if none is running, delete it")
    with os.fdopen(fd, "w") as f:
        f.write(json.dumps({"run": run, "pid": os.getpid(), "ts": now()}))


def release_lock(lock=None):
    lock = pathlib.Path(lock or SPEND_LOCK)
    if lock.exists():
        lock.unlink()


# ---- reservation bound -------------------------------------------------------------------------------------------

def as_messages(request):
    return [{"role": "user", "content": request}] if isinstance(request, str) else list(request)


def request_bytes(request):
    return sum(len((m.get("content") or "").encode("utf-8")) for m in as_messages(request))


def input_bound_tokens(request):
    """An upper bound on the input tokens: a token of ordinary text is never shorter than one byte."""
    return request_bytes(request) + MESSAGE_ALLOWANCE * len(as_messages(request)) + REQUEST_ALLOWANCE


def input_price_bound(m, live=None):
    """US$ per million input tokens: the larger of the input price and the cache-write price (config factor, the
    recorded endpoint price and, when a preflight ran, the live endpoint prices)."""
    p = float(m["price_in"])
    cands = [p, p * float(m.get("cache_write_factor") or 1.0)]
    pin = m.get("pin") or {}
    for d in (pin, live or {}):
        for k in ("prompt_usd_per_m", "cache_write_usd_per_m"):
            if d.get(k) is not None:
                cands.append(float(d[k]))
    return max(cands)


def output_price_bound(m, live=None):
    cands = [float(m["price_out"])]
    for d in (m.get("pin") or {}, live or {}):
        if d.get("completion_usd_per_m") is not None:
            cands.append(float(d["completion_usd_per_m"]))
    return max(cands)


def call_bound(m, request, out_cap, live=None, price_factor=1.0):
    """Worst-case cost of one call (Section 12.5). price_factor < 1 only for a batch price on a direct provider."""
    return price_factor * (input_bound_tokens(request) * input_price_bound(m, live)
                           + int(out_cap) * output_price_bound(m, live)) / 1e6


def listed_cost(m, out, price_factor=1.0):
    """List-price cost of a parsed response, with cached input at cache rates. input_tokens includes cached tokens.
    Factors come from the config; the defaults are conservative (cache reads at the full input price, Anthropic
    cache writes at 1.25x)."""
    tin = out.get("input_tokens") or 0
    cr = out.get("cache_read_tokens") or 0
    cw = out.get("cache_write_tokens") or 0
    f_read = m.get("cache_read_factor", 1.0)
    f_write = m.get("cache_write_factor", 1.25 if m["provider"] == "anthropic" else 1.0)
    tin_eq = (tin - cr - cw) + cr * f_read + cw * f_write
    return price_factor * (tin_eq * m["price_in"] + (out.get("output_tokens") or 0) * m["price_out"]) / 1e6


def settled_cost(m, out, price_factor=1.0):
    """Section 12.5: the larger of the list-price cost and the cost that the provider reports."""
    return max(listed_cost(m, out, price_factor), float(out.get("cost_reported") or 0.0))


def settle_failed(exc, reserved, providers_mod):
    """What a failed call is charged: 0 if our own check stopped it before sending or the provider rejected it with
    a 4xx status (not billed); otherwise (time-out, connection loss, 5xx, a response that came back but could not
    be parsed) the reserved amount, because it may have been sent and billed."""
    if isinstance(exc, providers_mod.ResponseParseError):
        return reserved
    if isinstance(exc, (providers_mod.ProjectKeyError, providers_mod.PreSendError, providers_mod.SuspectedBlock)):
        return 0.0                  # stopped before sending, or a 400/403 rejection (not billed)
    status = getattr(exc, "status_code", None)
    if status is not None and 400 <= int(status) < 500:
        return 0.0
    return reserved


REQUEST_INDEPENDENT = (401, 402, 403, 404, 408, 409, 425, 429)


def failure_kind(exc, providers_mod, is_overflow):
    """How a failed call is handled (Sections 10.1 to 10.3):
      'blocked'    a 400/403 that matched no moderation marker and no parameter-error signature (SuspectedBlock)
      'overflow'   the request does not fit the model's context (never retried, never shortened)
      'config'     a 400/422 that names a parameter: our configuration is wrong; the model's calls stop
      'transient'  does not depend on the request (authentication, quota, model not found, rate limit, time-out,
                   server error, connection loss): retried up to three times in the session, then pending
      'rejected'   the provider rejected this request for another reason: a final outcome, never retried
    """
    text = providers_mod.error_text(exc)
    if is_overflow(text):           # before the block test: an overflow message can lack the parameter markers
        return "overflow"
    if isinstance(exc, providers_mod.SuspectedBlock):
        return "blocked"
    status = getattr(exc, "status_code", None)
    if status is None:
        return "transient"
    status = int(status)
    if status == 413:
        return "overflow"
    if status in REQUEST_INDEPENDENT or status >= 500:
        return "transient"
    if status in (400, 422) and any(k in text.lower() for k in providers_mod.PARAM_ERROR_MARKERS):
        return "config"
    return "rejected"


# ---- accounts and hosts (Section 16.5) ---------------------------------------------------------------------------

def account_of(m):
    if m["provider"] in ("anthropic", "openai"):
        return m["provider"]
    if m["provider"] == "ollama":
        return "local"
    return "openrouter" if "openrouter.ai" in (m.get("base_url") or "") else "other:" + (m.get("base_url") or "")


def host_of(m):
    """The serving host: the pinned endpoint's provider for a model reached through a router, else the account."""
    pin = m.get("pin") or {}
    return pin.get("provider_name") or account_of(m)


# ---- holds file ----------------------------------------------------------------------------------------------------

def item_id(block, role, model_key, part):
    return f"{block}|{role}|{model_key}|{part}"


def load_holds(path=None):
    path = pathlib.Path(path or HOLDS)
    d = json.loads(path.read_text(encoding="utf-8"))
    if d.get("protocol") != "2.3":
        sys.exit(f"{path.name} is not the v2.3 holds file (blocks of Section 12.3): run scripts/holds_v23.py")
    for it in d["items"]:
        it.setdefault("id", item_id(it["block"], it["role"], it["model_key"], it["part"]))
    return d


# ---- books -------------------------------------------------------------------------------------------------------

class Books:
    """The ledger in memory for one paid process (the lock guarantees that no other process writes to it)."""

    def __init__(self, run, holds=None, study_cap=None, run_cap=None, ledger=None, write=True):
        self.run, self.path, self.write_enabled = run, pathlib.Path(ledger or LEDGER), write
        self.holds = holds if holds is not None else load_holds()
        self.items = {it["id"]: it for it in self.holds["items"]}
        env = (os.environ.get("STUDY_BUDGET_USD") or "").strip()
        if study_cap is None and env:
            try:
                same = abs(float(env) - STUDY_CAP_DEFAULT) < 1e-9
            except ValueError:
                same = False
            if not same:
                raise SystemExit(f"STUDY_BUDGET_USD (environment or .env) differs from the study cap of decision D14, "
                                 f"US${STUDY_CAP_DEFAULT:.2f} (Section 12.4): remove it, or set it to that value. Fees "
                                 f"and taxes on credit purchases are recorded with 'spend_v23.py fee' and count "
                                 f"against the cap in the ledger; the cap itself is not lowered")
        self.study_cap = float(study_cap if study_cap is not None else STUDY_CAP_DEFAULT)
        self.run_cap = float(run_cap) if run_cap else None
        self.lock = threading.Lock()
        self.inflight = 0.0
        self.run_spent = 0.0
        self.stopped_reason = None
        self.spent = 0.0
        self.final = {}
        self.complete, self.abandoned, self.cuts, self.stops = set(), set(), {}, set()
        self.freeze = None
        self.registration = None
        self.overrun_open = False
        for e in read_ledger(self.path):
            self._apply(e)

    # state ------------------------------------------------------------------------------------------------------
    def _apply(self, e):
        self.spent += float(e.get("spent_usd") or 0.0)
        k = e.get("kind")
        if k == "call" and e.get("final") and e.get("item"):
            self.final[e["item"]] = self.final.get(e["item"], 0) + 1
        elif k == "block_complete":
            for mk in e.get("models") or ["*"]:
                self.complete.add((str(e["block"]), e.get("role") or "*", mk))
        elif k == "block_abandon":
            for mk in e.get("models") or ["*"]:
                self.abandoned.add((str(e["block"]), mk))
        elif k == "freeze":
            self.freeze = e.get("tag")
        elif k == "registration":
            self.registration = e.get("tag")
        elif k == "cut":
            self.cuts[int(e["cut"])] = e
        elif k == "overrun":
            self.overrun_open = True
        elif k == "overrun_resolved":
            self.overrun_open = False
        elif k == "provider_stop":
            self.stops.add((e["account"], e.get("host")))
        elif k == "provider_resume":
            self.stops.discard((e["account"], e.get("host")))

    def record(self, entry, durable=True):
        """Write one ledger line and apply it."""
        entry = dict(entry, run=entry.get("run", self.run), ts=entry.get("ts", now()))
        with self.lock:
            if self.write_enabled:
                append_line(self.path, entry, durable)
            self._apply(entry)
        return entry

    # holds --------------------------------------------------------------------------------------------------------
    def closed(self, block, role, model_key="*"):
        """True when a block_complete line covers this block, role and model."""
        b = str(block)
        return any(x in self.complete for x in ((b, role, model_key), (b, role, "*"), (b, "*", model_key),
                                                (b, "*", "*")))

    def block_done(self, block):
        """Every role of the block is closed for every model."""
        return all(self.closed(block, r) for r in ROLES[str(block)])

    def abandoned_for(self, block, model_key):
        return (str(block), model_key) in self.abandoned or (str(block), "*") in self.abandoned

    def item_live(self, it):
        """True when the item still has calls to make: not cut, not abandoned, its block part not closed."""
        b = str(it["block"])
        return not (self.closed(b, it.get("role") or "*", it["model_key"]) or int(it.get("cut") or 0) in self.cuts
                    or self.abandoned_for(b, it["model_key"]))

    def remaining_calls(self, it):
        return max(0, int(it["calls"]) - self.final.get(it["id"], 0)) if self.item_live(it) else 0

    def remaining(self, block=None, cut=None):
        """Pessimistic US$ of the calls that remain, for one block (or all), optionally of one cut only."""
        tot = 0.0
        for it in self.items.values():
            if block is not None and str(it["block"]) != str(block):
                continue
            if cut is not None and int(it.get("cut") or 0) != cut:
                continue
            tot += self.remaining_calls(it) * float(it["usd_per_call"])
        return tot

    def hold(self, block):
        """Pessimistic US$ of every unfinished block of higher priority (Section 12.5)."""
        i = BLOCKS.index(str(block))
        return sum(self.remaining(b) for b in BLOCKS[:i])

    def left(self):
        return self.study_cap - self.spent

    # rules before a run -------------------------------------------------------------------------------------------
    def start_check(self, block, role=None, apply_cuts=True):
        """(ok, message). The freeze, an open overrun, the order of the blocks (Section 12.3), the start rule, and
        for blocks 4, 6 and 7 the cuts. role: the part of the block that the caller runs (default: every part)."""
        block = str(block)
        if block in NEEDS_FREEZE and not self.freeze:
            return False, f"block {block} runs after the freeze: no freeze line in the ledger (spend_v23.py freeze)"
        if self.overrun_open:
            return False, "a call settled above its reservation: no paid call until the cause is recorded"
        roles = (role,) if role else ROLES[block]
        if all(self.closed(block, r) for r in roles):
            return False, f"block {block} is closed" + (f" for the {role} calls" if role else "")
        for b in PREREQ.get(block, ()):
            if not self.block_done(b):
                return False, f"block {block} starts after block {b} is closed (Section 12.3)"
        for b in PAID_FIRST.get(block, ()):
            if self.remaining(b) > EPS:
                return False, (f"block {block} starts after the paid calls of block {b} (models 22 and 23) are "
                               f"closed: run_judges_v23.py --complete-block {b} --judges <their keys> (Section 12.3)")
        if block in COMMERCIAL_MAIN:
            ok, msg = self.cut_check(block, apply_cuts)
            if not ok:
                return ok, msg
        need = self.spent + self.hold(block) + self.remaining(block)
        if need > self.study_cap + EPS:
            return False, (f"block {block} does not fit: ledger ${self.spent:.2f} + holds ${self.hold(block):.2f} "
                           f"+ its own ${self.remaining(block):.2f} > cap ${self.study_cap:.2f}")
        return True, (f"block {block} fits: ledger ${self.spent:.2f} + holds ${self.hold(block):.2f} + its own "
                      f"${self.remaining(block):.2f} <= cap ${self.study_cap:.2f}")

    def cut_check(self, block, apply_cuts=True):
        """Section 12.4: all unfinished work against what is left; cuts in order until it fits."""
        applied = []
        for c in CUTS:
            if self.spent + self.remaining() <= self.study_cap + EPS:
                break
            if c in self.cuts or self.remaining(cut=c) <= 0:
                continue
            saving = self.remaining(cut=c)
            if apply_cuts:
                self.record({"kind": "cut", "cut": c, "before_block": block, "saves_usd_at_cut": round(saving, 6),
                             "spent_usd": 0.0, "ledger_usd": round(self.spent, 6),
                             "unfinished_usd": round(self.remaining(), 6), "cap_usd": self.study_cap})
            else:
                self.cuts[c] = {"cut": c, "simulated": True}
            applied.append((c, round(saving, 4)))
        if self.spent + self.remaining() > self.study_cap + EPS:
            return False, (f"block {block} does not start: unfinished work ${self.remaining():.2f} > left "
                           f"${self.left():.2f} after the four cuts")
        return True, ("cuts applied: " + ", ".join(f"{c} (${s:.2f})" for c, s in applied)) if applied else "no cut needed"

    def stopped(self, m):
        """The provider-stop line that covers this model, or None (Section 16.5)."""
        acc, host = account_of(m), host_of(m)
        for a, h in self.stops:
            if a == acc and (h is None or h == host):
                return (a, h)
            if h is not None and h == host:
                return (a, h)
        return None

    # per call -----------------------------------------------------------------------------------------------------
    def reserve(self, block, amount):
        """(ok, why). Thread-safe. Needs: no open overrun, room beside the holds of higher priority, the run cap."""
        with self.lock:
            if self.stopped_reason:
                return False, self.stopped_reason
            if self.overrun_open:
                return False, "overrun"
            if self.spent + self.inflight + self.hold(block) + amount > self.study_cap + EPS:
                return False, "cap"
            if self.run_cap is not None and self.run_spent + self.inflight + amount > self.run_cap + EPS:
                return False, "run_cap"
            self.inflight += amount
            return True, ""

    def settle(self, reserved, actual, entry):
        """Release the reservation and write the call line (entry: model_key, block, role, item, final, ...).
        A settlement above the reservation writes an overrun line and stops every further paid call."""
        actual = max(0.0, float(actual))
        with self.lock:
            self.inflight -= reserved
            self.run_spent += actual
        line = self.record(dict(entry, kind="call", reserved_usd=round(reserved, 6), spent_usd=round(actual, 6)))
        if actual > reserved + 1e-9:
            self.record({"kind": "overrun", "model_key": entry.get("model_key"), "block": entry.get("block"),
                         "item": entry.get("item"), "reserved_usd": round(reserved, 6),
                         "settled_usd": round(actual, 6), "spent_usd": 0.0})
            with self.lock:
                self.stopped_reason = "overrun"
        return line

    def release(self, reserved):
        """A reservation that was not used (nothing was sent)."""
        with self.lock:
            self.inflight -= reserved


# ---- endpoint preflight (Section 3.3, decision D16; Section 19.4) -----------------------------------------------------

def fetch_zdr(url=ZDR_URL, timeout=60):
    """OpenRouter's public list of zero-retention endpoints. No key and no model call."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))["data"]


def endpoint_facts(e):
    p = e.get("pricing") or {}
    per_m = lambda k: (round(float(p[k]) * 1e6, 6) if p.get(k) not in (None, "") else None)
    return {"tag": e.get("tag"), "provider_name": e.get("provider_name"), "quantization": e.get("quantization"),
            "prompt_usd_per_m": per_m("prompt"), "completion_usd_per_m": per_m("completion"),
            "cache_write_usd_per_m": per_m("input_cache_write"), "safety_retention": bool(e.get("safety_retention")),
            "status": e.get("status"), "context_length": e.get("context_length")}


def preflight(m, zdr, harmful=True):
    """(ok, live facts, problems) for a model reached through OpenRouter.

    ok needs: the pinned endpoint is on the zero-retention list with the recorded precision and prices; an endpoint
    marked for safety retention only if decision D2 allows it for this model ('d2_safety_retention' of
    config/models.json: 'safe_only' admits safe prompts, 'all' admits harmful prompts too; empty means not decided);
    and the request routing names that endpoint only (provider_order, allow_fallbacks false, zdr true)."""
    pin = m.get("pin") or {}
    problems = []
    if not pin.get("tag"):
        return False, None, ["no pinned endpoint recorded (config 'pin')"]
    if (m.get("provider_order") or [None])[0] != pin["tag"]:
        problems.append(f"provider_order {m.get('provider_order')} does not name the pinned endpoint {pin['tag']}")
    if m.get("allow_fallbacks", False) or m.get("zdr", True) is not True:
        problems.append("fallbacks must be off and zdr on")
    hit = [e for e in zdr if e.get("model_id") == m["model"] and e.get("tag") == pin["tag"]]
    if not hit:
        return False, None, problems + [f"{pin['tag']} is not on the zero-retention list for {m['model']}"]
    live = endpoint_facts(hit[0])
    if live["quantization"] != pin.get("quantization"):
        problems.append(f"precision {live['quantization']} != recorded {pin.get('quantization')}")
    for k in ("prompt_usd_per_m", "completion_usd_per_m", "cache_write_usd_per_m"):
        if live.get(k) != pin.get(k):
            problems.append(f"{k} {live.get(k)} != recorded {pin.get(k)}")
    d2 = m.get("d2_safety_retention")
    if live["safety_retention"]:
        if d2 not in ("safe_only", "all"):
            problems.append("endpoint marked for safety retention and decision D2 does not allow it")
        elif harmful and d2 != "all":
            problems.append("endpoint marked for safety retention: decision D2 admits safe prompts only")
    return not problems, live, problems


def may_send_harmful(m, live=None):
    """False when a safety-retention endpoint is allowed for safe prompts only (D2)."""
    sr = (live or {}).get("safety_retention", (m.get("pin") or {}).get("safety_retention"))
    return not sr or m.get("d2_safety_retention") == "all"


def d2_safe_only(ledger, key):
    """The latest preflight of this model admitted its endpoint for safe prompts only (decision D2): its harmful-side
    calls were not sent, and the close of a block counts them as excluded under D2."""
    lines = [e for e in ledger if e.get("kind") == "preflight" and e.get("model_key") == key]
    return bool(lines and lines[-1].get("safe_only"))


# ---- command line ----------------------------------------------------------------------------------------------------

def _status(books):
    print(f"ledger ${books.spent:.2f} of cap ${books.study_cap:.2f}; registration: {books.registration or 'not yet'}; "
          f"freeze: {books.freeze or 'not yet'}; "
          f"open overrun: {books.overrun_open}")
    print("closed (block, role, model):", sorted(books.complete) or "none", "| cuts:", sorted(books.cuts) or "none",
          "| provider stops:", sorted(books.stops, key=str) or "none")
    for b in BLOCKS:
        print(f"  block {b} ({BLOCK_NAMES[b]}): remaining ${books.remaining(b):.2f}, hold before it ${books.hold(b):.2f}")
    print(f"unfinished work ${books.remaining():.2f}; left under the cap ${books.left():.2f}")


def main(argv=None):
    ap = argparse.ArgumentParser(description="The PI's records in the spending ledger (no call is sent)")
    ap.add_argument("what", choices=["status", "register", "freeze", "fee", "stop", "resume", "resolve-overrun",
                                     "abandon"])
    ap.add_argument("--tag", default="")
    ap.add_argument("--usd", type=float, default=None)
    ap.add_argument("--account", default="")
    ap.add_argument("--host", default=None)
    ap.add_argument("--note", default="")
    ap.add_argument("--reason", default="")
    ap.add_argument("--block", default="")
    ap.add_argument("--models", default="")
    a = ap.parse_args(argv)
    if a.what == "status":
        _status(Books("status", write=False))
        return
    need = {"register": a.tag, "freeze": a.tag, "fee": a.usd is not None and a.account, "stop": a.account and a.reason,
            "resume": a.account and a.reason, "resolve-overrun": a.reason, "abandon": a.block and a.reason}
    if not need[a.what]:
        sys.exit(f"{a.what}: missing argument (see the usage in the docstring)")
    acquire_lock("ledger:" + a.what)
    try:
        books = Books("pi_record")
        if a.what in ("register", "freeze"):
            books.record({"kind": "registration" if a.what == "register" else "freeze", "tag": a.tag,
                          "spent_usd": 0.0})
        elif a.what == "fee":
            if a.usd < 0:
                sys.exit("--usd must be >= 0")
            books.record({"kind": "credit_fee", "account": a.account, "note": a.note, "spent_usd": round(a.usd, 6)})
        elif a.what in ("stop", "resume"):
            books.record({"kind": "provider_" + a.what, "account": a.account, "host": a.host, "reason": a.reason,
                          "spent_usd": 0.0})
        elif a.what == "resolve-overrun":
            books.record({"kind": "overrun_resolved", "reason": a.reason, "spent_usd": 0.0})
        elif a.what == "abandon":
            books.record({"kind": "block_abandon", "block": a.block,
                          "models": [x for x in a.models.split(",") if x] or None, "reason": a.reason,
                          "spent_usd": 0.0})
        print("recorded:", a.what)
        _status(books)
    finally:
        release_lock()


if __name__ == "__main__":
    main()
