"""Offline tests of the answering runner of protocol v2.3 (src/run_models.py) and the spending rules of
src/spend_v23.py that it uses.

Fake providers, synthetic answer files and the recorded prices; every file goes to a scratch folder (AC_TEST_TMP,
default E:/claude/agentsControl_work/tmp/respondent_agent). Nothing is sent over the network, no model is called,
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

TMP = pathlib.Path(os.environ.get("AC_TEST_TMP", "E:/claude/agentsControl_work/tmp/respondent_agent")) \
    / "test_runner_offline"
REAL_MODELS = json.loads((ROOT / "config" / "models.json").read_text(encoding="utf-8"))
REAL_DESIGN = json.loads((ROOT / "config" / "panel_v23.json").read_text(encoding="utf-8"))
REAL_HOLDS = json.loads((ROOT / "config" / "stage_holds.json").read_text(encoding="utf-8"))
REAL_SETTINGS = json.loads((ROOT / "config" / "judge_v23.json").read_text(encoding="utf-8"))
SNAPSHOT = json.loads((ROOT / "data/selection/2026-11-11/raw/or_endpoints_zdr.json").read_text(encoding="utf-8"))["data"]
FR = frames_v23.frames()
PILOT = P.load_pilot()
ROWS = R.load_rows()
INSTALLED = {m["model"]: m.get("digest") for m in REAL_MODELS["models"] if m["provider"] == "ollama"}
SENTINEL = "SENTINEL-SEALED-ANSWER-7f3a"          # text of the synthetic sealed answers: must never leave them
ANSWER = "Synthetic answer of a fake model."
PILOT_REPORT_FIELDS = ("model_key", "prompt_id", "error", "input_tokens", "output_tokens", "reasoning_tokens",
                       "cost_usd", "latency_s", "pilot")
LOCAL = (4, 5, 6, 15, 16, 17, 18, 19, 20, 21)
API = (1, 2, 3, 7, 8, 9, 10, 11, 12, 13, 14, 22, 23)
for v in ("STUDY_BUDGET_USD", "BUDGET_USD"):
    os.environ.pop(v, None)

_orig_append_line = S.append_line


def fast_append_line(path, obj, durable=True):        # no fsync in tests
    return _orig_append_line(path, obj, False)


SLEEPS = []
S.append_line = fast_append_line
R.SLEEP = lambda s: SLEEPS.append(s)
R.load_env = lambda: None                             # never the real .env in tests


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
    for m in models["models"]:
        if m["n"] == 14:
            m["d2_safety_retention"] = "all"          # decision D2 is the PI's; the D2 test sets other values
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
    S.STUDY_CAP_DEFAULT = cap
    Fake.rules, Fake.sent, Fake.batches, Fake.submits, Fake.deleted, Fake.uploads_deleted = {}, [], {}, [], [], []
    Fake.batch_rules, Fake.result_rules, Fake.running, Fake.zdr_calls = {}, {}, set(), 0
    Fake.ollama_version, Fake.zdr = "0.40.15", SNAPSHOT
    SLEEPS.clear()
    OUTPUTS.clear()
    return tmp, models["models"]


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
    write_sealed("full", model_of(models, 4), ids1[:-3], error_ids={ids1[0]})   # 3 missing, 1 transport error
    write_sealed("v22_local", model_of(models, 15), ids1)                      # complete: tail answers of a sealed run
    write_sealed("pilot_local", model_of(models, 5), ids1)                     # the version-1 pilot: not used
    c1 = run(["--run", "p1", "--block", "1", "--round", "1", "--run-cap", "100", "--workers", "4"])
    recs = records("p1")
    per = collections.Counter(r["model_key"] for r in recs)
    ck("round 1 exit", c1 == 0)
    ck("sealed answers are done; a sealed transport error is sent again", per[K[4]] == 4 and K[15] not in per)
    ck("pilot_local is not used", per[K[5]] == 100)
    ck("local models answer 100", all(per[K[n]] == 100 for n in LOCAL if n not in (4, 15)))
    ck("API models answer 20", all(per[K[n]] == 20 for n in API))
    ck("record fields", all(r["protocol"] == "2.3" and r["block"] == "1" and r["round"] == 1 and r["pilot"] is True
                            and r["final"] is True and r["error"] is None and r["answer_status"] == "ok"
                            and r["item"] == f"1|respondent|{r['model_key']}|pilot_r1" for r in recs))
    ck("pilot report fields kept", all(f in r for r in recs for f in PILOT_REPORT_FIELDS))
    ck("returned model and serving provider recorded", all(r.get("model_returned") and r.get("served_provider")
                                                            for r in recs))
    calls = led("call")
    paid = [r for r in recs if r["provider"] != "ollama"]
    ck("one ledger call line per paid attempt", len(calls) == len(paid) == 13 * 20)
    ck("call lines", all(e["role"] == "respondent" and e["block"] == "1" and e["final"] is True
                         and e["item"].endswith("|pilot_r1") and e["model_key"] in M for e in calls))
    pre = {e["model_key"]: e for e in led("preflight")}
    ck("preflight of every routed model", sorted(pre) == sorted(K[n] for n in (7, 8, 10, 12, 13, 14, 22, 23))
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
    ck("session line", len(ses) == 1 and ses[0]["block"] == "1" and ses[0]["round"] == 1 and ses[0]["to_do"] == 1064)
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
    ck("round 2 done", c4 == 0 and len(records("p2b")) == 1260 - 3)
    cc2 = run(["--run", "close1", "--block", "1", "--complete-block", "--reason", "pilot done"])
    bc = led("block_complete")
    ck("block 1 closed on both rounds", cc2 == 0 and len(bc) == 1 and bc[0]["role"] == "respondent"
       and bc[0]["models"] is None and bc[0]["rounds"] == [1, 2] and bc[0]["planned"] == 2520
       and bc[0]["final_by_status"] == {"ok": 2520} and bc[0]["not_attempted"] == {})
    ck("closed in the books", S.Books("probe", write=False).closed("1", "respondent"))
    c5 = run(["--run", "p3", "--block", "1", "--round", "1", "--run-cap", "100", "--models", K[22]])
    ck("closed block not started", c5 in (0, 2) and len(Fake.sent) == n + 1260)
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
    write_sealed("full", model_of(models, 4), ids[2:])
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
    ck("counts", c2 == 0 and by == {K[22]: 390, K[4]: 2})
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
    ck("session line", ses[-1]["block"] == "2" and set(ses[-1]["models"]) == {K[4], K[22]})
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
    tmp, models = setup("d2_safe_only", models_edit=lambda ms: model_of(ms, 14).update(d2_safety_retention="safe_only"))
    K, M = keymap(models)
    ledger(kind="registration", tag="t")
    c = run(["--run", "d1", "--block", "1", "--round", "1", "--run-cap", "100", "--models", f"{K[14]},{K[7]}"])
    r14 = [r for r in records("d1") if r["model_key"] == K[14]]
    pre = {e["model_key"]: e for e in led("preflight")}
    ck("safe prompts only", c == 0 and len(r14) == sum(1 for p in api if ROWS[p]["expected"] == "comply")
       and all(ROWS[r["prompt_id"]]["expected"] == "comply" for r in r14) and "not_sent_d2" in run.out)
    ck("preflight line", pre[K[14]]["ok"] and pre[K[14]]["safe_only"] and pre[K[7]]["ok"]
       and not pre[K[7]]["safe_only"])
    ck("D2 harmful prompts never sent", not any(m == M[K[14]]["model"] and ROWS[p]["expected"] == "refuse"
                                                for m, p in Fake.sent))
    c = run(["--run", "d1close", "--block", "1", "--complete-block", "--models", K[14]])
    bc = [e for e in led("block_complete") if e.get("role") == "respondent"]
    ck("D2 close: the harmful prompts are excluded under D2, not abandoned",
       c == 0 and bool(bc) and bc[-1].get("excluded_d2") == {K[14]: sum(1 for p in api if ROWS[p]["expected"] == "refuse")}
       and not bc[-1]["not_attempted"] and not led("block_abandon"))
    tmp, models = setup("d2_none", models_edit=lambda ms: model_of(ms, 14).update(d2_safety_retention=None))
    ledger(kind="registration", tag="t")
    c = run(["--run", "d2", "--block", "1", "--round", "1", "--run-cap", "100", "--models", f"{K[14]},{K[7]}"])
    pre = {e["model_key"]: e for e in led("preflight")}
    ck("D2 undecided: no call", c == 3 and not [r for r in records("d2") if r["model_key"] == K[14]]
       and "preflight: " in run.out and pre[K[14]]["ok"] is False and pre[K[7]]["ok"] is True)
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
    ck("a repeated key: one test call", collections.Counter(e["run"] for e in led("availability_call"))
       == {"d1": 2, "d2": 2})
    ck("abandoned in the pilot: fact 2 does not hold", c2 == 0 and c == 0 and fact(f[K[23]], 2)[0] is False
       and "abandoned in block 1" in fact(f[K[23]], 2)[1] and "15 calls not_attempted" in fact(f[K[23]], 2)[1])
    ck("the other model: fact 2 holds", fact(f[K[22]], 2)[0] is True and fact(f[K[22]], 1)[0] is True)
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
    c = run(["--run", "f6", "--availability-check", "--run-cap", "0.000001"])
    ck("run cap", c == 3 and len(Fake.sent) == 2 and "run cap" in fact(avail_facts()[K[22]], 3)[1])

    def no_key(cfg):
        raise providers.ProjectKeyError("no key")
    saved = R.MAKE_PROVIDER
    R.MAKE_PROVIDER = no_key
    try:
        c = run(["--run", "f7", "--availability-check", "--run-cap", "1"])
    finally:
        R.MAKE_PROVIDER = saved
    ck("no project key: not sent, incomplete", c == 3 and len(Fake.sent) == 2
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


TESTS = [t_block1_rounds_sealed_and_close, t_block2_registered_hosted_first, t_block4_batch_lost_reply_and_collect,
         t_batch_item_kinds_overrun_and_stale, t_outcomes_final_suspected_config, t_pending_five_in_a_row_and_resume,
         t_overrun_stops_paid_calls, t_run_cap_and_study_cap, t_preflight_and_d2, t_provider_stop,
         t_block_order_registration_and_arguments, t_holds_cover_every_paid_call, t_complete_block_models_and_abandon,
         t_local_identity_checks, t_answer_guard_dry_run_and_errors, t_lock_and_interrupted_lines,
         t_availability_check_facts_and_ledger, t_availability_pilot_and_d2, t_availability_call_failures,
         t_adapters_offline]


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
