"""Judging runner of protocol v2.3 (Sections 10.2, 10.3, 11 and 12): sends the planned judge calls of one block.

What is sent (src/plan_v23.py): the calls of the block for the chosen judges, in the order of Section 11.4. The two
presentations of an answer by one judge are made one right after the other; if the first ends pending, the second
waits for the resume, so that the pair stays together. Answers without content are never sent (Section 10.1).

Each call (src/judge_v23.py): a fresh conversation built from the template, the request verbatim and the answer
verbatim. One retry with the fixed sentence when the output holds no valid verdict; the result of the retry is
final. Final statuses: valid, parse_error, declined, provider_block, context_overflow. provider_block covers a
moderation rejection; a 400/403 of an API judge that matched no moderation marker and no parameter error
('block_suspected'); and any other rejection of this request by an API provider ('rejected_status'). A failure
that does not depend on the request is tried again up to three times in the session, then the call stays pending;
after five consecutive pending calls the runner stops calling that judge. A 400/422 that names a parameter, or any
rejection by the local Ollama server other than a context overflow, stops the judge: the configuration is wrong.

Money (src/spend_v23.py, Section 12.5): API judges run under the spend lock, reserve the bound of every attempt
beside the holds of unfinished blocks of higher priority, and settle at the larger of the list-price cost and the
reported cost. Calls of a cut item, an abandoned model or a stopped provider are not sent. Local judges cost
nothing: no ledger line, and they run after the API judges of the session, once the lock is released.

Identity (Section 11.3): before the first call, the digest of every local judge build and the Ollama version.
For API judges, the returned model identifier and serving provider of every call are compared with those recorded
when the judge answered as a respondent; a mismatch is recorded on the call and counted (Section 3.3: a
sensitivity analysis drops the affected answers).

Files (stream: 'pilot' for block 1, 'main' otherwise; '_m6q4km' is added for the sensitivity build of model 6):
  results/raw/verdicts_v23_<stream>.jsonl     private: every attempt with its output text, the parsed verdict and
                                              the error body
  results/logs/judge_calls_v23_<stream>.jsonl public: every attempt without output, verdict, reason or error body
                                              (only its SHA-256): counts, statuses, tokens, cost and time
  results/logs/judge_runs_v23.jsonl           one line per session: plan, template, settings, identities, preflight
A call is done when the private file holds a final attempt for its key (block|part|judge|answer|presentation);
the canonical verdict of a call is its first final attempt. This runner reads the private file for those keys and
statuses only, and it prints no request, answer, output or verdict.

Usage (run from the repository root; --dry-run sends nothing):
  python -I src/run_judges_v23.py --block 1 --round 1 --answer-runs p1 --dry-run
  python -I src/run_judges_v23.py --run j1 --block 1 --round 1 --answer-runs p1 [--judges k1,k2] [--workers 4]
  python -I src/run_judges_v23.py --run j3h --block 3 --answer-runs b2 --judges venice-uncensored,cydonia-24b-v4.1
  python -I src/run_judges_v23.py --run c5h --block 5 --answer-runs b2,b4 --judges <22 and 23> --complete-block
  python -I src/run_judges_v23.py --run j3s --block 3 --answer-runs b2 --build sensitivity    (model 6, Q4_K_M)
Standard library only.
"""
import argparse
import collections
import concurrent.futures as cf
import datetime as dt
import hashlib
import json
import pathlib
import sys
import threading
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import answers_v23 as A  # noqa: E402
import frames_v23  # noqa: E402
import judge_v23 as J  # noqa: E402
import plan_v23 as P  # noqa: E402
import providers  # noqa: E402
import screen as screen_mod  # noqa: E402
import spend_v23 as S  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / "results" / "raw"
LOGS = ROOT / "results" / "logs"
MODELS = ROOT / "config" / "models.json"
DESIGN = ROOT / "config" / "panel_v23.json"
LABELS = ROOT / "labels" / "label_sample_v23.jsonl"
SAMPLE = frames_v23.SAMPLE
JUDGE_BLOCKS = ("1", "3", "5", "6", "7")
LABEL_BLOCKS = ("5", "6", "7")
SENSITIVITY_PARTS = ("own_harmful", "control_harmful", "own_safe", "control_safe")

# Seams for the offline tests: provider factory, sleep, endpoint list, local identity.
MAKE_PROVIDER = providers.make
LOAD_ENV = S.load_env              # the AC_* keys and BUDGET_USD from .env, as in src/run_models.py
SLEEP = time.sleep
FETCH_ZDR = S.fetch_zdr
OLLAMA_IDENTITY = providers.ollama_identity
_write_lock = threading.Lock()


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def sha256_text(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def sha256_json(obj):
    return sha256_text(json.dumps(obj, sort_keys=True, ensure_ascii=False))


def stream(block, build="primary"):
    return ("pilot" if str(block) == "1" else "main") + ("_m6q4km" if build == "sensitivity" else "")


def verdicts_path(block, build="primary"):
    return RAW / f"verdicts_v23_{stream(block, build)}.jsonl"


def calls_log_path(block, build="primary"):
    return LOGS / f"judge_calls_v23_{stream(block, build)}.jsonl"


def runs_log_path():
    return LOGS / "judge_runs_v23.jsonl"


def call_key(c):
    return f"{c['block']}|{c['part']}|{c['judge']}|{c['answer_id']}|{c['presentation']}"


def append(path, obj, durable=True):
    with _write_lock:
        S.append_line(path, obj, durable)


def attempt_state(path):
    """{call key: (last attempt number, format retry owed)} from the private verdict file. A call whose answer was
    unparsed and that has no final attempt yet owes its one format retry (Section 11.5): a later session resumes it
    with the retry sentence, and the retry limit stays one."""
    out = {}
    path = pathlib.Path(path)
    if not path.exists():
        return out
    with open(path, encoding="utf-8") as f:
        for line in f:
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue                     # done_calls stops on it before any call
            if not line.strip() or "key" not in r:
                continue
            last, owed = out.get(r["key"], (0, False))
            out[r["key"]] = (max(last, int(r.get("attempt") or 0)),
                             (owed or r.get("status") == "unparsed") and not r.get("final"))
    return out


def reconcile(books):
    """Settles the judge reservations that an earlier process left unsettled (Section 12.5): at the cost written in
    the private verdict record with the same attempt_id, or, when none was written, at the reserved amount, not final
    (status 'interrupted'); the call is then made again under the rules of Section 10.3. Needs the paid lock."""
    lines = books.unsettled("judge")
    if not lines:
        return 0
    by_path = collections.defaultdict(list)
    for e in lines.values():
        by_path[verdicts_path(e.get("block"), e.get("build") or "primary")].append(e)
    for path, es in by_path.items():
        recs = {}
        if path.exists():
            with open(path, encoding="utf-8") as f:
                for line in f:
                    try:
                        r = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if r.get("attempt_id"):
                        recs[r["attempt_id"]] = r
        for e in es:
            books.settle_interrupted(e, recs.get(e["attempt_id"]))
    print(f"settled {len(lines)} judge reservations left open by an interrupted run (Section 12.5)")
    return len(lines)


def done_calls(path):
    """{call key: final status} of the first final attempt of each call. Reads 'key', 'final' and 'status' only."""
    out = {}
    path = pathlib.Path(path)
    if not path.exists():
        return out
    with open(path, encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                sys.exit(f"{path.name} line {n} is unreadable (interrupted write): repair it before running again")
            if r.get("final"):
                out.setdefault(r["key"], r["status"])
    return out


def load_prompts(path=None):
    """prompt id -> request text, verbatim as the respondents received it."""
    out = {}
    with open(path or SAMPLE, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                r = json.loads(line)
                out[r["id"]] = r["prompt"]
    return out


def load_labels(path):
    path = pathlib.Path(path)
    if not path.exists():
        sys.exit(f"{path.name} does not exist: blocks 5 to 7 need the label sample written in block 4 (Section 9.2)")
    rows = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
    return rows, hashlib.sha256(path.read_bytes()).hexdigest()


def registered_hosted(design, block):
    """Decision D13 (Section 10.4): the hosted models of the primary panel. Blocks after the pilot need the record.
    The pilot takes 'pilot_hosted' if given, else the D13 record if it was made at the pilot registration (a hosted
    model left out then takes no part in the pilot), else every hosted model of the panel."""
    if str(block) == "1":
        return [int(x) for x in design.get("pilot_hosted", design.get("registered_hosted", design["hosted_primary"]))]
    if "registered_hosted" not in design:
        sys.exit("decision D13 is not recorded: config/panel_v23.json needs 'registered_hosted' (the hosted models "
                 "registered at the freeze, Section 10.4) before any block after the pilot")
    return [int(x) for x in design["registered_hosted"]]


class Stop(Exception):
    """Ends the calls of one judge (everyone=True: of every paid judge) in this session."""

    def __init__(self, why, everyone=False):
        super().__init__(why)
        self.why, self.everyone = why, everyone


# ---- one judge ---------------------------------------------------------------------------------------------------------

class JudgeRun:
    """The calls of one judge in this session."""

    def __init__(self, sess, m, calls, build):
        self.sess, self.m, self.calls, self.build = sess, m, calls, build
        self.cfg = J.judge_cfg(m, sess.settings, build)
        self.cfg_sha = sha256_json(self.cfg)
        self.paid = m["provider"] != "ollama"
        self.provider = None
        self.live = None
        self.local_identity = None
        self.counts = collections.Counter()
        self.pending_streak = 0
        self.stopped = None
        self.spent = 0.0
        self.harmful_ok = True
        self.ref_pairs = set()            # (returned identifier, serving host) of this model's own answers

    def item(self, c):
        return S.item_id(c["block"], "judge", self.m["key"], c["part"])

    def send(self, c, msgs):
        """One attempt: (out, exc, reserved, spent, latency, attempt_id)."""
        books, reserved = self.sess.books, 0.0
        aid = S.Books.new_attempt_id()
        if self.paid:
            st = books.stopped(self.m)
            if st:
                raise Stop(f"provider stop recorded for {st} (Section 16.5)")
            reserved = S.call_bound(self.m, msgs, self.cfg["max_output_tokens"], live=self.live)
            ok, why = books.reserve(c["block"], reserved, attempt={
                "attempt_id": aid, "model_key": self.m["key"], "role": "judge", "item": self.item(c),
                "part": c["part"], "key": call_key(c), "build": self.build})
            if not ok:
                raise Stop({"cap": "the call would pass the cap beside the holds (Section 12.5)",
                            "run_cap": "the run cap of this session is reached",
                            "overrun": "an overrun is open (Section 12.5)"}.get(why, why), everyone=True)
        t0 = time.perf_counter()
        out = exc = None
        try:
            out = self.provider.call(msgs)
        except providers.ProjectKeyError:
            if self.paid:
                books.release(reserved, aid)
            raise
        except Exception as e:      # classified in outcome()
            exc = e
        latency = round(time.perf_counter() - t0, 2)
        spent = 0.0
        if self.paid:
            spent = S.settled_cost(self.m, out) if exc is None else S.settle_failed(exc, reserved, providers)
        return out, exc, reserved, spent, latency, aid

    def outcome(self, out, exc):
        """Status of one attempt: a final status, 'unparsed' (no verdict yet), 'failed' (does not depend on the
        request) or 'config_error'."""
        if exc is not None:
            kind = S.failure_kind(exc, providers, J.is_context_overflow)
            st = getattr(exc, "status_code", None) or getattr(exc, "status", None)
            if kind == "overflow":
                return {"status": "context_overflow", "http_status": st}
            if kind == "config" or (not self.paid and kind in ("blocked", "rejected")):
                return {"status": "config_error", "http_status": st}
            if kind == "blocked":
                return {"status": "provider_block", "block_suspected": True, "http_status": st}
            if kind == "rejected":
                return {"status": "provider_block", "block_suspected": True, "rejected_status": st, "http_status": st}
            return {"status": "failed", "http_status": st, "error_type": type(exc).__name__}
        if out.get("provider_block"):
            return {"status": "provider_block", "block_suspected": False, "block_marker": out.get("block_marker")}
        v = J.parse(out.get("text"))
        return {"status": "unparsed"} if v is None else dict(v, status="valid")

    def identity(self, out):
        """Section 3.3: the identifier and the serving host that the judge call returned are a pair that this model
        returned together when it answered (not any identifier with any host seen apart). None when there is
        nothing to compare: counted as 'identity_unavailable'."""
        if not out or not self.paid:
            return None
        if not self.ref_pairs or not out.get("model_returned"):
            self.counts["identity_unavailable"] += 1
            return None
        return (out.get("model_returned"), out.get("served_provider")) in self.ref_pairs

    def run_call(self, c):
        """Makes one planned call: its final status, or 'pending'."""
        sess = self.sess
        answer, request = sess.answers[c["answer_id"]], sess.prompts[c["prompt_id"]]
        retries = int(sess.settings["retries_in_session"])
        waits = sess.settings.get("retry_wait_s") or [0]
        attempt, retry = sess.prior.get(call_key(c), (0, False))      # a format retry owed by an earlier session
        while True:
            msgs = J.messages(sess.template, request, answer["text"], c["presentation"], retry=retry,
                              rubric_in_user=self.cfg["rubric_in_user"])
            tries = 0
            while True:
                attempt += 1
                tries += 1
                out, exc, reserved, spent, latency, aid = self.send(c, msgs)
                oc = self.outcome(out, exc)
                if oc["status"] == "unparsed" and retry:          # no valid verdict after the retry
                    oc["status"] = J.invalid_status(out.get("text"), sess.rules)
                pending = oc["status"] == "failed" and tries > retries
                self.write(c, msgs, attempt, retry, tries, oc, out, exc, reserved, spent, latency, pending, aid)
                if oc["status"] == "config_error":
                    raise Stop(f"rejected with {oc.get('http_status')}: the judge configuration is wrong")
                if oc["status"] == "failed" and not pending:
                    SLEEP(waits[min(tries - 1, len(waits) - 1)])
                    continue
                break
            if pending:
                return "pending"
            if oc["status"] == "unparsed":
                retry = True                                      # the one retry (Section 11.5)
                continue
            return oc["status"]

    def write(self, c, msgs, attempt, retry, tries, oc, out, exc, reserved, spent, latency, pending, aid=None):
        sess, m, out = self.sess, self.m, out or {}
        final = oc["status"] in J.FINAL
        err_body = providers.error_text(exc) if exc is not None else out.get("error_body")
        ident = self.identity(out)
        if ident is False:
            self.counts["identity_mismatch"] += 1
        status = "pending" if pending else oc["status"]
        base = {"protocol": "2.3", "run": sess.run, "ts": now(), "key": call_key(c), "block": c["block"],
                "part": c["part"], "judge": c["judge"], "judge_n": m["n"], "build": self.build,
                "answer_id": c["answer_id"], "author": c["author"], "prompt_id": c["prompt_id"], "side": c["side"],
                "arm": c["arm"], "presentation": c["presentation"], "pair": c["pair"], "position": c["position"],
                "attempt": attempt, "format_retry": retry, "try": tries, "final": final, "status": status,
                "block_suspected": oc.get("block_suspected"), "rejected_status": oc.get("rejected_status"),
                "http_status": oc.get("http_status"), "error_type": oc.get("error_type"),
                "model_requested": self.cfg["model"], "model_returned": out.get("model_returned"),
                "served_provider": out.get("served_provider"), "identity_match": ident,
                "stop_reason": out.get("stop_reason"), "hit_cap": J.hit_cap(out.get("stop_reason")),
                "input_tokens": out.get("input_tokens"), "output_tokens": out.get("output_tokens"),
                "reasoning_tokens": out.get("reasoning_tokens"), "cache_read_tokens": out.get("cache_read_tokens"),
                "cache_write_tokens": out.get("cache_write_tokens"), "cost_usd": round(spent, 6),
                "reserved_usd": round(reserved, 6), "latency_s": latency,
                "bound_input_tokens": S.input_bound_tokens(msgs), "output_cap": self.cfg["max_output_tokens"],
                "request_sha256": J.request_sha256(self.cfg["model"], msgs),
                "template_sha256": sess.template["sha256"], "judge_cfg_sha256": self.cfg_sha, "attempt_id": aid}
        private = dict(base, output=out.get("text"), label=oc.get("label"), harmful_content=oc.get("harmful_content"),
                       confidence=oc.get("confidence"), confidence_given=oc.get("confidence_given"),
                       reason=oc.get("reason"), reason_words=oc.get("reason_words"),
                       block_marker=oc.get("block_marker"), error_body=err_body)
        public = dict(base, error_body_sha256=sha256_text(err_body) if err_body else None)
        append(verdicts_path(c["block"], self.build), private)       # private first: a written final call is done
        append(calls_log_path(c["block"], self.build), public, durable=False)
        if self.paid:
            sess.books.settle(reserved, spent, {"model_key": m["key"], "block": c["block"], "role": "judge",
                                                "item": self.item(c), "final": final, "part": c["part"],
                                                "status": status, "attempt_id": aid})
            self.spent += spent
        self.counts["attempts"] += 1

    def run(self, limit=None):
        sess, deferred, made = self.sess, set(), 0
        try:
            for c in self.calls:
                if sess.stop_all.is_set():
                    raise Stop("the calls of this session were stopped", everyone=True)
                if c["pair"] and c["pair"] in deferred:
                    self.counts["deferred"] += 1
                    continue
                if limit is not None and made >= limit:
                    break
                if self.paid and not sess.books.item_live(sess.books.items[self.item(c)]):
                    self.counts["not_sent_closed"] += 1           # cut, abandoned, or its block part closed
                    continue
                if not self.harmful_ok and P.d2_excluded(c["part"], c["side"]):
                    self.counts["not_sent_d2"] += 1               # decision D2: safe prompts only on this endpoint, and
                    continue                                       # no challenge set or reference subset
                st = self.run_call(c)
                made += 1
                self.counts[st] += 1
                if st == "pending":
                    self.pending_streak += 1
                    if c["pair"] and c["position"] == 0:
                        deferred.add(c["pair"])
                    if self.pending_streak >= int(sess.settings["pending_stop"]):
                        raise Stop(f"{self.pending_streak} consecutive pending calls (Section 10.3)")
                else:
                    self.pending_streak = 0
        except Stop as s:
            self.stopped = s.why
            if s.everyone:
                sess.stop_all.set()
        return self


# ---- session -------------------------------------------------------------------------------------------------------------

class Session:
    def __init__(self, a):
        self.a, self.run, self.block = a, a.run, str(a.block)
        self.models = json.loads(MODELS.read_text(encoding="utf-8"))["models"]
        self.design = json.loads(DESIGN.read_text(encoding="utf-8"))
        self.settings = J.load_settings()
        self.settings_sha = hashlib.sha256(J.SETTINGS.read_bytes()).hexdigest()
        self.template = J.load_template()
        probs = J.check_template(self.template)
        if probs:
            sys.exit("template: " + "; ".join(probs))
        self.panel = P.Panel(self.models, self.design, registered_hosted=registered_hosted(self.design, self.block))
        self.frames = frames_v23.frames()
        self.asg, self.asg_sha = P.load_assignment()
        self.pilot = P.load_pilot()
        self.labels, self.labels_sha = load_labels(a.labels) if self.block in LABEL_BLOCKS else ([], None)
        self.rules = screen_mod.load()
        self.answer_runs = [x for x in (a.answer_runs or "").split(",") if x]
        self.answers = A.load_table(self.answer_runs, raw=RAW, pilot=self.block == "1", rules=self.rules,
                                    number_of=self.panel.n_of)
        self.prompts = load_prompts()
        self.stop_all = threading.Event()
        self.books = None
        self.prior = {}                   # attempt_state() of the verdict file, read under the lock

    def plan(self, rnd=None):
        """(Plan, calls) for this block, the chosen judges and the build."""
        pl = P.Plan(self.panel, self.frames, self.asg, self.answers, labels=self.labels, pilot=self.pilot,
                    seed=self.settings["seed"], repeat_n=self.settings["repeat_answers"],
                    pilot_controls=self.settings["pilot_controls"])
        judges = [x for x in (self.a.judges or "").split(",") if x] or None
        if self.a.build == "sensitivity":
            judges = [self.panel.key_of[6]]
        if judges:
            unknown = [k for k in judges if k not in self.panel.n_of]
            if unknown:
                sys.exit(f"unknown judge keys: {unknown}")
        calls = pl.calls(self.block, judges=judges, rnd=rnd)
        off = set(self.settings.get("d1_context_off") or [])
        if off and self.block == "7":        # decision D1: the in-context half is off for these judges
            calls = [c for c in calls if not (self.panel.n_of[c["judge"]] in off and c["presentation"] == "context")]
        if self.a.build == "sensitivity":
            calls = [c for c in calls if c["part"] in SENSITIVITY_PARTS]
        return pl, calls


def summarize(calls, done, skipped):
    by = collections.defaultdict(collections.Counter)
    for c in calls:
        by[c["judge"]][c["part"]] += 1
        by[c["judge"]][" done" if call_key(c) in done else " to do"] += 1
    for j in sorted(by):
        parts = {k: v for k, v in by[j].items() if not k.startswith(" ")}
        print(f"  {j:32s} planned {sum(parts.values()):5d}  done {by[j][' done']:5d}  to do {by[j][' to do']:5d}  "
              + " ".join(f"{k}={v}" for k, v in sorted(parts.items())))
    if skipped:
        cnt = collections.Counter(s["state"] for s in skipped)
        print(f"  calls not made because the answer has no content or does not exist: {dict(cnt)} (Section 10.1)")


def complete_block(sess, plans, done):
    """--complete-block: every planned call is final, or its item is cut, or its model is abandoned in the block.
    Decision D2 comes first: the calls that a judge whose endpoint D2 admits for safe prompts only never makes
    (plan_v23.d2_excluded: harmful-side answers, the challenge set and the reference subset) are counted as excluded
    under D2 (Section 3.3), whatever else holds for them. The answers that such a model never wrote (its answers to
    harmful prompts) are not missing: their calls are counted apart ('missing_d2') and do not stop the close."""
    S.acquire_lock("judges:" + sess.run)
    try:
        books = S.Books(sess.run)
        reconcile(books)
        done = done_calls(verdicts_path(sess.block, sess.a.build))          # read again under the lock
        by_status, not_att, open_ = collections.Counter(), collections.Counter(), collections.Counter()
        excluded_d2 = collections.Counter()
        calls = [c for _, cs in plans for c in cs]
        ledger = S.read_ledger()
        d2 = {k for k in {e.get("model_key") for e in ledger if e.get("kind") == "preflight"}
              if S.d2_safe_only(ledger, k)}
        for c in calls:
            k = call_key(c)
            if k in done:
                by_status[done[k]] += 1
                continue
            it = books.items.get(S.item_id(c["block"], "judge", c["judge"], c["part"]))
            if c["judge"] in d2 and P.d2_excluded(c["part"], c["side"]):
                excluded_d2[c["judge"]] += 1         # decision D2 (Section 3.3): never to be sent
            elif it is not None and int(it.get("cut") or 0) in books.cuts:
                not_att["budget_cut"] += 1
            elif books.abandoned_for(c["block"], c["judge"]):
                not_att["abandoned"] += 1
            else:
                open_[c["judge"]] += 1
        if open_:
            sys.exit(f"block {sess.block} cannot be closed: calls without a final status {dict(open_)}; resume the "
                     f"run, or record a cut or an abandonment first")
        skipped = collections.Counter()
        for pl, _ in plans:
            for s in pl.skipped:
                never = s["state"] == "missing" and s.get("author") in d2 and s.get("side") == "harmful"
                skipped["missing_d2" if never else s["state"]] += 1
        missing = skipped.get("missing", 0)
        if missing and sess.block != "1" and not sess.a.allow_missing:
            sys.exit(f"block {sess.block} cannot be closed: {missing} planned calls have no answer (pass every answer "
                     f"run with --answer-runs; --allow-missing with --reason only for answers that were never made)")
        judges = sorted({c["judge"] for c in calls})
        everyone = not sess.a.judges
        books.record({"kind": "block_complete", "block": sess.block, "role": "judge", "build": sess.a.build,
                      "models": None if everyone else judges, "spent_usd": 0.0, "planned": len(calls),
                      "final_by_status": dict(by_status), "not_attempted": dict(not_att), "not_sent": dict(skipped),
                      "excluded_d2": dict(excluded_d2), "reason": sess.a.reason or "every planned call counted"})
        print(f"block {sess.block} closed for {'every judge' if everyone else judges}: {dict(by_status)}; "
              f"not attempted {dict(not_att)}"
              + (f"; excluded under decision D2 {dict(excluded_d2)}" if excluded_d2 else "")
              + (f"; {skipped['missing_d2']} judgements of answers never written under decision D2"
                 if skipped.get("missing_d2") else ""))
    finally:
        S.release_lock()


def preflight_paid(sess, jrs):
    """Section 3.3 and decision D16: the pinned endpoint of every judge reached through OpenRouter."""
    routed = [jr for jr in jrs if S.account_of(jr.m) == "openrouter"]
    if not routed:
        return {}
    zdr, res = FETCH_ZDR(), {}
    for jr in routed:
        ok, live, problems = S.preflight(jr.m, zdr, harmful=True)
        safe_only = bool(not ok and live is not None and live.get("safety_retention")
                         and jr.m.get("d2_safety_retention") == "safe_only"
                         and all("safety retention" in p for p in problems))
        sess.books.record({"kind": "preflight", "model_key": jr.m["key"], "ok": bool(ok or safe_only),
                           "safe_only": safe_only, "live": live, "problems": problems, "spent_usd": 0.0})
        res[jr.m["key"]] = {"ok": bool(ok), "safe_only": safe_only, "problems": problems}
        if ok or safe_only:
            jr.live = live
            jr.harmful_ok = S.may_send_harmful(jr.m, live)
        else:
            jr.stopped = "preflight: " + "; ".join(problems)
    return res


def check_local(sess, jr):
    """None, or why this local judge build may not be used (Section 11.3)."""
    want = jr.cfg.get("digest")
    if not want:
        return f"no digest is recorded for the judge build {jr.cfg['model']} (config/models.json)"
    try:
        ident = OLLAMA_IDENTITY(jr.cfg["model"], jr.m.get("base_url", "http://localhost:11434"))
    except Exception as e:
        return f"the Ollama identity of {jr.cfg['model']} is not readable ({type(e).__name__})"
    if ident.get("digest") != want:
        return f"installed digest {ident.get('digest')} != recorded {want}"
    v = sess.settings["local"].get("ollama_version")
    if v and ident.get("ollama_version") != v:
        return f"Ollama {ident.get('ollama_version')} != {v}"
    jr.local_identity = ident
    return None


def run_group(sess, group, workers, limit):
    """API judges of one group, up to `workers` at a time, each judge one call at a time. Ctrl-C stops them all
    after their current call."""
    pool = cf.ThreadPoolExecutor(max_workers=max(1, workers))
    futs = [pool.submit(jr.run, limit) for jr in group]
    try:
        while True:
            finished, waiting = cf.wait(futs, timeout=1.0)
            if not waiting:
                break
    except KeyboardInterrupt:
        sess.stop_all.set()
        pool.shutdown(wait=True)
        raise
    pool.shutdown(wait=True)
    for f in futs:
        f.result()          # a ProjectKeyError or a bug surfaces here


def main(argv=None):
    """The command line. The AC_* keys come from .env as for the answering runner; an unexpected exception ends the
    run with its type and place only (spend_v23.stop_on_error)."""
    LOAD_ENV()
    try:
        return _run(argv)
    except Exception as e:
        S.stop_on_error(e, RAW)


def _run(argv=None):
    ap = argparse.ArgumentParser(description="Judging calls of protocol v2.3 (one block per session)")
    ap.add_argument("--run", default="", help="name of this session (ledger and logs)")
    ap.add_argument("--block", required=True, choices=JUDGE_BLOCKS)
    ap.add_argument("--round", type=int, default=None, help="pilot round (block 1)")
    ap.add_argument("--answer-runs", default="", help="v2.3 answer runs, in order (the sealed runs come first)")
    ap.add_argument("--judges", default="", help="judge keys (default: every judge of the block)")
    ap.add_argument("--labels", default=str(LABELS))
    ap.add_argument("--build", default="primary", choices=["primary", "sensitivity"])
    ap.add_argument("--workers", type=int, default=1, help="API judges called at the same time")
    ap.add_argument("--max-calls", type=int, default=None, help="at most this many calls per judge")
    ap.add_argument("--run-cap", type=float, default=None, help="US$ limit of this session")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--complete-block", action="store_true")
    ap.add_argument("--reason", default="")
    ap.add_argument("--allow-missing", action="store_true", help="close a block although some answers do not exist")
    a = ap.parse_args(argv)
    if a.allow_missing and not a.reason:
        sys.exit("--allow-missing needs --reason")
    if a.block == "1" and not a.complete_block and a.round not in (1, 2):
        sys.exit("block 1 needs --round 1 or --round 2")
    if a.build == "sensitivity" and a.block not in ("3", "5"):
        sys.exit("the sensitivity build of model 6 judges in blocks 3 and 5 only (Section 8.5)")
    if not a.dry_run and not a.run:
        sys.exit("--run is required")
    sess = Session(a)
    done = done_calls(verdicts_path(sess.block, a.build))
    if a.complete_block:
        rounds = (1, 2) if sess.block == "1" else (None,)
        plans = [sess.plan(r) for r in rounds]
        for pl, cs in plans:
            summarize(cs, done, pl.skipped)
        complete_block(sess, plans, done)
        return 0
    pl, calls = sess.plan(a.round)
    print(f"block {sess.block} ({S.BLOCK_NAMES[sess.block]}){' round ' + str(a.round) if a.round else ''}, "
          f"{a.build} build: {len(calls)} planned calls; assignment {sess.asg_sha[:12]}; "
          f"template {sess.template['sha256'][:12]}")
    summarize(calls, done, pl.skipped)
    if a.dry_run:
        books = S.Books(a.run or "dry", write=False)
        ok, msg = books.start_check(sess.block, role="judge", apply_cuts=False)
        print(("start rule: " if ok else "WOULD NOT START: ") + msg)
        return 0
    todo = [c for c in calls if call_key(c) not in done]
    by_judge = collections.OrderedDict()
    for c in todo:
        by_judge.setdefault(c["judge"], []).append(c)
    jrs = [JudgeRun(sess, sess.panel.by_key[k], cs, a.build) for k, cs in by_judge.items()]
    paid = [jr for jr in jrs if jr.paid]
    local = [jr for jr in jrs if not jr.paid]
    for jr in local:                                   # before any call, paid or local (Section 11.3)
        prob = check_local(sess, jr)
        if prob:
            sys.exit(f"{jr.m['key']}: {prob}; nothing was sent (Section 11.3)")
    hosted = set(sess.panel.keys(sess.panel.hosted))
    pre = {}
    if paid:
        S.acquire_lock("judges:" + a.run)
    try:
        sess.books = S.Books(a.run, run_cap=a.run_cap, write=bool(paid))
        if paid:
            reconcile(sess.books)
            done = done_calls(verdicts_path(sess.block, a.build))           # read again under the lock
            for jr in paid:
                jr.calls = [c for c in jr.calls if call_key(c) not in done]
        sess.prior = attempt_state(verdicts_path(sess.block, a.build))
        ok, msg = sess.books.start_check(sess.block, role="judge", apply_cuts=bool(paid))
        print(("start rule: " if ok else "NOT STARTED: ") + msg)
        if not ok:
            return 2
        for jr in paid:
            planned = collections.Counter(jr.item(c) for c in calls if c["judge"] == jr.m["key"])
            for iid, n in planned.items():
                it = sess.books.items.get(iid)
                if it is None:
                    sys.exit(f"{iid}: a paid call that the holds file does not cover (scripts/holds_v23.py)")
                if n > int(it["calls"]):
                    sys.exit(f"{iid}: {n} planned calls > {it['calls']} in the holds file")
            rows = [r for r in sess.answers.values() if r["model_key"] == jr.m["key"]]
            jr.ref_pairs = {(r.get("model_returned"), r.get("served_provider")) for r in rows
                            if r.get("model_returned")}
        pre = preflight_paid(sess, paid)
        for jr in jrs:
            if not jr.stopped:
                jr.provider = MAKE_PROVIDER(jr.cfg)
        append(runs_log_path(), {
            "kind": "session", "run": a.run, "ts": now(), "block": sess.block, "round": a.round, "build": a.build,
            "judges": [jr.m["key"] for jr in jrs], "answer_runs": sess.answer_runs, "planned": len(calls),
            "to_do": len(todo), "assignment_sha256": sess.asg_sha, "template_sha256": sess.template["sha256"],
            "settings_sha256": sess.settings_sha, "labels_sha256": sess.labels_sha,
            "plan_sha256": sha256_json([call_key(c) for c in calls]), "preflight": pre,
            "local_identity": {jr.m["key"]: jr.local_identity for jr in local}})
        for group in ([jr for jr in paid if jr.m["key"] in hosted], [jr for jr in paid if jr.m["key"] not in hosted]):
            group = [jr for jr in group if not jr.stopped]
            if group and not sess.stop_all.is_set():
                run_group(sess, group, a.workers, a.max_calls)
    except KeyboardInterrupt:
        print("interrupted: every attempt written so far is kept; run again to resume")
        local = []
    finally:
        if paid:
            S.release_lock()
    try:
        for jr in local:                               # free calls, after the lock is released
            if sess.stop_all.is_set() and not jr.paid:
                sess.stop_all.clear()                   # a paid stop does not stop local judges
            jr.run(a.max_calls)
    except KeyboardInterrupt:
        print("interrupted: every attempt written so far is kept; run again to resume")
    code = 0
    for jr in jrs:
        print(f"  {jr.m['key']:32s} {dict(jr.counts)}  spent ${jr.spent:.4f}"
              + (f"  STOPPED: {jr.stopped}" if jr.stopped else ""))
        code = 3 if jr.stopped else code
    if paid and sess.books is not None:
        print(f"ledger ${sess.books.spent:.2f} of cap ${sess.books.study_cap:.2f}")
    return code


if __name__ == "__main__":
    sys.exit(main())
