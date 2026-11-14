"""Offline tests of the answering runner of protocol v2.3 (src/run_models.py) and the spending rules of
src/spend_v23.py that it uses.

Fake providers, synthetic answer files and the recorded prices; every file goes to a scratch folder (AC_TEST_TMP,
default E:/claude/agentsControl_tests/respondent_agent). Nothing is sent over the network, no model is called,
and no file under results/ is read or written. Benchmark prompts are read from data/processed/sample.jsonl, as the
runner does; nothing is printed from them. The real Anthropic and OpenAI adapters are checked at the end with
stand-in SDK clients.

Run: python -I -X utf8 tests/test_runner_offline.py [test names]     (exit code 0 when every test passes)
"""
import collections
import contextlib
import copy
import datetime as dt
import hashlib
import io
import json
import os
import pathlib
import shutil
import sys
import traceback
import types

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
import answers_v23 as A  # noqa: E402
import frames_v23  # noqa: E402
import judge_v23 as J  # noqa: E402
import plan_v23 as P  # noqa: E402
import providers  # noqa: E402
import run_judges_v23 as RJ  # noqa: E402
import run_models as R  # noqa: E402
import spend_v23 as S  # noqa: E402

TMP = pathlib.Path(os.environ.get("AC_TEST_TMP", "E:/claude/agentsControl_tests/respondent_agent")) \
    / "test_runner_offline"
REAL_MODELS = json.loads((ROOT / "config" / "models.json").read_text(encoding="utf-8"))
REAL_DESIGN = json.loads((ROOT / "config" / "panel_v23.json").read_text(encoding="utf-8"))
REAL_HOLDS = json.loads((ROOT / "config" / "stage_holds.json").read_text(encoding="utf-8"))
REAL_MANIFEST = json.loads((ROOT / "analysis" / "output" / "manifest_v23.json").read_text(encoding="utf-8"))
REAL_SETTINGS = json.loads((ROOT / "config" / "judge_v23.json").read_text(encoding="utf-8"))
SNAPSHOT = json.loads((ROOT / "data/selection/2026-11-11/raw/or_endpoints_zdr.json").read_text(encoding="utf-8"))["data"]
for _m in REAL_MODELS["models"]:      # a pin recorded from a later snapshot: the fake live list lists it as recorded there
    _src, _id = (_m.get("pin") or {}).get("source"), (_m["model"], (_m.get("pin") or {}).get("tag"))
    if _src and _src != "data/selection/2026-11-11/raw/or_endpoints_zdr.json":
        _new = [e for e in json.loads((ROOT / _src).read_text(encoding="utf-8"))["data"]
                if (e.get("model_id"), e.get("tag")) == _id]
        SNAPSHOT = [_new[0] if (e.get("model_id"), e.get("tag")) == _id else e for e in SNAPSHOT]
FR = frames_v23.frames()
PILOT = P.load_pilot()
ROWS = R.load_rows()
INSTALLED = {m["model"]: m.get("digest") for m in REAL_MODELS["models"] if m["provider"] == "ollama"}
SENTINEL = "SENTINEL-SEALED-ANSWER-7f3a"          # text of the synthetic sealed answers: must never leave them
ANSWER = "Synthetic answer of a fake model."
PILOT_REPORT_FIELDS = ("model_key", "prompt_id", "error", "input_tokens", "output_tokens", "reasoning_tokens",
                       "cost_usd", "latency_s", "pilot")
LOCAL = (4, 5, 6, 15, 16, 17, 18, 19, 20, 21)
API = (1, 2, 3, 7, 8, 9, 10, 11, 12, 13, 22, 23)
PER_ROUND = len(LOCAL) * 100 + len(API) * 20     # pilot answers per round: 1,240 since decision D17
for v in ("STUDY_BUDGET_USD", "BUDGET_USD"):
    os.environ.pop(v, None)

# The route of model 14 before decision D2 (11 November 2026): through OpenRouter, pinned to an endpoint with safety
# retention. Decision D17 (12 November 2026) took model 14 out of the study, and no pinned endpoint of the panel keeps
# data for safety review. The D2 tests put this route on model D2_N of the commercial panel: their example of a pinned
# endpoint with safety retention, the case that the D2 rules still cover.
D2_N = 13
ROUTED_14 = {
    "provider": "openai_compatible", "base_url": "https://openrouter.ai/api/v1", "api_key_env": "AC_OPENROUTER_API_KEY",
    "model": "google/gemini-4-argon", "zdr": True, "allow_fallbacks": False, "provider_order": ["google-vertex/global"],
    "price_checked": "2026-11-11 pinned endpoint google-vertex/global (data/selection/2026-11-11)",
    "pin": {"tag": "google-vertex/global", "provider_name": "Google", "quantization": "unknown",
            "prompt_usd_per_m": 2.0, "completion_usd_per_m": 10.0, "cache_write_usd_per_m": 0.1875,
            "safety_retention": True, "status": -2, "context_length": 1048576,
            "supported_parameters": ["include_reasoning", "max_tokens", "reasoning", "reasoning_effort",
                                     "response_format", "seed", "stop", "structured_outputs", "temperature",
                                     "tool_choice", "tools", "top_p"],
            "discount": 0.5, "source": "data/selection/2026-11-11/raw/or_endpoints_zdr.json", "recorded": "2026-11-11"},
}


def via_openrouter_14(models, d2):
    """Puts the OpenRouter route that model 14 had before decision D2 on model D2_N, with this D2 value."""
    m = next(x for x in models if x["n"] == D2_N)
    for k in ("price_schedule", "cache_read_factor", "cache_write_factor"):
        m.pop(k, None)
    m.update(copy.deepcopy(ROUTED_14), d2_safety_retention=d2)


_orig_append_line = S.append_line


def fast_append_line(path, obj, durable=True):        # no fsync in tests
    return _orig_append_line(path, obj, False)


SLEEPS = []
S.append_line = fast_append_line
R.SLEEP = lambda s: SLEEPS.append(s)
R.load_env = lambda: None                             # never the real .env in tests
RJ.LOAD_ENV = lambda: None
R.FSYNC = False


def sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


PROMPT_ID = {sha(r["prompt"]): r["id"] for r in ROWS.values()}


# ---- fakes ------------------------------------------------------------------------------------------------------------

class FakeHTTP(Exception):
    def __init__(self, status, msg):
        super().__init__(msg)
        self.status_code, self.message = status, msg


def served(m):
    return (m.get("pin") or {}).get("provider_name") or ("ollama-local" if m["provider"] == "ollama" else m["provider"])


def answer(cfg, prompt):
    return {"text": ANSWER, "stop_reason": "stop", "provider_block": False, "served_provider": served(cfg),
            "model_returned": cfg["model"] + ("" if cfg["provider"] in ("ollama", "openai_compatible") else "-2026"),
            "input_tokens": len(prompt.encode("utf-8")) // 4 + 8, "output_tokens": 40, "reasoning_tokens": None,
            "cost_reported": None, "request_id": None}


class Fake:
    """A provider. Fake.rules[model] is a list of behaviours used one per call (then 'ok'), or a callable of
    (cfg, prompt id). Batches live in Fake.batches; Fake.batch_rules[model] lists submission behaviours ('ok', 'lost':
    the batch exists but the reply is lost, 'none': no batch and no reply, or an exception)."""
    rules, sent, batches, submits, deleted, uploads_deleted = {}, [], {}, [], [], []
    batch_rules, result_rules, running = {}, {}, set()
    zdr_calls = 0

    def __init__(self, cfg):
        self.cfg = cfg

    def call(self, prompt):
        model, pid = self.cfg["model"], PROMPT_ID.get(sha(prompt))
        Fake.sent.append((model, pid))
        beh = Fake.rules.get(model)
        r = beh(self.cfg, pid) if callable(beh) else (beh.pop(0) if beh else "ok")
        if isinstance(r, BaseException):
            raise r
        out = answer(self.cfg, prompt)
        if isinstance(r, dict):
            out.update(r)
        return out

    def batch_submit(self, items):
        model = self.cfg["model"]
        Fake.submits.append(model)
        rule = Fake.batch_rules.get(model)
        beh = rule.pop(0) if rule else "ok"
        if isinstance(beh, BaseException):
            raise beh
        bid = f"fakebatch_{len(Fake.batches) + 1:03d}"
        if beh != "none":
            Fake.batches[bid] = {"model": model, "cfg": self.cfg, "items": list(items)}
        if beh in ("lost", "none"):
            e = TimeoutError("the reply was lost")
            if beh == "none":
                e.uploaded_file_id = "file-upload-1"
            raise e
        return bid

    def batch_status(self, bid):
        if bid not in Fake.batches:
            raise FakeHTTP(404, "no such batch")
        return (False, "in_progress") if bid in Fake.running else (True, "ended")

    def batch_request_count(self, bid):
        return len(Fake.batches[bid]["items"])

    def batch_results(self, bid):
        b = Fake.batches[bid]
        rule = Fake.result_rules.get(b["model"])
        for i, (cid, prompt) in enumerate(b["items"]):
            res = rule(i, cid, prompt, b["cfg"]) if rule else None
            if res is None:
                yield cid, answer(b["cfg"], prompt), None
            else:
                yield from res

    def batch_delete(self, bid):
        Fake.deleted.append(bid)
        return [bid]

    def batch_cancel(self, bid):
        Fake.running.discard(bid)

    def batch_errors(self, bid):
        return None

    def delete_upload(self, fid):
        Fake.uploads_deleted.append(fid)


def fake_identity(model, base=None):
    return {"digest": INSTALLED.get(model), "ollama_version": Fake.ollama_version, "quantization": "Q4_K_M",
            "template_sha256": "t"}


def fake_zdr():
    Fake.zdr_calls += 1
    return Fake.zdr


Fake.ollama_version, Fake.zdr = "0.40.15", SNAPSHOT
R.MAKE_PROVIDER = lambda cfg: Fake(cfg)
R.OLLAMA_IDENTITY = fake_identity
R.OLLAMA_VRAM = lambda model, base=None: {"size_vram": 1, "size": 1}
R.FETCH_ZDR = fake_zdr


# ---- scratch study ------------------------------------------------------------------------------------------------------

def setup(name, cap=128.0, models_edit=None, design_edit=None, holds_edit=None, settings_edit=None):
    tmp = TMP / name
    shutil.rmtree(tmp, ignore_errors=True)
    (tmp / "raw").mkdir(parents=True)
    (tmp / "logs").mkdir()
    R.RAW, R.LOGS = tmp / "raw", tmp / "logs"
    S.LEDGER, S.SPEND_LOCK = tmp / "logs" / "spend_ledger.jsonl", tmp / "logs" / "spend.lock"
    models = copy.deepcopy(REAL_MODELS)
    if models_edit:
        models_edit(models["models"])
    design = copy.deepcopy(REAL_DESIGN)
    design["registered_hosted"] = [22, 23]
    if design_edit:
        design_edit(design)
    holds = copy.deepcopy(REAL_HOLDS)
    if holds_edit:
        holds_edit(holds)
    settings = copy.deepcopy(REAL_SETTINGS)
    if settings_edit:
        settings_edit(settings)
    for obj, fname in ((models, "models.json"), (design, "panel.json"), (holds, "holds.json"),
                       (settings, "judge.json")):
        (tmp / fname).write_text(json.dumps(obj, indent=1), encoding="utf-8")
    R.CONFIG, R.DESIGN, S.HOLDS, J.SETTINGS = tmp / "models.json", tmp / "panel.json", tmp / "holds.json", \
        tmp / "judge.json"
    S.MANIFEST = tmp / "manifest.json"                 # none until write_manifest()
    S.STUDY_CAP_DEFAULT = cap
    Fake.rules, Fake.sent, Fake.batches, Fake.submits, Fake.deleted, Fake.uploads_deleted = {}, [], {}, [], [], []
    Fake.batch_rules, Fake.result_rules, Fake.running, Fake.zdr_calls = {}, {}, set(), 0
    Fake.ollama_version, Fake.zdr = "0.40.15", SNAPSHOT
    SLEEPS.clear()
    OUTPUTS.clear()
    return tmp, models["models"]


def write_manifest(scale=1.0, repriced=True, holds_from_it=True):
    """The manifest of the scratch study: the registered one, every pessimistic figure times scale, with the record of
    a (synthetic) repricing after the pilot if repriced; holds_from_it: the holds name its SHA-256, as
    scripts/holds_v23.py does when it writes them from it."""
    import hashlib
    assert S.MANIFEST != ROOT / "analysis" / "output" / "manifest_v23.json" and S.HOLDS != ROOT / "config" /         "stage_holds.json", "write_manifest() writes only in a scratch study"
    man = copy.deepcopy(REAL_MANIFEST)
    man["totals"] = {k: round(v * scale, 2) for k, v in man["totals"].items()}
    for c in man["cuts"]:
        c["saves_pessimistic"] = round(c["saves_pessimistic"] * scale, 2)
    man["repricing"] = ({"file": "synthetic_repricing.json", "sha256": "0" * 64, "snapshot": "synthetic",
                         "source": "offline test", "snapshot_files": {}, "assumptions": {}} if repriced else None)
    S.MANIFEST.write_text(json.dumps(man, indent=1), encoding="utf-8")
    if holds_from_it:
        h = json.loads(S.HOLDS.read_text(encoding="utf-8"))
        h["manifest_sha256"] = hashlib.sha256(S.MANIFEST.read_bytes()).hexdigest()
        S.HOLDS.write_text(json.dumps(h, indent=1), encoding="utf-8")
    return man


class Checks:
    def __init__(self, name):
        self.name, self.failed = name, []

    def __call__(self, label, cond):
        if not cond:
            self.failed.append(label)
        return bool(cond)

    def ok(self):
        if self.failed:
            print(f"    {self.name}: failed checks {self.failed}")
        return not self.failed


OUTPUTS = []


def run(argv):
    buf, err = io.StringIO(), io.StringIO()
    try:
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(err):
            code = R.main(argv)
    except SystemExit as e:
        code = e.code if isinstance(e.code, int) or e.code is None else str(e.code)
    run.out, run.err = buf.getvalue(), err.getvalue()
    OUTPUTS.extend([run.out, run.err, code if isinstance(code, str) else ""])
    return code


def jsonl(p):
    p = pathlib.Path(p)
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()] if p.exists() else []


def ledger(**kw):
    S.append_line(S.LEDGER, dict(kw, spent_usd=kw.get("spent_usd", 0.0)))


def led(kind=None):
    return [e for e in jsonl(S.LEDGER) if kind is None or e.get("kind") == kind]


def close(block, role, models=None):
    ledger(kind="block_complete", block=str(block), role=role, models=models, reason="test")


def open_blocks_before(block):
    """The ledger of a study after the freeze, with the blocks before `block` closed."""
    ledger(kind="registration", tag="t-registration")
    ledger(kind="freeze", tag="t-freeze")
    for b, role in (("1", "respondent"), ("1", "judge"), ("2", "respondent"), ("3", "judge")):
        if int(b) < int(block):
            close(b, role)


def records(run_name):
    return jsonl(R.raw_path(run_name))


def public(run_name):
    return jsonl(R.calls_log_path(run_name))


def keymap(models):
    return {m["n"]: m["key"] for m in models}, {m["key"]: m for m in models}


def model_of(models, n):
    return next(m for m in models if m["n"] == n)


def write_sealed(run_name, m, ids, error_ids=()):
    """Answers of a sealed run in the version-1 format; the text is a sentinel."""
    with open(R.RAW / f"responses_{run_name}.jsonl", "a", encoding="utf-8") as f:
        for pid in ids:
            row = ROWS[pid]
            bad = pid in error_ids
            f.write(json.dumps({"run": run_name, "model_key": m["key"], "provider": m["provider"], "model": m["model"],
                                "prompt_id": pid, "source": row["source"], "category": row["category"],
                                "expected": row["expected"], "framing": row.get("framing", ""),
                                "ts": "2026-11-08T00:00:00+00:00", "text": None if bad else SENTINEL,
                                "cost_usd": 0.0, "error": ("ConnectionError: " + SENTINEL) if bad else None}) + "\n")


def write_pilot(run_name, ms, returned=None):
    """Pilot answers of a v2.3 run (round 1, the 'api' prompts) with a returned model identifier."""
    with open(R.RAW / f"responses_{run_name}.jsonl", "a", encoding="utf-8") as f:
        for m in ms:
            for pid in PILOT["rounds"][0]["api"]:
                f.write(json.dumps({"protocol": "2.3", "run": run_name, "block": "1", "round": 1, "pilot": True,
                                    "model_key": m["key"], "model": m["model"], "provider": m["provider"],
                                    "prompt_id": pid, "text": SENTINEL, "error": None, "answer_status": "ok",
                                    "final": True,
                                    "model_returned": (returned or {}).get(m["key"], m["model"] + "-2026")}) + "\n")


def bound(m, pid, live=None, factor=1.0):
    return S.call_bound(m, ROWS[pid]["prompt"], m["max_output_tokens"], live=live, price_factor=factor)


def no_leaks(tmp, sealed_files=("full", "v22_local", "pilot_local", "p0")):
    """The sealed sentinel, the fake answer text and the prompts appear in no output and no log; the answer text only
    in the private answer files of the runs."""
    blob = "\n".join(str(x) for x in OUTPUTS)
    logs = "\n".join(p.read_text(encoding="utf-8") for p in (tmp / "logs").glob("*.jsonl"))
    raws = "\n".join(p.read_text(encoding="utf-8") for p in (tmp / "raw").glob("*.jsonl")
                     if p.stem[len("responses_"):] not in sealed_files)
    prompts = [r["prompt"] for r in ROWS.values() if len(r["prompt"]) >= 20]
    sent = sorted({ROWS[p]["prompt"] for _, p in Fake.sent if p and len(ROWS[p]["prompt"]) >= 20})[:150]
    ok = SENTINEL not in blob and SENTINEL not in logs and SENTINEL not in raws
    ok &= ANSWER not in blob and ANSWER not in logs
    ok &= not any(p in blob for p in prompts)
    ok &= not any(p in logs for p in sent)
    return ok


# ---- tests --------------------------------------------------------------------------------------------------------------

def t_block1_rounds_sealed_and_close():
    ck = Checks("block1")
    tmp, models = setup("block1")
    K, M = keymap(models)
    ledger(kind="registration", tag="t")
    r1, r2 = PILOT["rounds"]
    ids1 = list(r1["harmful"]) + list(r1["safe"])
    # decision D18: no sealed run holds an answer of the study, complete or not
    write_sealed("full", model_of(models, 4), ids1[:-3], error_ids={ids1[0]})   # 3 missing, 1 transport error
    write_sealed("v22_local", model_of(models, 15), ids1)                      # complete
    write_sealed("pilot_local", model_of(models, 5), ids1)                     # the version-1 pilot
    c1 = run(["--run", "p1", "--block", "1", "--round", "1", "--run-cap", "100", "--workers", "4"])
    recs = records("p1")
    per = collections.Counter(r["model_key"] for r in recs)
    ck("round 1 exit", c1 == 0)
    ck("sealed answers are not used (decision D18)", per[K[4]] == 100 and per[K[15]] == 100)
    ck("pilot_local is not used", per[K[5]] == 100)
    ck("local models answer 100", all(per[K[n]] == 100 for n in LOCAL))
    ck("API models answer 20", all(per[K[n]] == 20 for n in API))
    ck("record fields", all(r["protocol"] == "2.3" and r["block"] == "1" and r["round"] == 1 and r["pilot"] is True
                            and r["final"] is True and r["error"] is None and r["answer_status"] == "ok"
                            and r["item"] == f"1|respondent|{r['model_key']}|pilot_r1" for r in recs))
    ck("pilot report fields kept", all(f in r for r in recs for f in PILOT_REPORT_FIELDS))
    ck("returned model and serving provider recorded", all(r.get("model_returned") and r.get("served_provider")
                                                            for r in recs))
    calls = led("call")
    paid = [r for r in recs if r["provider"] != "ollama"]
    ck("one ledger call line per paid attempt", len(calls) == len(paid) == len(API) * 20)
    ck("call lines", all(e["role"] == "respondent" and e["block"] == "1" and e["final"] is True
                         and e["item"].endswith("|pilot_r1") and e["model_key"] in M for e in calls))
    pre = {e["model_key"]: e for e in led("preflight")}
    ck("preflight of every routed model", sorted(pre) == sorted(K[n] for n in (7, 8, 10, 12, 13, 22, 23))
       and all(e["ok"] and e["role"] == "respondent" for e in pre.values()))
    lines = jsonl(S.LEDGER)
    first_call = next(i for i, e in enumerate(lines) if e.get("kind") == "call")
    ck("preflight before the first paid call", max(i for i, e in enumerate(lines) if e.get("kind") == "preflight")
       < first_call)
    good = True
    for r in paid:
        m = M[r["model_key"]]
        b = bound(m, r["prompt_id"], live=(pre.get(r["model_key"]) or {}).get("live"))
        good &= abs(r["reserved_usd"] - round(b, 6)) < 1e-9 and r["cost_usd"] <= r["reserved_usd"]
        good &= r["bound_input_tokens"] == S.input_bound_tokens(ROWS[r["prompt_id"]]["prompt"])
        good &= r["output_cap"] == m["max_output_tokens"]
    ck("reservation = bound >= settlement", good)
    ck("ledger = records", abs(sum(e["spent_usd"] for e in calls) - sum(r["cost_usd"] for r in paid)) < 1e-6)
    ck("public log without text", all("text" not in x and "error_body" not in x for x in public("p1")))
    ses = jsonl(R.runs_log_path())
    ck("session line", len(ses) == 1 and ses[0]["block"] == "1" and ses[0]["round"] == 1 and ses[0]["to_do"] == PER_ROUND)
    ck("manifest", {e["model_key"] for e in jsonl(R.manifest_path("p1"))} >= {K[n] for n in API}
       and any(e.get("event") == "vram_after_first_call" for e in jsonl(R.manifest_path("p1"))))
    # the pilot report reads these records (scripts/pilot_report_v23.py)
    import pilot_report_v23 as PR
    RJ.RAW, RJ.LOGS, RJ.MODELS, RJ.DESIGN = R.RAW, R.LOGS, R.CONFIG, R.DESIGN
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        PR.main(["--round", "1", "--answer-runs", "p1", "--out", str(tmp / "pilot")])
    rep = json.loads((tmp / "pilot" / "pilot_report_r1.json").read_text(encoding="utf-8"))["respondents"]
    ck("pilot report counts", rep[K[22]]["answers"] == 20 and rep[K[4]]["answers"] == 100
       and rep[K[15]]["answers"] == 100 and rep[K[1]]["over_bound"] == 0)
    ck("pilot report cost", abs(rep[K[22]]["cost_usd"] - sum(r["cost_usd"] for r in recs if r["model_key"] == K[22]))
       < 1e-6)
    # a second session finds every answer (the registry of sessions names run p1)
    n = len(Fake.sent)
    c2 = run(["--run", "p1b", "--block", "1", "--round", "1", "--run-cap", "100"])
    ck("second session sends nothing", c2 == 0 and "nothing to do" in run.out and len(Fake.sent) == n)
    # round 2 started but not finished: the block cannot be closed
    c3 = run(["--run", "p2", "--block", "1", "--round", "2", "--run-cap", "100", "--models", K[22], "--max-calls", "3"])
    cc = run(["--run", "close1", "--block", "1", "--complete-block"])
    ck("partial round 2", c3 == 0 and len(records("p2")) == 3)
    ck("complete-block refused", isinstance(cc, str) and "cannot be closed" in cc and not led("block_complete"))
    c4 = run(["--run", "p2b", "--block", "1", "--round", "2", "--run-cap", "100", "--workers", "4"])
    ck("round 2 done", c4 == 0 and len(records("p2b")) == PER_ROUND - 3)
    cc2 = run(["--run", "close1", "--block", "1", "--complete-block", "--reason", "pilot done"])
    bc = led("block_complete")
    ck("block 1 closed on both rounds", cc2 == 0 and len(bc) == 1 and bc[0]["role"] == "respondent"
       and bc[0]["models"] is None and bc[0]["rounds"] == [1, 2] and bc[0]["planned"] == 2 * PER_ROUND
       and bc[0]["final_by_status"] == {"ok": 2 * PER_ROUND} and bc[0]["not_attempted"] == {})
    ck("closed in the books", S.Books("probe", write=False).closed("1", "respondent"))
    c5 = run(["--run", "p3", "--block", "1", "--round", "1", "--run-cap", "100", "--models", K[22]])
    ck("closed block not started", c5 in (0, 2) and len(Fake.sent) == n + PER_ROUND)
    ck("each prompt sent once, verbatim", all(v == 1 for v in collections.Counter(Fake.sent).values())
       and all(pid is not None for _, pid in Fake.sent))
    ck("no leaks", no_leaks(tmp))
    return ck.ok()


def t_block2_registered_hosted_first():
    ck = Checks("block2")
    tmp, models = setup("block2_no_d13", design_edit=lambda d: d.pop("registered_hosted"))
    open_blocks_before(2)
    c = run(["--run", "b2", "--block", "2", "--run-cap", "50"])
    ck("D13 refused", isinstance(c, str) and "decision D13" in c and not Fake.sent)
    tmp, models = setup("block2", design_edit=lambda d: d.update(registered_hosted=[22]))
    K, M = keymap(models)
    ids = list(FR["harmful"][0]) + list(FR["safe"][0])
    write_sealed("full", model_of(models, 4), ids[2:])          # sealed answers are not used (decision D18)
    write_sealed("full", model_of(models, 5), ids)
    ledger(kind="registration", tag="t")
    c0 = run(["--run", "b2", "--block", "2", "--run-cap", "50", "--models", f"{K[22]},{K[4]}"])
    ck("not before the freeze", c0 == 2 and "freeze" in run.out and not Fake.sent)
    ledger(kind="freeze", tag="f")
    c1 = run(["--run", "b2", "--block", "2", "--run-cap", "50", "--models", K[23]])
    ck("model 23 not registered", isinstance(c1, str) and "not respondents of block 2" in c1)
    c2 = run(["--run", "b2", "--block", "2", "--run-cap", "50", "--models", f"{K[4]},{K[22]},{K[5]}"])
    recs = records("b2")
    by = collections.Counter(r["model_key"] for r in recs)
    ck("counts", c2 == 0 and by == {K[22]: 390, K[4]: 390, K[5]: 390})
    first_local = min(i for i, r in enumerate(recs) if r["model_key"] == K[4])
    ck("hosted model first", first_local == 390)
    parts = collections.Counter((r["model_key"], r["part"]) for r in recs)
    ck("parts", parts[(K[22], "frame_harmful")] == 300 and parts[(K[22], "frame_safe")] == 90)
    ck("fields", all(r["block"] == "2" and r["round"] is None and r["pilot"] is False and r["protocol"] == "2.3"
                     and r["final"] for r in recs))
    calls = led("call")
    ck("ledger", len(calls) == 390 and {e["item"] for e in calls} == {f"2|respondent|{K[22]}|frame_harmful",
                                                                      f"2|respondent|{K[22]}|frame_safe"})
    ses = jsonl(R.runs_log_path())
    ck("session line", ses[-1]["block"] == "2" and set(ses[-1]["models"]) == {K[4], K[5], K[22]})
    ck("no leaks", no_leaks(tmp))
    return ck.ok()


def t_block4_batch_lost_reply_and_collect():
    ck = Checks("block4")
    tmp, models = setup("block4")
    K, M = keymap(models)
    open_blocks_before(4)
    write_pilot("p0", [model_of(models, n) for n in (1, 2, 3, 9, 11)], returned={K[2]: "claude-other-model"})
    base = ["--run", "b4", "--block", "4", "--run-cap", "100", "--answer-runs", "p0"]
    # without --batch: direct models are skipped, routed models answer synchronously
    c1 = run(base + ["--models", f"{K[1]},{K[7]}"])
    ck("sync for routed models only", c1 == 0 and collections.Counter(r["model_key"] for r in records("b4"))
       == {K[7]: 150} and "SKIPPED" in run.out and not Fake.submits)
    # --batch: one chunk per direct model, reserved at the batch price before the submission
    c2 = run(base + ["--batch", "--models", f"{K[1]},{K[3]},{K[7]}"])
    ent = jsonl(R.batch_log_path("b4"))
    subs = [e for e in ent if e.get("batch_id")]
    pend = [e for e in ent if e.get("pending_ref")]
    ck("two chunks of 100", c2 == 0 and len(subs) == 2 and len(pend) == 2
       and all(len(e["items"]) == 100 for e in subs) and Fake.submits == [M[K[1]]["model"], M[K[3]]["model"]])
    ck("pending entry before the submission", all(ent.index(p) < ent.index(s) for p in pend for s in subs
                                                  if s["ref"] == p["pending_ref"]))
    good = True
    for e in subs:
        m = M[e["model_key"]]
        want = sum(bound(m, p, factor=R.BATCH_FACTOR) for p in e["items"].values())
        res = [x for x in led("batch_reservation") if x["batch_id"] == e["ref"]]
        good &= len(res) == 1 and abs(res[0]["spent_usd"] - round(want, 6)) < 1e-6
        good &= abs(e["reserved_usd"] - round(want, 6)) < 1e-6
    ck("chunk reservation = sum of the bounds at the batch price", good)
    # a model with an unsettled batch gets no other call
    n_sub = len(Fake.submits)
    run(base + ["--batch", "--models", K[1]])
    ck("no second chunk before collect", len(Fake.submits) == n_sub and "collect it first" in run.out)
    run(base + ["--sync", "--models", K[1]])
    ck("no sync call beside a batch", "unsettled or pending" in run.out
       and not [r for r in records("b4") if r["model_key"] == K[1]])
    # collect: every result settled against its own bound; the reservation returned; deleted at the provider
    s1 = next(e for e in subs if e["model_key"] == K[1])
    bid1 = s1["batch_id"]
    c5 = run(["--run", "b4", "--collect", bid1])
    rec1 = [r for r in records("b4") if r.get("batch_id") == bid1]
    ck("collected", c5 == 0 and len(rec1) == 100 and all(r["mode"] == "batch" and r["final"] and not r["error"]
                                                          and r["item"].startswith(f"4|respondent|{K[1]}|")
                                                          for r in rec1))
    calls = [e for e in led("call") if e.get("batch_id") == bid1]
    st = [e for e in led("batch_settlement") if e["batch_id"] == bid1]
    cid_of = {p: c for c, p in s1["items"].items()}
    ck("each result against its bound", len(calls) == 100 and all(
        abs(e["reserved_usd"] - round(s1["bounds"][cid_of[e["prompt_id"]]], 6)) < 1e-9
        and e["spent_usd"] <= e["reserved_usd"] for e in calls))
    ck("reservation returned", len(st) == 1 and abs(st[0]["spent_usd"] + s1["reserved_usd"]) < 1e-6)
    ck("deleted at the provider", bid1 in Fake.deleted)
    c6 = run(["--run", "b4", "--collect", bid1])
    ck("second collect refused", isinstance(c6, str) and "already collected" in c6)
    run(base + ["--batch", "--models", K[1]])
    s1b = [e for e in jsonl(R.batch_log_path("b4")) if e.get("batch_id") and e["model_key"] == K[1]]
    ck("next chunk = the 50 left", len(s1b) == 2 and len(s1b[1]["items"]) == 50
       and not set(s1b[1]["items"].values()) & set(s1["items"].values()))
    # a lost reply: the batch exists, the reply is lost; never submitted again, adopted after a console check
    Fake.batch_rules[M[K[9]]["model"]] = ["lost"]
    c8 = run(base + ["--batch", "--models", K[9]])
    ck("lost reply stops the model", c8 == 3 and "outcome unknown" in run.out)
    n_sub = len(Fake.submits)
    run(base + ["--batch", "--models", K[9]])
    ck("never submitted again", len(Fake.submits) == n_sub and "unknown outcome" in run.out)
    run(base + ["--sync", "--models", K[9]])
    ck("no sync call beside a pending submission", not [r for r in records("b4") if r["model_key"] == K[9]])
    ref9 = next(e["pending_ref"] for e in jsonl(R.batch_log_path("b4")) if e.get("model_key") == K[9])
    bid9 = next(b for b, v in Fake.batches.items() if v["model"] == M[K[9]]["model"])
    c10 = run(["--run", "b4", "--adopt", bid9, "--ref", ref9])
    c11 = run(["--run", "b4", "--collect", bid9])
    ck("adopted and collected", c10 == 0 and c11 == 0 and len([r for r in records("b4")
                                                                if r.get("batch_id") == bid9]) == 100)
    # no batch was created: released after a console check (the upload deleted), then submitted again
    Fake.batch_rules[M[K[11]]["model"]] = ["none"]
    run(base + ["--batch", "--models", K[11]])
    ref11 = next(e["pending_ref"] for e in jsonl(R.batch_log_path("b4")) if e.get("model_key") == K[11])
    res11 = next(x for x in led("batch_reservation") if x["batch_id"] == ref11)
    c13 = run(["--run", "b4", "--release", ref11])
    rel = [x for x in led("batch_release") if x.get("ref") == ref11]
    ck("released", c13 == 0 and len(rel) == 1 and abs(rel[0]["spent_usd"] + res11["spent_usd"]) < 1e-9
       and Fake.uploads_deleted == ["file-upload-1"])
    run(base + ["--batch", "--models", K[11]])
    ck("submitted after the release", sum(1 for x in Fake.submits if x == M[K[11]]["model"]) == 2
       and any(e.get("batch_id") and e["model_key"] == K[11] for e in jsonl(R.batch_log_path("b4"))))
    # a rejected submission (4xx): nothing was created, the reservation is released at once
    s3 = next(e for e in subs if e["model_key"] == K[3])
    run(["--run", "b4", "--collect", s3["batch_id"]])
    Fake.batch_rules[M[K[3]]["model"]] = [FakeHTTP(400, "invalid batch input")]
    c14 = run(base + ["--batch", "--models", K[3]])
    ck("rejected submission released", c14 == 3 and "rejected" in run.out
       and len([x for x in led("batch_release") if x.get("error") == "FakeHTTP 400"]) == 1)
    run(base + ["--batch", "--models", K[3]])
    ck("submitted after the rejection", sum(1 for x in Fake.submits if x == M[K[3]]["model"]) == 3)
    # the pilot's returned identifier is checked before any batch
    c15 = run(base + ["--batch", "--models", K[2]])
    ck("pilot returned ID checked", isinstance(c15, str) and "do not start with" in c15)
    c16 = run(["--run", "b4", "--block", "4", "--batch", "--run-cap", "100", "--models", K[2]])
    ck("no pilot, no batch", isinstance(c16, str) and "no pilot answer" in c16)
    # money: the ledger equals the results, the open reservations and nothing else
    lines = jsonl(S.LEDGER)
    open_res = sum(x["spent_usd"] for x in lines if x.get("kind") == "batch_reservation"
                   and x["batch_id"] not in {e.get("ref") for e in lines if e.get("kind") in ("batch_settlement",
                                                                                            "batch_release")})
    total = sum(float(x.get("spent_usd") or 0) for x in lines)
    ck("ledger = calls + open reservations", abs(total - sum(x["spent_usd"] for x in lines if x.get("kind") == "call")
                                                 - open_res) < 1e-6)
    ck("no leaks", no_leaks(tmp))
    return ck.ok()


def t_batch_item_kinds_overrun_and_stale():
    ck = Checks("batch items")
    tmp, models = setup("batch_items")
    K, M = keymap(models)
    open_blocks_before(4)
    write_pilot("p0", [model_of(models, 1)])
    base = ["--run", "b4", "--block", "4", "--batch", "--run-cap", "100", "--answer-runs", "p0", "--models", K[1]]

    def kinds(i, cid, prompt, cfg):
        if i == 0:
            return [(cid, None, (400, '{"error":{"type":"invalid_request_error","message":"input length exceeds '
                                      'the limit"}}'))]
        if i == 1:
            return [(cid, None, (400, '{"error":{"type":"invalid_request_error","message":"Request rejected"}}'))]
        if i == 2:
            return [(cid, None, (400, '{"error":{"code":"content_filter","message":"SYNTHETIC-QUOTE"}}'))]
        if i == 3:
            return [(cid, None, (None, "batch_result:canceled"))]
        if i == 4:
            return [(cid, None, ("parse_error", "KeyError"))]
        if i == 5:
            return [(cid, None, (400, '{"error":{"message":"max_tokens: 99999 > 64000"}}'))]
        if i == 6:
            return [(cid, dict(answer(cfg, prompt), model_returned="another-model"), None)]
        if i == 7:
            return [(cid, dict(answer(cfg, prompt), cost_reported=5.0), None),
                    (None, None, ("parse_error", "unreadable_line")), ("unknown_cid", answer(cfg, prompt), None)]
        return None
    Fake.result_rules[M[K[1]]["model"]] = kinds
    run(base)
    sub = next(e for e in jsonl(R.batch_log_path("b4")) if e.get("batch_id"))
    bid, by_cid = sub["batch_id"], {c: p for c, p in sub["items"].items()}
    cids = sorted(by_cid)
    c1 = run(["--run", "b4", "--collect", bid])
    recs = {r["prompt_id"]: r for r in records("b4") if r.get("batch_id") == bid}
    rec = [recs.get(by_cid[c]) for c in cids]
    ck("collect", c1 == 0 and len(recs) == 99 and rec[6] is None)
    ck("overflow: final error", rec[0]["final"] and rec[0]["final_error"] and rec[0]["failure_kind"] == "overflow"
       and rec[0]["answer_status"] == "error")
    ck("suspected block: final", rec[1]["final"] and rec[1]["answer_status"] == "provider_block_suspected"
       and not rec[1]["error"])
    ck("moderation: final", rec[2]["final"] and rec[2]["answer_status"] == "provider_block")
    ck("canceled: pending", not rec[3]["final"] and rec[3]["pending"] and rec[3]["cost_usd"] == 0)
    ck("parse error: charged at its bound, pending", not rec[4]["final"]
       and abs(rec[4]["cost_usd"] - rec[4]["reserved_usd"]) < 1e-9 and rec[4]["cost_usd"] > 0)
    ck("parameter error: not final, warned", not rec[5]["final"] and rec[5]["failure_kind"] == "config"
       and "parameter" in run.out)
    ck("another model's answer is not recorded", "another model" in run.out)
    over = [e for e in led("overrun") if e.get("batch_id") == bid]
    ck("overrun recorded", len(over) >= 1 and S.Books("probe", write=False).overrun_open)
    flagged = [e for e in led("call") if e.get("batch_id") == bid and e.get("overrun") is True]
    without = [e for e in led() if e.get("kind") != "overrun"]       # as after a crash before each overrun line
    real_read = S.read_ledger
    S.read_ledger = lambda *a: without
    try:
        still = S.Books("probe", write=False).overrun_open
    finally:
        S.read_ledger = real_read
    ck("the stop survives without the overrun lines", flagged and still)
    st = next(e for e in led("batch_settlement") if e["batch_id"] == bid)
    worst = max(sub["bounds"].values())
    ck("lines without a request charged at the largest bound", st["unreadable_lines"] == 1
       and st["unattributed_lines"] == 1 and st["model_mismatch_lines"] == 1
       and abs(st["unattributed_usd"] - round(3 * worst, 6)) < 1e-6)
    ck("public log without error body", "SYNTHETIC-QUOTE" not in R.calls_log_path("b4").read_text(encoding="utf-8"))
    c2 = run(base)
    ck("an open overrun stops paid work", c2 == 2 and "settled above its reservation" in run.out)
    ledger(kind="overrun_resolved", reason="test")
    run(base)
    sub2 = [e for e in jsonl(R.batch_log_path("b4")) if e.get("batch_id")][-1]
    again = {by_cid[cids[i]] for i in (3, 4, 5, 6)}
    ck("not final answers go in the next chunk", len(sub2["items"]) == 54 and again <= set(sub2["items"].values()))
    # a batch older than 48 h blocks new paid work; collect cancels it first
    Fake.result_rules = {}
    Fake.running.add(sub2["batch_id"])
    p = R.batch_log_path("b4")
    old = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=49)).isoformat(timespec="seconds")
    lines = [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
    for e in lines:
        if e.get("batch_id") == sub2["batch_id"] or e.get("pending_ref") == sub2["ref"]:
            e["ts"] = old
    p.write_text("".join(json.dumps(e) + "\n" for e in lines), encoding="utf-8")
    c3 = run(["--run", "b4", "--block", "4", "--run-cap", "100", "--answer-runs", "p0", "--models", K[7]])
    ck("stale batch blocks paid work", isinstance(c3, str) and "more than 48 h" in c3)
    c4 = run(["--run", "b4", "--collect", sub2["batch_id"]])
    ck("stale batch cancelled, then collected", c4 == 0 and any(e.get("cancel_requested") == sub2["batch_id"]
                                                                 for e in jsonl(p)))
    ck("no leaks", no_leaks(tmp))
    return ck.ok()


def t_batch_overrun_aggregate_only():
    """Section 12.5 (review round 8): a batch whose items all settle within their bounds but whose lines without a
    request take the total above the batch reservation stops every paid call; the stop is on the batch settlement
    line itself, so a crash before the overrun line keeps it."""
    ck = Checks("batch aggregate overrun")
    tmp, models = setup("batch_aggregate")
    K, M = keymap(models)
    open_blocks_before(4)
    write_pilot("p0", [model_of(models, 1)])
    base = ["--run", "b4", "--block", "4", "--batch", "--run-cap", "100", "--answer-runs", "p0", "--models", K[1]]

    def kinds(i, cid, prompt, cfg):
        if i == 0:
            return [(cid, answer(cfg, prompt), None)] + [(None, None, ("parse_error", "unreadable_line"))] * 300
        return None
    Fake.result_rules[M[K[1]]["model"]] = kinds
    run(base)
    bid = next(e for e in jsonl(R.batch_log_path("b4")) if e.get("batch_id"))["batch_id"]
    c = run(["--run", "b4", "--collect", bid])
    calls = [e for e in led("call") if e.get("batch_id") == bid]
    st = next(e for e in led("batch_settlement") if e["batch_id"] == bid)
    ck("no item above its bound", c == 0 and calls and not any(e.get("overrun") for e in calls)
       and all(e["spent_usd"] <= e["reserved_usd"] + 1e-12 for e in calls))
    ck("the batch settlement carries the stop", st.get("overrun") is True and led("overrun"))
    without = [e for e in led() if e.get("kind") != "overrun"]
    real_read = S.read_ledger
    S.read_ledger = lambda *a: without
    try:
        still = S.Books("probe", write=False).overrun_open
    finally:
        S.read_ledger = real_read
    ck("the stop survives without the overrun line", still)
    return ck.ok()


def t_outcomes_final_suspected_config():
    ck = Checks("outcomes")
    tmp, models = setup("outcomes")
    K, M = keymap(models)
    ledger(kind="registration", tag="t")
    api = list(PILOT["rounds"][0]["api"])
    harm = [p for p in api if ROWS[p]["expected"] == "refuse"]
    safe = [p for p in api if ROWS[p]["expected"] == "comply"]
    seen = collections.Counter()
    moderation = {"text": "", "provider_block": True, "stop_reason": "moderation_block:403",
                  "served_provider": "https://openrouter.ai/api/v1", "model_returned": None,
                  "error_body": "flagged_input SYNTHETIC-QUOTE"}

    def rule7(cfg, pid):
        seen[pid] += 1
        if pid == harm[0]:
            return providers.SuspectedBlock(400, "SYNTHETIC-QUOTE")
        if pid == safe[0]:
            return providers.SuspectedBlock(403, "SYNTHETIC-QUOTE")
        if pid == harm[1]:
            return moderation
        if pid == harm[2]:
            return FakeHTTP(400, "This model's maximum context length is 8192 tokens SYNTHETIC-QUOTE")
        if pid == harm[3]:
            return FakeHTTP(422, "unprocessable request SYNTHETIC-QUOTE")
        if pid == safe[1] and seen[pid] == 1:
            return FakeHTTP(429, "rate limit")
        return "ok"
    Fake.rules[M[K[7]]["model"]] = rule7
    Fake.rules[M[K[8]]["model"]] = [FakeHTTP(400, "unsupported parameter: temperature")]
    Fake.rules[M[K[1]]["model"]] = [providers.ResponseParseError("KeyError")]
    c = run(["--run", "o1", "--block", "1", "--round", "1", "--run-cap", "100",
             "--models", f"{K[7]},{K[8]},{K[1]}"])
    recs = records("o1")
    r7 = collections.defaultdict(list)
    for r in recs:
        if r["model_key"] == K[7]:
            r7[r["prompt_id"]].append(r)
    ck("exit 3 (a model stopped)", c == 3 and "configuration of the model is wrong" in run.out)
    ck("suspected block on a harmful prompt: final, sent once", len(r7[harm[0]]) == 1 and seen[harm[0]] == 1
       and r7[harm[0]][0]["answer_status"] == "provider_block_suspected" and r7[harm[0]][0]["final"])
    ck("suspected block on a safe prompt: final, sent once", len(r7[safe[0]]) == 1 and seen[safe[0]] == 1
       and r7[safe[0]][0]["answer_status"] == "provider_block_suspected" and r7[safe[0]][0]["final"])
    ck("moderation: final", r7[harm[1]][0]["answer_status"] == "provider_block" and len(r7[harm[1]]) == 1)
    ck("overflow: final error", r7[harm[2]][0]["final_error"] and r7[harm[2]][0]["failure_kind"] == "overflow"
       and r7[harm[2]][0]["answer_status"] == "error" and r7[harm[2]][0]["final"] and seen[harm[2]] == 1)
    ck("rejected: final error", r7[harm[3]][0]["final_error"] and r7[harm[3]][0]["failure_kind"] == "rejected"
       and seen[harm[3]] == 1)
    ck("transient then ok", [x["final"] for x in r7[safe[1]]] == [False, True] and r7[safe[1]][0]["pending"] is False
       and r7[safe[1]][0]["failure_kind"] == "transient" and SLEEPS == [10, 10])
    ck("model 7 answered every prompt", len(r7) == 20 and all(v[-1]["final"] for v in r7.values()))
    ck("returned model and serving provider on every record", all(
        "model_returned" in r and "served_provider" in r and r["protocol"] == "2.3" and "final_error" in r
        for r in recs))
    r8 = [r for r in recs if r["model_key"] == K[8]]
    ck("parameter error stops the model", len(r8) == 1 and not r8[0]["final"] and r8[0]["failure_kind"] == "config"
       and sum(1 for m, _ in Fake.sent if m == M[K[8]]["model"]) == 1)
    r1 = [r for r in recs if r["model_key"] == K[1]]
    ck("unparsed response charged at its reservation, sent again", len(r1) == 21 and not r1[0]["final"]
       and abs(r1[0]["cost_usd"] - r1[0]["reserved_usd"]) < 1e-9 and r1[1]["final"])
    calls = led("call")
    ck("one call line per paid attempt", len(calls) == len(recs))
    zero = {e["prompt_id"] for e in calls if e["model_key"] == K[7] and e["spent_usd"] == 0}
    ck("4xx rejections not charged", {harm[0], safe[0], harm[2], harm[3]} <= zero)
    pub = R.calls_log_path("o1").read_text(encoding="utf-8")
    ck("public log: no error body", "SYNTHETIC-QUOTE" not in pub and '"error_body_sha256"' in pub)
    # the next session sends model 8's prompts after the fix, nothing again for model 7
    Fake.rules = {}
    n7 = sum(1 for m, _ in Fake.sent if m == M[K[7]]["model"])
    c2 = run(["--run", "o2", "--block", "1", "--round", "1", "--run-cap", "100", "--models", f"{K[7]},{K[8]}"])
    ck("resume", c2 == 0 and sum(1 for m, _ in Fake.sent if m == M[K[7]]["model"]) == n7
       and len(records("o2")) == 20)
    ck("no leaks", no_leaks(tmp))
    return ck.ok()


def t_pending_five_in_a_row_and_resume():
    ck = Checks("pending")
    tmp, models = setup("pending")
    K, M = keymap(models)
    ledger(kind="registration", tag="t")
    Fake.rules[M[K[10]]["model"]] = lambda cfg, pid: FakeHTTP(503, "server error")
    c = run(["--run", "q1", "--block", "1", "--round", "1", "--run-cap", "100", "--models", f"{K[10]},{K[12]}"])
    r10 = [r for r in records("q1") if r["model_key"] == K[10]]
    ck("stopped after five pending prompts", c == 3 and "5 consecutive pending prompts" in run.out)
    ck("four attempts per prompt, the last pending", len(r10) == 20 and sum(r["pending"] for r in r10) == 5
       and not any(r["final"] for r in r10) and [r["try"] for r in r10[:4]] == [1, 2, 3, 4])
    ck("waits of the settings", SLEEPS == [10, 30, 90] * 5)
    ck("other model unaffected", len([r for r in records("q1") if r["model_key"] == K[12]]) == 20)
    ck("server errors charged at the reservation", all(e["spent_usd"] == e["reserved_usd"]
                                                       for e in led("call") if e["model_key"] == K[10]))
    Fake.rules = {}
    c2 = run(["--run", "q2", "--block", "1", "--round", "1", "--run-cap", "100", "--models", f"{K[10]},{K[12]}"])
    ck("resume sends the pending and the unsent prompts", c2 == 0 and collections.Counter(
        r["model_key"] for r in records("q2")) == {K[10]: 20})
    return ck.ok()


def t_overrun_stops_paid_calls():
    ck = Checks("overrun")
    tmp, models = setup("overrun")
    K, M = keymap(models)
    ledger(kind="registration", tag="t")
    Fake.rules[M[K[7]]["model"]] = [{"cost_reported": 5.0}]
    c = run(["--run", "v1", "--block", "1", "--round", "1", "--run-cap", "100", "--models", f"{K[7]},{K[8]}"])
    recs = records("v1")
    ck("stopped", c == 3 and "an overrun is open" in run.out)
    ck("one call only", len(recs) == 1 and recs[0]["cost_usd"] == 5.0 and recs[0]["reserved_usd"] < 5.0)
    ov = led("overrun")
    ck("overrun line", len(ov) == 1 and ov[0]["model_key"] == K[7] and ov[0]["settled_usd"] == 5.0)
    c2 = run(["--run", "v2", "--block", "1", "--round", "1", "--run-cap", "100", "--models", K[8]])
    ck("no session while it is open", c2 == 2 and "settled above its reservation" in run.out
       and not records("v2"))
    ledger(kind="overrun_resolved", reason="test")
    c3 = run(["--run", "v3", "--block", "1", "--round", "1", "--run-cap", "100", "--models", K[8]])
    ck("after the resolution", c3 == 0 and len(records("v3")) == 20)
    return ck.ok()


def t_run_cap_and_study_cap():
    ck = Checks("caps")
    tmp, models = setup("caps")
    K, M = keymap(models)
    ledger(kind="registration", tag="t")
    m7 = M[K[7]]
    near = lambda cfg, pid: {"cost_reported": 0.9 * bound(cfg, pid)}       # noqa: E731
    c0 = run(["--run", "k0", "--block", "1", "--round", "1", "--models", K[7]])
    ck("a paid session needs a run cap", isinstance(c0, str) and "run cap" in c0 and not Fake.sent)
    os.environ["BUDGET_USD"] = "0.0001"
    try:
        c1 = run(["--run", "k1", "--block", "1", "--round", "1", "--models", K[7]])
    finally:
        os.environ.pop("BUDGET_USD", None)
    ck("BUDGET_USD as run cap", c1 == 3 and "run cap of this session is reached" in run.out and not Fake.sent)
    b = max(bound(m7, p) for p in PILOT["rounds"][0]["api"])
    Fake.rules[m7["model"]] = near
    c2 = run(["--run", "k2", "--block", "1", "--round", "1", "--run-cap", f"{3.5 * b:.6f}", "--models", K[7]])
    spent = sum(e["spent_usd"] for e in led("call") if e.get("run") == "k2")
    ck("run cap: three calls fit", c2 == 3 and len(records("k2")) == 3 and spent <= 3.5 * b
       and "run cap of this session is reached" in run.out)
    # the study cap beside the holds: holds of block 1 made tiny so that the start rule passes
    def tiny(h):
        for it in h["items"]:
            if str(it["block"]) == "1":
                it["usd_per_call"] = 1e-9
    tmp, models = setup("caps_study", cap=2.5 * b, holds_edit=tiny)
    ledger(kind="registration", tag="t")
    Fake.rules[m7["model"]] = near
    c3 = run(["--run", "k3", "--block", "1", "--round", "1", "--run-cap", "100", "--models", K[7]])
    ck("study cap: two calls fit", c3 == 3 and len(records("k3")) == 2
       and "would pass the cap beside the holds" in run.out and S.Books("p", write=False).spent <= 2.5 * b)
    return ck.ok()


def t_preflight_and_d2():
    ck = Checks("preflight")
    api = list(PILOT["rounds"][0]["api"])
    tmp, models = setup("d2_safe_only", models_edit=lambda ms: via_openrouter_14(ms, "safe_only"))
    K, M = keymap(models)
    ledger(kind="registration", tag="t")
    c = run(["--run", "d1", "--block", "1", "--round", "1", "--run-cap", "100", "--models", f"{K[D2_N]},{K[7]}"])
    r14 = [r for r in records("d1") if r["model_key"] == K[D2_N]]
    pre = {e["model_key"]: e for e in led("preflight")}
    ck("safe prompts only", c == 0 and len(r14) == sum(1 for p in api if ROWS[p]["expected"] == "comply")
       and all(ROWS[r["prompt_id"]]["expected"] == "comply" for r in r14) and "not_sent_d2" in run.out)
    ck("preflight line", pre[K[D2_N]]["ok"] and pre[K[D2_N]]["safe_only"] and pre[K[7]]["ok"]
       and not pre[K[7]]["safe_only"])
    ck("D2 harmful prompts never sent", not any(m == M[K[D2_N]]["model"] and ROWS[p]["expected"] == "refuse"
                                                for m, p in Fake.sent))
    c = run(["--run", "d1close", "--block", "1", "--complete-block", "--models", K[D2_N]])
    bc = [e for e in led("block_complete") if e.get("role") == "respondent"]
    ck("D2 close: the harmful prompts are excluded under D2, not abandoned",
       c == 0 and bool(bc) and bc[-1].get("excluded_d2") == {K[D2_N]: sum(1 for p in api if ROWS[p]["expected"] == "refuse")}
       and not bc[-1]["not_attempted"] and not led("block_abandon"))
    tmp, models = setup("d2_none", models_edit=lambda ms: via_openrouter_14(ms, None))
    ledger(kind="registration", tag="t")
    c = run(["--run", "d2", "--block", "1", "--round", "1", "--run-cap", "100", "--models", f"{K[D2_N]},{K[7]}"])
    pre = {e["model_key"]: e for e in led("preflight")}
    ck("D2 undecided: no call", c == 3 and not [r for r in records("d2") if r["model_key"] == K[D2_N]]
       and "preflight: " in run.out and pre[K[D2_N]]["ok"] is False and pre[K[7]]["ok"] is True)
    ck("the other model answers", len([r for r in records("d2") if r["model_key"] == K[7]]) == 20)

    def price(ms):
        model_of(ms, 7)["pin"]["completion_usd_per_m"] = 0.123
    tmp, models = setup("preflight_price", models_edit=price)
    ledger(kind="registration", tag="t")
    c = run(["--run", "d3", "--block", "1", "--round", "1", "--run-cap", "100", "--models", f"{K[7]},{K[1]}"])
    pl = led("preflight")
    ck("price change: no call", c == 3 and len(pl) == 1 and not pl[0]["ok"] and "completion_usd_per_m" in
       " ".join(pl[0]["problems"]) and not [r for r in records("d3") if r["model_key"] == K[7]])
    ck("direct model unaffected", len([r for r in records("d3") if r["model_key"] == K[1]]) == 20)
    tmp, models = setup("preflight_direct")
    ledger(kind="registration", tag="t")
    run(["--run", "d4", "--block", "1", "--round", "1", "--run-cap", "100", "--models", K[1]])
    ck("no endpoint list for direct models", Fake.zdr_calls == 0 and not led("preflight"))
    return ck.ok()


def t_provider_stop():
    ck = Checks("provider stop")
    tmp, models = setup("stop")
    K, M = keymap(models)
    ledger(kind="registration", tag="t")
    ledger(kind="provider_stop", account="openrouter", host=M[K[7]]["pin"]["provider_name"], reason="test")
    c = run(["--run", "s1", "--block", "1", "--round", "1", "--run-cap", "100", "--models", f"{K[7]},{K[8]}"])
    by = collections.Counter(r["model_key"] for r in records("s1"))
    ck("host stop", c == 3 and by == {K[8]: 20} and "provider stop recorded" in run.out)
    ledger(kind="provider_stop", account="anthropic", host=None, reason="test")
    run(["--run", "s2", "--block", "1", "--round", "1", "--run-cap", "100", "--models", f"{K[1]},{K[2]},{K[3]}"])
    by = collections.Counter(r["model_key"] for r in records("s2"))
    ck("account stop", by == {K[3]: 20})
    ledger(kind="provider_resume", account="openrouter", host=M[K[7]]["pin"]["provider_name"], reason="test")
    run(["--run", "s3", "--block", "1", "--round", "1", "--run-cap", "100", "--models", K[7]])
    ck("resumed", len(records("s3")) == 20)
    return ck.ok()


def t_block_order_registration_and_arguments():
    ck = Checks("order")
    tmp, models = setup("order")
    K, M = keymap(models)
    c = run(["--run", "a1", "--block", "1", "--round", "1", "--run-cap", "100", "--models", K[7]])
    ck("registration first", c == 2 and "registration is not recorded" in run.out and not Fake.sent)
    ledger(kind="registration", tag="t")
    write_pilot("p0", [model_of(models, 7)])
    c = run(["--run", "a2", "--block", "4", "--run-cap", "100", "--models", K[7]])
    ck("freeze before block 4", c == 2 and "freeze" in run.out and not Fake.sent)
    ledger(kind="freeze", tag="f")
    c = run(["--run", "a3", "--block", "4", "--run-cap", "100", "--models", K[7]])
    ck("block 4 after block 3", c == 2 and "starts after block 3 is closed" in run.out and not Fake.sent)
    close(1, "respondent")
    c = run(["--run", "a4", "--block", "1", "--round", "2", "--run-cap", "100", "--models", K[7]])
    ck("closed block", c == 2 and "closed for the respondent calls" in run.out and not Fake.sent)
    for argv, words in ((["--run", "x", "--block", "1", "--round", "1", "--batch"], "--batch is for block 4"),
                        (["--run", "x", "--block", "2", "--round", "1"], "--round is for block 1"),
                        (["--run", "x", "--block", "1"], "--round 1 or --round 2"),
                        (["--run", "full", "--block", "1", "--round", "1"], "sealed"),
                        (["--block", "1", "--round", "1"], "--run is required"),
                        (["--run", "x", "--block", "4", "--batch", "--sync"], "exclude each other"),
                        (["--run", "x", "--block", "1", "--complete-block", "--dry-run"], "sends nothing")):
        c = run(argv)
        ck(f"refused: {words}", isinstance(c, str) and words in c)
    ck("nothing sent", not Fake.sent and not led("call"))
    return ck.ok()


def t_holds_cover_every_paid_call():
    ck = Checks("holds")
    for name, edit, words in (
            ("holds_missing", lambda h: h.update(items=[it for it in h["items"]
                                                        if it.get("id") != "1|respondent|deepseek-v4.1-flash|pilot_r1"
                                                        and not (it["block"] in (1, "1") and it["role"] == "respondent"
                                                                 and it["model_key"] == "deepseek-v4.1-flash"
                                                                 and it["part"] == "pilot_r1")]),
             "does not cover"),
            ("holds_short", lambda h: [it.update(calls=10) for it in h["items"]
                                       if str(it["block"]) == "1" and it["role"] == "respondent"
                                       and it["model_key"] == "deepseek-v4.1-flash" and it["part"] == "pilot_r1"],
             "20 planned calls > 10")):
        tmp, models = setup(name, holds_edit=edit)
        K, M = keymap(models)
        ledger(kind="registration", tag="t")
        c = run(["--run", "h", "--block", "1", "--round", "1", "--run-cap", "100", "--models", f"{K[7]},{K[15]}"])
        ck(name, isinstance(c, str) and words in c and not Fake.sent and not led("call") and not records("h"))
        ck(name + ": lock released", not S.SPEND_LOCK.exists())
    return ck.ok()


def t_complete_block_models_and_abandon():
    ck = Checks("complete")
    tmp, models = setup("complete")
    K, M = keymap(models)
    open_blocks_before(2)
    c = run(["--run", "b2", "--block", "2", "--run-cap", "100", "--models", K[22]])
    ck("model 22 answered", c == 0 and len(records("b2")) == 390)
    bc2 = lambda: [e for e in led("block_complete") if e["block"] == "2"]      # noqa: E731
    c = run(["--run", "close", "--block", "2", "--complete-block", "--models", K[23]])
    ck("open answers: refused", isinstance(c, str) and "cannot be closed" in c and not bc2())
    c = run(["--run", "close", "--block", "2", "--complete-block", "--models", K[22]])
    bc = bc2()
    ck("closed for model 22", c == 0 and len(bc) == 1 and bc[-1]["models"] == [K[22]]
       and bc[-1]["final_by_status"] == {"ok": 390} and bc[-1]["role"] == "respondent")
    books = S.Books("probe", write=False)
    ck("books", books.closed("2", "respondent", K[22]) and not books.closed("2", "respondent"))
    ledger(kind="block_abandon", block="2", models=[K[23]], reason="test")
    n = len(Fake.sent)
    c = run(["--run", "b2b", "--block", "2", "--run-cap", "100", "--models", K[23]])
    ck("abandoned model: no call", len(Fake.sent) == n and "not_sent_closed" in run.out)
    c = run(["--run", "close", "--block", "2", "--complete-block", "--models", K[23], "--reason", "abandoned"])
    bc = bc2()
    ck("closed by abandonment", c == 0 and bc[-1]["models"] == [K[23]] and bc[-1]["not_attempted"] == {"abandoned": 390})
    c = run(["--run", "close", "--block", "2", "--complete-block"])
    ck("whole block: local answers open", isinstance(c, str) and "cannot be closed" in c)
    return ck.ok()


def t_local_identity_checks():
    ck = Checks("identity")
    tmp, models = setup("digest", models_edit=lambda ms: model_of(ms, 15).update(digest="sha256:another-build"))
    K, M = keymap(models)
    ledger(kind="registration", tag="t")
    c = run(["--run", "i1", "--block", "1", "--round", "1", "--run-cap", "100", "--models", f"{K[15]},{K[7]}"])
    ck("digest mismatch: nothing sent", isinstance(c, str) and "installed digest" in c and "nothing was sent" in c
       and not Fake.sent and not led("call"))
    tmp, models = setup("ollama_version")
    ledger(kind="registration", tag="t")
    Fake.ollama_version = "0.40.14"
    c = run(["--run", "i2", "--block", "1", "--round", "1", "--models", K[15]])
    ck("Ollama version pinned", isinstance(c, str) and "0.40.14 != 0.40.15" in c and not Fake.sent)
    Fake.ollama_version = "0.40.15"
    Fake.rules[M[K[1]]["model"]] = lambda cfg, pid: {"model_returned": "claude-other-model"}
    Fake.rules[M[K[7]]["model"]] = lambda cfg, pid: {"served_provider": "Another Host"}
    c = run(["--run", "i3", "--block", "1", "--round", "1", "--run-cap", "100", "--models", f"{K[15]},{K[1]},{K[7]}"])
    recs = records("i3")
    man = jsonl(R.manifest_path("i3"))
    ck("local run without the lock file left behind", c == 0 and not S.SPEND_LOCK.exists())
    ck("identity mismatches recorded", all(r["identity_match"] is False for r in recs if r["model_key"] in (K[1], K[7]))
       and "identity_mismatch" in run.out)
    ck("local identity in the manifest", any(e.get("model_key") == K[15] and e.get("digest") == INSTALLED[
        M[K[15]]["model"]] and e.get("ollama_version") == "0.40.15" for e in man)
       and any(e.get("event") == "vram_after_first_call" for e in man))
    ck("local records", sum(1 for r in recs if r["model_key"] == K[15]) == 100
       and all(r["cost_usd"] == 0 and r["digest"] == INSTALLED[M[K[15]]["model"]] for r in recs
               if r["model_key"] == K[15]))
    return ck.ok()


def t_answer_guard_dry_run_and_errors():
    ck = Checks("guard")
    tmp, models = setup("guard")
    K, M = keymap(models)
    saved = A.RAW
    A.RAW = R.RAW                    # the scratch folder plays results/raw
    try:
        c = run(["--run", "g1", "--block", "1", "--round", "1", "--run-cap", "100", "--models", K[7]])
        ck("no answer file read before the registration", isinstance(c, str) and "pilot registration" in c
           and not Fake.sent)
        c = run(["--block", "1", "--round", "1", "--dry-run"])
        ck("dry run before the registration", c == 0 and "dry run shows the plan only" in run.out
           and "WOULD NOT START" in run.out)
        ck("dry run writes nothing", not list((tmp / "logs").iterdir()) and not list((tmp / "raw").iterdir()))
    finally:
        A.RAW = saved
    ledger(kind="registration", tag="t")
    c = run(["--block", "4", "--dry-run"])
    ck("dry run of block 4", c == 0 and "WOULD NOT START" in run.out and "freeze" in run.out
       and len(list((tmp / "logs").iterdir())) == 1)

    def broken(cfg):
        raise ValueError("SYNTHETIC-QUOTE")
    saved_make, saved_debug = R.MAKE_PROVIDER, os.environ.pop("AC_DEBUG", None)
    R.MAKE_PROVIDER = broken
    try:
        c = run(["--run", "g2", "--block", "1", "--round", "1", "--run-cap", "100", "--models", K[7]])
    finally:
        R.MAKE_PROVIDER = saved_make
        if saved_debug is not None:
            os.environ["AC_DEBUG"] = saved_debug
    ck("unexpected error: type and place only", isinstance(c, str) and c.startswith("stopped: ValueError at ")
       and "SYNTHETIC-QUOTE" not in c and not S.SPEND_LOCK.exists())
    return ck.ok()


def t_lock_and_interrupted_lines():
    ck = Checks("lock")
    tmp, models = setup("lock")
    K, M = keymap(models)
    ledger(kind="registration", tag="t")
    S.SPEND_LOCK.write_text("{}", encoding="utf-8")
    c = run(["--run", "l1", "--block", "1", "--round", "1", "--run-cap", "100", "--models", K[7]])
    ck("paid session waits for the lock", isinstance(c, str) and "holds spend.lock" in c and not Fake.sent)
    c = run(["--run", "l2", "--block", "1", "--round", "1", "--models", K[15]])
    ck("local session runs beside it", c == 0 and len(records("l2")) == 100 and S.SPEND_LOCK.exists())
    S.SPEND_LOCK.unlink()
    # an answer line cut short by an interrupted write: skipped with a warning, its prompt sent again
    p = R.raw_path("l2")
    lines = p.read_text(encoding="utf-8").splitlines()
    p.write_text("\n".join(lines[:-1]) + "\n" + lines[-1][:40], encoding="utf-8")
    c = run(["--run", "l3", "--block", "1", "--round", "1", "--models", K[15]])
    ck("cut answer line sent again", c == 0 and len(records("l3")) == 1 and "skipping unreadable line" in run.err)
    # a ledger line cut short: no paid work until it is repaired
    with open(S.LEDGER, "a", encoding="utf-8") as f:
        f.write('{"kind": "call", "spent')
    c = run(["--run", "l4", "--block", "1", "--round", "1", "--run-cap", "100", "--models", K[7]])
    ck("cut ledger line stops paid work", isinstance(c, str) and "unreadable" in c and not records("l4")
       and not S.SPEND_LOCK.exists())
    return ck.ok()


# ---- decision D13: the availability check (Section 10.4) -------------------------------------------------------------

def avail_facts():
    """{model_key: its latest 'facts' line in the public availability log}."""
    return {e["model_key"]: e for e in jsonl(R.availability_log_path()) if e.get("kind") == "facts"}


def fact(line, i):
    """(holds, evidence) of fact i (1 to 3) of decision D13 in a facts line."""
    x = line[R.D13_FACTS[i - 1][0]]
    return x["holds"], x["evidence"]


def judge_pilot(keys, n=3):
    """The judge side of the pilot in the ledger: n final calls of each model, then the close of the role."""
    for k in keys:
        for _ in range(n):
            ledger(kind="call", role="judge", block="1", model_key=k, item=f"1|judge|{k}|pilot_r1", part="pilot_r1",
                   final=True, status="ok", reserved_usd=0.002, spent_usd=0.001)
    close(1, "judge")


def t_availability_check_facts_and_ledger():
    ck = Checks("availability")
    tmp, models = setup("availability")
    K, M = keymap(models)
    hosted = [K[22], K[23]]
    c = run(["--run", "d13", "--availability-check", "--run-cap", "1"])
    ck("registration first", c == 2 and "registration is not recorded" in run.out and not Fake.sent
       and Fake.zdr_calls == 0 and not led() and not S.SPEND_LOCK.exists())
    ledger(kind="registration", tag="t")
    c1 = run(["--run", "p1", "--block", "1", "--round", "1", "--run-cap", "100", "--models", ",".join(hosted)])
    c2 = run(["--run", "close1", "--block", "1", "--complete-block", "--models", ",".join(hosted)])
    judge_pilot(hosted)
    ck("pilot of the hosted models closed", c1 == 0 and c2 == 0 and len(records("p1")) == 40)
    sent, calls, design = len(Fake.sent), len(led("call")), R.DESIGN.read_text(encoding="utf-8")
    c = run(["--run", "d13", "--availability-check", "--run-cap", "1"])
    f = avail_facts()
    ck("runs before the freeze", c == 0 and not led("freeze"))
    ck("the three facts hold for both models", sorted(f) == sorted(hosted)
       and all(fact(x, i)[0] is True for x in f.values() for i in (1, 2, 3)))
    ck("evidence of fact 2", all("respondent: block 1 closed, 20 final calls" in fact(f[k], 2)[1]
                                 and "judge: block 1 closed, 3 final calls" in fact(f[k], 2)[1] for k in hosted))
    new = Fake.sent[sent:]
    ck("one test call per model, never a benchmark prompt",
       sorted(x for x, _ in new) == sorted(M[k]["model"] for k in hosted) and all(p is None for _, p in new)
       and all(r["prompt"].strip() != R.AVAILABILITY_PROMPT for r in ROWS.values()))
    pre = {e["model_key"]: e for e in led("preflight") if e.get("role") == "availability"}
    av = led("availability_call")
    ck("ledger: a preflight line and a call line per model", sorted(pre) == sorted(hosted)
       and all(e["ok"] and not e["safe_only"] for e in pre.values())
       and sorted(e["model_key"] for e in av) == sorted(hosted)
       and all(e["role"] == "availability" and e["final"] is True and e["status"] == "ok"
               and e["identity_match"] is True and e["prompt_sha256"] == sha(R.AVAILABILITY_PROMPT)
               and e["run"] == "d13" for e in av))
    ck("reservation = bound >= settlement", all(
        abs(e["reserved_usd"] - round(S.call_bound(M[e["model_key"]], R.AVAILABILITY_PROMPT,
                                                   M[e["model_key"]]["max_output_tokens"],
                                                   live=pre[e["model_key"]]["live"]), 6)) < 1e-9
        and 0 < e["spent_usd"] <= e["reserved_usd"] for e in av))
    lines = jsonl(S.LEDGER)
    ck("every preflight before the first test call",
       max(i for i, e in enumerate(lines) if e.get("kind") == "preflight" and e.get("role") == "availability")
       < min(i for i, e in enumerate(lines) if e.get("kind") == "availability_call"))
    books = S.Books("probe", write=False)
    ck("against the cap, in no holds item", len(led("call")) == calls and sum(books.final.values()) == 46
       and abs(books.spent - sum(e["spent_usd"] for e in led("call") + av)) < 1e-9)
    raw, pub = jsonl(R.availability_raw_path()), jsonl(R.availability_log_path())
    ck("the answer only in the private record", len(raw) == 2 and all(r["text"] == ANSWER for r in raw)
       and len(pub) == 4 and all("text" not in e and "error_body" not in e for e in pub))
    ck("no answer record, no session line", not (R.RAW / "responses_d13.jsonl").exists()
       and "d13" not in R.session_runs())
    ck("reported, not decided", "model 22" in run.out and "model 23" in run.out and run.out.count(": yes.") == 6
       and "decision is the PI's" in run.out and R.DESIGN.read_text(encoding="utf-8") == design)
    ck("lock released", not S.SPEND_LOCK.exists())
    ledger(kind="freeze", tag="f")
    sent = len(Fake.sent)
    c = run(["--run", "d13b", "--availability-check", "--run-cap", "1"])
    ck("refused after the freeze", c == 2 and "freeze is recorded" in run.out and len(Fake.sent) == sent)
    for argv, words in ((["--run", "x", "--availability-check", "--block", "1"], "takes --run, --models"),
                        (["--run", "x", "--availability-check", "--models", K[7]], "not hosted models"),
                        (["--availability-check"], "--run is required"),
                        (["--run", "full", "--availability-check"], "sealed"),
                        (["--run", "x", "--availability-check"], "run cap")):
        c = run(argv)
        ck(f"refused: {words}", isinstance(c, str) and words in c)
    ck("nothing else sent", len(Fake.sent) == sent and not S.SPEND_LOCK.exists())
    ck("no leaks", no_leaks(tmp))
    return ck.ok()


def t_availability_recovered_after_crash():
    """Section 12.5 (review rounds 6 and 7): a test call of the availability check whose answer was recorded is not
    sent again when the check runs again the same day, whether the process died before its ledger line (the
    reconciliation settles it at its recorded cost) or after it; its answer gives fact 3. A test call killed before
    its record is settled at its reservation as interrupted and is sent again."""
    ck = Checks("availability crash")

    def prepare(name):
        tmp, models = setup(name)
        K, M = keymap(models)
        hosted = [K[22], K[23]]
        ledger(kind="registration", tag="t")
        run(["--run", "p1", "--block", "1", "--round", "1", "--run-cap", "100", "--models", ",".join(hosted)])
        run(["--run", "close1", "--block", "1", "--complete-block", "--models", ",".join(hosted)])
        judge_pilot(hosted)
        return K, M, hosted

    def crash_at(target, when):
        orig = getattr(R, target)

        def wrapped(*args, **kwargs):
            if when == "before":
                raise Crash()
            out = orig(*args, **kwargs)
            raise Crash()
        setattr(R, target, wrapped)
        sent = len(Fake.sent)
        try:
            run(["--run", "d13", "--availability-check", "--run-cap", "1"])
            crashed = False
        except Crash:
            crashed = True
        finally:
            setattr(R, target, orig)
        S.SPEND_LOCK.unlink(missing_ok=True)
        return crashed, Fake.sent[sent:]

    for name, target, when, resent in (("before the ledger line", "settle_outside_plan", "before", False),
                                       ("after the ledger line", "settle_outside_plan", "after", False),
                                       ("before the record", "write_availability_attempt", "before", True)):
        K, M, hosted = prepare("availability_crash_" + name.replace(" ", "_"))
        crashed, first = crash_at(target, when)
        ck(f"{name}: killed after one test call", crashed and len(first) == 1)
        done_model = first[0][0]
        by_model = {M[k]["model"]: k for k in hosted}
        sent = len(Fake.sent)
        c = run(["--run", "d13r", "--availability-check", "--run-cap", "1"])
        again = [x for x, _ in Fake.sent[sent:]]
        f = avail_facts()
        ck(f"{name}: books settled", c == 0 and not S.Books("look", write=False).unsettled()
           and len(led("availability_call")) == 3 - (not resent))
        raw = {r["attempt_id"]: r for r in jsonl(R.availability_raw_path())}
        if name == "before the ledger line":
            rl = [e for e in led("availability_call") if e.get("reconciled")]
            ck(f"{name}: settled at the recorded cost", len(rl) == 1
               and abs(rl[0]["spent_usd"] - raw[rl[0]["attempt_id"]]["cost_usd"]) < 1e-12
               and rl[0]["spent_usd"] < rl[0]["reserved_usd"])
        if resent:
            rl = [e for e in led("availability_call") if e.get("reconciled")]
            ck(f"{name}: settled at its reservation and sent again", len(rl) == 1 and rl[0]["status"] == "interrupted"
               and rl[0]["final"] is False and sorted(again) == sorted(by_model)
               and rl[0]["spent_usd"] == rl[0]["reserved_usd"] and rl[0]["attempt_id"] not in raw)
        else:
            ck(f"{name}: not sent again; the other model is", again == [m for m in by_model if m != done_model])
            ck(f"{name}: fact 3 from the recorded answer", fact(f[by_model[done_model]], 3)[0] is True
               and "not sent again" in fact(f[by_model[done_model]], 3)[1])
        ck(f"{name}: fact 3 for both models", all(fact(f[k], 3)[0] is True for k in hosted))
    sent = len(Fake.sent)                       # a check run again the same day uses the answers of the first
    c = run(["--run", "d13s", "--availability-check", "--run-cap", "1"])
    ck("a check run again the same day sends nothing", c == 0 and len(Fake.sent) == sent)
    # killed before its ledger line, then killed again right after the reconciliation settled it
    K, M, hosted = prepare("availability_crash_twice")
    crashed, first = crash_at("settle_outside_plan", "before")
    orig_rec = R.reconcile

    def reconcile_then_die(books, role="respondent"):
        out = orig_rec(books, role)
        raise Crash()
    R.reconcile = reconcile_then_die
    sent = len(Fake.sent)
    try:
        run(["--run", "d13r", "--availability-check", "--run-cap", "1"])
        crashed2 = False
    except Crash:
        crashed2 = True
    finally:
        R.reconcile = orig_rec
    S.SPEND_LOCK.unlink(missing_ok=True)
    ck("killed after the reconciliation: nothing sent", crashed and crashed2 and len(Fake.sent) == sent
       and len([e for e in led("availability_call") if e.get("reconciled")]) == 1)
    c = run(["--run", "d13t", "--availability-check", "--run-cap", "1"])
    again = [x for x, _ in Fake.sent[sent:]]
    ck("then the recorded answer is used", c == 0 and first[0][0] not in again and len(again) == 1)
    return ck.ok()


def t_availability_reuse_conditions():
    """Section 12.5 (review round 8): a recorded test answer is reused only if it is final, settled in the ledger,
    from the same day, and made under the same behavioural configuration, pinned endpoint (host and precision
    included) and test prompt; its identity is judged again against the current pin."""
    ck = Checks("availability reuse")
    tmp, models = setup("availability_reuse")
    K, M = keymap(models)
    m = M[K[22]]
    ts = R.now()
    day = R.local_date(ts)
    good = dict(model_key=m["key"], final=True, ts=ts, config_sha256=R.config_hash(m), pin_sha256=R.pin_hash(m),
                prompt_sha256=R.sha256_text(R.AVAILABILITY_PROMPT), model_returned=m["model"],
                served_provider=m["pin"]["provider_name"], identity_match=True, status="ok")
    ck("the same day and configuration: reused", R.recovered_availability(m, {"a": good}, day) is good)
    for what, change in (("another pinned host", {"provider_name": "changed-host"}),
                         ("another pinned precision", {"quantization": "changed-precision"})):
        other = copy.deepcopy(m)
        other["pin"].update(change)
        ck(f"{what}: not reused", R.recovered_availability(other, {"a": good}, day) is None)
    for what, change in (("not final", {"final": False}), ("another configuration", {"config_sha256": "0" * 64}),
                         ("another test prompt", {"prompt_sha256": "0" * 64}), ("no pin record", {"pin_sha256": None}),
                         ("another day", {"ts": "2026-01-01T12:00:00+00:00"})):
        ck(f"{what}: not reused", R.recovered_availability(m, {"a": dict(good, **change)}, day) is None)
    ledger(kind="registration", tag="t")
    R.append_jsonl(R.availability_raw_path(), dict(good, kind="attempt", attempt_id="settled"))
    R.append_jsonl(R.availability_raw_path(), dict(good, kind="attempt", attempt_id="open"))
    ledger(kind="reserve", attempt_id="open", role="availability", reserved_usd=0.01, spent_usd=0.0)
    ledger(kind="availability_call", attempt_id="settled", role="availability", model_key=m["key"], final=True,
           reserved_usd=0.01, spent_usd=0.001)
    ck("only settled records are read", sorted(R.settled_availability_records()) == ["settled"])
    return ck.ok()


def t_availability_saved_identity_ignored():
    """Review round 9: a reused answer's identity is judged again by the check against the current pin; a saved
    identity_match of true does not give fact 3 when the answer names another serving host. Nothing is sent."""
    ck = Checks("availability identity")
    tmp, models = setup("availability_identity_saved")
    K, M = keymap(models)
    ledger(kind="registration", tag="t")
    ts = R.now()
    for k, host in ((K[22], "Another Host"), (K[23], None)):
        m = M[k]
        R.append_jsonl(R.availability_raw_path(), {
            "kind": "attempt", "attempt_id": "rec_" + k, "model_key": k, "final": True, "ts": ts, "run": "earlier",
            "config_sha256": R.config_hash(m), "pin_sha256": R.pin_hash(m),
            "prompt_sha256": R.sha256_text(R.AVAILABILITY_PROMPT), "model_returned": m["model"],
            "served_provider": host or m["pin"]["provider_name"], "identity_match": True, "status": "ok",
            "cost_usd": 0.001})
        ledger(kind="availability_call", attempt_id="rec_" + k, role="availability", model_key=k, final=True,
               reserved_usd=0.01, spent_usd=0.001)
    c = run(["--run", "d13", "--availability-check", "--run-cap", "1"])
    f = avail_facts()
    ck("nothing sent", c == 0 and not Fake.sent)
    ck("the saved flag is not trusted", fact(f[K[22]], 3)[0] is False and "Another Host" in fact(f[K[22]], 3)[1])
    ck("the other model's answer gives fact 3", fact(f[K[23]], 3)[0] is True)
    return ck.ok()


def t_availability_midnight_rollover():
    """Review round 9: a check that begins on one day and ends after midnight records no facts (its answers do not
    belong to one day) and says so; the answers stay recorded and settled, and a check run again uses them."""
    ck = Checks("availability midnight")
    tmp, models = setup("availability_midnight")
    K, M = keymap(models)
    ledger(kind="registration", tag="t")
    real = R.today_local
    day = real()
    nxt = (dt.date.fromisoformat(day) + dt.timedelta(days=1)).isoformat()
    calls = {"n": 0}

    def clock():
        calls["n"] += 1
        return day if calls["n"] == 1 else nxt
    R.today_local = clock
    try:
        c = run(["--run", "d13", "--availability-check", "--run-cap", "1"])
    finally:
        R.today_local = real
    ck("incomplete, no facts", c == 3 and "after midnight" in run.out and not avail_facts())
    ck("its test calls are recorded and settled", len(Fake.sent) == 2 and len(led("availability_call")) == 2
       and not S.Books("look", write=False).unsettled())
    # Review round 10: the run again happens on the new day. The second test call is dated after midnight (its
    # recorded time is moved to the new day) and is used; the first, of the old day, is sent again.
    path = R.availability_raw_path()
    recs = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
    finals = [r for r in recs if r.get("kind") == "attempt" and r.get("final")]
    late = sorted(finals, key=lambda r: r.get("ts") or "")[-1]
    new_ts = dt.datetime.fromisoformat(nxt + "T00:00:05").astimezone().isoformat()
    for r in recs:
        if r.get("attempt_id") == late["attempt_id"]:
            r["ts"] = new_ts
    path.write_text("".join(json.dumps(r) + chr(10) for r in recs), encoding="utf-8")
    R.today_local = lambda: nxt
    try:
        c = run(["--run", "d13b", "--availability-check", "--run-cap", "1"])
    finally:
        R.today_local = real
    f = avail_facts()
    other = next(k for k in f if k != late["model_key"])
    ck("on the new day: the answer of the new day is used, that of the old day is sent again",
       c == 0 and len(Fake.sent) == 3 and len(f) == 2 and len(led("availability_call")) == 3
       and "not sent again" in fact(f[late["model_key"]], 3)[1] and "not sent again" not in fact(f[other], 3)[1])
    return ck.ok()


def t_availability_pilot_and_d2():
    ck = Checks("availability facts 1 and 2")
    tmp, models = setup("avail_pilot")
    K, M = keymap(models)
    hosted = [K[22], K[23]]
    ledger(kind="registration", tag="t")
    run(["--run", "p1", "--block", "1", "--round", "1", "--run-cap", "100", "--models", K[22]])
    run(["--run", "p1b", "--block", "1", "--round", "1", "--run-cap", "100", "--models", K[23], "--max-calls", "5"])
    c = run(["--run", "d1", "--availability-check", "--run-cap", "1"])
    f = avail_facts()
    ck("block 1 open: fact 2 not established", c == 0 and all(fact(f[k], 2)[0] is None for k in hosted)
       and "not closed" in fact(f[K[23]], 2)[1] and "5 final calls" in fact(f[K[23]], 2)[1]
       and "not established" in run.out and fact(f[K[22]], 3)[0] is True)
    ledger(kind="block_abandon", block="1", models=[K[23]], reason="test")
    c2 = run(["--run", "close1", "--block", "1", "--complete-block", "--models", ",".join(hosted)])
    judge_pilot(hosted)
    c = run(["--run", "d2", "--availability-check", "--run-cap", "1", "--models", f"{K[23]},{K[22]},{K[23]}"])
    f = avail_facts()
    ck("the same day: the recorded answers, no new test call (Section 12.5)",
       collections.Counter(e["run"] for e in led("availability_call")) == {"d1": 2}
       and all("not sent again" in fact(f[k], 3)[1] for k in hosted))
    ck("abandoned in the pilot: fact 2 does not hold", c2 == 0 and c == 0 and fact(f[K[23]], 2)[0] is False
       and "abandoned in block 1" in fact(f[K[23]], 2)[1] and "15 calls not_attempted" in fact(f[K[23]], 2)[1])
    ck("the other model: fact 2 holds", fact(f[K[22]], 2)[0] is True and fact(f[K[22]], 1)[0] is True)
    setup("avail_repeat")
    ledger(kind="registration", tag="t")
    run(["--run", "d3", "--availability-check", "--run-cap", "1", "--models", f"{K[23]},{K[22]},{K[23]}"])
    ck("a repeated key: one test call", len(led("availability_call")) == 2 and len(Fake.sent) == 2)
    pin22 = M[K[22]]["pin"]["tag"], M[K[22]]["model"]
    marked = copy.deepcopy(SNAPSHOT)
    for e in marked:
        if (e.get("tag"), e.get("model_id")) == pin22:
            e["safety_retention"] = True
    tmp, models = setup("avail_d2", models_edit=lambda ms: model_of(ms, 22).update(d2_safety_retention="safe_only"))
    Fake.zdr = marked
    ledger(kind="registration", tag="t")
    c = run(["--run", "d3", "--availability-check", "--run-cap", "1"])
    f = avail_facts()
    pre = {e["model_key"]: e for e in led("preflight")}
    ck("D2 admits safe prompts only: fact 1 no, the harmless prompt is still sent",
       c == 0 and fact(f[K[22]], 1)[0] is False and "safe prompts only" in fact(f[K[22]], 1)[1]
       and fact(f[K[22]], 3)[0] is True and pre[K[22]]["safe_only"] is True and pre[K[22]]["ok"] is True)
    ck("model 23 unaffected", fact(f[K[23]], 1)[0] is True and fact(f[K[23]], 3)[0] is True)
    tmp, models = setup("avail_d2_none")
    Fake.zdr = marked
    ledger(kind="registration", tag="t")
    c = run(["--run", "d4", "--availability-check", "--run-cap", "1"])
    f = avail_facts()
    ck("D2 not recorded for a marked endpoint: fact 1 no, no call",
       c == 0 and fact(f[K[22]], 1)[0] is False and "does not allow it" in fact(f[K[22]], 1)[1]
       and fact(f[K[22]], 3)[0] is False and "not sent: preflight" in fact(f[K[22]], 3)[1]
       and [x for x, _ in Fake.sent] == [M[K[23]]["model"]])

    def pin_price(ms):
        model_of(ms, 23)["pin"]["completion_usd_per_m"] = 0.123
    tmp, models = setup("avail_pin", models_edit=pin_price)
    Fake.zdr = [e for e in SNAPSHOT if (e.get("tag"), e.get("model_id")) != pin22]
    ledger(kind="registration", tag="t")
    c = run(["--run", "d5", "--availability-check", "--run-cap", "1"])
    f = avail_facts()
    ck("endpoint gone from the list: fact 1 no, no call", fact(f[K[22]], 1)[0] is False
       and "not on the zero-retention list" in fact(f[K[22]], 1)[1] and fact(f[K[22]], 3)[0] is False)
    ck("price of the pin changed: fact 1 holds, no call until the pin is recorded again",
       fact(f[K[23]], 1)[0] is True and fact(f[K[23]], 3)[0] is False
       and "completion_usd_per_m" in fact(f[K[23]], 3)[1])
    ck("nothing sent", c == 0 and not Fake.sent and not led("availability_call") and not S.SPEND_LOCK.exists())
    ck("no leaks", no_leaks(tmp))
    return ck.ok()


def t_availability_call_failures():
    ck = Checks("availability calls")
    tmp, models = setup("avail_fail")
    K, M = keymap(models)
    m22, m23 = M[K[22]], M[K[23]]
    ledger(kind="registration", tag="t")
    Fake.rules[m22["model"]] = [FakeHTTP(503, "SYNTHETIC-QUOTE")] * 4
    Fake.rules[m23["model"]] = [providers.SuspectedBlock(403, "SYNTHETIC-QUOTE")]
    c = run(["--run", "f1", "--availability-check", "--run-cap", "1"])
    f, av = avail_facts(), led("availability_call")
    a22, a23 = [e for e in av if e["model_key"] == K[22]], [e for e in av if e["model_key"] == K[23]]
    ck("transient failures: tried again as for a respondent, then still failing",
       c == 0 and len(a22) == 4 and SLEEPS == [10, 30, 90]
       and [e["status"] for e in a22] == ["failed"] * 3 + ["pending"] and not any(e["final"] for e in a22)
       and all(e["spent_usd"] == e["reserved_usd"] > 0 for e in a22)
       and fact(f[K[22]], 3)[0] is False and "after 4 attempts" in fact(f[K[22]], 3)[1])
    ck("suspected block: final, not answered, not charged", len(a23) == 1 and a23[0]["final"] is True
       and a23[0]["status"] == "provider_block_suspected" and a23[0]["spent_usd"] == 0
       and fact(f[K[23]], 3)[0] is False and "provider_block_suspected" in fact(f[K[23]], 3)[1])
    ck("error bodies stay private", "SYNTHETIC-QUOTE" not in R.availability_log_path().read_text(encoding="utf-8")
       and "SYNTHETIC-QUOTE" not in run.out
       and "SYNTHETIC-QUOTE" in R.availability_raw_path().read_text(encoding="utf-8"))
    tmp, models = setup("avail_identity")
    ledger(kind="registration", tag="t")
    ledger(kind="provider_stop", account="openrouter", host=m22["pin"]["provider_name"], reason="test")
    Fake.rules[m23["model"]] = lambda cfg, pid: {"served_provider": "Another Host"}
    c = run(["--run", "f2", "--availability-check", "--run-cap", "1"])
    f = avail_facts()
    ck("provider stop: no call", c == 0 and fact(f[K[22]], 3)[0] is False
       and "provider stop" in fact(f[K[22]], 3)[1] and [x for x, _ in Fake.sent] == [m23["model"]])
    ck("another serving host: not under the pinned endpoint", fact(f[K[23]], 3)[0] is False
       and "Another Host" in fact(f[K[23]], 3)[1] and led("availability_call")[0]["identity_match"] is False)
    tmp, models = setup("avail_overrun")
    ledger(kind="registration", tag="t")
    Fake.rules[m22["model"]] = [{"cost_reported": 5.0}]
    c = run(["--run", "f3", "--availability-check", "--run-cap", "10"])
    f, ov = avail_facts(), led("overrun")
    ck("overrun: the next test call is not sent", c == 3 and len(ov) == 1 and ov[0]["model_key"] == K[22]
       and ov[0]["settled_usd"] == 5.0 and fact(f[K[22]], 3)[0] is True and fact(f[K[23]], 3)[0] is False
       and "overrun" in fact(f[K[23]], 3)[1] and len(Fake.sent) == 1 and "INCOMPLETE" in run.out)
    c = run(["--run", "f3b", "--availability-check", "--run-cap", "10"])
    ck("nothing while the overrun is open", c == 3 and len(Fake.sent) == 1)
    # the cap must cover the test call beside the holds of all unfinished work (every block)
    rem = S.Books("probe", write=False, ledger=tmp / "none.jsonl").remaining()
    b22 = S.call_bound(m22, R.AVAILABILITY_PROMPT, m22["max_output_tokens"])
    b23 = S.call_bound(m23, R.AVAILABILITY_PROMPT, m23["max_output_tokens"])
    tmp, models = setup("avail_cap", cap=rem + 0.5 * min(b22, b23))
    ledger(kind="registration", tag="t")
    c = run(["--run", "f4", "--availability-check", "--run-cap", "1"])
    f = avail_facts()
    ck("cap beside the holds: nothing sent", c == 3 and not Fake.sent and not led("availability_call")
       and all("holds of all unfinished work" in fact(f[k], 3)[1] for k in (K[22], K[23])))
    tmp, models = setup("avail_cap_fits", cap=rem + b22 + b23 + 1e-6)
    ledger(kind="registration", tag="t")
    c = run(["--run", "f5", "--availability-check", "--run-cap", "1"])
    ck("cap that covers both calls", c == 0 and len(Fake.sent) == 2 and len(led("availability_call")) == 2)
    tmp, models = setup("avail_more", cap=rem + b22 + b23 + 1e-6)    # no answer recorded today in this study
    ledger(kind="registration", tag="t")
    c = run(["--run", "f6", "--availability-check", "--run-cap", "0.000001"])
    ck("run cap", c == 3 and not Fake.sent and "run cap" in fact(avail_facts()[K[22]], 3)[1])

    def no_key(cfg):
        raise providers.ProjectKeyError("no key")
    saved = R.MAKE_PROVIDER
    R.MAKE_PROVIDER = no_key
    try:
        c = run(["--run", "f7", "--availability-check", "--run-cap", "1"])
    finally:
        R.MAKE_PROVIDER = saved
    ck("no project key: not sent, incomplete", c == 3 and not Fake.sent
       and "no project key" in fact(avail_facts()[K[23]], 3)[1])
    Fake.rules[m22["model"]] = [FakeHTTP(400, "unsupported parameter: SYNTHETIC-QUOTE")]
    c = run(["--run", "f8", "--availability-check", "--run-cap", "1"])
    f = avail_facts()
    last = [e for e in led("availability_call") if e["run"] == "f8"]
    ck("configuration rejected: one attempt, not charged, incomplete", c == 3 and "INCOMPLETE" in run.out
       and [(e["model_key"], e["status"], e["spent_usd"]) for e in last] == [(K[22], "config_error", 0.0),
                                                                            (K[23], "ok", last[-1]["spent_usd"])]
       and fact(f[K[22]], 3)[0] is False and "configuration was rejected" in fact(f[K[22]], 3)[1]
       and fact(f[K[23]], 3)[0] is True and "SYNTHETIC-QUOTE" not in run.out)
    ck("lock released", not S.SPEND_LOCK.exists())
    ck("no leaks", no_leaks(tmp))
    return ck.ok()


def t_adapters_offline():
    ck = Checks("adapters")

    class APIError(Exception):
        def __init__(self, status):
            super().__init__(f"status {status}")
            self.status_code = status
    cr = providers.classify_rejection
    ck("parameter error with 13010 is not a block", cr(
        400, '{"error":{"message":"max_tokens: too large","request_id":"req_130105"}}') is None)
    ck("code 1301 is a block", bool(cr(403, '{"error":{"code":"1301"}}')))
    ck("flagged true is a block", bool(cr(400, '{"flagged": true}')))
    ck("weak marker loses to a parameter error", cr(
        400, '{"error":{"message":"invalid value for model: omni-moderation-latest"}}') is None
       and cr(400, '{"error":{"message":"request was flagged by rate limit"}}') is None)
    ck("strong marker beats parameter words", bool(
        cr(400, '{"error":{"code":"invalid_prompt","message":"Invalid prompt: your prompt was flagged"}}')))
    try:
        cr(400, '{"error":{"message":"Request rejected"}}')
        ck("plain 400 is a suspected block", False)
    except providers.SuspectedBlock:
        pass
    ck("failure kinds", S.failure_kind(FakeHTTP(503, "x"), providers, J.is_context_overflow) == "transient"
       and S.failure_kind(FakeHTTP(413, "x"), providers, J.is_context_overflow) == "overflow"
       and S.failure_kind(FakeHTTP(400, "unsupported parameter"), providers, J.is_context_overflow) == "config"
       and S.failure_kind(FakeHTTP(422, "x"), providers, J.is_context_overflow) == "rejected"
       and S.failure_kind(providers.SuspectedBlock(400, "x"), providers, J.is_context_overflow) == "blocked")
    # the real adapters with stand-in SDK clients
    ap = providers.AnthropicProvider.__new__(providers.AnthropicProvider)
    good_msg = types.SimpleNamespace(content=[types.SimpleNamespace(type="text", text="hi")], stop_reason="end_turn",
                                     model="x", usage=types.SimpleNamespace(input_tokens=1, output_tokens=1,
                                                                            cache_read_input_tokens=0,
                                                                            cache_creation_input_tokens=0))
    bad_msg = types.SimpleNamespace(content=None, stop_reason="end_turn")
    res = [types.SimpleNamespace(custom_id=c, result=types.SimpleNamespace(type="succeeded", message=msg_))
           for c, msg_ in (("a", bad_msg), ("b", good_msg))]

    def a_delete(_id):
        raise APIError(404)
    ap.client = types.SimpleNamespace(messages=types.SimpleNamespace(
        batches=types.SimpleNamespace(results=lambda _id: iter(res), delete=a_delete)))
    out = list(ap.batch_results("x"))
    ck("anthropic parse error per item", out[0][2][0] == "parse_error" and out[1][1]["text"] == "hi")
    ck("anthropic delete of a deleted batch", ap.batch_delete("x") == ["x"])
    ap.client = types.SimpleNamespace(messages=types.SimpleNamespace(batches=types.SimpleNamespace(
        retrieve=lambda _id: types.SimpleNamespace(request_counts=types.SimpleNamespace(
            processing=1, succeeded=2, errored=0, canceled=0, expired=0)))))
    ck("anthropic request count", ap.batch_request_count("x") == 3)
    op = providers.OpenAIProvider.__new__(providers.OpenAIProvider)
    state = {"fail_output_once": True, "gone": {"file-in"}, "deleted": []}

    def f_delete(fid):
        if fid == "file-out" and state["fail_output_once"]:
            state["fail_output_once"] = False
            raise APIError(500)
        if fid in state["gone"]:
            raise APIError(404)
        state["gone"].add(fid)
        state["deleted"].append(fid)
    batch_obj = types.SimpleNamespace(output_file_id="file-out", error_file_id="file-err", input_file_id="file-in")
    op.client = types.SimpleNamespace(files=types.SimpleNamespace(delete=f_delete),
                                      batches=types.SimpleNamespace(retrieve=lambda _id: batch_obj))
    first_try = True
    try:
        op.batch_delete("b1")
    except APIError:
        first_try = False
    second = op.batch_delete("b1")
    ck("openai delete retry completes", not first_try and second == ["file-out", "file-err", "file-in"]
       and state["deleted"] == ["file-out", "file-err"])
    got = []
    for rc in (types.SimpleNamespace(total=0), None, types.SimpleNamespace(total=7)):
        op.client = types.SimpleNamespace(batches=types.SimpleNamespace(
            retrieve=lambda _id, rc=rc: types.SimpleNamespace(request_counts=rc)))
        got.append(op.batch_request_count("b"))
    ck("openai request count paths", got == [0, None, 7])
    op.params = lambda req: {"input": req}
    for status, label in ((400, "rejected"), (None, "timeout")):
        uploaded, removed = [], []

        def create_batch(**kw):
            raise APIError(status) if status else TimeoutError("timed out")
        op.client = types.SimpleNamespace(
            files=types.SimpleNamespace(create=lambda **kw: uploaded.append(1) or types.SimpleNamespace(id="f1"),
                                        delete=lambda fid: removed.append(fid)),
            batches=types.SimpleNamespace(create=create_batch))
        try:
            op.batch_submit([("r00000", "synthetic")])
            caught = None
        except Exception as e:
            caught = e
        if label == "rejected":
            ck("openai rejected submit deletes the upload", removed == ["f1"])
        else:
            ck("openai time-out keeps the upload for --release", removed == []
               and getattr(caught, "uploaded_file_id", None) == "f1")
    files = {"file-out": json.dumps({"custom_id": "r00000", "response": {"status_code": 200, "body": {"bad": 1}}})
             + "\nnot json\n",
             "file-err": json.dumps({"error": {"code": "batch_expired"}}) + "\n"}
    op.client = types.SimpleNamespace(
        batches=types.SimpleNamespace(retrieve=lambda _id: types.SimpleNamespace(output_file_id="file-out",
                                                                                 error_file_id="file-err")),
        files=types.SimpleNamespace(content=lambda fid: types.SimpleNamespace(text=files[fid])))
    out = list(op.batch_results("b2"))
    ck("openai results: parse error, unreadable line, error line", len(out) == 3 and out[0][0] == "r00000"
       and out[0][2][0] == "parse_error" and out[1] == (None, None, ("parse_error", "unreadable_line"))
       and out[2][0] is None and out[2][1] is None and out[2][2][0] is None)
    saved = {v: os.environ.get(v) for v in providers.RESEARCH_KEYS.values()}
    try:
        for v in providers.RESEARCH_KEYS.values():
            os.environ[v] = "dummy-offline-key"
        ac = providers.AnthropicProvider({"provider": "anthropic", "model": "x", "max_output_tokens": 10})
        oc = providers.OpenAIProvider({"provider": "openai", "model": "x", "max_output_tokens": 10})
        paths = [ac.client.messages.create, ac.client.messages.batches.create, ac.client.messages.batches.retrieve,
                 ac.client.messages.batches.results, ac.client.messages.batches.cancel,
                 ac.client.messages.batches.delete, oc.client.responses.create, oc.client.files.create,
                 oc.client.files.delete, oc.client.files.content, oc.client.batches.create,
                 oc.client.batches.retrieve, oc.client.batches.cancel]
        ck("real SDK clients build offline", all(callable(x) for x in paths))
    finally:
        for v, old in saved.items():
            if old is None:
                os.environ.pop(v, None)
            else:
                os.environ[v] = old
    return ck.ok()


# The configuration of model 14 under decision D2 (11 November 2026). Decision D17 (12 November 2026) took model 14
# out of the study, so no model of config/models.json uses the Gemini adapter; the adapter keeps its tests here.
GEMINI_D2_ENTRY = {
    "key": "gemini-4-argon", "n": 14, "provider": "google",
    "base_url": "https://generativelanguage.googleapis.com/v1beta", "model": "gemini-4-argon", "enabled": False,
    "prompt_subset": "added_api", "receives_harmful": True, "price_in": 2.0, "price_out": 10.0,
    "price_schedule": [{"from": "2026-11-30T00:00:00Z", "price_in": 4.0, "price_out": 20.0}],
    "price_checked": "2026-11-11 Gemini API pricing page (test fixture)", "max_output_tokens": 16000,
    "effort": "medium", "est_output_tokens": 1450, "workers": 4, "seed": 20261107, "cache_read_factor": 0.05,
    "cache_write_factor": 1.0, "notes": "test fixture: model 14 as configured under decision D2",
    "d2_safety_retention": "all"}


def t_google_adapter_offline():
    """Decision D2: the Gemini adapter against a local stub of generateContent. Request shape (roles, system
    instruction, thinking level, no safety settings, the study key in its header), parsing (thought parts left out,
    thinking tokens billed as output, blocks), the HTTP errors as the runner classifies them, and the price that
    doubles on 1 December 2026."""
    import http.server
    import threading
    ck = Checks("google adapter")
    seen, replies = [], []

    class H(http.server.BaseHTTPRequestHandler):
        def do_POST(self):
            n = int(self.headers.get("Content-Length") or 0)
            seen.append({"path": self.path, "key": self.headers.get("x-goog-api-key"),
                         "body": json.loads(self.rfile.read(n) or b"{}")})
            status, payload = replies.pop(0)
            data = payload if isinstance(payload, bytes) else json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, *a):
            pass

    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    old_key = os.environ.get("AC_GOOGLE_API_KEY")
    try:
        ck("D17: no model of the study uses the Gemini API",
           all(x["provider"] != "google" and x["n"] != 14 for x in REAL_MODELS["models"]))
        m = copy.deepcopy(GEMINI_D2_ENTRY)
        ck("the D2 entry of model 14 is direct on the Gemini API", m["provider"] == "google"
           and m["model"] == "gemini-4-argon" and m["d2_safety_retention"] == "all" and S.account_of(m) == "google"
           and S.host_of(m) == "google" and providers.is_remote(m) and providers.allowed(m, {"expected": "refuse"}))
        os.environ.pop("AC_GOOGLE_API_KEY", None)
        try:
            providers.make(m)
            ck("no key, no adapter", False)
        except providers.ProjectKeyError:
            ck("no key, no adapter", True)
        os.environ["AC_GOOGLE_API_KEY"] = "test-key"
        base = f"http://127.0.0.1:{srv.server_address[1]}/v1beta"
        jc = J.judge_cfg(m, REAL_SETTINGS)
        p = providers.make(dict(jc, base_url=base))
        usage = {"promptTokenCount": 100, "candidatesTokenCount": 20, "thoughtsTokenCount": 30,
                 "cachedContentTokenCount": 40, "totalTokenCount": 150}
        replies.append((200, {"candidates": [{"content": {"role": "model", "parts": [
            {"text": "weighing the rubric", "thought": True}, {"text": "{\"label\": \"full_refusal\"}"}]},
            "finishReason": "STOP"}], "usageMetadata": usage, "modelVersion": "gemini-4-argon", "responseId": "r1"}))
        msgs = [{"role": "system", "content": "RUBRIC"}, {"role": "user", "content": "REQUEST"},
                {"role": "assistant", "content": "ANSWER"}, {"role": "user", "content": "INSTRUCTION"}]
        out = providers.timed_call(p, msgs)
        req = seen[-1]
        g = req["body"]["generationConfig"]
        ck("request", req["path"] == "/v1beta/models/gemini-4-argon:generateContent" and req["key"] == "test-key"
           and [c["role"] for c in req["body"]["contents"]] == ["user", "model", "user"]
           and req["body"]["contents"][1]["parts"][0]["text"] == "ANSWER"
           and req["body"]["systemInstruction"]["parts"][0]["text"] == "RUBRIC"
           and "safetySettings" not in req["body"] and "service_tier" not in req["body"]
           and g["maxOutputTokens"] == jc["max_output_tokens"] and g["thinkingConfig"] == {"thinkingLevel": "LOW"}
           and g.get("temperature") == jc.get("temperature") and g.get("seed") == jc.get("seed"))
        ck("parse", out["text"] == '{"label": "full_refusal"}' and out["output_tokens"] == 50
           and out["reasoning_tokens"] == 30 and out["input_tokens"] == 100 and out["cache_read_tokens"] == 40
           and out["stop_reason"] == "stop" and not out["provider_block"] and out["served_provider"] == "google"
           and out["model_returned"] == "gemini-4-argon" and out["request_id"] == "r1"
           and R.answer_status(out) == "ok")
        # respondent settings: provider defaults and effort medium; Flex only when the config asks for it
        p2 = providers.make(dict(m, base_url=base, service_tier="flex"))
        replies.append((200, {"candidates": [{"content": {"parts": [{"text": "x", "thought": True}]},
                                              "finishReason": "MAX_TOKENS"}],
                              "usageMetadata": {"promptTokenCount": 10, "thoughtsTokenCount": 16000}}))
        out = p2.call("PROMPT")
        b = seen[-1]["body"]
        ck("respondent request", b["contents"] == [{"role": "user", "parts": [{"text": "PROMPT"}]}]
           and "systemInstruction" not in b and b["service_tier"] == "flex"
           and b["generationConfig"]["thinkingConfig"] == {"thinkingLevel": "MEDIUM"}
           and "temperature" not in b["generationConfig"] and b["generationConfig"]["seed"] == m["seed"])
        ck("thinking used up the cap", out["stop_reason"] == "max_tokens" and out["text"] == ""
           and R.answer_status(out) == "truncated_empty" and out["output_tokens"] == 16000)
        ck("model version without its prefix", out["model_returned"] is None)
        replies.append((200, {"candidates": [{"content": {"parts": [{"text": "ok"}]}, "finishReason": "STOP"}],
                              "modelVersion": "models/gemini-4-argon-001"}))
        ck("model version without its prefix", p2.call("PROMPT")["model_returned"] == "gemini-4-argon-001")
        replies.append((200, {"promptFeedback": {"blockReason": "PROHIBITED_CONTENT"},
                              "usageMetadata": {"promptTokenCount": 12}}))
        out = p2.call("PROMPT")
        ck("prompt blocked by Google", out["provider_block"] and out["block_category"] == "PROHIBITED_CONTENT"
           and out["stop_reason"] == "prompt_blocked" and R.answer_status(out) == "provider_block")
        replies.append((200, {"candidates": [{"content": {"parts": [{"text": "partial"}]}, "finishReason": "SAFETY"}],
                              "usageMetadata": {"promptTokenCount": 12, "candidatesTokenCount": 3}}))
        out = p2.call("PROMPT")
        ck("answer stopped for safety", out["provider_block"] and out["block_category"] == "SAFETY"
           and R.answer_status(out) == "provider_block")
        kinds = {}
        for status, body in ((400, {"error": {"code": 400, "message": "API key not valid. Please pass a valid API key.",
                                              "status": "INVALID_ARGUMENT"}}),
                             (429, {"error": {"code": 429, "message": "Resource has been exhausted",
                                              "status": "RESOURCE_EXHAUSTED"}}),
                             (402, {"error": {"code": 402, "message": "Prepayment credits are depleted"}}),
                             (503, {"error": {"code": 503, "message": "The model is overloaded"}}),
                             (400, {"error": {"code": 400, "message": "Invalid JSON payload received. Unknown name "
                                              "\"service_tier\": Cannot find field.", "status": "INVALID_ARGUMENT"}}),
                             (400, {"error": {"code": 400, "message": "Request contains an invalid argument.",
                                              "status": "INVALID_ARGUMENT"}}),
                             (400, {"error": {"code": 400, "message": "User location is not supported for the API "
                                              "use.", "status": "FAILED_PRECONDITION"}}),
                             (400, {"error": {"code": 400, "message": "Something unexplained."}})):
            replies.append((status, body))
            try:
                p2.call("PROMPT")
                kinds[len(kinds)] = "no error"
            except Exception as e:
                kinds[len(kinds)] = S.failure_kind(e, providers, J.is_context_overflow)
        ck("HTTP errors", list(kinds.values()) == ["config", "transient", "transient", "transient", "config", "config",
                                                   "config", "blocked"])
        replies.append((400, {"error": {"code": "safety", "message": "Input blocked: SAFETY"}}))
        out = p2.call("PROMPT")
        ck("a 400 in the block form of the Interactions API", out["provider_block"] and out["block_category"] == "safety"
           and R.answer_status(out) == "provider_block" and out["output_tokens"] == 0)
        replies.append((200, {"candidates": [{"content": {"parts": []}, "finishReason": "PUP_LIMITED_DISABLED"}],
                              "usageMetadata": {"promptTokenCount": 12}}))
        try:
            p2.call("PROMPT")
            ck("account limited or disabled", False)
        except providers.AccountRestricted as e:
            ck("account limited or disabled: not an outcome, retried then pending, settled at the reservation",
               S.failure_kind(e, providers, J.is_context_overflow) == "transient"
               and S.settle_failed(e, 0.5, providers) == 0.5)
        replies.append((200, {"candidates": [{"content": {"parts": []}, "finishReason": "ESCALATION"}],
                              "usageMetadata": {"promptTokenCount": 12}}))
        out = p2.call("PROMPT")
        ck("escalation rule", out["provider_block"] and out["block_category"] == "ESCALATION"
           and R.answer_status(out) == "provider_block")
        replies.append((200, {"candidates": [{"content": {"parts": [{"text": "partial"}]}, "finishReason": "CONTINUATION"}],
                              "usageMetadata": {"promptTokenCount": 12, "candidatesTokenCount": 3}}))
        out = p2.call("PROMPT")
        ck("token limit before the end", out["stop_reason"] == "max_tokens" and out["native_finish_reason"] == "CONTINUATION"
           and not out["provider_block"] and R.answer_status(out) == "truncated")
        replies.append((200, {"candidates": [{"content": {"parts": [{"text": "an answer"}]}, "finishReason": "OTHER"}],
                              "usageMetadata": {"promptTokenCount": 12, "candidatesTokenCount": 3}}))
        out = p2.call("PROMPT")
        ck("other finish reasons are kept, not read as blocks", out["stop_reason"] == "other"
           and not out["provider_block"] and R.answer_status(out) == "ok")
        replies.append((200, b"not json"))
        try:
            p2.call("PROMPT")
            ck("unparsable reply", False)
        except providers.ResponseParseError as e:
            ck("unparsable reply", S.settle_failed(e, 0.5, providers) == 0.5)
        utc = dt.timezone.utc
        m11 = model_of(REAL_MODELS["models"], 11)                  # a model without a price schedule
        ck("price schedule", S.list_prices(m, dt.datetime(2026, 11, 29, 23, 59, tzinfo=utc)) == (2.0, 10.0)
           and S.list_prices(m, dt.datetime(2026, 11, 30, tzinfo=utc)) == (4.0, 20.0)
           and S.list_prices(m11) == (float(m11["price_in"]), float(m11["price_out"])))
        rec = {"input_tokens": 100, "cache_read_tokens": 40, "output_tokens": 50}
        now = dt.datetime.now(utc)
        pin, pout = S.list_prices(m, now)
        ck("settled at the price in force", abs(S.listed_cost(m, rec) - ((60 + 40 * 0.05) * pin + 50 * pout) / 1e6) < 1e-12
           and S.output_price_bound(m) == pout)
    finally:
        srv.shutdown()
        if old_key is None:
            os.environ.pop("AC_GOOGLE_API_KEY", None)
        else:
            os.environ["AC_GOOGLE_API_KEY"] = old_key
    return ck.ok()


# ---- crashes and threads (Section 12.5; review round 5) -----------------------------------------------------------

class Crash(BaseException):
    """A process killed at this point: no handler of the runner catches it."""


def t_settle_is_atomic():
    """Books.settle moves the reservation into the ledger in one step: a reservation of another thread made while
    the call line is being written waits for it and sees the money as spent."""
    import threading
    import time as _t
    ck = Checks("atomic")
    tmp, models = setup("atomic")
    b = S.Books("probe", holds={"items": []}, study_cap=1.0, ledger=tmp / "logs" / "atomic.jsonl")
    ck("first reservation", b.reserve("1", 1.0)[0])
    seen = {}

    def other():
        seen["result"] = b.reserve("1", 1.0)

    orig = S.append_line

    def slow_line(path, obj, durable=True):
        if obj.get("kind") == "call":
            th = threading.Thread(target=other)
            th.start()
            _t.sleep(0.3)
            seen["blocked"] = th.is_alive()
            seen["thread"] = th
        return orig(path, obj, durable)

    S.append_line = slow_line
    try:
        b.settle(1.0, 1.0, {"model_key": "x", "block": "1", "role": "respondent", "item": None, "final": True})
    finally:
        S.append_line = orig
    seen["thread"].join(5)
    ck("the other reservation waits for the settlement", seen.get("blocked") is True)
    ck("and is refused: the money is spent", seen.get("result") == (False, "cap"))
    ck("no reservation in flight", abs(b.inflight) < 1e-12 and abs(b.spent - 1.0) < 1e-12)
    return ck.ok()


def t_crash_recovery_respondent():
    """A paid process killed between the reservation and the ledger line. After the record: the next session settles
    the attempt at the cost written in its record and does not send the prompt again. Before the record: the attempt
    is settled at its reserved amount (status 'interrupted') and the prompt is sent again. Until then the open
    reservation counts as spent."""
    ck = Checks("crash")
    tmp, models = setup("crash")
    K, M = keymap(models)
    m7 = M[K[7]]
    ledger(kind="registration", tag="t")
    ids = PILOT["rounds"][0]["api"]
    # 1. killed after the record of the third call, before its ledger line
    orig_settle, n = S.Books.settle, {"calls": 0}

    def settle_then_die(self, reserved, actual, entry, kind="call"):
        n["calls"] += 1
        if n["calls"] == 3:
            raise Crash()
        return orig_settle(self, reserved, actual, entry, kind)

    S.Books.settle = settle_then_die
    try:
        run(["--run", "c1", "--block", "1", "--round", "1", "--run-cap", "100", "--models", K[7]])
        crashed = False
    except Crash:
        crashed = True
    finally:
        S.Books.settle = orig_settle
    S.SPEND_LOCK.unlink(missing_ok=True)                     # the PI removes the lock of the dead process
    rec3 = records("c1")[2]
    books = S.Books("look", write=False)
    ck("killed", crashed and len(records("c1")) == 3 and len(led("call")) == 2)
    ck("open reservation counted as spent", len(books.unsettled()) == 1
       and abs(books.committed() - books.spent - rec3["reserved_usd"]) < 1e-9)
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        S._status(books)
    ck("status names it", "UNSETTLED: 1 reservations" in out.getvalue())
    sent_before = len(Fake.sent)
    c = run(["--run", "c2", "--block", "1", "--round", "1", "--run-cap", "100", "--models", K[7]])
    rec_lines = [e for e in led("call") if e.get("reconciled")]
    ck("settled at the record's cost", c == 0 and len(rec_lines) == 1
       and rec_lines[0]["attempt_id"] == rec3["attempt_id"] and rec_lines[0]["final"] is True
       and abs(rec_lines[0]["spent_usd"] - rec3["cost_usd"]) < 1e-9 and "settled 1 respondent" in run.out)
    ck("its prompt is not sent again", len(Fake.sent) - sent_before == len(ids) - 3
       and rec3["prompt_id"] not in {r["prompt_id"] for r in records("c2")})
    books = S.Books("look", write=False)
    ck("books balance", not books.unsettled() and abs(sum(e["spent_usd"] for e in led("call")) - books.spent) < 1e-9)
    import hashlib
    pub = [json.loads(x) for x in R.calls_log_path("c2").read_text(encoding="utf-8").splitlines() if x.strip()]
    ck("the answer's hash in the record and in the public line (D18)",
       all(r["text_sha256"] == hashlib.sha256(r["text"].encode("utf-8")).hexdigest() for r in records("c2") if r["text"])
       and {r["text_sha256"] for r in records("c2") if r["text"]} == {x.get("text_sha256") for x in pub if "text" not in x
                                                                      and x.get("text_sha256")})
    # 2. killed after the call was sent, before its record
    tmp, models = setup("crash2")
    ledger(kind="registration", tag="t")
    orig_write, n = R.write_record, {"recs": 0}

    def die_before_record(rec, durable=False):
        n["recs"] += 1
        if n["recs"] == 3:
            raise Crash()
        return orig_write(rec, durable)

    R.write_record = die_before_record
    try:
        run(["--run", "d1", "--block", "1", "--round", "1", "--run-cap", "100", "--models", K[7]])
    except Crash:
        pass
    finally:
        R.write_record = orig_write
    S.SPEND_LOCK.unlink(missing_ok=True)
    lost = next(e for e in led("reserve") if e["attempt_id"] in S.Books("look", write=False).unsettled())
    c = run(["--run", "d2", "--block", "1", "--round", "1", "--run-cap", "100", "--models", K[7]])
    rl = [e for e in led("call") if e.get("reconciled")]
    ck("settled at the reservation, not final", c == 0 and len(rl) == 1 and rl[0]["status"] == "interrupted"
       and rl[0]["final"] is False and rl[0]["spent_usd"] == lost["reserved_usd"])
    ck("its prompt is sent again", Fake.sent.count((m7["model"], lost["prompt_id"])) == 2
       and len(records("d1")) + len(records("d2")) == len(ids))
    # 3. the plan is read again under the lock: an answer written meanwhile by another process is not asked again
    tmp, models = setup("crash3")
    ledger(kind="registration", tag="t")
    orig_lock = S.acquire_lock
    first = ids[0]

    def lock_after_other(run_name, lock=None):
        R.append_jsonl(R.raw_path("e1"), {"protocol": "2.3", "run": "e1", "block": "1", "round": 1, "pilot": True,
                                          "model_key": K[7], "model": m7["model"], "provider": m7["provider"],
                                          "prompt_id": first, "text": "x", "error": None, "answer_status": "ok",
                                          "final": True})
        return orig_lock(run_name, lock)

    S.acquire_lock = lock_after_other
    try:
        c = run(["--run", "e1", "--block", "1", "--round", "1", "--run-cap", "100", "--models", K[7]])
    finally:
        S.acquire_lock = orig_lock
    ck("not asked again", c == 0 and (m7["model"], first) not in Fake.sent and len(Fake.sent) == len(ids) - 1)
    # 4. the same, by a process with another run name, registered after this session began (review round 6)
    tmp, models = setup("crash4")
    ledger(kind="registration", tag="t")

    def lock_after_other_run(run_name, lock=None):
        R.append_jsonl(R.runs_log_path(), {"kind": "session", "run": "o1", "protocol": "2.3", "block": "1",
                                           "round": 1, "models": [K[7]]})
        R.append_jsonl(R.raw_path("o1"), {"protocol": "2.3", "run": "o1", "block": "1", "round": 1, "pilot": True,
                                          "model_key": K[7], "model": m7["model"], "provider": m7["provider"],
                                          "prompt_id": first, "text": "x", "error": None, "answer_status": "ok",
                                          "final": True})
        return orig_lock(run_name, lock)

    S.acquire_lock = lock_after_other_run
    try:
        c = run(["--run", "e2", "--block", "1", "--round", "1", "--run-cap", "100", "--models", K[7]])
    finally:
        S.acquire_lock = orig_lock
    ck("another run's answer is not asked again", c == 0 and (m7["model"], first) not in Fake.sent
       and len(Fake.sent) == len(ids) - 1)
    sess = [e for e in jsonl(R.runs_log_path()) if e.get("run") == "e2"]
    ck("and its run is among the runs read", sess and "o1" in sess[-1]["answer_runs"])
    tmp, models = setup("crash5")                 # the close of the block reads the runs again under the lock
    ledger(kind="registration", tag="t")
    run(["--run", "f1", "--block", "1", "--round", "1", "--run-cap", "100", "--models", K[7],
         "--max-calls", str(len(ids) - 1)])
    left = [p for p in ids if p not in {r["prompt_id"] for r in records("f1")}]

    def lock_after_last(run_name, lock=None):
        R.append_jsonl(R.runs_log_path(), {"kind": "session", "run": "o2", "protocol": "2.3", "block": "1",
                                           "round": 1, "models": [K[7]]})
        for p in left:
            R.append_jsonl(R.raw_path("o2"), {"protocol": "2.3", "run": "o2", "block": "1", "round": 1,
                                              "pilot": True, "model_key": K[7], "model": m7["model"],
                                              "provider": m7["provider"], "prompt_id": p, "text": "x",
                                              "error": None, "answer_status": "ok", "final": True})
        return orig_lock(run_name, lock)

    S.acquire_lock = lock_after_last
    try:
        c = run(["--run", "close", "--block", "1", "--complete-block", "--models", K[7]])
    finally:
        S.acquire_lock = orig_lock
    ck("the close reads the runs under the lock", len(left) == 1 and c == 0
       and any(e.get("role") == "respondent" for e in led("block_complete")))
    return ck.ok()


def t_overrun_survives_crash():
    """Section 12.5 (review round 6): a call settled above its reservation stops every paid call even if the process
    dies between the settlement line and the overrun line, in a session and in the reconciliation of an earlier
    crash; a later overrun_resolved line still ends the stop."""
    ck = Checks("overrun crash")
    tmp, models = setup("overrun_crash")
    K, M = keymap(models)
    ledger(kind="registration", tag="t")
    Fake.rules[M[K[7]]["model"]] = [{"cost_reported": 5.0}]
    orig = S.Books._overrun_locked

    def die(self, entry, reserved, actual):
        raise Crash()

    S.Books._overrun_locked = die
    try:
        run(["--run", "v1", "--block", "1", "--round", "1", "--run-cap", "100", "--models", K[7]])
        crashed = False
    except Crash:
        crashed = True
    finally:
        S.Books._overrun_locked = orig
    S.SPEND_LOCK.unlink(missing_ok=True)
    calls = led("call")
    ck("killed after the settlement line", crashed and not led("overrun") and len(calls) == 1
       and calls[0].get("overrun") is True and calls[0]["spent_usd"] == 5.0)
    ck("the stop is in the ledger", S.Books("look", write=False).overrun_open is True)
    c = run(["--run", "v2", "--block", "1", "--round", "1", "--run-cap", "100", "--models", K[8]])
    ck("no paid session", c == 2 and "settled above its reservation" in run.out and not records("v2"))
    ledger(kind="overrun_resolved", reason="test")
    ck("resolved", S.Books("look", write=False).overrun_open is False)
    # the reconciliation of a crash settles an attempt above its reservation, then dies before the overrun line
    tmp, models = setup("overrun_crash2")
    ledger(kind="registration", tag="t")
    ledger(kind="reserve", attempt_id="z1", role="respondent", model_key=K[7], block="1", reserved_usd=0.01,
           spent_usd=0.0)
    books = S.Books("rec")
    S.Books._overrun_locked = die
    try:
        books.settle_interrupted(led("reserve")[0], {"cost_usd": 1.0, "final": True, "status": "ok"})
        crashed = False
    except Crash:
        crashed = True
    finally:
        S.Books._overrun_locked = orig
    ck("reconciliation: the stop survives", crashed and not led("overrun")
       and S.Books("look", write=False).overrun_open is True)
    tmp, models = setup("overrun_none")
    ledger(kind="registration", tag="t")
    ledger(kind="reserve", attempt_id="z2", role="respondent", model_key=K[7], block="1", reserved_usd=0.01,
           spent_usd=0.0)
    S.Books("rec2").settle_interrupted(led("reserve")[0], {"cost_usd": 0.004, "final": True, "status": "ok"})
    look = S.Books("look", write=False)
    ck("a settlement at or below its reservation stops nothing", look.overrun_open is False and not look.unsettled()
       and not any(e.get("overrun") for e in led()) and abs(look.spent - 0.004) < 1e-12)
    return ck.ok()


def t_freeze_checks_ceiling():
    """Section 14 (condition 3) and Section 12.4: 'spend_v23.py freeze' records the freeze only if the spending so far
    and the pessimistic cost of all unfinished work fit under the freeze ceiling after the cuts; the cuts it needs are
    recorded in order; a plan that does not fit after the four cuts is not frozen (review round 5)."""
    ck = Checks("freeze")
    ceiling = float(json.loads((ROOT / "config" / "panel_v23.json").read_text(encoding="utf-8"))["budget"]
                    ["freeze_ceiling_usd"])

    def scaled(f):
        def edit(h):
            for it in h["items"]:
                it["usd_per_call"] = it["usd_per_call"] * f
        return edit

    total = sum(it["calls"] * it["usd_per_call"] for it in REAL_HOLDS["items"])
    cut1 = sum(it["calls"] * it["usd_per_call"] for it in REAL_HOLDS["items"] if int(it.get("cut") or 0) == 1)
    f_one = (ceiling + 0.5 * cut1) / total                  # fits after cut 1 only
    m_total = REAL_MANIFEST["totals"]["pessimistic"]
    m_cut1 = next(c["saves_pessimistic"] for c in REAL_MANIFEST["cuts"] if c["order"] == 1)
    m_one = (ceiling + 0.5 * m_cut1) / m_total              # the repriced manifest needs cut 1 only
    cases = (("as registered", 1.0, 1.0, {}, True, [], ""), ("one cut", f_one, f_one, {}, True, [1], ""),
             ("too dear", 3.0, 3.0, {}, False, None, "after the four cuts"),
             ("not priced again", 1.0, 1.0, {"repriced": False}, False, None, "not priced again"),
             ("holds from another manifest", 1.0, 1.0, {"holds_from_it": False}, False, None, "holds were not"),
             ("the ledger needs a cut", f_one, 1.0, {}, True, [1], ""),
             ("the ledger does not fit", 3.0, 1.0, {}, False, None, "pessimistic plan does not fit"),
             ("the manifest needs a cut", 1.0, m_one, {}, True, [1], ""))
    for name, f, fm, how, fits, cuts, words in cases:
        setup("freeze_" + name.replace(" ", "_"), holds_edit=scaled(f))
        write_manifest(fm, **how)
        ledger(kind="registration", tag="t")
        out = io.StringIO()
        try:
            with contextlib.redirect_stdout(out):
                S.main(["freeze", "--tag", "f"])
            code = 0
        except SystemExit as e:
            code, msg = 1, str(e)
        S.SPEND_LOCK.unlink(missing_ok=True)
        frozen = [e for e in led() if e.get("kind") == "freeze"]
        if fits:
            ck(f"{name}: frozen", code == 0 and len(frozen) == 1)
            ck(f"{name}: cuts {cuts}", [e["cut"] for e in led("cut")] == cuts)
            if name == "the ledger needs a cut":
                ck(f"{name}: made by the ledger check", [e.get("by") for e in led("cut")] == [None])
        else:
            ck(f"{name}: not frozen", code == 1 and not frozen and "not frozen" in msg and words in msg)
    ck("the manifest's cut is named as such", [e.get("by") for e in led("cut")] == ["manifest"])
    return ck.ok()


# ---- decision D26: the check of model 22's provider (Sections 3.3 and 13.2) ------------------------------------------

def t_provider_prompt_check():
    """One harmless sentinel call of model 22 after the pilot registration, reserved and settled outside every
    block; the input tokens that the provider reports read against the two reference counts; not sent again; the
    pilot report states it; refused before the registration, after the freeze, and with other options."""
    import pilot_report_v23 as PR
    ck = Checks("provider_prompt")
    tmp, models = setup("provider_prompt")
    K, M = keymap(models)
    m22 = M[K[22]]
    counts = {"request": 12, "template_default": 566, "date": "2026-11-13"}
    real = R.d26_counts
    R.d26_counts = lambda d, prompt=R.D26_PROMPT, date=None: dict(counts)
    argv = ["--run", "d26", "--provider-prompt-check", "--tokenizer-dir", "unused", "--run-cap", "1"]
    try:
        c = run(argv)
        ck("registration first", c == 2 and "registration is not recorded" in run.out and not Fake.sent
           and not led(R.D26_KIND) and not S.SPEND_LOCK.exists())
        ledger(kind="registration", tag="t")
        Fake.rules[m22["model"]] = [{"input_tokens": 566}]
        c = run(argv)
        lines = [e for e in jsonl(R.d26_log_path()) if e.get("kind") == "counts"]
        ck("one sentinel call, of model 22 only, never a benchmark prompt",
           c == 0 and Fake.sent == [(m22["model"], None)]
           and all(r["prompt"].strip() != R.D26_PROMPT for r in ROWS.values()))
        ck("the counts and their reading", len(lines) == 1 and lines[0]["model_key"] == K[22]
           and lines[0]["reported_input_tokens"] == 566 and lines[0]["request_tokens"] == 12
           and lines[0]["template_default_tokens"] == 566 and lines[0]["reading"] == "template_default"
           and "default system message of the published chat template" in run.out)
        pc, pre = led(R.D26_KIND), [e for e in led("preflight") if e.get("role") == "provider_prompt"]
        ck("ledger: a preflight line, then one call line outside every block",
           len(pre) == 1 and pre[0]["ok"] and len(pc) == 1 and pc[0]["role"] == "provider_prompt"
           and pc[0]["final"] is True and pc[0]["status"] == "ok" and pc[0]["prompt_sha256"] == sha(R.D26_PROMPT)
           and 0 < pc[0]["spent_usd"] <= pc[0]["reserved_usd"] and not led("call") and not led("availability_call"))
        books = S.Books("probe", write=False)
        ck("against the cap, in no holds item", not books.final and abs(books.spent - pc[0]["spent_usd"]) < 1e-9)
        raw, pub = jsonl(R.d26_raw_path()), jsonl(R.d26_log_path())
        ck("the answer only in the private record", len(raw) == 1 and raw[0]["text"] == ANSWER
           and all("text" not in e and "error_body" not in e for e in pub))
        c = run(argv)
        ck("recorded: not sent again", c == 0 and len(Fake.sent) == 1 and len(led(R.D26_KIND)) == 1
           and "not sent again" in run.out)
        ck("the pilot report states it", PR.provider_prompt(R.LOGS)[K[22]]["reading"] == "template_default"
           and PR.provider_prompt(R.LOGS)[K[22]]["reported_input_tokens"] == 566)
        ck("readings", [R.d26_reading(x, counts)[0] for x in (12, 16, 563, 300, 5, None)]
           == ["none_added", "none_added", "template_default", "other_added", "fewer", "no_count"])
        ledger(kind="freeze", tag="f")
        c = run(["--run", "d26b"] + argv[2:])
        ck("refused after the freeze", c == 2 and "freeze is recorded" in run.out and len(Fake.sent) == 1)
    finally:
        R.d26_counts = real
    bad = tmp / "tok"
    bad.mkdir()
    for name in R.D26_TOKENIZER["files"]:
        (bad / name).write_text("not the pinned file", encoding="utf-8")
    try:
        R.d26_counts(bad)
        pinned = False
    except SystemExit as e:
        pinned = "not the pinned file" in str(e)
    ck("the tokenizer files must be the pinned ones", pinned)
    for args, words in ((["--run", "x", "--provider-prompt-check", "--block", "1"], "takes --run, --tokenizer-dir"),
                        (["--run", "x", "--provider-prompt-check", "--models", K[22]], "takes --run, --tokenizer-dir"),
                        (["--run", "x", "--provider-prompt-check", "--run-cap", "1"], "--tokenizer-dir is required"),
                        (["--provider-prompt-check"], "--run is required"),
                        (["--run", "full", "--provider-prompt-check"], "sealed")):
        c = run(args)
        ck(f"refused: {words}", isinstance(c, str) and words in c)
    ck("nothing else sent", len(Fake.sent) == 1 and not S.SPEND_LOCK.exists())
    ck("no leaks", no_leaks(tmp))
    return ck.ok()


def t_provider_prompt_recovery_and_edges():
    """Review round 15, decision D26: the exact request and configuration; a check killed before its ledger line,
    after it, or before its private record (recovered as the test call of D13: a recorded final call is never sent
    again, an unrecorded one is settled at its reservation and sent again); a reservation that does not fit the cap;
    an empty answer that reports its input tokens; each pinned tokenizer file checked on its own; the counts through
    the pilot report's JSON and Markdown."""
    import pilot_report_v23 as PR
    ck = Checks("provider_prompt recovery")
    counts = {"request": 12, "template_default": 566, "date": "2026-11-13"}
    real = R.d26_counts
    R.d26_counts = lambda d, prompt=R.D26_PROMPT, date=None: dict(counts)
    argv = ["--run", "d26", "--provider-prompt-check", "--tokenizer-dir", "unused", "--run-cap", "1"]

    def prepare(name, rules):
        tmp, models = setup(name)
        K, M = keymap(models)
        ledger(kind="registration", tag="t")
        m22 = M[K[22]]
        Fake.rules[m22["model"]] = list(rules)
        return tmp, K, m22

    def counts_lines():
        return [e for e in jsonl(R.d26_log_path()) if e.get("kind") == "counts"]

    try:
        # the exact request and configuration
        tmp, K, m22 = prepare("provider_prompt_exact", [{"input_tokens": 566}])
        seen, orig_call = [], Fake.call

        def spy(self, prompt):
            seen.append((copy.deepcopy(self.cfg), prompt))
            return orig_call(self, prompt)
        Fake.call = spy
        try:
            c = run(argv)
        finally:
            Fake.call = orig_call
        raw = jsonl(R.d26_raw_path())
        ck("exactly the sentinel request, with the respondent configuration of model 22",
           c == 0 and len(seen) == 1 and seen[0][1] == R.D26_PROMPT == "Please reply with the single word: ready."
           and seen[0][0] == m22 and len(raw) == 1 and raw[0]["config_sha256"] == R.config_hash(m22)
           and raw[0]["pin_sha256"] == R.pin_hash(m22)
           and raw[0]["request_sha256"] == R.request_hash(m22, R.D26_PROMPT)
           and raw[0]["output_cap"] == m22["max_output_tokens"])
        # the counts through the pilot report's JSON and Markdown
        pp = PR.provider_prompt(R.LOGS)
        rep = {"round": 1, "rules": {}, "respondents": {}, "judges": {}, "blocks": [],
               "ledger": {"block1_spent_usd": 0.0}, "provider_prompt": pp}
        md, back = PR.markdown(rep), json.loads(json.dumps(rep))["provider_prompt"][K[22]]
        ck("the report: JSON and Markdown state the counts and the reading",
           back["reported_input_tokens"] == 566 and back["request_tokens"] == 12
           and back["template_default_tokens"] == 566 and back["reading"] == "template_default"
           and back["status"] == "ok" and f"{K[22]} (model 22" in md and "input tokens reported 566" in md
           and "the request alone 12" in md and "default system message 566" in md
           and PR.D26_TEXT["template_default"] in md and "The check was not made" not in md)

        # killed at three points; run again
        for name, target, when, resent in (("before the ledger line", "settle_outside_plan", "before", False),
                                           ("after the ledger line", "settle_outside_plan", "after", False),
                                           ("before the record", "write_availability_attempt", "before", True)):
            tmp, K, m22 = prepare("provider_prompt_crash_" + name.replace(" ", "_"),
                                  [{"input_tokens": 566}, {"input_tokens": 566}])
            orig = getattr(R, target)

            def wrapped(*args, _orig=orig, _when=when, **kwargs):
                if _when == "before":
                    raise Crash()
                _orig(*args, **kwargs)
                raise Crash()
            setattr(R, target, wrapped)
            try:
                run(argv)
                crashed = False
            except Crash:
                crashed = True
            finally:
                setattr(R, target, orig)
            S.SPEND_LOCK.unlink(missing_ok=True)
            ck(f"{name}: killed after one call", crashed and len(Fake.sent) == 1 and not counts_lines())
            c = run(["--run", "d26r"] + argv[2:])
            calls = led(R.D26_KIND)
            rl = [e for e in calls if e.get("reconciled")]
            raw = {r["attempt_id"]: r for r in jsonl(R.d26_raw_path())}
            lines = counts_lines()
            ck(f"{name}: books settled, counts read", c == 0 and not S.Books("look", write=False).unsettled()
               and len(lines) == 1 and lines[0]["reported_input_tokens"] == 566
               and lines[0]["reading"] == "template_default")
            if when == "before" and not resent:
                ck(f"{name}: settled at the recorded cost, not sent again", len(Fake.sent) == 1 and len(calls) == 1
                   and len(rl) == 1 and abs(rl[0]["spent_usd"] - raw[rl[0]["attempt_id"]]["cost_usd"]) < 1e-12
                   and rl[0]["spent_usd"] < rl[0]["reserved_usd"] and "not sent again" in run.out)
            elif not resent:
                ck(f"{name}: not sent again", len(Fake.sent) == 1 and len(calls) == 1 and not rl
                   and "not sent again" in run.out)
            else:
                ck(f"{name}: settled at its reservation as interrupted, then sent again",
                   len(Fake.sent) == 2 and len(calls) == 2 and len(rl) == 1 and rl[0]["status"] == "interrupted"
                   and rl[0]["final"] is False and rl[0]["spent_usd"] == rl[0]["reserved_usd"]
                   and rl[0]["attempt_id"] not in raw and len(raw) == 1)
            c = run(["--run", "d26s"] + argv[2:])
            ck(f"{name}: a third run sends nothing", c == 0 and len(Fake.sent) == 1 + resent)

        # a reservation that does not fit the run cap
        tmp, K, m22 = prepare("provider_prompt_cap", [{"input_tokens": 566}])
        c = run(argv[:-1] + ["0.0000001"])
        ck("a reservation over the run cap: not sent, nothing settled, incomplete",
           c == 3 and not Fake.sent and not led(R.D26_KIND) and "not sent" in run.out
           and not S.Books("look", write=False).unsettled() and not counts_lines())

        # an empty answer that reports its input tokens
        tmp, K, m22 = prepare("provider_prompt_empty", [{"text": "", "input_tokens": 566}])
        c = run(argv)
        lines = counts_lines()
        ck("an empty answer keeps its count", c == 0 and len(lines) == 1 and lines[0]["status"] == "empty"
           and lines[0]["reported_input_tokens"] == 566 and lines[0]["reading"] == "template_default")
        c = run(["--run", "d26e"] + argv[2:])
        ck("an empty final answer is not sent again", c == 0 and len(Fake.sent) == 1 and len(counts_lines()) == 2
           and counts_lines()[1]["reported_input_tokens"] == 566)
    finally:
        R.d26_counts = real

    # each pinned file is checked on its own
    pins = copy.deepcopy(R.D26_TOKENIZER)
    d = tmp / "pins"
    d.mkdir()
    good = {name: f"content of {name}" for name in pins["files"]}
    try:
        R.D26_TOKENIZER["files"] = {name: sha(text) for name, text in good.items()}
        for name in good:
            for how in ("changed", "missing"):
                for n2, text in good.items():
                    (d / n2).write_text(text, encoding="utf-8", newline="")
                if how == "changed":
                    (d / name).write_text(good[name] + " ", encoding="utf-8", newline="")
                else:
                    (d / name).unlink()
                try:
                    real(d)
                    msg = ""
                except SystemExit as e:
                    msg = str(e)
                ck(f"{name} {how}: refused", msg.startswith(f"{name} in ") and "not the pinned file" in msg)
        for n2, text in good.items():
            (d / n2).write_text(text, encoding="utf-8", newline="")
        try:
            real(d)
            passed = True
        except SystemExit:
            passed = False
        except Exception:               # past the pins: the stand-in files are not a tokenizer
            passed = True
        ck("all three pinned files: past the check", passed)
    finally:
        R.D26_TOKENIZER.clear()
        R.D26_TOKENIZER.update(pins)
    ck("no leaks", no_leaks(tmp))
    return ck.ok()


TESTS = [t_block1_rounds_sealed_and_close, t_block2_registered_hosted_first, t_block4_batch_lost_reply_and_collect,
         t_batch_item_kinds_overrun_and_stale, t_outcomes_final_suspected_config, t_pending_five_in_a_row_and_resume,
         t_overrun_stops_paid_calls, t_run_cap_and_study_cap, t_preflight_and_d2, t_provider_stop,
         t_block_order_registration_and_arguments, t_holds_cover_every_paid_call, t_complete_block_models_and_abandon,
         t_local_identity_checks, t_answer_guard_dry_run_and_errors, t_lock_and_interrupted_lines,
         t_availability_check_facts_and_ledger, t_availability_pilot_and_d2, t_availability_call_failures,
         t_adapters_offline, t_google_adapter_offline, t_settle_is_atomic, t_crash_recovery_respondent,
         t_freeze_checks_ceiling, t_overrun_survives_crash, t_availability_recovered_after_crash,
         t_availability_reuse_conditions, t_batch_overrun_aggregate_only, t_availability_saved_identity_ignored,
         t_availability_midnight_rollover, t_provider_prompt_check, t_provider_prompt_recovery_and_edges]


def main():
    only = sys.argv[1:]
    failed = ran = 0
    for t in TESTS:
        if only and t.__name__ not in only:
            continue
        ran += 1
        try:
            ok = bool(t())
        except Exception:
            traceback.print_exc()
            ok = False
        finally:
            if S.SPEND_LOCK.exists() and "lock" not in t.__name__:
                S.SPEND_LOCK.unlink()
        failed += not ok
        print(("PASS " if ok else "FAIL ") + t.__name__, flush=True)
    print(f"\n{ran - failed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
