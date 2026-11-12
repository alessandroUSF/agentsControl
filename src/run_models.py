"""Answering runner of protocol v2.3 (Sections 3.3, 3.4, 5, 10.1, 10.3, 10.4, 12.3 to 12.5, 13.2 and 16.5): sends the
planned respondent calls of one block, under the spending rules of src/spend_v23.py.

What is sent (src/plan_v23.respondent_plan; --models keeps some respondents of the block):
  block 1  pilot round r (--round r): each local model answers the round's 100 prompts, each hosted and commercial
           model the round's 20 'api' prompts. Hosted models: 'pilot_hosted' of config/panel_v23.json, else
           'hosted_primary'
  block 2  the primary panel, with the hosted models registered at the freeze (decision D13, 'registered_hosted'):
           the harmful frame (300) and the safe frame (90). Models 22 and 23 first, then the local models
  block 4  the eleven commercial models: the common set (60) and the safe frame (90)
Only answers that do not exist yet are generated. An answer exists when answers_v23.canonical keeps a record of its
(model, prompt) pair among the sealed runs used by v2.3 ('full' and 'v22_local', never 'pilot_local') and the v2.3
runs: a record without a transport error, or a final rejection (final_error). Pilot records count for block 1 only;
the records of the sealed runs count for both, so that their tail answers are pilot answers (Section 5.3). The
runner keeps identifiers, flags and statuses of the records and drops their text as each line is parsed; it
computes no screen. The answer files of results/raw are read only after the pilot registration (answers_v23.guard).
The v2.3 runs are the runs of the sessions listed in results/logs/respondent_runs_v23.jsonl, then --answer-runs,
then this run.

Outcome of one prompt (Section 10.1; spend_v23.failure_kind). Each prompt is sent once and verbatim:
  ok, truncated, empty, truncated_empty  the answer as delivered: final
  provider_block            a moderation rejection or a native block of the provider: final, never retried
  provider_block_suspected  a 400/403 that matched no moderation marker and no parameter error ('blocked'): final, on
                            harmful and on safe prompts alike (the v2.2 runner sent it again on safe prompts)
  error, final_error true   the request does not fit the context ('overflow'), or the provider rejected it for another
                            reason ('rejected'): final, never retried, never shortened
  pending                   a failure that does not depend on the request ('transient': authentication, quota, model
                            not found, rate limit, time-out, server error, connection loss), tried again up to
                            retries_in_session (3) times in the session, then left without a final record: the next
                            session tries it again. After pending_stop (5) consecutive pending prompts the model stops
                            for the session (both settings in config/judge_v23.json, shared with the judging runner)
  model stopped             a 400/422 that names a parameter ('config'), or any rejection by the local Ollama server
                            other than an overflow: the configuration is wrong
Every attempt is one record; the record that ends a prompt has final true.

Money (Section 12.5, src/spend_v23.py). A session with paid calls takes the spend lock (results/logs/spend.lock) before
it reads the ledger and keeps it until its last paid call; a session of local models only reads the ledger. Before
any call: the pilot registration (Section 13.1), Books.start_check(block, role='respondent') (freeze, order of the
blocks, the start rule, the cuts before block 4), holds that cover every paid planned call, no batch unsettled for
more than 48 h, and the endpoint preflight of every model reached through OpenRouter (ledger 'preflight' line). Every
paid attempt reserves spend_v23.call_bound(model, prompt, output cap, live endpoint prices) beside the holds of the
unfinished blocks of higher priority and the run cap; it settles at the larger of the list-price cost and the cost
that the provider reports, or, for a failure that may have been billed, at the reserved amount. Each paid attempt
writes one ledger 'call' line (model_key, block, role 'respondent', item, final, part, status, prompt_id) before its
record. A settlement above the reservation (overrun) stops every paid call. Calls of a model abandoned in the block,
of a closed block part or of a stopped provider (the account, or the serving host of a routed model) are not sent; an
endpoint that decision D2 admits for safe prompts only receives no harmful prompt.

Batch path (block 4, direct Anthropic and OpenAI models, --batch): one chunk per model and invocation, at most
BATCH_CHUNK requests at the batch price (BATCH_FACTOR of list, the price that config/stage_holds.json assumes for
them), shrunk to what fits beside the holds and the caps, never below BATCH_MIN_CHUNK. The chunk reserves the sum of
the bounds of its requests: a 'batch_reservation' ledger line (counted as spent until collected) and a pending entry
in the batch log, both written before the submission, so that a lost reply is never resubmitted; it is resolved with
--adopt or --release after a look at the provider console. At collection every result is settled against its own
bound (one 'call' line each) and one 'batch_settlement' line returns the reservation; a second collect of a settled
batch is refused and an interrupted collect can be repeated without duplicates. Deletion at the provider is a
separate, idempotent, logged step (--purge), tried after each collect. A batch still running 48 h after submission
is cancelled at collection, and an unsettled batch older than 48 h blocks new paid work. Without --batch, direct
models are skipped in block 4 unless --sync (recorded in the session line with --reason; the holds assume the batch
price for them); with --batch, models without a batch path are skipped. A model with an unsettled or pending batch
gets no other call. Pilots and block 2 are synchronous.

Identity (Section 3.3): before the first call, the digest of every local build (config/models.json 'digest') and the
Ollama version (config/judge_v23.json local.ollama_version: Ollama stays at it until local judging ends). Every record
keeps the requested and the returned model identifier, the serving provider, the pinned endpoint and whether they
match (identity_match). Before any batch, the pilot must show a returned identifier that starts with the configured
one.

Decision D13 (Section 10.4), --availability-check: run by the PI on the day of the freeze, before its ledger line
(it is refused after it). For each hosted model of the pilot ('pilot_hosted', else 'hosted_primary'; --models keeps
some): the endpoint preflight (ledger 'preflight' line, role 'availability'), then one fixed harmless prompt that is
not a benchmark prompt (AVAILABILITY_PROMPT), through the adapter and configuration of the respondent calls
(identifier, pinned endpoint and settings of Section 3.3; transient failures tried again as for respondents). Each
attempt reserves call_bound beside the holds of all unfinished work (the call belongs to no block) and the run cap,
settles like a respondent call and writes one ledger line of kind 'availability_call'. Printed and logged for each
model, with evidence: (1) decision D2 allows the harmful frame (preflight: the pinned endpoint is on the
zero-retention list, without safety retention unless D2 admits it for every prompt; receives_harmful true); (2) no
pilot call, as respondent or as judge, ended not_attempted (ledger: block 1 closed for both roles of the model, no
abandonment or cut behind a not_attempted count; not established while block 1 is open); (3) the test prompt was
answered (status ok or truncated, under the configured identifier and pinned endpoint). The decision is the PI's.

Files:
  results/raw/responses_<run>.jsonl      private: every attempt, with the answer text and the error body
  results/logs/calls_<run>.jsonl          public: the same without answer text and error body (their SHA-256 only)
  results/logs/manifest_<run>.jsonl       identity of each model at the start of a session
  results/logs/batches_<run>.jsonl        batch log: pending entries, submissions, settlements, deletions
  results/logs/respondent_runs_v23.jsonl  one line per session
  results/raw/availability_answers_v23.jsonl   private: the test calls of decision D13, with the answer text
  results/logs/availability_v23.jsonl          public: the same without text, and the three facts of each model
Nothing is printed from a prompt, an answer or an error body. Errors that stop a run are reported by type and place
only (AC_DEBUG=1 shows the message).

Usage (from the repository root; --dry-run sends nothing and writes nothing):
  python -I src/run_models.py --block 1 --round 1 --dry-run
  python -I src/run_models.py --run p1 --block 1 --round 1 [--models k1,k2] [--workers 4] [--run-cap 5]
  python -I src/run_models.py --run b2 --block 2
  python -I src/run_models.py --run b4 --block 4                    OpenRouter models, synchronous
  python -I src/run_models.py --run b4 --block 4 --batch            one chunk per direct model; again after collects
  python -I src/run_models.py --run b4 --collect BATCH_ID           then --purge BATCH_ID if the deletion failed
  python -I src/run_models.py --run b4 --adopt BATCH_ID --ref REF   a submission whose reply was lost
  python -I src/run_models.py --run b4 --release REF [--undeletable]
  python -I src/run_models.py --run c1 --block 1 --complete-block [--models k1,k2] [--reason TEXT]
  python -I src/run_models.py --run d13 --availability-check [--models k1,k2] [--run-cap 1]
A session with API models needs a run cap: --run-cap USD, or BUDGET_USD in .env. Sealed run names are refused.
"""
import argparse
import collections
import concurrent.futures as cf
import datetime as dt
import hashlib
import json
import os
import pathlib
import re
import sys
import threading
import time
import traceback

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import answers_v23 as A  # noqa: E402
import frames_v23  # noqa: E402
import judge_v23 as J  # noqa: E402
import plan_v23 as P  # noqa: E402
import providers  # noqa: E402
import spend_v23 as S  # noqa: E402
import subsets  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
SAMPLE = frames_v23.SAMPLE                                          # sealed benchmark sample (Section 4.1)
CONFIG = ROOT / "config" / "models.json"
DESIGN = ROOT / "config" / "panel_v23.json"
RAW = ROOT / "results" / "raw"
LOGS = ROOT / "results" / "logs"
RESPONDENT_BLOCKS = ("1", "2", "4")
SEALED_RUNS = {"full", "pilot_local", "v22_local"}   # written 7-9 Nov 2026; hashes in docs/SEALED_HASHES.md
BEHAVIOURAL = ("provider", "model", "base_url", "max_output_tokens", "effort", "temperature", "seed", "zdr",
               "allow_fallbacks", "provider_order", "num_ctx", "think", "options", "digest")   # allowlist (B3-m5)
TRUNCATION = {"length", "max_tokens", "incomplete:max_output_tokens"}
BATCH_FACTOR = 0.5            # Anthropic Message Batches and OpenAI Batch API: 50% of list (the price of the holds)
BATCH_POLL_S = 60
BATCH_CHUNK = 100             # requests per batch (A4-M3, B4-M2)
BATCH_MIN_CHUNK = 10          # a chunk shrinks to the headroom, never below this (B5-M2)
BATCH_PROVIDERS = ("anthropic", "openai")       # direct APIs with a batch path
BATCH_BLOCK = "4"             # the main run of the commercial models (Section 16.2: batch files)
BATCH_STALE_H = 48            # an unsettled batch older than this blocks new paid work
SAFE_ERROR = re.compile(r"^(batch:(\d{3}|batch_result:[a-z_]+|parse_error|None)|SuspectedBlock \d{3})$")
KEY_FIELDS = ("model_key", "model", "provider", "prompt_id", "pilot", "final", "final_error", "pending",
              "answer_status", "block", "round", "item", "batch_id", "mode", "model_returned", "served_provider",
              "protocol")     # what read_keys keeps of a record: never 'text' or 'error_body'

# Seams for the offline tests: provider factory, sleep, endpoint list, local identity and memory.
MAKE_PROVIDER = providers.make
SLEEP = time.sleep
FETCH_ZDR = S.fetch_zdr
OLLAMA_IDENTITY = providers.ollama_identity
OLLAMA_VRAM = providers.ollama_vram
_write_lock = threading.Lock()


# ---- small helpers ---------------------------------------------------------------------------------------------------

def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def public_error(err):
    """Error text for logs that may be published: exception type (or batch code) only, never a body that could
    quote the input (B5-m1). The raw record keeps the full text."""
    if not err:
        return err
    return err if SAFE_ERROR.match(err) else err.split(":", 1)[0][:80]


def error_label(e):
    status = getattr(e, "status_code", None)
    return type(e).__name__ + (f" {status}" if status is not None else "")


def load_env():
    """The AC_* keys and BUDGET_USD from .env (python-dotenv, when installed). A STUDY_BUDGET_USD there may only
    repeat the cap of decision D14: spend_v23.Books stops on any other value."""
    try:
        from dotenv import load_dotenv
        load_dotenv(ROOT / ".env")
    except ImportError:
        pass


def sha256_text(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def sha256_json(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def config_hash(m):
    return sha256_json({k: m[k] for k in BEHAVIOURAL if k in m})


def request_hash(m, prompt):
    return sha256_json({"model": m["model"], "messages": [{"role": "user", "content": prompt}]})


def answer_status(rec):
    """ok | truncated | truncated_empty | empty | provider_block | provider_block_suspected | error (Section 10.1).

    Truncation is checked before emptiness, so an answer whose reasoning used up the output cap is
    "truncated_empty", not "empty"."""
    if rec.get("provider_block_suspected"):
        return "provider_block_suspected"
    if rec.get("error"):
        return "error"
    if rec.get("provider_block"):
        return "provider_block"
    has_text = bool((rec.get("text") or "").strip())
    if str(rec.get("stop_reason")) in TRUNCATION:
        return "truncated" if has_text else "truncated_empty"
    if not has_text:
        return "empty"
    return "ok"


def read_jsonl(path, strict=False):
    """Read a JSONL file. A line cut short by an interrupted run is skipped with a warning. strict (the batch logs
    and the session log, B6-M3): an unreadable line stops the run instead, because skipping it would drop money or
    a pending submission from the books. (Also used by src/judge.py and src/gold_sample.py.)"""
    path = pathlib.Path(path)
    if not path.exists():
        return []
    rows = []
    with open(path, encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                if strict:
                    sys.exit(f"{path.name} line {n} is unreadable (interrupted write): repair it before any "
                             f"paid or bookkeeping run")
                print(f"warning: skipping unreadable line {n} of {path.name} (interrupted write)", file=sys.stderr)
    return rows


def end_with_newline(path):
    """After an interrupted write, start the next record on a fresh line."""
    path = pathlib.Path(path)
    if path.exists() and path.stat().st_size:
        with open(path, "rb") as f:
            f.seek(-1, os.SEEK_END)
            last = f.read(1)
        if last != b"\n":
            with open(path, "ab") as f:
                f.write(b"\n")


def append_jsonl(path, obj, durable=False):
    """Append one JSON line, always on a fresh line; durable lines (pending entries) are flushed to disk at once."""
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    end_with_newline(path)
    with open(path, "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(obj) + "\n")
        if durable:
            f.flush()
            os.fsync(f.fileno())


def append(path, obj, durable=False):
    with _write_lock:
        append_jsonl(path, obj, durable)


# ---- files -----------------------------------------------------------------------------------------------------------

def raw_path(run):
    return RAW / f"responses_{run}.jsonl"


def calls_log_path(run):
    return LOGS / f"calls_{run}.jsonl"


def manifest_path(run):
    return LOGS / f"manifest_{run}.jsonl"


def batch_log_path(run):
    return LOGS / f"batches_{run}.jsonl"


def runs_log_path():
    return LOGS / "respondent_runs_v23.jsonl"


def load_rows(path=None):
    """prompt id -> row of the sealed sample (id, source, expected, category, framing, prompt)."""
    out = {}
    with open(path or SAMPLE, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                r = json.loads(line)
                out[r["id"]] = r
    return out


def read_keys(path, run=None):
    """The records of an answer file without their text: the fields of KEY_FIELDS, the run, and 'error' as a flag
    (its message can quote the input). The text is dropped as each line is parsed; nothing of it is used."""
    out = []
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
                print(f"warning: skipping unreadable line {n} of {path.name} (interrupted write)", file=sys.stderr)
                continue
            k = {x: r.get(x) for x in KEY_FIELDS}
            k["run"] = r.get("run") or run
            k["error"] = bool(r.get("error"))
            out.append(k)
    return out


def session_runs():
    """Run names of the v2.3 respondent sessions, in the order of their first session."""
    names = []
    for e in read_jsonl(runs_log_path(), strict=True):
        if e.get("run") and e["run"] not in names:
            names.append(e["run"])
    return names


def v23_runs(extra=(), current=None):
    names = session_runs()
    for r in list(extra) + [current]:
        if r and r not in names:
            names.append(r)
    sealed = [r for r in names if r in SEALED_RUNS]
    if sealed:
        sys.exit(f"sealed runs {sealed} are not v2.3 runs (Section 3.4); the sealed runs used are read anyway")
    return names


def load_records(runs):
    """Key records (read_keys) of the sealed runs used by v2.3 and of the given v2.3 runs, in canonical order. The
    answer files of this repository are read only after the pilot registration (answers_v23.guard)."""
    A.guard(RAW)
    out = []
    for p in A.run_files(runs, raw=RAW):
        out += read_keys(p, p.name[len("responses_"):-len(".jsonl")])
    return out


# ---- plan ------------------------------------------------------------------------------------------------------------

def registered_hosted(design, block):
    """Decision D13 (Section 10.4), as in src/run_judges_v23.py: the hosted models of the primary panel. Block 1 takes
    'pilot_hosted' (every hosted model if absent); the blocks after the pilot need 'registered_hosted'."""
    if str(block) == "1":
        return [int(x) for x in design.get("pilot_hosted", design["hosted_primary"])]
    if "registered_hosted" not in design:
        sys.exit("decision D13 is not recorded: config/panel_v23.json needs 'registered_hosted' (the hosted models "
                 "registered at the freeze, Section 10.4) before any block after the pilot")
    return [int(x) for x in design["registered_hosted"]]


def part_of(block, rnd, row):
    """The part of the holds file (scripts/holds_v23.py): pilot_r<round> in block 1, else frame_harmful or
    frame_safe by the benchmark label of the prompt."""
    if str(block) == "1":
        return f"pilot_r{int(rnd)}"
    return "frame_harmful" if row["expected"] == "refuse" else "frame_safe"


def new_record(run, block, rnd, m, row, ident, mode="sync"):
    part = part_of(block, rnd, row)
    return {"protocol": "2.3", "run": run, "block": str(block), "round": rnd, "part": part,
            "item": S.item_id(block, "respondent", m["key"], part),
            "model_key": m["key"], "provider": m["provider"], "model": m["model"],
            "prompt_id": row["id"], "base_prompt_id": subsets.base_prompt_id(row),
            "cluster_id": subsets.cluster_id(row), "source": row["source"], "category": row["category"],
            "expected": row["expected"], "framing": row.get("framing", ""), "domain": row.get("domain", ""),
            "uso_indevido": row.get("uso_indevido", ""), "pair_group": row.get("pair_group", ""),
            "request_sha256": request_hash(m, row["prompt"]),
            "config_sha256": (ident or {}).get("config_sha256") or config_hash(m),
            "digest": (ident or {}).get("digest"), "endpoint": (m.get("pin") or {}).get("tag"),
            "mode": mode, "pilot": str(block) == "1", "ts": now()}


def write_record(rec):
    """The private record (answer text, error body), then the public line without them."""
    log = {k: v for k, v in rec.items() if k not in ("text", "error_body")}
    if rec.get("error_body"):
        log["error_body_sha256"] = sha256_text(str(rec["error_body"]))
    if rec.get("error"):
        log["error"] = public_error(rec["error"])
    with _write_lock:
        with open(raw_path(rec["run"]), "a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        with open(calls_log_path(rec["run"]), "a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(log, ensure_ascii=False) + "\n")


def identity_record(m, local=None, live=None):
    ident = {"model_key": m["key"], "model": m["model"], "provider": m["provider"], "config_sha256": config_hash(m),
             "ts": now()}
    if local:
        ident.update(local)
    if m.get("pin"):
        ident.update(endpoint=m["pin"].get("tag"), endpoint_provider=m["pin"].get("provider_name"), live=live)
    return ident


class Stop(Exception):
    """Ends the calls of one model (everyone=True: of every paid model) in this session."""

    def __init__(self, why, everyone=False):
        super().__init__(why)
        self.why, self.everyone = why, everyone


class Session:
    def __init__(self, a):
        self.a, self.run, self.block = a, a.run, str(a.block)
        self.models = json.loads(CONFIG.read_text(encoding="utf-8"))["models"]
        self.by_key = {m["key"]: m for m in self.models}
        self.design = json.loads(DESIGN.read_text(encoding="utf-8"))
        self.settings = J.load_settings()
        self.panel = P.Panel(self.models, self.design, registered_hosted=registered_hosted(self.design, self.block))
        self.frames = frames_v23.frames()
        self.pilot = P.load_pilot()
        self.rows = load_rows()
        self.runs = v23_runs([x for x in (a.answer_runs or "").split(",") if x], current=a.run or None)
        self.want = [x for x in (a.models or "").split(",") if x]
        unknown = [k for k in self.want if k not in self.by_key]
        if unknown:
            sys.exit(f"unknown model keys: {unknown}")
        self.books = None
        self.stop_all = threading.Event()

    def plan(self, rnd=None):
        """{model_key: [prompt ids]} of the block (and round) for the chosen models, in the order of the plan."""
        full = P.respondent_plan(self.block, self.panel, self.frames, self.pilot, rnd)
        if not self.want:
            return full
        outside = [k for k in self.want if k not in full]
        if outside:
            sys.exit(f"not respondents of block {self.block}: {outside}")
        return {k: v for k, v in full.items() if k in self.want}

    def item(self, key, pid, rnd):
        return S.item_id(self.block, "respondent", key, part_of(self.block, rnd, self.rows[pid]))


# ---- one model -------------------------------------------------------------------------------------------------------

class ModelRun:
    """The calls of one model in this session, one at a time."""

    def __init__(self, sess, m, todo, rnd):
        self.sess, self.m, self.todo, self.rnd = sess, m, todo, rnd
        self.key = m["key"]
        self.paid = m["provider"] != "ollama"
        self.routed = S.account_of(m) == "openrouter"
        self.batch = False
        self.batch_id = None
        self.provider = None
        self.live = None
        self.harmful_ok = True
        self.ident = None
        self.counts = collections.Counter()
        self.pending_streak = 0
        self.stopped = None
        self.skipped = None
        self.spent = 0.0
        self.vram_checked = False

    def item(self, pid):
        return self.sess.item(self.key, pid, self.rnd)

    def live_item(self, pid):
        """False when this model's part of the block is closed, the model is abandoned in the block, or its item is
        cut (respondent items never are)."""
        books, block = self.sess.books, self.sess.block
        if self.paid:
            return books.item_live(books.items[self.item(pid)])
        return not (books.closed(block, "respondent", self.key) or books.abandoned_for(block, self.key))

    def send(self, pid):
        """One attempt: (out, exc, reserved, spent, latency)."""
        books, reserved, prompt = self.sess.books, 0.0, self.sess.rows[pid]["prompt"]
        if self.paid:
            st = books.stopped(self.m)
            if st:
                raise Stop(f"provider stop recorded for {st} (Section 16.5)")
            reserved = S.call_bound(self.m, prompt, self.m["max_output_tokens"], live=self.live)
            ok, why = books.reserve(self.sess.block, reserved)
            if not ok:
                raise Stop({"cap": "the call would pass the cap beside the holds (Section 12.5)",
                            "run_cap": "the run cap of this session is reached",
                            "overrun": "an overrun is open (Section 12.5)"}.get(why, why), everyone=True)
        t0 = time.perf_counter()
        out = exc = None
        try:
            out = self.provider.call(prompt)
        except providers.ProjectKeyError:
            if self.paid:
                books.release(reserved)
            raise
        except Exception as e:      # classified in outcome()
            exc = e
        latency = round(time.perf_counter() - t0, 2)
        spent = 0.0
        if self.paid:
            spent = S.settled_cost(self.m, out) if exc is None else S.settle_failed(exc, reserved, providers)
        return out, exc, reserved, spent, latency

    def outcome(self, out, exc):
        """{'kind': final | transient | config, 'status': answer status, ...} of one attempt."""
        if exc is None:
            return {"kind": "final", "status": answer_status(out)}
        kind = S.failure_kind(exc, providers, J.is_context_overflow)
        http = getattr(exc, "status_code", None) or getattr(exc, "status", None)
        if not self.paid and kind in ("blocked", "rejected"):
            kind = "config"           # a rejection by the local Ollama server: the configuration is wrong
        if kind == "blocked":
            return {"kind": "final", "status": "provider_block_suspected", "failure_kind": kind, "http_status": http}
        if kind in ("overflow", "rejected"):
            return {"kind": "final", "status": "error", "final_error": True, "failure_kind": kind, "http_status": http}
        return {"kind": kind, "status": "error", "failure_kind": kind, "http_status": http}

    def identity(self, out):
        """Section 3.3: the returned identifier starts with the configured one and, through a router, the serving
        provider is the pinned endpoint's. None when nothing was returned to compare."""
        if not out or not self.paid or not out.get("model_returned"):
            return None
        ok = str(out["model_returned"]).startswith(self.m["model"])
        pin = (self.m.get("pin") or {}).get("provider_name")
        if self.routed and pin:
            ok = ok and out.get("served_provider") == pin
        return ok

    def run_prompt(self, pid):
        """Sends one prompt: its final answer status, or 'pending'."""
        retries = int(self.sess.settings["retries_in_session"])
        waits = self.sess.settings.get("retry_wait_s") or [0]
        tries = 0
        while True:
            tries += 1
            out, exc, reserved, spent, latency = self.send(pid)
            oc = self.outcome(out, exc)
            pending = oc["kind"] == "transient" and tries > retries
            self.write(pid, tries, oc, out, exc, reserved, spent, latency, pending)
            if oc["kind"] == "config":
                raise Stop(f"rejected with {oc.get('http_status')}: the configuration of the model is wrong "
                           f"(Section 10.3)")
            if oc["kind"] == "transient" and not pending:
                SLEEP(waits[min(tries - 1, len(waits) - 1)])
                continue
            return "pending" if pending else oc["status"]

    def write(self, pid, tries, oc, out, exc, reserved, spent, latency, pending):
        sess, m, row = self.sess, self.m, self.sess.rows[pid]
        rec = new_record(sess.run, sess.block, self.rnd, m, row, self.ident)
        rec.update({"model_returned": None, "served_provider": None}, **(out or {}))
        if exc is not None:
            body = providers.error_text(exc)
            if oc["status"] == "provider_block_suspected":
                rec.update(text="", provider_block_suspected=True, error=None,
                           stop_reason=f"suspected_block:{oc.get('http_status')}",
                           error_body=getattr(exc, "body", None) or body)
            else:
                rec.update(text=None, error=f"{error_label(exc)}: {str(exc)[:300]}", error_body=body)
        else:
            rec["error"] = None
        final = oc["kind"] == "final"
        ident = self.identity(out)
        if ident is False:
            self.counts["identity_mismatch"] += 1
        rec.update({"final": final, "final_error": bool(oc.get("final_error")), "pending": pending,
                    "failure_kind": oc.get("failure_kind"), "http_status": oc.get("http_status"), "try": tries,
                    "identity_match": ident, "cost_usd": round(spent, 6), "reserved_usd": round(reserved, 6),
                    "bound_input_tokens": S.input_bound_tokens(row["prompt"]),
                    "output_cap": m["max_output_tokens"], "latency_s": latency})
        rec["answer_status"] = answer_status(rec)
        status = ("pending" if pending else "failed" if oc["kind"] == "transient" else
                  "config_error" if oc["kind"] == "config" else rec["answer_status"])
        if self.paid:                     # the charge first, then the record (B6-m1)
            sess.books.settle(reserved, spent, {"model_key": m["key"], "block": sess.block, "role": "respondent",
                                                "item": self.item(pid), "final": final, "part": rec["part"],
                                                "status": status, "prompt_id": pid, "round": self.rnd})
            self.spent += spent
        write_record(rec)
        self.counts["attempts"] += 1
        if not self.paid and not self.vram_checked and final:
            self.vram_checked = True
            try:
                vram = OLLAMA_VRAM(m["model"], m.get("base_url", "http://localhost:11434"))
                append(manifest_path(sess.run), dict(self.ident or {}, event="vram_after_first_call", **vram))
            except Exception:
                pass

    def run(self, limit=None):
        sess, made = self.sess, 0
        try:
            for pid in self.todo:
                if self.paid and sess.stop_all.is_set():
                    raise Stop("the paid calls of this session were stopped", everyone=True)
                if limit is not None and made >= limit:
                    break
                row = sess.rows[pid]
                if not self.live_item(pid):
                    self.counts["not_sent_closed"] += 1           # abandoned, or its block part closed
                    continue
                if not self.harmful_ok and row["expected"] == "refuse":
                    self.counts["not_sent_d2"] += 1               # decision D2: safe prompts only on this endpoint
                    continue
                if not providers.allowed(self.m, row):
                    self.counts["not_sent_not_allowed"] += 1      # receives_harmful is not true in config/models.json
                    continue
                st = self.run_prompt(pid)
                made += 1
                self.counts[st] += 1
                if st == "pending":
                    self.pending_streak += 1
                    if self.pending_streak >= int(sess.settings["pending_stop"]):
                        raise Stop(f"{self.pending_streak} consecutive pending prompts (Section 10.3)")
                else:
                    self.pending_streak = 0
        except Stop as s:
            self.stopped = s.why
            if s.everyone:
                sess.stop_all.set()
        return self

    def go(self, limit=None):
        if not self.batch:
            return self.run(limit)
        try:
            bid, n = submit_batch(self.sess, self)
        except Stop as s:
            self.stopped = s.why
            if s.everyone:
                self.sess.stop_all.set()
            return self
        if bid is None:
            self.skipped = "not submitted: " + n
        else:
            self.batch_id = bid
            self.counts["submitted"] += n
        return self


# ---- batches ---------------------------------------------------------------------------------------------------------

class BatchItemError(Exception):
    """An errored batch item, classified with spend_v23.failure_kind like a synchronous failure."""

    def __init__(self, status, raw):
        super().__init__(raw or "")
        self.status_code, self.message = status, raw or ""


def batch_line(run, obj, durable=False):
    """obj may carry its own ts (an adopted batch keeps its submission time, B6-m5)."""
    append(batch_log_path(run), {"ts": now(), **obj}, durable)


def all_batch_entries():
    out = []
    for p in sorted(LOGS.glob("batches_*.jsonl")):
        out += read_jsonl(p, strict=True)
    return out


def settled_ids():
    ids = {e["settled"] for e in all_batch_entries() if e.get("settled")}
    led = S.read_ledger()
    ids |= {e["batch_id"] for e in led if e.get("kind") == "batch_settlement"}
    ids |= {e["ref"] for e in led if e.get("kind") == "batch_release"}
    return ids


def unresolved_pending():
    """Submissions written before submit whose outcome is unknown: no batch entry, no release (B5-M5)."""
    entries = all_batch_entries()
    resolved = {e.get("ref") for e in entries if e.get("batch_id")} | settled_ids()
    return [e for e in entries if e.get("pending_ref") and e["pending_ref"] not in resolved]


def unsettled_batches(model_key=None):
    done = settled_ids()
    out = [e["batch_id"] for e in all_batch_entries()
           if (model_key is None or e.get("model_key") == model_key) and e.get("batch_id")
           and e["batch_id"] not in done and e.get("ref") not in done]
    out += ["pending:" + e["pending_ref"] for e in unresolved_pending()
            if model_key is None or e.get("model_key") == model_key]
    return out


def age_hours(entry):
    return (dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(entry["ts"])).total_seconds() / 3600


def stale_batches():
    entries = all_batch_entries()
    by_id = {e["batch_id"]: e for e in entries if e.get("batch_id")}
    by_ref = {e["pending_ref"]: e for e in entries if e.get("pending_ref")}
    out = []
    for b in unsettled_batches():
        e = by_ref.get(b.split(":", 1)[1]) if b.startswith("pending:") else by_id.get(b)
        if e and age_hours(e) > BATCH_STALE_H:
            out.append(b)
    return out


def headroom(books, block):
    """US$ that a new reservation of this block may take: under the cap beside the holds, and under the run cap."""
    with books.lock:
        free = books.study_cap - books.spent - books.inflight - books.hold(block)
        if books.run_cap is not None:
            free = min(free, books.run_cap - books.run_spent - books.inflight)
    return free


def submit_batch(sess, mr):
    """One chunk of at most BATCH_CHUNK requests of this model: (batch_id, n) or (None, why). The chunk reserves the
    sum of the bounds of its requests before the submission (Section 12.5)."""
    m, books, block = mr.m, sess.books, sess.block
    busy = unsettled_batches(m["key"])
    if busy:
        if busy[0].startswith("pending:"):
            ref = busy[0].split(":", 1)[1]
            return None, (f"submission {ref} has an unknown outcome: check the provider console, then --adopt "
                          f"BATCH_ID --ref {ref} if a batch exists, or --release {ref} if none does")
        return None, f"unsettled batch {busy[0]}: collect it first"
    st = books.stopped(m)
    if st:
        raise Stop(f"provider stop recorded for {st} (Section 16.5)")
    todo = []
    for p in mr.todo:
        if not mr.live_item(p):
            mr.counts["not_sent_closed"] += 1
        elif not providers.allowed(m, sess.rows[p]):
            mr.counts["not_sent_not_allowed"] += 1
        else:
            todo.append(p)
    if not todo:
        return None, "nothing to send"
    cap = m["max_output_tokens"]
    bounds = [S.call_bound(m, sess.rows[p]["prompt"], cap, price_factor=BATCH_FACTOR) for p in todo[:BATCH_CHUNK]]
    free = headroom(books, block)
    n, reserve = 0, 0.0
    for w in bounds:
        if reserve + w > free + S.EPS:
            break
        n, reserve = n + 1, reserve + w
    need = min(BATCH_MIN_CHUNK, BATCH_CHUNK, len(todo))
    if n < need:
        return None, f"less than {need} requests fit beside the holds and the caps (${free:.2f} free)"
    todo, bounds = todo[:n], bounds[:n]
    ok, why = books.reserve(block, reserve)
    if not ok:
        return None, f"the chunk (${reserve:.2f} worst case) does not fit ({why})"
    ref = f"pending-{m['key']}-{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%f')}"
    stamp = ref.rsplit("-", 1)[1]                  # unique per submission: a wrong batch has unknown IDs (D8-m1)
    items = [(f"{stamp}_{i:05d}", sess.rows[p]["prompt"]) for i, p in enumerate(todo)]
    entry = {"ref": ref, "model_key": m["key"], "run": sess.run, "protocol": "2.3", "block": block,
             "reserved_usd": round(reserve, 6), "price_factor": BATCH_FACTOR, "output_cap": cap, "ident": mr.ident,
             "items": {cid: p for (cid, _), p in zip(items, todo)},
             "bounds": {cid: b for (cid, _), b in zip(items, bounds)}}
    books.record({"kind": "batch_reservation", "batch_id": ref, "model_key": m["key"], "block": block,
                  "role": "respondent", "requests": n, "spent_usd": round(reserve, 6)})
    with books.lock:                   # the reservation now stands in the ledger: counted as spent until collected
        books.inflight -= reserve
        books.run_spent += reserve
    pend = {k: v for k, v in entry.items() if k != "ref"}
    batch_line(sess.run, dict(pend, pending_ref=ref), durable=True)   # before submit: a lost reply is never resubmitted
    try:
        batch_id = mr.provider.batch_submit(items)
    except Exception as e:
        if S.settle_failed(e, reserve, providers) == 0.0:      # rejected before any batch existed: release it
            books.record({"kind": "batch_release", "ref": ref, "model_key": m["key"], "block": block,
                          "spent_usd": -round(reserve, 6), "error": error_label(e)})
            with books.lock:
                books.run_spent -= reserve
            batch_line(sess.run, {"released": ref})
            raise Stop(f"batch submission rejected ({error_label(e)}); its reservation was released")
        books.record({"kind": "batch_submit_unknown", "ref": ref, "model_key": m["key"], "block": block,
                      "spent_usd": 0.0, "error": error_label(e),
                      "uploaded_file_id": getattr(e, "uploaded_file_id", None)})
        raise Stop(f"batch submission failed ({error_label(e)}): outcome unknown, the reservation stays; check the "
                   f"provider console, then --adopt BATCH_ID --ref {ref} if a batch exists, or --release {ref}")
    batch_line(sess.run, dict(entry, batch_id=batch_id))
    return batch_id, n


def adopt_batch(run, batch_id, ref, by_key):
    """Link a pending submission (reply lost) to the batch that the provider console shows."""
    pend = next((e for e in unresolved_pending() if e["pending_ref"] == ref), None)
    if pend is None:
        sys.exit(f"no unresolved pending submission {ref}")
    if pend.get("run", run) != run:
        sys.exit(f"submission {ref} belongs to run {pend['run']}; pass --run {pend['run']}")
    if any(e.get("batch_id") == batch_id for e in all_batch_entries()):      # B6-m3
        sys.exit(f"batch {batch_id} is already linked to another submission; look for the lost one in the console")
    prov = MAKE_PROVIDER(by_key[pend["model_key"]])
    _, status = prov.batch_status(batch_id)                       # raises if the batch does not exist
    count = getattr(prov, "batch_request_count", lambda _id: None)(batch_id)
    if not count:                                                  # D8-m1: OpenAI reports 0 while validating
        sys.exit(f"batch {batch_id} reports no request count yet; retry --adopt when it shows one, or, if the "
                 f"console shows it failed or was cancelled before validation (nothing billed), --release {ref}")
    if count != len(pend["items"]):                                # C7-m5
        sys.exit(f"batch {batch_id} has {count} requests; submission {ref} listed {len(pend['items'])}: "
                 f"not the same batch")
    print(f"  batch {batch_id}: {status}; the submission listed {len(pend['items'])} requests")
    entry = {k: v for k, v in pend.items() if k != "pending_ref"}          # keeps the submission time
    batch_line(run, dict(entry, ref=ref, batch_id=batch_id, adopted=True))
    print(f"  submission {ref} adopted as batch {batch_id}; collect with --collect {batch_id}")


def release_pending(run, ref, by_key, undeletable_ok):
    """Release a pending submission that created no batch, or whose batch failed validation (the PI has checked the
    provider console)."""
    pend = next((e for e in unresolved_pending() if e["pending_ref"] == ref), None)
    if pend is None:
        sys.exit(f"no unresolved pending submission {ref}")
    if pend.get("run", run) != run:
        sys.exit(f"submission {ref} belongs to run {pend['run']}; pass --run {pend['run']}")
    fids = [e["uploaded_file_id"] for e in S.read_ledger()
            if e.get("kind") == "batch_submit_unknown" and e.get("ref") == ref and e.get("uploaded_file_id")]
    undeletable = []
    if fids:                                          # the input uploaded for a batch that was never created
        prov = MAKE_PROVIDER(by_key[pend["model_key"]])
        for fid in fids:
            try:
                prov.delete_upload(fid)
            except Exception as e:                    # the upload may hold prompts: keep trying (C7-M3)
                batch_line(run, {"release_failed": ref, "error": error_label(e)})
                if not undeletable_ok:
                    sys.exit(f"the uploaded input {fid} could not be deleted ({error_label(e)}); the reservation "
                             f"stays; retry --release {ref}, or add --undeletable after a console check")
                undeletable.append(fid)
                batch_line(run, {"undeletable_upload": fid, "ref": ref,
                                 "open_item": "uploaded input not deleted; delete it in the provider console and "
                                              "log the date"})
    books = S.Books(run)
    books.record({"kind": "batch_release", "ref": ref, "model_key": pend["model_key"], "block": pend.get("block"),
                  "spent_usd": -pend["reserved_usd"], "error": "released after a console check"})
    batch_line(run, {"released": ref, "uploads_deleted": [f for f in fids if f not in undeletable],
                     "uploads_undeletable": undeletable})
    print(f"  submission {ref} released (${pend['reserved_usd']:.2f})")


def purge_batch(batch_id, by_key, entry=None):
    """Delete a batch's files at the provider; idempotent and logged."""
    entries = all_batch_entries()
    entry = entry or next((e for e in entries if e.get("batch_id") == batch_id), None)
    if entry is None:
        sys.exit(f"batch {batch_id} is not in results/logs/batches_*.jsonl")
    if any(e.get("purged") == batch_id for e in entries):
        print(f"  batch {batch_id}: already deleted at the provider")
        return True
    if batch_id not in settled_ids():                 # results first, then deletion (B5-M5)
        sys.exit(f"batch {batch_id} is not settled yet: --collect {batch_id} first")
    run = entry.get("run")
    try:
        deleted = MAKE_PROVIDER(by_key[entry["model_key"]]).batch_delete(batch_id)
    except Exception as e:
        batch_line(run, {"purge_failed": batch_id, "error": error_label(e)})
        print(f"  batch {batch_id}: deletion failed ({type(e).__name__}); retry with --purge {batch_id}")
        return False
    batch_line(run, {"purged": batch_id, "deleted_at_provider": deleted})
    print(f"  batch {batch_id}: deleted at the provider {deleted}")
    return True


def collect_batch(run, batch_id, by_key, rows):
    """Settle every result of a batch against its own bound and return the chunk's reservation (Section 12.5)."""
    entries = all_batch_entries()
    entry = next((e for e in entries if e.get("batch_id") == batch_id), None)
    if entry is None:
        sys.exit(f"batch {batch_id} is not in results/logs/batches_*.jsonl")
    done_ids = settled_ids()
    if batch_id in done_ids or entry.get("ref") in done_ids:
        sys.exit(f"batch {batch_id} was already collected and settled; use --purge {batch_id} to delete it")
    if entry.get("run", run) != run:                  # records go to the batch's own run (B5-M5)
        sys.exit(f"batch {batch_id} belongs to run {entry['run']}; pass --run {entry['run']}")
    m = by_key[entry["model_key"]]
    books = S.Books(run)
    prov, ident = MAKE_PROVIDER(m), entry.get("ident") or {}
    block = str(entry.get("block") or BATCH_BLOCK)
    factor = float(entry.get("price_factor") or BATCH_FACTOR)
    cap = int(entry.get("output_cap") or m["max_output_tokens"])
    cancel_sent = any(e.get("cancel_requested") == batch_id for e in entries)
    while True:
        ended, status = prov.batch_status(batch_id)
        print(f"  batch {batch_id}: {status}")
        if ended:
            break
        if not cancel_sent and age_hours(entry) > BATCH_STALE_H:      # cancel, collect, delete
            prov.batch_cancel(batch_id)
            batch_line(run, {"cancel_requested": batch_id})
            cancel_sent = True
        SLEEP(BATCH_POLL_S)
    for p in (raw_path(run), calls_log_path(run)):
        end_with_newline(p)
    written = {x["prompt_id"] for x in read_keys(raw_path(run), run) if x.get("batch_id") == batch_id}
    charged = {e.get("prompt_id"): float(e.get("spent_usd") or 0.0) for e in S.read_ledger()
               if e.get("kind") == "call" and e.get("batch_id") == batch_id}
    bounds = entry.get("bounds") or {}

    def bound_of(cid):
        if cid in bounds:
            return float(bounds[cid])
        return S.call_bound(m, rows[entry["items"][cid]]["prompt"], cap, price_factor=factor)
    worst = max(bound_of(c) for c in entry["items"])
    total, unattributed_usd = 0.0, 0.0
    counts = collections.Counter({"final": 0, "pending": 0, "skipped_already_written": 0, "unreadable_lines": 0,
                                  "unattributed_lines": 0, "model_mismatch_lines": 0})
    for cid, out, err in prov.batch_results(batch_id):
        returned = (out or {}).get("model_returned")
        if cid is None and err == ("parse_error", "unreadable_line"):
            kind = "unreadable_lines"
        elif cid is None or cid not in entry["items"]:
            kind = "unattributed_lines"                  # no or unknown custom_id (D8-m1)
        elif returned and not str(returned).startswith(m["model"]):
            kind = "model_mismatch_lines"                # another model's answer (D8-m1): never recorded
        else:
            kind = None
        if kind:                     # may have been billed: charged once, at settlement, at the largest bound
            counts[kind] += 1
            unattributed_usd += worst
            continue
        row = rows[entry["items"][cid]]
        pid, bound = row["id"], bound_of(cid)
        if pid in written:                                # a collect interrupted earlier wrote it already
            counts["skipped_already_written"] += 1
            total += charged.get(pid, 0.0)
            continue
        rec = new_record(run, block, None, m, row, ident, mode="batch")
        rec.update(batch_id=batch_id, model_returned=None, served_provider=None)
        final, final_error, fkind, http, spent = True, False, None, None, 0.0
        if out is not None:
            rec.update(out)
            rec["error"] = None
            spent = S.settled_cost(m, out, price_factor=factor)
        elif err[0] == "parse_error":                    # answered and billed, but unreadable: its bound; sent again
            rec.update(text=None, error="batch:parse_error", error_body=str(err[1])[:2000])
            final, fkind, spent = False, "transient", bound
        else:                                            # errored, canceled and expired requests are not billed
            http, raw = err
            exc, block_rec = BatchItemError(http, raw), None
            if http and not J.is_context_overflow(providers.error_text(exc)):   # an overflow first, as failure_kind
                try:
                    block_rec = providers.classify_rejection(http, raw)
                except providers.SuspectedBlock as sb:
                    exc = sb
            if block_rec is not None:                    # moderation: final, never sent again (Section 10.1)
                rec.update(block_rec, served_provider=m["provider"], error=None)
            else:
                fkind = S.failure_kind(exc, providers, J.is_context_overflow)
                if fkind == "blocked":                   # final on harmful and safe prompts alike (Section 10.1)
                    rec.update(text="", provider_block_suspected=True, stop_reason=f"suspected_block:{http}",
                               error_body=(raw or "")[:2000], error=None)
                else:
                    rec.update(text=None, error=f"batch:{http if http is not None else raw}",
                               error_body=(raw or "")[:2000])
                    if fkind in ("overflow", "rejected"):
                        final_error = True
                    else:
                        final = False                    # transient: sent again in a later chunk; config: fix first
        rec.update({"final": final, "final_error": final_error, "pending": not final and fkind != "config",
                    "failure_kind": fkind,
                    "http_status": http, "identity_match": (str(returned).startswith(m["model"]) if returned
                                                            else None),
                    "cost_usd": round(spent, 6), "reserved_usd": round(bound, 6),
                    "bound_input_tokens": S.input_bound_tokens(row["prompt"]), "output_cap": cap,
                    "latency_s": None})
        rec["answer_status"] = answer_status(rec)
        status_line = rec["answer_status"] if final else ("config_error" if fkind == "config" else "pending")
        if pid not in charged:                            # the charge first, then the record (B6-m1)
            books.record({"kind": "call", "model_key": m["key"], "block": block, "role": "respondent",
                          "item": rec["item"], "final": final, "part": rec["part"], "status": status_line,
                          "prompt_id": pid, "batch_id": batch_id, "reserved_usd": round(bound, 6),
                          "spent_usd": round(spent, 6)})
            if spent > bound + 1e-9:
                books.record({"kind": "overrun", "model_key": m["key"], "block": block, "item": rec["item"],
                              "batch_id": batch_id, "reserved_usd": round(bound, 6), "settled_usd": round(spent, 6),
                              "spent_usd": 0.0})
        write_record(rec)
        total += spent
        counts["final" if final else "pending"] += 1
        if fkind == "config":
            counts["config_errors"] += 1
    total += unattributed_usd
    batch_errors = getattr(prov, "batch_errors", lambda _id: None)(batch_id)
    books.record({"kind": "batch_settlement", "batch_id": batch_id, "ref": entry.get("ref"), "model_key": m["key"],
                  "block": block, "role": "respondent",
                  "spent_usd": round(-entry["reserved_usd"] + unattributed_usd, 6),
                  "unreadable_lines": counts["unreadable_lines"], "unattributed_lines": counts["unattributed_lines"],
                  "model_mismatch_lines": counts["model_mismatch_lines"],
                  "unattributed_usd": round(unattributed_usd, 6)})
    if total > entry["reserved_usd"] + 1e-6:
        books.record({"kind": "overrun", "model_key": m["key"], "block": block, "batch_id": batch_id,
                      "reserved_usd": entry["reserved_usd"], "settled_usd": round(total, 6), "spent_usd": 0.0})
    if counts["model_mismatch_lines"]:
        print(f"  WARNING: {counts['model_mismatch_lines']} answers came from another model than {m['model']}; "
              f"they were charged and not recorded (check the adoption of {batch_id})")
    if counts["config_errors"]:
        print(f"  WARNING: {counts['config_errors']} requests were rejected for a parameter: fix the configuration "
              f"of {m['key']} before its next chunk (Section 10.3)")
    batch_line(run, {"settled": batch_id, "collected": batch_id, "spent_usd": round(total, 6), "counts": dict(counts),
                     "batch_errors_sha256": sha256_text(batch_errors) if batch_errors else None})
    if batch_errors:
        print(f"  batch-level errors reported by the provider (sha256 {sha256_text(batch_errors)[:12]}; text in "
              f"results/raw only)")
        append(RAW / f"batch_errors_{run}.jsonl", {"batch_id": batch_id, "errors": batch_errors})
    print(f"  collected {counts['final'] + counts['pending']} results (final {counts['final']}, pending "
          f"{counts['pending']}), ${total:.4f}")
    purge_batch(batch_id, by_key, entry)


def bookkeeping(a):
    """--collect, --purge, --adopt, --release: under the spend lock, no new request is sent."""
    run = a.run
    if not run:
        sys.exit("--run is required")
    if run in SEALED_RUNS:
        sys.exit(f"run '{run}' is sealed (docs/SEALED_HASHES.md)")
    by_key = {m["key"]: m for m in json.loads(CONFIG.read_text(encoding="utf-8"))["models"]}
    RAW.mkdir(parents=True, exist_ok=True)
    LOGS.mkdir(parents=True, exist_ok=True)
    S.acquire_lock("respondents:" + run)
    try:
        if a.collect:
            collect_batch(run, a.collect, by_key, load_rows())
        elif a.purge:
            purge_batch(a.purge, by_key)
        elif a.adopt:
            if not a.ref:
                sys.exit("--adopt needs --ref PENDING_REF")
            adopt_batch(run, a.adopt, a.ref, by_key)
        else:
            release_pending(run, a.release, by_key, a.undeletable)
    finally:
        S.release_lock()
    return 0


# ---- session ---------------------------------------------------------------------------------------------------------

def check_local(sess, mr):
    """None, or why this local build may not be used (Section 3.3): pinned digest and Ollama version."""
    m = mr.m
    want = m.get("digest")
    if not want:
        return f"no digest is recorded for {m['model']} (config/models.json)"
    try:
        ident = OLLAMA_IDENTITY(m["model"], m.get("base_url", "http://localhost:11434"))
    except Exception as e:
        return f"the Ollama identity of {m['model']} is not readable ({type(e).__name__})"
    if ident.get("digest") != want:
        return f"installed digest {ident.get('digest')} != pinned {want}"
    v = sess.settings["local"].get("ollama_version")
    if v and ident.get("ollama_version") != v:
        return f"Ollama {ident.get('ollama_version')} != {v} (the version pinned until local judging ends)"
    mr.ident = identity_record(m, local=ident)
    return None


def preflight_paid(sess, mrs):
    """Section 3.3 and decision D16: the pinned endpoint of every model reached through OpenRouter, before its first
    paid call. An endpoint marked for safety retention that D2 admits for safe prompts only gets no harmful prompt."""
    routed = [mr for mr in mrs if mr.routed and not mr.stopped]
    if not routed:
        return {}
    zdr, res = FETCH_ZDR(), {}
    for mr in routed:
        ok, live, problems = S.preflight(mr.m, zdr, harmful=True)
        safe_only = bool(not ok and live is not None and live.get("safety_retention")
                         and mr.m.get("d2_safety_retention") == "safe_only"
                         and all("safety retention" in p for p in problems))
        sess.books.record({"kind": "preflight", "model_key": mr.key, "role": "respondent", "block": sess.block,
                           "ok": bool(ok or safe_only), "safe_only": safe_only, "live": live, "problems": problems,
                           "spent_usd": 0.0})
        res[mr.key] = {"ok": bool(ok), "safe_only": safe_only, "problems": problems}
        if ok or safe_only:
            mr.live = live
            mr.harmful_ok = S.may_send_harmful(mr.m, live)
        else:
            mr.stopped = "preflight: " + "; ".join(problems)
    return res


def check_holds(sess, plan, rnd):
    """Every paid planned call has an item in the holds file, with at least as many calls (Section 12.5)."""
    for k, ids in plan.items():
        if sess.by_key[k]["provider"] == "ollama":
            continue
        planned = collections.Counter(sess.item(k, p, rnd) for p in ids)
        for iid, n in planned.items():
            it = sess.books.items.get(iid)
            if it is None:
                sys.exit(f"{iid}: a paid call that the holds file does not cover (scripts/holds_v23.py)")
            if n > int(it["calls"]):
                sys.exit(f"{iid}: {n} planned calls > {it['calls']} in the holds file")


def pilot_ids_problem(m, records):
    """E9-m1: the collect check needs the returned ID format, seen on the pilot of this model ID (F10-4)."""
    seen = {r.get("model_returned") for r in records if r.get("pilot") and not r.get("error")
            and r.get("model_key") == m["key"] and r.get("model") == m["model"]} - {None, ""}
    if not seen:
        return "no pilot answer shows a returned model ID; run its pilot (block 1) before any batch"
    bad = sorted(str(x) for x in seen if not str(x).startswith(m["model"]))
    if bad:
        return (f"the pilot returned model ID(s) {bad}, which do not start with '{m['model']}'; fix the configuration "
                f"under a logged decision before any batch")
    return None


def run_group(sess, group, workers, limit):
    """Paid models of one group, up to `workers` at a time, each model one call at a time. Ctrl-C stops them all
    after their current call."""
    pool = cf.ThreadPoolExecutor(max_workers=max(1, workers))
    futs = [pool.submit(mr.go, limit) for mr in group]
    try:
        while True:
            _, waiting = cf.wait(futs, timeout=1.0)
            if not waiting:
                break
    except KeyboardInterrupt:
        sess.stop_all.set()
        pool.shutdown(wait=True)
        raise
    pool.shutdown(wait=True)
    for f in futs:
        f.result()          # a ProjectKeyError or a bug surfaces here


def summarize(sess, plan, todo, rnd, known):
    for k, ids in plan.items():
        m = sess.by_key[k]
        parts = collections.Counter(part_of(sess.block, rnd, sess.rows[p]) for p in ids)
        worst = 0.0
        if m["provider"] != "ollama":
            factor = BATCH_FACTOR if (sess.a.batch and m["provider"] in BATCH_PROVIDERS) else 1.0
            worst = sum(S.call_bound(m, sess.rows[p]["prompt"], m["max_output_tokens"], price_factor=factor)
                        for p in todo[k])
        done = str(len(ids) - len(todo[k])) if known else "?"
        left = str(len(todo[k])) if known else "?"
        print(f"  {k:32s} planned {len(ids):4d}  done {done:>4s}  to do {left:>4s}  bounds ${worst:8.4f}  "
              + " ".join(f"{x}={n}" for x, n in sorted(parts.items())))


def run_block(sess):
    a, block = sess.a, sess.block
    rnd = a.round if block == "1" else None
    plan = sess.plan(rnd)
    try:
        records = load_records(sess.runs)
    except SystemExit as e:
        if not a.dry_run:
            raise
        print(f"{e}: the dry run shows the plan only")
        records = None
    done = A.canonical(records, pilot=block == "1") if records is not None else {}
    todo = {k: [p for p in ids if (k, p) not in done] for k, ids in plan.items()}
    print(f"block {block} ({S.BLOCK_NAMES[block]}){' round ' + str(rnd) if rnd else ''}: "
          f"{sum(len(v) for v in plan.values())} planned answers of {len(plan)} models; v2.3 runs read: "
          f"{sess.runs or 'none'}")
    summarize(sess, plan, todo, rnd, records is not None)
    if a.dry_run:
        books = S.Books(a.run or "dry", write=False)
        if not books.registration:
            print("WOULD NOT START: the pilot registration is not recorded (spend_v23.py register)")
        ok, msg = books.start_check(block, role="respondent", apply_cuts=False)
        print(("start rule: " if ok else "WOULD NOT START: ") + msg)
        return 0
    mrs = [ModelRun(sess, sess.by_key[k], todo[k], rnd) for k in plan if todo[k]]
    if not mrs:
        print("nothing to do: every planned answer exists")
        return 0
    sync_override = []
    for mr in mrs:
        direct = mr.m["provider"] in BATCH_PROVIDERS
        if a.batch:
            if direct:
                mr.batch = True
            else:
                mr.skipped = "no batch path (run it without --batch)"
        elif direct and block == BATCH_BLOCK:
            if a.sync:
                sync_override.append(mr.key)
            else:
                mr.skipped = "main runs of direct Anthropic and OpenAI models use --batch (or --sync under a decision)"
        if not mr.skipped and mr.paid and not mr.batch:
            busy = unsettled_batches(mr.key)
            if busy:                                      # B6-M2: its prompts may be answered in that batch
                mr.skipped = f"{busy[0]} is unsettled or pending; resolve it first"
    if sync_override:
        print(f"--sync: {sync_override} answer synchronously at the full price; the holds assume the batch price "
              f"for them (about half), reason: {a.reason or 'none given'}")
    active = [mr for mr in mrs if not mr.skipped]
    paid = [mr for mr in active if mr.paid]
    local = [mr for mr in active if not mr.paid]
    for mr in local:                                   # before any call, paid or local (Section 3.3)
        prob = check_local(sess, mr)
        if prob:
            sys.exit(f"{mr.key}: {prob}; nothing was sent (Section 3.3)")
    run_cap = a.run_cap if a.run_cap is not None else float(os.environ.get("BUDGET_USD") or 0) or None
    if paid and not (run_cap and run_cap > 0):
        sys.exit("a session with API models needs a run cap: --run-cap USD, or BUDGET_USD in .env")
    hosted = set(sess.panel.keys(sess.panel.hosted))
    pre = {}
    if paid:
        S.acquire_lock("respondents:" + sess.run)         # before the ledger is read (B5-m5)
    try:
        sess.books = S.Books(sess.run, run_cap=run_cap if paid else None, write=bool(paid))
        if not sess.books.registration:
            print("NOT STARTED: the pilot registration is not recorded (spend_v23.py register; Sections 13.1, 14)")
            return 2
        ok, msg = sess.books.start_check(block, role="respondent", apply_cuts=bool(paid))
        print(("start rule: " if ok else "NOT STARTED: ") + msg)
        if not ok:
            return 2
        check_holds(sess, plan, rnd)
        if paid:
            stale = stale_batches()
            if stale:
                sys.exit(f"batches unsettled for more than {BATCH_STALE_H} h: {stale}; collect them first")
            for mr in paid:
                if mr.batch:
                    prob = pilot_ids_problem(mr.m, records)
                    if prob:
                        sys.exit(f"{mr.key}: {prob}")
        pre = preflight_paid(sess, paid)
        RAW.mkdir(parents=True, exist_ok=True)
        LOGS.mkdir(parents=True, exist_ok=True)
        for p in (raw_path(sess.run), calls_log_path(sess.run)):
            end_with_newline(p)
        for mr in active:
            if mr.paid:
                mr.ident = identity_record(mr.m, live=mr.live)
            append(manifest_path(sess.run), dict(mr.ident, block=block, round=rnd, stopped=mr.stopped))
            if mr.stopped:
                continue
            try:
                mr.provider = MAKE_PROVIDER(mr.m)
            except providers.ProjectKeyError as e:
                mr.stopped = f"no project key ({type(e).__name__}); nothing was sent"
        append(runs_log_path(), {
            "kind": "session", "run": sess.run, "ts": now(), "protocol": "2.3", "block": block, "round": rnd,
            "models": [mr.key for mr in active], "skipped": {mr.key: mr.skipped for mr in mrs if mr.skipped},
            "batch": bool(a.batch), "sync_override": sync_override, "reason": a.reason or None,
            "answer_runs": sess.runs, "planned": sum(len(v) for v in plan.values()),
            "to_do": sum(len(mr.todo) for mr in active), "run_cap_usd": run_cap,
            "plan_sha256": sha256_json(sorted([k, p] for k, ids in plan.items() for p in ids)),
            "holds_sha256": hashlib.sha256(pathlib.Path(S.HOLDS).read_bytes()).hexdigest(),
            "settings": {k: sess.settings.get(k) for k in ("retries_in_session", "retry_wait_s", "pending_stop")},
            "preflight": pre, "local_identity": {mr.key: mr.ident for mr in local}}, durable=True)
        for group in ([mr for mr in paid if mr.key in hosted], [mr for mr in paid if mr.key not in hosted]):
            group = [mr for mr in group if not mr.stopped]
            if group and not sess.stop_all.is_set():
                run_group(sess, group, a.workers, a.max_calls)
    except KeyboardInterrupt:
        print("interrupted: every attempt written so far is kept; run again to resume")
        local = []
    finally:
        if paid:
            S.release_lock()
    try:
        for mr in local:                               # free calls, after the lock is released
            if not mr.stopped:
                mr.go(a.max_calls)
    except KeyboardInterrupt:
        print("interrupted: every attempt written so far is kept; run again to resume")
    code = 0
    for mr in mrs:
        line = f"  {mr.key:32s} {dict(mr.counts)}  spent ${mr.spent:.4f}"
        if mr.batch_id:
            line += (f"  submitted batch {mr.batch_id} ({mr.counts['submitted']} of {len(mr.todo)} requests): "
                     f"collect with --collect {mr.batch_id}, then run again for the next chunk")
        if mr.skipped:
            line += f"  SKIPPED: {mr.skipped}"
        if mr.stopped:
            line += f"  STOPPED: {mr.stopped}"
            code = 3
        print(line)
    if paid and sess.books is not None:
        print(f"ledger ${sess.books.spent:.2f} of cap ${sess.books.study_cap:.2f}")
    return code


# ---- closing a block -------------------------------------------------------------------------------------------------

def round_started(sess, records, ledger, rnd):
    """Block 1: a v2.3 run holds a pilot record of this round, or the ledger a paid respondent call of it."""
    r = sess.pilot["rounds"][int(rnd) - 1]
    ids = set(r["harmful"]) | set(r["safe"])
    if any(x.get("pilot") and x.get("run") not in A.SEALED_USED and x.get("prompt_id") in ids for x in records):
        return True
    tail = f"|pilot_r{int(rnd)}"
    return any(e.get("kind") == "call" and e.get("role") == "respondent" and str(e.get("item") or "").endswith(tail)
               for e in ledger)


def complete_block(sess):
    """--complete-block: every planned answer has a final record, or its model is abandoned in the block (spend_v23
    'block_abandon' line). The harmful prompts of a model whose endpoint decision D2 admits for safe prompts only
    were never sent: they are counted as excluded under D2 (Section 3.3), not as open. Block 1 counts both rounds,
    round 2 only if any of it was run. Writes 'block_complete' with role 'respondent' and the counts by status."""
    a, block = sess.a, sess.block
    records = load_records(sess.runs)
    done = A.canonical(records, pilot=block == "1")
    S.acquire_lock("respondents:" + (sess.run or "complete"))
    try:
        books = S.Books(sess.run or "complete")
        ledger = S.read_ledger()
        plans = []
        for rnd in ((1, 2) if block == "1" else (None,)):
            if rnd == 2 and not round_started(sess, records, ledger, 2):
                print("  round 2 was not run: block 1 is counted on round 1 (Section 13.3)")
                continue
            plans.append((rnd, sess.plan(rnd)))
        keys = sorted({k for _, plan in plans for k in plan})
        busy = [b for k in keys for b in unsettled_batches(k)]
        if busy:
            sys.exit(f"unsettled or pending batches {busy}: collect or resolve them before closing block {block}")
        by_status, not_att, open_ = collections.Counter(), collections.Counter(), collections.Counter()
        excluded_d2 = collections.Counter()
        planned = 0
        for rnd, plan in plans:
            for k, ids in plan.items():
                d2 = S.d2_safe_only(ledger, k)
                for p in ids:
                    planned += 1
                    rec = done.get((k, p))
                    it = books.items.get(sess.item(k, p, rnd))
                    if rec is not None:
                        by_status[A.status_of(rec)] += 1
                    elif d2 and sess.rows[p]["expected"] == "refuse":
                        excluded_d2[k] += 1                 # decision D2 (Section 3.3): never to be sent; counted first
                    elif it is not None and int(it.get("cut") or 0) in books.cuts:
                        not_att["budget_cut"] += 1          # no respondent item carries a cut today
                    elif books.abandoned_for(block, k):
                        not_att["abandoned"] += 1
                    else:
                        open_[k] += 1
        if open_:
            sys.exit(f"block {block} cannot be closed: planned answers without a final record {dict(open_)}; resume "
                     f"the run, or record an abandonment first (spend_v23.py abandon)")
        everyone = not sess.want
        books.record({"kind": "block_complete", "block": block, "role": "respondent",
                      "models": None if everyone else keys, "rounds": [r for r, _ in plans] if block == "1" else None,
                      "planned": planned, "final_by_status": dict(by_status), "not_attempted": dict(not_att),
                      "excluded_d2": dict(excluded_d2),
                      "reason": a.reason or "every planned answer counted", "spent_usd": 0.0})
        print(f"block {block} closed for the respondent calls of {'every model' if everyone else keys}: "
              f"{dict(by_status)}; not attempted {dict(not_att)}"
              + (f"; excluded under decision D2 {dict(excluded_d2)}" if excluded_d2 else ""))
    finally:
        S.release_lock()
    return 0


# ---- decision D13: the availability check of the hosted models (Section 10.4) ----------------------------------------

AVAILABILITY_PROMPT = "Please reply with one short sentence to confirm that you received this message."
AVAILABILITY_KIND = "availability_call"       # ledger kind of a test call: it belongs to no block and to no holds item
D13_FACTS = (("d2_allows_harmful_frame", "1. decision D2 allows the prompts of the harmful frame"),
             ("no_pilot_call_not_attempted", "2. no pilot call, as respondent or as judge, ended not_attempted"),
             ("answered_test_prompt", "3. answered the harmless test prompt under the settings of Section 3.3"))
NOT_SENT = {"cap": "the call would pass the cap beside the holds of all unfinished work (Section 12.5)",
            "run_cap": "the run cap of this session is reached",
            "overrun": "an overrun is open (Section 12.5)"}


def availability_raw_path():
    return RAW / "availability_answers_v23.jsonl"


def availability_log_path():
    return LOGS / "availability_v23.jsonl"


def availability_models(a, models, design):
    """The hosted models that took part in the pilot ('pilot_hosted' of config/panel_v23.json, else
    'hosted_primary'), or those of --models among them. A hosted model left out at the pilot registration has left
    the study (Section 10.4) and gets no test call."""
    by_n, by_key = {m["n"]: m for m in models}, {m["key"]: m for m in models}
    primary = [by_n[int(n)]["key"] for n in design["hosted_primary"]]
    pilot = [by_n[n]["key"] for n in registered_hosted(design, "1")]
    want = list(dict.fromkeys(x for x in (a.models or "").split(",") if x)) or pilot
    bad = [k for k in want if k not in primary]
    if bad:
        sys.exit(f"not hosted models of the primary panel (config/panel_v23.json 'hosted_primary'): {bad}")
    left = [k for k in want if k not in pilot]
    if left:
        sys.exit(f"{left} were left out at the pilot registration ('pilot_hosted'): they have left the study "
                 f"(Section 10.4) and get no test call")
    direct = [k for k in want if S.account_of(by_key[k]) != "openrouter" or not (by_key[k].get("pin") or {}).get("tag")]
    if direct:
        sys.exit(f"{direct}: a hosted model is reached through OpenRouter with a pinned endpoint (decision D16); "
                 f"the preflight has nothing to check")
    return [by_key[k] for k in want]


def d2_fact(m, live, problems):
    """Fact 1 of D13, from the preflight: the pinned endpoint is on the zero-retention list, it is not marked for
    safety retention unless decision D2 admits it for every prompt ('d2_safety_retention' 'all'), and the model
    receives harmful prompts (receives_harmful in config/models.json). Prices, precision and routing are pin
    matters (decision D16): they stop the test call, not this fact."""
    tag = m["pin"]["tag"]
    if live is None:
        return False, "; ".join(problems) or f"{tag} is not on the zero-retention list"
    d2 = m.get("d2_safety_retention")
    if live.get("safety_retention") and d2 != "all":
        return False, (f"{tag} is marked for safety retention and decision D2 "
                       + ("admits it for safe prompts only" if d2 == "safe_only" else "does not allow it"))
    if m.get("receives_harmful") is not True:
        return False, "receives_harmful is not true in config/models.json"
    return True, (f"{tag} is on the zero-retention list "
                  + ("with safety retention, which decision D2 admits for every prompt" if live.get("safety_retention")
                     else "without safety retention") + "; receives_harmful is true")


def pilot_fact(books, ledger, key):
    """Fact 2 of D13, from the ledger, role by role: (holds, evidence), holds None while block 1 is not closed for
    the model. A block_complete line of block 1 that covers the model is needed: the close is refused while a
    planned call is open (Section 10.3), so after it every planned pilot call is final, excluded under D2, or
    not_attempted. A call ends not_attempted only through an abandonment of its model in block 1 or a cut of its
    item. The fact fails when one of these touches the model and a close line that covers it counts not_attempted
    calls: a line counts them for all the models it covers, so this reading errs towards 'no'."""
    states, notes = [], []
    for role in ("respondent", "judge"):
        finals = {p: books.final.get(S.item_id("1", role, key, p), 0) for p in ("pilot_r1", "pilot_r2")}
        fin = f"{sum(finals.values())} final calls (" + ", ".join(f"{p[-2:]} {n}" for p, n in finals.items()) + ")"
        lines = [e for e in ledger if e.get("kind") == "block_complete" and str(e.get("block")) == "1"
                 and (e.get("role") or "*") in (role, "*") and (not e.get("models") or key in e["models"])]
        if not lines:
            states.append(None)
            notes.append(f"{role}: block 1 is not closed for it yet, {fin} so far")
            continue
        counted = sum(int(n) for e in lines for n in (e.get("not_attempted") or {}).values())
        why = (["abandoned in block 1"] if books.abandoned_for("1", key) else []) + \
              [f"item {it['part']} cut" for it in books.items.values()
               if str(it["block"]) == "1" and it.get("role") == role and it["model_key"] == key
               and int(it.get("cut") or 0) in books.cuts]
        excluded = sum(int((e.get("excluded_d2") or {}).get(key, 0)) for e in lines)
        if counted and why:
            states.append(False)
            notes.append(f"{role}: {', '.join(why)}, and the close counted {counted} calls not_attempted; {fin}")
        else:
            states.append(True)
            notes.append(f"{role}: block 1 closed, {fin}" + (f", {excluded} excluded under D2" if excluded else ""))
    holds = False if False in states else None if None in states else True
    return holds, "; ".join(notes)


def reserve_outside_plan(books, amount):
    """(ok, why) for a call that no block plans: room beside the holds of all unfinished work, every block included
    (Books.reserve counts the blocks of higher priority only), and the run cap (Section 12.5)."""
    with books.lock:
        if books.stopped_reason:
            return False, books.stopped_reason
        if books.overrun_open:
            return False, "overrun"
        if books.spent + books.inflight + books.remaining() + amount > books.study_cap + S.EPS:
            return False, "cap"
        if books.run_cap is not None and books.run_spent + books.inflight + amount > books.run_cap + S.EPS:
            return False, "run_cap"
        books.inflight += amount
        return True, ""


def settle_outside_plan(books, reserved, actual, entry):
    """Books.settle with the ledger kind of the test calls, so that no holds item counts them. A settlement above
    the reservation writes an overrun line and stops every further paid call."""
    actual = max(0.0, float(actual))
    with books.lock:
        books.inflight -= reserved
        books.run_spent += actual
    books.record(dict(entry, kind=AVAILABILITY_KIND, reserved_usd=round(reserved, 6), spent_usd=round(actual, 6)))
    if actual > reserved + 1e-9:
        books.record({"kind": "overrun", "model_key": entry.get("model_key"), "role": entry.get("role"),
                      "block": None, "item": None, "reserved_usd": round(reserved, 6),
                      "settled_usd": round(actual, 6), "spent_usd": 0.0})
        with books.lock:
            books.stopped_reason = "overrun"


def write_availability_attempt(run, m, live, attempt, out, exc, oc, status, ident, reserved, spent, latency):
    """The private record (answer text, error body), then the public line without them."""
    out = out or {}
    body = providers.error_text(exc) if exc is not None else None
    rec = {"protocol": "2.3", "kind": "attempt", "run": run, "ts": now(), "model_key": m["key"], "model": m["model"],
           "provider": m["provider"], "endpoint": m["pin"]["tag"], "live": live, "attempt": attempt,
           "prompt_sha256": sha256_text(AVAILABILITY_PROMPT), "request_sha256": request_hash(m, AVAILABILITY_PROMPT),
           "config_sha256": config_hash(m), "text": out.get("text"), "stop_reason": out.get("stop_reason"),
           "model_returned": out.get("model_returned"), "served_provider": out.get("served_provider"),
           "identity_match": ident, "input_tokens": out.get("input_tokens"), "output_tokens": out.get("output_tokens"),
           "reasoning_tokens": out.get("reasoning_tokens"), "cost_reported": out.get("cost_reported"),
           "status": status, "final": oc["kind"] == "final", "failure_kind": oc.get("failure_kind"),
           "http_status": oc.get("http_status"),
           "error": f"{error_label(exc)}: {str(exc)[:300]}" if exc is not None else None, "error_body": body,
           "cost_usd": round(spent, 6), "reserved_usd": round(reserved, 6),
           "bound_input_tokens": S.input_bound_tokens(AVAILABILITY_PROMPT), "output_cap": m["max_output_tokens"],
           "latency_s": latency}
    pub = {k: v for k, v in rec.items() if k not in ("text", "error_body")}
    if rec["text"]:
        pub["text_sha256"] = sha256_text(str(rec["text"]))
    if body:
        pub["error_body_sha256"] = sha256_text(str(body))
    if rec["error"]:
        pub["error"] = public_error(rec["error"])
    append(availability_raw_path(), rec)
    append(availability_log_path(), pub)


def availability_call(books, run, m, live, provider, settings):
    """Fact 3 of D13: the test prompt through the adapter and the configuration of the respondent calls (identifier,
    pinned endpoint and settings of Section 3.3, from config/models.json). Each attempt reserves call_bound beside
    the holds of all unfinished work, settles like a respondent call and writes one ledger line; a transient failure
    is tried again as for a respondent. (holds, evidence, complete): complete is False when an attempt could not be
    sent for a reason of the books, or the provider rejected the configuration."""
    mr = ModelRun(None, m, [], None)          # outcome() and identity() of a respondent call
    retries = int(settings["retries_in_session"])
    waits = settings.get("retry_wait_s") or [0]
    tries, spent_all, reserved_all = 0, 0.0, 0.0
    while True:
        tries += 1
        bound = S.call_bound(m, AVAILABILITY_PROMPT, m["max_output_tokens"], live=live)
        ok, why = reserve_outside_plan(books, bound)
        if not ok:
            return False, f"not sent{' again' if tries > 1 else ''}: {NOT_SENT.get(why, why)}", False
        t0 = time.perf_counter()
        out = exc = None
        try:
            out = provider.call(AVAILABILITY_PROMPT)
        except providers.ProjectKeyError:
            books.release(bound)
            return False, "not sent: no project key for this model", False
        except Exception as e:      # classified as for a respondent call
            exc = e
        latency = round(time.perf_counter() - t0, 2)
        spent = S.settled_cost(m, out) if exc is None else S.settle_failed(exc, bound, providers)
        oc = mr.outcome(out, exc)
        ident = mr.identity(out)
        pending = oc["kind"] == "transient" and tries > retries
        status = ("pending" if pending else "failed" if oc["kind"] == "transient" else
                  "config_error" if oc["kind"] == "config" else oc["status"])
        settle_outside_plan(books, bound, spent, {
            "model_key": m["key"], "role": "availability", "attempt": tries, "final": oc["kind"] == "final",
            "status": status, "identity_match": ident, "prompt_sha256": sha256_text(AVAILABILITY_PROMPT)})
        write_availability_attempt(run, m, live, tries, out, exc, oc, status, ident, bound, spent, latency)
        spent_all, reserved_all = spent_all + spent, reserved_all + bound
        if oc["kind"] == "transient" and not pending:
            SLEEP(waits[min(tries - 1, len(waits) - 1)])
            continue
        break
    cost = f"{tries} attempt{'s' if tries > 1 else ''}, ${spent_all:.6f} settled of ${reserved_all:.6f} reserved"
    got = (f"returned '{(out or {}).get('model_returned')}', served by '{(out or {}).get('served_provider')}' "
           f"(pinned: '{m['pin'].get('provider_name')}')")
    err = f" ({type(exc).__name__}, HTTP {oc.get('http_status')})" if exc is not None else ""
    if status in ("ok", "truncated") and ident is True:
        return True, f"answered (status {status}); {got}; {cost}", True
    if status in ("ok", "truncated"):
        return False, (f"an answer came back (status {status}), but "
                       + ("the response names no model identifier, so the identity of Section 3.3 is not shown"
                          if ident is None else "not under the configured identifier and pinned endpoint")
                       + f"; {got}; {cost}"), True
    if status == "pending":
        return False, f"no answer: still failing after {tries} attempts{err}; {cost}", True
    if status == "config_error":                 # our side, as a missing key: the check is incomplete
        return False, f"no answer: the configuration was rejected{err}; fix it under a logged decision; {cost}", False
    return False, f"no answer: status {status}{err}; {cost}", True


def availability_check(a):
    """--availability-check: decision D13 on the day of the freeze, before its ledger line (Section 10.4). For each
    hosted model of the pilot: the endpoint preflight, one test call, and the three facts. Reports only: the
    decision is the PI's."""
    models = json.loads(CONFIG.read_text(encoding="utf-8"))["models"]
    design = json.loads(DESIGN.read_text(encoding="utf-8"))
    settings = J.load_settings()
    if any(r["prompt"].strip() == AVAILABILITY_PROMPT.strip() for r in load_rows().values()):
        sys.exit("the availability test prompt is a benchmark prompt: it must not be")
    chosen = availability_models(a, models, design)
    if not chosen:
        print("no hosted model took part in the pilot ('pilot_hosted' is empty): nothing to check")
        return 0
    run_cap = a.run_cap if a.run_cap is not None else float(os.environ.get("BUDGET_USD") or 0) or None
    if not (run_cap and run_cap > 0):
        sys.exit("the test calls are paid: a run cap is needed (--run-cap USD, or BUDGET_USD in .env)")
    S.acquire_lock("availability:" + a.run)          # before the ledger is read
    try:
        books = S.Books(a.run, run_cap=run_cap)
        if not books.registration:
            print("NOT STARTED: the pilot registration is not recorded (spend_v23.py register; Sections 13.1, 14)")
            return 2
        if books.freeze:
            print(f"NOT STARTED: the freeze is recorded ('{books.freeze}'): the availability check of decision D13 is "
                  f"made on the day of the freeze, before its ledger line (Section 10.4)")
            return 2
        ledger = S.read_ledger()
        zdr, pre = FETCH_ZDR(), {}
        for m in chosen:                              # every preflight before the first test call
            ok, live, problems = S.preflight(m, zdr, harmful=True)
            safe_only = bool(not ok and live is not None and live.get("safety_retention")
                             and m.get("d2_safety_retention") == "safe_only"
                             and all("safety retention" in p for p in problems))
            books.record({"kind": "preflight", "model_key": m["key"], "role": "availability", "block": None,
                          "ok": bool(ok or safe_only), "safe_only": safe_only, "live": live, "problems": problems,
                          "spent_usd": 0.0})
            pre[m["key"]] = (bool(ok or safe_only), live, problems)
        facts, complete = {}, True
        for m in chosen:
            sendable, live, problems = pre[m["key"]]
            stop = books.stopped(m)
            if stop:
                f3 = (False, f"not sent: a provider stop is recorded for {stop} (Section 16.5)")
            elif not sendable:
                f3 = (False, "not sent: preflight: " + "; ".join(problems))
            else:
                try:
                    provider = MAKE_PROVIDER(m)
                except providers.ProjectKeyError:
                    f3, complete = (False, "not sent: no project key for this model"), False
                else:
                    h, ev, done = availability_call(books, a.run, m, live, provider, settings)
                    f3, complete = (h, ev), complete and done
            facts[m["key"]] = (d2_fact(m, live, problems), pilot_fact(books, ledger, m["key"]), f3)
        date = dt.datetime.now().astimezone().date().isoformat()
        print(f"availability check of decision D13 (Section 10.4), run {a.run}, {date}")
        print(f"  test prompt: fixed and harmless, not a benchmark prompt (SHA-256 "
              f"{sha256_text(AVAILABILITY_PROMPT)[:16]}), under each model's configuration in config/models.json")
        for m in chosen:
            print(f"  model {m['n']} {m['key']} ({m['model']}, endpoint {m['pin']['tag']})")
            line = {"kind": "facts", "protocol": "2.3", "run": a.run, "ts": now(), "date": date, "model_key": m["key"],
                    "n": m["n"], "model": m["model"], "endpoint": m["pin"]["tag"], "config_sha256": config_hash(m),
                    "prompt_sha256": sha256_text(AVAILABILITY_PROMPT)}
            for (name, label), (holds, ev) in zip(D13_FACTS, facts[m["key"]]):
                print(f"    {label}: {'yes' if holds else 'not established' if holds is None else 'no'}. {ev}")
                line[name] = {"holds": holds, "evidence": ev}
            append(availability_log_path(), line)
        print("These are the facts of Section 10.4. The decision is the PI's: record D13 in docs/PI_DECISIONS.md, "
              "with these facts and the date, and in config/panel_v23.json ('registered_hosted').")
        log = availability_log_path()
        print(f"ledger ${books.spent:.2f} of cap ${books.study_cap:.2f}; attempts and facts in "
              f"{log.relative_to(ROOT).as_posix() if log.is_relative_to(ROOT) else log}")
        if not complete:
            print("INCOMPLETE: a test call was not sent (the books or a key), or the provider rejected its "
                  "configuration; run the check again when this is resolved")
        return 0 if complete else 3
    finally:
        S.release_lock()


# ---- command line ----------------------------------------------------------------------------------------------------

def _main(a):
    if a.availability_check:
        given = [f for f, v in (("--block", a.block), ("--round", a.round), ("--batch", a.batch), ("--sync", a.sync),
                                ("--dry-run", a.dry_run), ("--complete-block", a.complete_block),
                                ("--answer-runs", a.answer_runs), ("--max-calls", a.max_calls),
                                ("--collect", a.collect), ("--purge", a.purge), ("--adopt", a.adopt),
                                ("--release", a.release)) if v]
        if given:
            sys.exit(f"--availability-check takes --run, --models and --run-cap only, not {given}")
        if not a.run:
            sys.exit("--run is required")
        if a.run in SEALED_RUNS:
            sys.exit(f"run '{a.run}' is sealed (docs/SEALED_HASHES.md); choose another run name")
        return availability_check(a)
    if a.collect or a.purge or a.adopt or a.release:
        return bookkeeping(a)
    if not a.block:
        sys.exit("--block is required (1, 2 or 4), a batch command, or --availability-check")
    if a.batch and a.sync:
        sys.exit("--batch and --sync exclude each other")
    if a.complete_block and (a.dry_run or a.batch or a.sync):
        sys.exit("--complete-block sends nothing: without --dry-run, --batch or --sync")
    if a.batch and a.block != BATCH_BLOCK:
        sys.exit("--batch is for block 4 (the main run of the direct Anthropic and OpenAI models); pilots and block 2 "
                 "are synchronous")
    if a.block == "1" and not a.complete_block and a.round not in (1, 2):
        sys.exit("block 1 needs --round 1 or --round 2")
    if a.block != "1" and a.round is not None:
        sys.exit("--round is for block 1 only")
    if not a.dry_run and not a.run:
        sys.exit("--run is required")
    if a.run in SEALED_RUNS:
        sys.exit(f"run '{a.run}' is sealed (docs/SEALED_HASHES.md); choose another run name")
    if a.workers < 1:
        sys.exit("--workers must be at least 1")
    sess = Session(a)
    if a.complete_block:
        return complete_block(sess)
    return run_block(sess)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Respondent calls of protocol v2.3 (one block per session), and the "
                                             "availability check of decision D13")
    ap.add_argument("--run", default="", help="run name of this session (a new name; sealed names are refused)")
    ap.add_argument("--block", default=None, choices=list(RESPONDENT_BLOCKS), help="respondent block: 1, 2 or 4")
    ap.add_argument("--round", type=int, default=None, help="pilot round (block 1)")
    ap.add_argument("--models", default="", help="model keys (default: every respondent of the block)")
    ap.add_argument("--answer-runs", default="",
                    help="v2.3 answer runs to read besides those of results/logs/respondent_runs_v23.jsonl")
    ap.add_argument("--batch", action="store_true", help="block 4: one batch chunk per direct Anthropic/OpenAI model")
    ap.add_argument("--sync", action="store_true",
                    help="block 4: direct models answer synchronously (under a logged decision; give --reason)")
    ap.add_argument("--workers", type=int, default=1, help="paid models called at the same time")
    ap.add_argument("--max-calls", type=int, default=None, help="at most this many prompts per model")
    ap.add_argument("--run-cap", type=float, default=None, help="US$ limit of this session (default BUDGET_USD)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--complete-block", action="store_true")
    ap.add_argument("--reason", default="")
    ap.add_argument("--collect", default="", help="collect the results of a batch submitted earlier")
    ap.add_argument("--purge", default="", help="delete a collected batch's files at the provider (idempotent)")
    ap.add_argument("--adopt", default="", help="BATCH_ID: link a submission whose reply was lost (with --ref)")
    ap.add_argument("--release", default="",
                    help="REF: release a submission that created no batch, or whose batch failed validation")
    ap.add_argument("--ref", default="", help="pending reference for --adopt")
    ap.add_argument("--undeletable", action="store_true",
                    help="with --release: an upload that cannot be deleted becomes an open item")
    ap.add_argument("--availability-check", action="store_true",
                    help="decision D13 (Section 10.4), on the day of the freeze and before its ledger line: the "
                         "preflight and one harmless test call of each hosted model, and the three facts")
    a = ap.parse_args(argv)
    load_env()
    try:
        return _main(a)
    except Exception as e:      # B6-m6: an SDK message can quote the input; report type and place only
        if os.environ.get("AC_DEBUG") == "1":
            raise
        tb = traceback.extract_tb(e.__traceback__)[-1]
        sys.exit(f"stopped: {error_label(e)} at {os.path.basename(tb.filename)}:{tb.lineno} "
                 f"(message kept out of the logs; AC_DEBUG=1 shows it)")


if __name__ == "__main__":
    sys.exit(main())
