"""Offline tests of the judging code of protocol v2.3: src/judge_v23.py, src/plan_v23.py, src/run_judges_v23.py and
the spending rules of src/spend_v23.py that it uses.

Synthetic answers, fake providers and the recorded prices; every file goes to a scratch folder (AC_TEST_TMP,
default E:/claude/agentsControl_tests/test_judges_v23). Nothing is sent over the network, no model is called,
and no file under results/ is read or written. Benchmark prompts are read from data/processed/sample.jsonl, as the
runner does; nothing is printed from them.

Run: python -I -X utf8 tests/test_judges_v23.py        (exit code 0 when every test passes)
"""
import contextlib
import copy
import hashlib
import io
import json
import os
import pathlib
import shutil
import sys
import traceback

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import answers_v23 as A  # noqa: E402
import frames_v23  # noqa: E402
import judge_v23 as J  # noqa: E402
import label_sample  # noqa: E402
import plan_v23 as P  # noqa: E402
import providers  # noqa: E402
import run_judges_v23 as R  # noqa: E402
import screen as screen_mod  # noqa: E402
import spend_v23 as S  # noqa: E402

TMP = pathlib.Path(os.environ.get("AC_TEST_TMP", "E:/claude/agentsControl_tests")) / "test_judges_v23"
REAL_MODELS = json.loads((ROOT / "config" / "models.json").read_text(encoding="utf-8"))
REAL_DESIGN = json.loads((ROOT / "config" / "panel_v23.json").read_text(encoding="utf-8"))
REAL_HOLDS = json.loads((ROOT / "config" / "stage_holds.json").read_text(encoding="utf-8"))
REAL_SETTINGS = json.loads((ROOT / "config" / "judge_v23.json").read_text(encoding="utf-8"))
SNAPSHOT = json.loads((ROOT / "data/selection/2026-11-11/raw/or_endpoints_zdr.json").read_text(encoding="utf-8"))["data"]
FR = frames_v23.frames()
PILOT = P.load_pilot()
RULES = screen_mod.load()
REFUSAL = "I'm sorry, but I can't help with that."
VALID = '{"label": "full_refusal", "harmful_content": false, "confidence": 80, "reason": "synthetic"}'
os.environ.pop("STUDY_BUDGET_USD", None)

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


S.append_line = fast_append_line
R.SLEEP = lambda s: None
R.LOAD_ENV = lambda: None                             # never the real .env in tests


# ---- fakes --------------------------------------------------------------------------------------------------------------

class FakeHTTP(Exception):
    def __init__(self, status, msg):
        super().__init__(msg)
        self.status_code, self.message = status, msg


def served(m):
    return (m.get("pin") or {}).get("provider_name") or ("ollama-local" if m["provider"] == "ollama" else m["provider"])


class Fake:
    """A provider. Fake.rules[model] is a list of behaviours used one per call (then 'ok'), or a callable."""
    rules, sent = {}, []

    def __init__(self, cfg):
        self.cfg = cfg

    def call(self, msgs):
        model = self.cfg["model"]
        Fake.sent.append({"model": model, "roles": [m["role"] for m in msgs],
                          "sha": hashlib.sha256(json.dumps(msgs).encode()).hexdigest()})
        beh = Fake.rules.get(model)
        r = beh(self.cfg, msgs) if callable(beh) else (beh.pop(0) if beh else "ok")
        if isinstance(r, Exception):
            raise r
        nbytes = sum(len(m["content"].encode()) for m in msgs)
        out = {"text": VALID, "stop_reason": "stop", "provider_block": False, "served_provider": served(self.cfg),
               "model_returned": self.cfg["model"], "input_tokens": nbytes // 4, "output_tokens": 40,
               "reasoning_tokens": None, "cost_reported": None, "request_id": None}
        if isinstance(r, dict):
            out.update(r)
        elif isinstance(r, str) and r != "ok":
            out["text"] = r
        return out


def fake_identity(model, base=None):
    for m in Fake.models:
        cfg = J.judge_cfg(m, REAL_SETTINGS) if m["provider"] == "ollama" else None
        if cfg and cfg["model"] == model:
            return {"digest": cfg["digest"], "ollama_version": Fake.ollama_version}
        if m.get("judge_model_sensitivity") == model:
            return {"digest": m.get("judge_model_sensitivity_digest"), "ollama_version": Fake.ollama_version}
    return {"digest": None, "ollama_version": Fake.ollama_version}


Fake.models, Fake.ollama_version, Fake.zdr = [], "0.40.15", SNAPSHOT
R.MAKE_PROVIDER = lambda cfg: Fake(cfg)
R.OLLAMA_IDENTITY = fake_identity
R.FETCH_ZDR = lambda: Fake.zdr


# ---- scratch study -------------------------------------------------------------------------------------------------------

def setup(name, cap=128.0, models_edit=None, design_edit=None, holds_edit=None, settings_edit=None):
    tmp = TMP / name
    shutil.rmtree(tmp, ignore_errors=True)
    (tmp / "raw").mkdir(parents=True)
    (tmp / "logs").mkdir()
    R.RAW, R.LOGS = tmp / "raw", tmp / "logs"
    S.LEDGER, S.SPEND_LOCK = tmp / "logs" / "spend_ledger.jsonl", tmp / "logs" / "spend.lock"
    models = copy.deepcopy(REAL_MODELS)
    for m in models["models"]:
        if m["n"] == 6:
            m["judge_model_digest"] = "sha256:test-q4_0-build"
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
    R.MODELS, R.DESIGN, S.HOLDS, J.SETTINGS = tmp / "models.json", tmp / "panel.json", tmp / "holds.json", \
        tmp / "judge.json"
    R.LABELS = tmp / "labels.jsonl"
    S.MANIFEST = tmp / "manifest.json"
    S.STUDY_CAP_DEFAULT = cap
    Fake.models, Fake.rules, Fake.sent, Fake.zdr, Fake.ollama_version = models["models"], {}, [], SNAPSHOT, "0.40.15"
    return tmp, models["models"]


def h01(*x):
    return int(hashlib.sha256("|".join(map(str, x)).encode()).hexdigest()[:8], 16) / 0xFFFFFFFF


def answer_text(m, pid, side, removed):
    u = h01("text", m["key"], pid)
    if side == "harmful":
        positive = u < (0.7 if removed else 0.2)
    else:
        positive = u < 0.9
    return (f"Synthetic answer to {pid}: here are some harmless placeholder sentences." if positive
            else f"{REFUSAL} (synthetic {pid})")


def write_answers(models, run, pilot_round=None, empty_share=0.0, skip=()):
    panel = P.Panel(models, REAL_DESIGN)
    rows = []
    for m in models:
        n = m["n"]
        if pilot_round:
            rnd = PILOT["rounds"][pilot_round - 1]
            if n in panel.local:
                ids = rnd["harmful"] + rnd["safe"]
            elif n in panel.hosted_all or n in panel.commercial:
                ids = rnd["api"]
            else:
                continue
            harmful = set(rnd["harmful"])
        else:
            if n in panel.primary:
                ids = FR["harmful"][0] + FR["safe"][0]
            elif n in panel.commercial:
                ids = FR["common"][0] + FR["safe"][0]
            else:
                continue
            harmful = set(FR["harmful"][1])
        for pid in ids:
            if (m["key"], pid) in skip:
                continue
            side = "harmful" if pid in harmful else "safe"
            src = (FR["harmful"][1].get(pid) or FR["safe"][1].get(pid) or FR["harmful_tail"][1].get(pid)
                   or FR["safe_tail"][1].get(pid))
            empty = h01("empty", m["key"], pid) < empty_share
            rec = {"run": run, "model_key": m["key"], "model": m["model"], "prompt_id": pid, "source": src,
                   "expected": "refuse" if side == "harmful" else "comply", "pilot": bool(pilot_round),
                   "text": "" if empty else answer_text(m, pid, side, n in panel.groups["refusal_removed"]),
                   "answer_status": "empty" if empty else "ok", "error": None,
                   "model_returned": m["model"], "served_provider": served(m)}
            rows.append(rec)
    with open(R.RAW / f"responses_{run}.jsonl", "a", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    return len(rows)


def write_labels(models, runs):
    """A label sample drawn by src/label_sample.py from the synthetic answers (public fields only)."""
    panel = P.Panel(models, REAL_DESIGN, registered_hosted=[22, 23])
    table = A.load_table(runs, raw=R.RAW, number_of=panel.n_of)
    rows = [{"model": r["model"], "prompt": r["prompt_id"], "side": r["side"], "screen": r["screen"],
             "source": r["source"], "answer_id": r["answer_id"]} for r in table.values()
            if r["model"] in panel.primary + panel.commercial
            and r["prompt_id"] in (FR["harmful"][1] if r["side"] == "harmful" else FR["safe"][1])]
    labels, _ = label_sample.select(rows, label_sample.load_design())
    R.LABELS.write_text("".join(json.dumps(x) + "\n" for x in labels), encoding="utf-8")
    return labels


def ledger(**kw):
    S.append_line(S.LEDGER, dict(kw, spent_usd=kw.get("spent_usd", 0.0)))


def close(block, role, models=None):
    ledger(kind="block_complete", block=str(block), role=role, models=models, reason="test")


def run(argv):
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            code = R.main(argv)
    except SystemExit as e:
        code = e.code if isinstance(e.code, int) else str(e.code)
    run.out = buf.getvalue()
    return code


def jsonl(p):
    p = pathlib.Path(p)
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()] if p.exists() else []


def keys(models, *ns):
    return ",".join(m["key"] for m in models if m["n"] in ns)


def key(models, n):
    return next(m["key"] for m in models if m["n"] == n)


def private(block="3"):
    return jsonl(R.verdicts_path(block))


def public(block="3"):
    return jsonl(R.calls_log_path(block))


def finals(block="3"):
    out = {}
    for r in private(block):
        if r["final"]:
            out.setdefault(r["key"], r)
    return out


def main_answers(models):
    write_answers(models, "b2", empty_share=0.02)


def open_main_blocks(through):
    """Ledger lines of a study after the freeze, with blocks before `through` closed."""
    ledger(kind="registration", tag="test-registration")
    ledger(kind="freeze", tag="test-freeze")
    close(1, "respondent")
    close(1, "judge")
    for b, role in (("2", "respondent"), ("3", "judge"), ("4", "respondent"), ("5", "judge"), ("6", "judge")):
        if int(b) < int(through):
            close(b, role)


# ---- tests --------------------------------------------------------------------------------------------------------------

def t_template_layouts():
    t = J.load_template()
    ok = not J.check_template(t)
    b = J.messages(t, "REQ", "ANS", "blind")
    c = J.messages(t, "REQ", "ANS", "context")
    r = J.messages(t, "REQ", "ANS", "context", retry=True)
    u = J.messages(t, "REQ", "ANS", "blind", rubric_in_user=True)
    ok &= [m["role"] for m in b] == ["system", "user"] and b[0]["content"] == t["rubric"]
    ok &= [m["role"] for m in c] == ["system", "user", "assistant", "user"]
    ok &= c[1]["content"] == "REQ" and c[2]["content"] == "ANS" and c[3]["content"] == t["instruction"]
    ok &= b[1]["content"].endswith("\n\n" + t["instruction"]) and "REQ" in b[1]["content"] and "ANS" in b[1]["content"]
    ok &= r[-1]["content"] == t["instruction"] + "\n\n" + t["retry"]
    ok &= [m["role"] for m in u] == ["user"] and u[0]["content"].startswith(t["rubric"] + "\n\n")
    ok &= "author" not in t["instruction"].lower() and "your own" not in t["instruction"].lower()
    return ok


def t_parser_rules():
    ok = J.parse(VALID)["label"] == "full_refusal"
    ok &= J.parse("```json\n" + VALID + "\n```")["harmful_content"] is False
    ok &= J.parse("Here it is: " + VALID + " done") is not None
    ok &= J.parse('{"label": "refusal", "harmful_content": false}') is None
    ok &= J.parse('{"label": "full_refusal", "harmful_content": "false"}') is None
    ok &= J.parse('{"x": 1} {"label": "full_refusal", "harmful_content": true}') is None      # the first object
    ok &= J.parse('{"label": "partial_refusal", "harmful_content": true, "confidence": 140}')["confidence"] is None
    ok &= J.invalid_status(REFUSAL + " I will not classify this.", RULES) == "declined"
    ok &= J.invalid_status("Hmm, unsure.", RULES) == "parse_error"
    ok &= J.flag({"status": "valid", "harmful_content": True}) == 1 and J.flag({"status": "declined"}) == 0
    ok &= J.hit_cap("length") and J.hit_cap("max_tokens") and not J.hit_cap("stop")
    return ok


def t_pilot_both_rounds_and_close():
    tmp, models = setup("pilot")
    ledger(kind="registration", tag="t")
    write_answers(models, "p1", pilot_round=1)
    write_answers(models, "p2", pilot_round=2)
    m6 = key(models, 6)
    c1 = run(["--run", "j1", "--block", "1", "--round", "1", "--answer-runs", "p1,p2", "--workers", "4"])
    out1 = run.out
    fin = finals("1")
    per = {}
    for r in fin.values():
        per[r["judge"]] = per.get(r["judge"], 0) + 1
    panel = P.Panel(models, REAL_DESIGN)
    n_api = len(panel.hosted_all + panel.commercial)        # 12 since decision D17
    ok = c1 == 0 and all(per.get(panel.key_of[n]) == 200 for n in panel.local)
    ok &= all(per.get(panel.key_of[n]) == 60 for n in panel.hosted_all + panel.commercial)
    pub = public("1")
    ok &= all("output" not in r and "reason" not in r and "label" not in r and "harmful_content" not in r for r in pub)
    text = (R.LOGS / "judge_calls_v23_pilot.jsonl").read_text(encoding="utf-8")
    ok &= "Synthetic answer" not in text and REFUSAL not in text
    calls = [e for e in jsonl(S.LEDGER) if e.get("kind") == "call"]
    ok &= len(calls) == n_api * 60 and all(e["item"].endswith("|pilot_r1") for e in calls)
    ok &= all(e["spent_usd"] <= e["reserved_usd"] + 1e-12 for e in calls)
    ok &= all(r["identity_match"] is True for r in pub if r["judge_n"] in panel.hosted_all + panel.commercial)
    by_judge = {}
    for r in pub:                                  # the two calls of a pair are next to each other, per judge
        by_judge.setdefault(r["judge"], []).append(r)
    adjacent = all(seq[i]["pair"] == seq[i + 1]["pair"] for seq in by_judge.values()
                   for i in range(0, len(seq), 2) if seq[i]["pair"])
    ok &= adjacent
    starts = [r["presentation"] for r in pub if r["position"] == 0 and r["pair"]]
    ok &= 0.4 < starts.count("blind") / len(starts) < 0.6
    q = [r for r in pub if r["arm"] == "Q"]
    ok &= len(q) == n_api * 20 and len({r["answer_id"] for r in q}) == 10
    early = run(["--run", "c1", "--block", "1", "--complete-block", "--answer-runs", "p1,p2"])   # round 2 not judged
    c2 = run(["--run", "j2", "--block", "1", "--round", "2", "--answer-runs", "p1,p2"])
    closed = run(["--run", "c1", "--block", "1", "--complete-block", "--answer-runs", "p1,p2"])
    lines = [e for e in jsonl(S.LEDGER) if e.get("kind") == "block_complete"]
    ok &= isinstance(early, str) and "cannot be closed" in early and c2 == 0 and closed == 0 and len(lines) == 1
    ok &= lines[0]["final_by_status"].get("valid") == 2 * (10 * 200 + n_api * 60)
    spent = sum(e["spent_usd"] for e in jsonl(S.LEDGER))
    ok &= abs(spent - sum(r["cost_usd"] for r in public("1"))) < 1e-6
    if not ok:
        print(out1[-1500:])
    return ok


def t_retry_paths():
    tmp, models = setup("retry")
    ledger(kind="registration", tag="t")
    write_answers(models, "p1", pilot_round=1)
    k1 = key(models, 1)
    m1 = next(m for m in models if m["n"] == 1)
    Fake.rules[m1["model"]] = ["no verdict here", "ok", "still nothing", "Hmm.", "nothing", REFUSAL + " No."]
    c = run(["--run", "r", "--block", "1", "--round", "1", "--answer-runs", "p1", "--judges", k1, "--max-calls", "4"])
    att = [r for r in private("1")]
    fin = [r for r in att if r["final"]]
    st = [r["status"] for r in fin]
    ok = c == 0 and st[:3] == ["valid", "parse_error", "declined"] and st[3] == "valid"
    ok &= [r["format_retry"] for r in att[:6]] == [False, True, False, True, False, True]
    ok &= sum(1 for e in jsonl(S.LEDGER) if e.get("kind") == "call") == 7
    return ok


def t_blocks_and_suspected():
    tmp, models = setup("blocks")
    ledger(kind="registration", tag="t")
    write_answers(models, "p1", pilot_round=1)
    m7 = next(m for m in models if m["n"] == 7)
    Fake.rules[m7["model"]] = [{"provider_block": True, "text": "", "block_marker": "content_filter",
                                "input_tokens": 0, "output_tokens": 0},
                               providers.SuspectedBlock(400, "bad request")]
    c = run(["--run", "b", "--block", "1", "--round", "1", "--answer-runs", "p1", "--judges", m7["key"],
             "--max-calls", "3"])
    att = private("1")
    ok = c == 0 and [r["status"] for r in att[:2]] == ["provider_block", "provider_block"]
    ok &= att[0]["block_suspected"] is False and att[1]["block_suspected"] is True and att[1]["final"]
    calls = [e for e in jsonl(S.LEDGER) if e.get("kind") == "call"]
    ok &= calls[0]["spent_usd"] == 0 and calls[1]["spent_usd"] == 0 and len(att) == 3
    return ok


def t_context_overflow():
    tmp, models = setup("overflow")
    ledger(kind="registration", tag="t")
    write_answers(models, "p1", pilot_round=1)
    m7 = next(m for m in models if m["n"] == 7)
    m4 = next(m for m in models if m["n"] == 4)
    Fake.rules[m7["model"]] = [FakeHTTP(400, "This endpoint's maximum context length is 32768 tokens."),
                               providers.SuspectedBlock(400, "prompt is too long: 40000 tokens > 32768 maximum")]
    Fake.rules[m4["model"]] = [providers.HTTPStatusError(400, '{"error":"input length exceeds the context length"}')]
    c = run(["--run", "o", "--block", "1", "--round", "1", "--answer-runs", "p1",
             "--judges", m7["key"] + "," + m4["key"], "--max-calls", "1"])
    att = {r["judge"]: r for r in private("1")}
    ok = c == 0 and att[m7["key"]]["status"] == "context_overflow" and att[m4["key"]]["status"] == "context_overflow"
    ok &= att[m7["key"]]["final"] and att[m4["key"]]["final"] and len(private("1")) == 2
    c2 = run(["--run", "o2", "--block", "1", "--round", "1", "--answer-runs", "p1", "--judges", m7["key"],
              "--max-calls", "1"])
    second = [r for r in private("1") if r["run"] == "o2"]
    ok &= c2 == 0 and len(second) == 1 and second[0]["status"] == "context_overflow" and not second[0]["block_suspected"]
    return ok


def t_transient_pending_defer_stop_resume():
    tmp, models = setup("transient")
    ledger(kind="registration", tag="t")
    write_answers(models, "p1", pilot_round=1)
    m8 = next(m for m in models if m["n"] == 8)
    seq = [FakeHTTP(429, "rate limited")] * 3 + ["ok"] + [FakeHTTP(503, "down")] * 40
    Fake.rules[m8["model"]] = seq
    c = run(["--run", "t", "--block", "1", "--round", "1", "--answer-runs", "p1", "--judges", m8["key"]])
    att = private("1")
    first = att[:4]
    ok = c == 3 and [r["status"] for r in first] == ["failed", "failed", "failed", "valid"] and first[3]["final"]
    pend = [r for r in att if r["status"] == "pending"]
    jr_out = run.out
    ok &= "5 consecutive pending calls" in jr_out and len(pend) == 5
    sent_pairs = [r["pair"] for r in att]
    ok &= all(r["try"] == 4 for r in pend)
    pairs_of_pending = {r["pair"] for r in pend if r["position"] == 0 and r["pair"]}
    second = [r for r in att if r["pair"] in pairs_of_pending and r["position"] == 1]
    ok &= not second                                       # the second call of a pending pair waits
    Fake.rules[m8["model"]] = []
    c2 = run(["--run", "t2", "--block", "1", "--round", "1", "--answer-runs", "p1", "--judges", m8["key"]])
    fin = finals("1")
    mine = [r for r in fin.values() if r["judge"] == m8["key"]]
    ok &= c2 == 0 and len(mine) == 60 and all(r["status"] == "valid" for r in mine)
    pub = [r for r in public("1") if r["run"] == "t2"]
    deferred_now = [r for r in pub if r["pair"] in pairs_of_pending]
    ok &= all(deferred_now[i]["pair"] == deferred_now[i + 1]["pair"] for i in range(0, len(deferred_now), 2))
    ok &= len(deferred_now) == 2 * len(pairs_of_pending) and len(sent_pairs) > 0
    return ok


def t_config_error_stops_judge():
    tmp, models = setup("config")
    ledger(kind="registration", tag="t")
    write_answers(models, "p1", pilot_round=1)
    m10 = next(m for m in models if m["n"] == 10)
    m5 = next(m for m in models if m["n"] == 5)
    Fake.rules[m10["model"]] = [FakeHTTP(400, "unsupported parameter: temperature")]
    Fake.rules[J.judge_cfg(m5, REAL_SETTINGS)["model"]] = [providers.HTTPStatusError(400, '{"error":"bad option"}')]
    c = run(["--run", "c", "--block", "1", "--round", "1", "--answer-runs", "p1",
             "--judges", m10["key"] + "," + m5["key"]])
    att = private("1")
    ok = c == 3 and len(att) == 2 and all(r["status"] == "config_error" and not r["final"] for r in att)
    ok &= run.out.count("STOPPED") == 2
    return ok


def t_overrun_stops_paid_calls():
    tmp, models = setup("overrun")
    ledger(kind="registration", tag="t")
    write_answers(models, "p1", pilot_round=1)
    m1, m2 = (next(m for m in models if m["n"] == n) for n in (1, 2))
    Fake.rules[m2["model"]] = [{"cost_reported": 50.0}]           # model 2 (haiku) runs first: key order
    c = run(["--run", "o", "--block", "1", "--round", "1", "--answer-runs", "p1", "--judges", m1["key"] + "," +
             m2["key"]])
    led = jsonl(S.LEDGER)
    ok = c == 3 and sum(1 for e in led if e.get("kind") == "overrun") == 1
    ok &= sum(1 for e in led if e.get("kind") == "call") == 1           # nothing after the overrun
    again = run(["--run", "o2", "--block", "1", "--round", "1", "--answer-runs", "p1", "--judges", m2["key"]])
    ok &= again == 2 and "settled above its reservation" in run.out
    return ok


def t_run_cap_and_study_cap():
    tmp, models = setup("cap")
    ledger(kind="registration", tag="t")
    write_answers(models, "p1", pilot_round=1)
    k1 = key(models, 1)
    c = run(["--run", "c", "--block", "1", "--round", "1", "--answer-runs", "p1", "--judges", k1, "--run-cap", "0.0001"])
    ok = c == 3 and not private("1") and "run cap" in run.out
    tmp, models = setup("cap2", cap=5.0)
    ledger(kind="registration", tag="t")
    write_answers(models, "p1", pilot_round=1)
    c2 = run(["--run", "c", "--block", "1", "--round", "1", "--answer-runs", "p1", "--judges", k1])
    ok &= c2 == 2 and "does not fit" in run.out and not private("1")
    os.environ["STUDY_BUDGET_USD"] = "110"           # a cap other than the cap of decision D14 stops a paid session
    try:
        c3 = run(["--run", "c", "--block", "1", "--round", "1", "--answer-runs", "p1", "--judges", k1])
    finally:
        os.environ.pop("STUDY_BUDGET_USD", None)
    ok &= isinstance(c3, str) and "STUDY_BUDGET_USD" in c3 and not private("1")
    os.environ["STUDY_BUDGET_USD"] = "5"             # the same value as the cap is accepted
    try:
        c4 = run(["--run", "c", "--block", "1", "--round", "1", "--answer-runs", "p1", "--judges", k1])
    finally:
        os.environ.pop("STUDY_BUDGET_USD", None)
    ok &= c4 == 2 and "does not fit" in run.out
    return ok


def t_block_order():
    tmp, models = setup("order")
    ledger(kind="registration", tag="t")
    main_answers(models)
    k22 = key(models, 22)
    a = run(["--run", "x", "--block", "3", "--answer-runs", "b2", "--judges", k22, "--max-calls", "2"])
    ok = a == 2 and "after the freeze" in run.out
    ledger(kind="freeze", tag="t")
    b = run(["--run", "x", "--block", "3", "--answer-runs", "b2", "--judges", k22, "--max-calls", "2"])
    ok &= b == 2 and "after block 2 is closed" in run.out
    close(1, "respondent"), close(1, "judge"), close(2, "respondent")
    c = run(["--run", "x", "--block", "3", "--answer-runs", "b2", "--judges", k22, "--max-calls", "2"])
    ok &= c == 0 and len(private("3")) == 2
    write_labels(models, ["b2"])
    d = run(["--run", "x", "--block", "5", "--answer-runs", "b2", "--judges", k22, "--max-calls", "2"])
    ok &= d == 2 and "after block 4 is closed" in run.out
    close(3, "judge"), close(4, "respondent")
    e = run(["--run", "x", "--block", "6", "--answer-runs", "b2", "--judges", key(models, 1), "--max-calls", "2"])
    ok &= e == 2 and "paid calls of block 5" in run.out
    close(5, "judge", models=[k22, key(models, 23)])
    f = run(["--run", "x", "--block", "6", "--answer-runs", "b2", "--judges", key(models, 1), "--max-calls", "2"])
    ok &= f == 0
    g = run(["--run", "x", "--block", "7", "--answer-runs", "b2", "--judges", key(models, 1), "--max-calls", "2"])
    ok &= g == 2 and "after block 6 is closed" in run.out
    nd = run(["--run", "x", "--block", "3", "--answer-runs", "b2"])
    ok &= nd == 2 and "is closed" in run.out
    return ok


def t_provider_stop_block7_and_abandon():
    tmp, models = setup("stop7")
    main_answers(models)
    write_labels(models, ["b2"])
    open_main_blocks(7)
    k12, k13, k1 = key(models, 12), key(models, 13), key(models, 1)
    a = run(["--run", "s1", "--block", "7", "--answer-runs", "b2", "--judges", f"{k12},{k13},{k1}", "--max-calls", "2"])
    first = private("7")
    ok = a == 0 and len(first) == 6
    ok &= all(first[i]["pair"] == first[i + 1]["pair"] for i in range(0, 6, 2))
    host12 = next(m for m in models if m["n"] == 12)["pin"]["provider_name"]
    ledger(kind="provider_stop", account="openrouter", host=host12, reason="test warning")
    b = run(["--run", "s2", "--block", "7", "--answer-runs", "b2", "--judges", f"{k12},{k13},{k1}", "--max-calls", "4"])
    new = [r for r in private("7") if r["run"] == "s2"]
    ok &= b == 3 and not [r for r in new if r["judge"] == k12] and len([r for r in new if r["judge"] == k13]) == 4
    ok &= len([r for r in new if r["judge"] == k1]) == 4
    cb = run(["--run", "c", "--block", "7", "--answer-runs", "b2", "--complete-block"])
    ok &= isinstance(cb, str) and "cannot be closed" in cb
    ledger(kind="block_abandon", block="7", models=[k12], reason="provider stop, PI decision (test)")
    for k in (k13, k1):
        run(["--run", "s3", "--block", "7", "--answer-runs", "b2", "--judges", k])
    others = [m["key"] for m in models if m["n"] in P.Panel(models, REAL_DESIGN).commercial and m["key"] not in
              (k12, k13, k1)]
    run(["--run", "s4", "--block", "7", "--answer-runs", "b2", "--judges", ",".join(others), "--workers", "4"])
    cc = run(["--run", "c", "--block", "7", "--answer-runs", "b2", "--complete-block"])
    line = [e for e in jsonl(S.LEDGER) if e.get("kind") == "block_complete" and e["block"] == "7"]
    per_judge = len([r for r in finals("7").values() if r["judge"] == k13])
    ok &= cc == 0 and len(line) == 1 and line[0]["not_attempted"].get("abandoned") == per_judge - 2
    return ok


def t_cut_on_half_done_block():
    tmp, models = setup("cut")
    main_answers(models)
    write_labels(models, ["b2"])
    open_main_blocks(6)
    k1 = key(models, 1)
    a = run(["--run", "h1", "--block", "6", "--answer-runs", "b2", "--judges", k1, "--max-calls", "10"])
    books = S.Books("probe", write=False)
    left = books.remaining()
    cap = books.spent + left - S.load_holds()["check"]["cut_1"][0] - 1.0     # cut 1 alone is not enough
    S.STUDY_CAP_DEFAULT = cap
    b = run(["--run", "h2", "--block", "6", "--answer-runs", "b2", "--judges", k1])
    cuts = [e for e in jsonl(S.LEDGER) if e.get("kind") == "cut"]
    new = [r for r in private("6") if r["run"] == "h2"]
    ok = a == 0 and b == 0 and [e["cut"] for e in cuts] == [1, 2]
    ok &= not [r for r in new if r["part"] in ("repeat", "control_safe")]
    ok &= len([r for r in new if r["part"] == "own"]) > 0 and "not_sent_closed" in run.out
    ok &= cuts[0]["saves_usd_at_cut"] < S.load_holds()["check"]["cut_1"][0] + 1e-9
    return ok


def t_price_rise():
    tmp, models = setup("price")
    ledger(kind="registration", tag="t")
    write_answers(models, "p1", pilot_round=1)
    m12 = next(m for m in models if m["n"] == 12)
    zdr = copy.deepcopy(SNAPSHOT)
    for e in zdr:
        if e["model_id"] == m12["model"] and e["tag"] == m12["pin"]["tag"]:
            e["pricing"]["completion"] = str(float(e["pricing"]["completion"]) * 1.5)
    Fake.zdr = zdr
    c = run(["--run", "p", "--block", "1", "--round", "1", "--answer-runs", "p1", "--judges", m12["key"]])
    ok = c == 3 and "preflight" in run.out and not private("1")
    pre = [e for e in jsonl(S.LEDGER) if e.get("kind") == "preflight"]
    ok &= len(pre) == 1 and not pre[0]["ok"]

    def dearer(h):
        for it in h["items"]:
            it["usd_per_call"] *= 1.2
    tmp, models = setup("price2", holds_edit=dearer)
    main_answers(models)
    write_labels(models, ["b2"])
    open_main_blocks(6)
    ledger(kind="credit_fee", account="test", note="spending of earlier blocks (synthetic)", spent_usd=74.5)
    # block 6 alone costs about US$54.4 at these prices: 74.5 + 54.4 > 128, and cut 1 (about US$1.9) makes it fit
    c2 = run(["--run", "p", "--block", "6", "--answer-runs", "b2", "--judges", key(models, 1), "--max-calls", "1"])
    cuts = [e["cut"] for e in jsonl(S.LEDGER) if e.get("kind") == "cut"]
    ok &= c2 == 0 and cuts and cuts[0] == 1
    return ok


def t_d2_safe_only():
    def edit(ms):
        via_openrouter_14(ms, "safe_only")
    tmp, models = setup("d2", models_edit=edit)
    main_answers(models)
    write_labels(models, ["b2"])
    open_main_blocks(6)
    k14 = key(models, D2_N)
    c = run(["--run", "d", "--block", "6", "--answer-runs", "b2", "--judges", k14, "--max-calls", "400"])
    sent = private("6")
    ok = (c == 0 and sent and all(r["side"] == "safe" for r in sent) and "not_sent_d2" in run.out
          and not any(r["part"].startswith(("challenge", "reference")) for r in sent))   # Section 19.1, D2
    c = run(["--run", "d", "--block", "6", "--answer-runs", "b2", "--judges", k14])          # the rest of its calls
    cc = run(["--run", "dc", "--block", "6", "--answer-runs", "b2", "--judges", k14, "--complete-block"])
    bc = [e for e in jsonl(S.LEDGER) if e.get("kind") == "block_complete" and e.get("block") == "6"]
    ok &= (c == 0 and cc == 0 and bool(bc) and bc[-1]["excluded_d2"].get(k14, 0) > 0 and not bc[-1]["not_attempted"]
           and not any(e.get("kind") == "block_abandon" for e in jsonl(S.LEDGER)))   # excluded, not abandoned
    ok &= not any(r["part"].startswith(("challenge", "reference")) for r in private("6"))
    # model D2_N under D2 wrote no answer to a harmful prompt: the judge that controls its common answers closes block 6
    # without --allow-missing, and those judgements are counted apart (missing_d2), not as missing
    tmp, models = setup("d2gap", models_edit=edit)
    k14 = key(models, D2_N)
    write_answers(models, "b2", skip={(k14, p) for p in FR["common"][0]})
    write_labels(models, ["b2"])
    open_main_blocks(6)
    run(["--run", "pre", "--block", "6", "--answer-runs", "b2", "--judges", k14, "--max-calls", "1"])   # its preflight
    asg, _ = P.load_assignment()
    jx = asg[("commercial", "common")][FR["common"][0][0]][D2_N]
    kx = key(models, jx)
    c = run(["--run", "x", "--block", "6", "--answer-runs", "b2", "--judges", kx])
    cc = run(["--run", "xc", "--block", "6", "--answer-runs", "b2", "--judges", kx, "--complete-block"])
    bc = [e for e in jsonl(S.LEDGER) if e.get("kind") == "block_complete" and e.get("block") == "6"]
    gap = (c == 0 and cc == 0 and bool(bc) and bc[-1]["not_sent"].get("missing_d2", 0) > 0
           and "missing" not in bc[-1]["not_sent"] and "never written under decision D2" in run.out)
    if not gap:
        print("   d2 gap:", c, cc, bc[-1] if bc else None, run.out[-300:])
    ok &= gap
    tmp, models = setup("d2none", models_edit=lambda ms: via_openrouter_14(ms, None))
    main_answers(models)
    write_labels(models, ["b2"])
    open_main_blocks(6)
    c2 = run(["--run", "d", "--block", "6", "--answer-runs", "b2", "--judges", k14, "--max-calls", "4"])
    ok &= c2 == 3 and not private("6") and "decision D2" in run.out
    return ok


def t_identity_mismatch_counted():
    tmp, models = setup("ident")
    ledger(kind="registration", tag="t")
    write_answers(models, "p1", pilot_round=1)
    m3 = next(m for m in models if m["n"] == 3)
    Fake.rules[m3["model"]] = [{"model_returned": "gpt-5.6-luna-2027-01-01"}]
    c = run(["--run", "i", "--block", "1", "--round", "1", "--answer-runs", "p1", "--judges", m3["key"],
             "--max-calls", "3"])
    att = private("1")
    ok = c == 0 and [r["identity_match"] for r in att] == [False, True, True] and "identity_mismatch" in run.out
    return ok


def t_local_checks():
    tmp, models = setup("local", models_edit=lambda ms: [m.update(judge_model_digest=None) for m in ms if m["n"] == 6])
    ledger(kind="registration", tag="t")
    write_answers(models, "p1", pilot_round=1)
    c = run(["--run", "l", "--block", "1", "--round", "1", "--answer-runs", "p1", "--judges", key(models, 6)])
    ok = isinstance(c, str) and "no digest is recorded" in c and not private("1")
    tmp, models = setup("local2")
    ledger(kind="registration", tag="t")
    write_answers(models, "p1", pilot_round=1)
    Fake.ollama_version = "0.41.0"
    c2 = run(["--run", "l", "--block", "1", "--round", "1", "--answer-runs", "p1", "--judges", key(models, 4) + "," +
              key(models, 1)])
    ok &= isinstance(c2, str) and "Ollama 0.41.0" in c2 and not private("1") and not jsonl(S.LEDGER)[1:]
    return ok


def t_sensitivity_build():
    tmp, models = setup("sens")
    main_answers(models)
    open_main_blocks(3)
    c = run(["--run", "s", "--block", "3", "--answer-runs", "b2", "--build", "sensitivity", "--max-calls", "6"])
    att = jsonl(R.verdicts_path("3", "sensitivity"))
    m6 = next(m for m in models if m["n"] == 6)
    ok = c == 0 and len(att) == 6 and not R.verdicts_path("3").exists()
    ok &= all(r["build"] == "sensitivity" and r["model_requested"] == m6["judge_model_sensitivity"] for r in att)
    return ok


def t_answer_guard():
    saved = S.LEDGER
    S.LEDGER = ROOT / "results" / "logs" / "spend_ledger.jsonl"      # the study's ledger: read, never written
    try:
        A.guard(A.RAW)
        return S.registered()            # only fine when the real ledger records a registration
    except SystemExit as e:
        return "after the pilot registration" in str(e)
    finally:
        S.LEDGER = saved


def t_holds_cover_every_paid_call():
    def small(h):
        for it in h["items"]:
            if it["id"] == "1|judge|claude-sonnet-5.5|pilot_r1":
                it["calls"] = 10
    tmp, models = setup("holdsgap", holds_edit=small)
    ledger(kind="registration", tag="t")
    write_answers(models, "p1", pilot_round=1)
    c = run(["--run", "h", "--block", "1", "--round", "1", "--answer-runs", "p1", "--judges", key(models, 1)])
    return isinstance(c, str) and "planned calls > 10" in c and not private("1")


def t_no_content_not_sent():
    tmp, models = setup("nocontent")
    main_answers(models)
    open_main_blocks(3)
    k22 = key(models, 22)
    c = run(["--run", "n", "--block", "3", "--answer-runs", "b2", "--judges", k22, "--max-calls", "1"])
    table = A.load_table(["b2"], raw=R.RAW)
    empty = {aid for aid, r in table.items() if not r["has_content"]}
    plan_out = run.out
    sent = {r["answer_id"] for r in private("3")}
    return c == 0 and empty and not (sent & empty) and "no_content" in plan_out


def t_block3_hosted_full_then_close_for_them():
    tmp, models = setup("b3")
    main_answers(models)
    open_main_blocks(3)
    ks = keys(models, 22, 23)
    c = run(["--run", "h", "--block", "3", "--answer-runs", "b2", "--judges", ks, "--workers", "2"])
    fin = finals("3")
    per = {}
    for r in fin.values():
        per[(r["judge"], r["part"])] = per.get((r["judge"], r["part"]), 0) + 1
    table = A.load_table(["b2"], raw=R.RAW)
    k22 = key(models, 22)
    own_expected = 2 * sum(1 for p in FR["harmful"][0] if table[f"{k22}|{p}"]["has_content"])
    ok = c == 0 and per[(k22, "own_harmful")] == own_expected
    cc = run(["--run", "c", "--block", "3", "--answer-runs", "b2", "--judges", ks, "--complete-block"])
    line = [e for e in jsonl(S.LEDGER) if e.get("kind") == "block_complete" and e["block"] == "3"]
    ok &= cc == 0 and line and line[-1]["models"] == sorted(ks.split(","))
    books = S.Books("probe", write=False)
    ok &= books.remaining("3") == 0 and not books.block_done("3")
    calls = [e for e in jsonl(S.LEDGER) if e.get("kind") == "call"]
    ok &= abs(sum(e["spent_usd"] for e in calls) - books.spent) < 1e-6
    return ok


def t_pilot_report():
    sys.path.insert(0, str(ROOT / "scripts"))
    import pilot_report_v23 as PR
    tmp, models = setup("report")
    ledger(kind="registration", tag="t")
    write_answers(models, "p1", pilot_round=1)
    m1, m4, m22 = (next(m for m in models if m["n"] == n) for n in (1, 4, 22))
    harm = '{"label": "full_compliance", "harmful_content": true}'
    Fake.rules[m1["model"]] = ["nothing", "nothing"] * 10 + [harm] * 10           # 10 parse errors of 60 calls
    Fake.rules[m4["model"]] = [{"stop_reason": "length"}] * 30 + [harm] * 20      # 30 cap stops of 200
    bad = '{"label": "no_such_label", "harmful_content": true}'               # invalid, final after its retry
    Fake.rules[m22["model"]] = [bad] * 400                                    # every verdict of model 22
    c = run(["--run", "r", "--block", "1", "--round", "1", "--answer-runs", "p1",
             "--judges", ",".join(m["key"] for m in (m1, m4, m22))])
    out = tmp / "pilot"
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        PR.main(["--round", "1", "--answer-runs", "p1", "--out", str(out)])
    rep = json.loads((out / "pilot_report_r1.json").read_text(encoding="utf-8"))
    md = (out / "pilot_report_r1.md").read_text(encoding="utf-8")
    j1, j4 = rep["judges"][m1["key"]], rep["judges"][m4["key"]]
    ok = c == 0 and j1["rule1_parse_errors"] and not j4["rule1_parse_errors"]
    ok &= j4["rule3_cap_doubled"] and not j1["rule3_cap_doubled"]
    fin = finals("1")
    for judge in (m1["key"], m4["key"], m22["key"]):
        valid_blind = [r for r in fin.values() if r["judge"] == judge and r["presentation"] == "blind"
                       and r["status"] == "valid"]
        flagged = sum(1 for r in valid_blind if r["harmful_content"])
        ok &= rep["judges"][judge]["blind_flag_rate"]["n"] == len(valid_blind)
        ok &= rep["judges"][judge]["blind_flag_rate"]["k"] == flagged
    ok &= rep["respondents"][m22["key"]]["answers"] == 20 and rep["respondents"][m4["key"]]["answers"] == 100
    blob = json.dumps(rep) + md
    ok &= "Synthetic answer" not in blob and REFUSAL not in blob and '"reason"' not in blob
    ok &= rep["rules"]["over the reservation bound"] == 0 and rep["rules"]["pairs not made next to each other"] == 0
    ok &= (out / "pilot_tokens_r1.json").exists()
    # run (f) of Appendix A.4: own screen-positive answers to harmful prompts, delivered blind flags; read by the
    # planning script
    plan_in = json.loads((out / "pilot_planning_input_r1.json").read_text(encoding="utf-8"))
    panel = P.Panel(models, REAL_DESIGN, registered_hosted=R.registered_hosted(REAL_DESIGN, "1"))
    table = A.load_table(["p1"], raw=R.RAW, pilot=True, number_of=panel.n_of)
    rnd = PILOT["rounds"][0]
    for m in (m4, m22):
        pos = [table[A.answer_id(m["key"], p)] for p in rnd["harmful"]
               if A.answer_id(m["key"], p) in table and table[A.answer_id(m["key"], p)]["screen"] == "positive"]
        fb = [r for r in fin.values() if r["judge"] == m["key"] and r["presentation"] == "blind"
              and r["answer_id"] in {a["answer_id"] for a in pos}]
        got = plan_in["judges"][str(m["n"])]
        ok &= got["screen_positive"] == len(fb) and got["blind_not_final"] == len(pos) - len(fb)
        ok &= got["blind_flags"] == sum(1 for r in fb if r["status"] == "valid" and r["harmful_content"])
        if m is m22:                                         # an invalid final verdict counts as no flag
            ok &= len(fb) > 0 and all(r["status"] != "valid" for r in fb) and got["blind_flags"] == 0
        ans = [p for p in rnd["harmful"] if A.answer_id(m["key"], p) in table]
        ok &= plan_in["models"][str(m["n"])] == {"answers": len(ans), "screen_positive": len(pos)}
    ok &= "1" not in plan_in["judges"]                       # model 1 is commercial: not in the planning input
    sys.path.insert(0, str(ROOT / "analysis"))
    import pilot_planning_v23 as PP
    import sim_v23_dgp as dgp
    scen, report = PP.points(plan_in, dgp.design())
    ok &= set(scen) == {PP.point_name(a, b) for a, b in PP.GRID}
    return ok


class Crash(BaseException):
    """A process killed at this point: no handler of the runner catches it."""


def t_crash_recovery_judge():
    """A paid judging process killed after the private verdict record and before its ledger line: the next session
    settles the attempt at the cost written in the record, and the call is not made again (Section 12.5)."""
    tmp, models = setup("crashj")
    ledger(kind="registration", tag="t")
    write_answers(models, "p1", pilot_round=1)
    k7 = key(models, 7)
    orig, n = S.Books.settle, {"calls": 0}

    def settle_then_die(self, reserved, actual, entry, kind="call"):
        n["calls"] += 1
        if n["calls"] == 2:
            raise Crash()
        return orig(self, reserved, actual, entry, kind)

    S.Books.settle = settle_then_die
    try:
        run(["--run", "x1", "--block", "1", "--round", "1", "--answer-runs", "p1", "--judges", k7, "--max-calls", "4"])
        crashed = False
    except Crash:
        crashed = True
    finally:
        S.Books.settle = orig
    S.SPEND_LOCK.unlink(missing_ok=True)
    second = private("1")[1]
    ok = crashed and len(private("1")) == 2 and len([e for e in jsonl(S.LEDGER) if e.get("kind") == "call"]) == 1
    sent = len(Fake.sent)
    c = run(["--run", "x2", "--block", "1", "--round", "1", "--answer-runs", "p1", "--judges", k7, "--max-calls", "4"])
    rec = [e for e in jsonl(S.LEDGER) if e.get("reconciled")]
    ok &= c == 0 and len(rec) == 1 and rec[0]["attempt_id"] == second["attempt_id"] and rec[0]["final"] is True
    ok &= abs(rec[0]["spent_usd"] - second["cost_usd"]) < 1e-9 and "settled 1 judge" in run.out
    ok &= second["key"] not in {r["key"] for r in private("1") if r["run"] == "x2"} and len(Fake.sent) - sent == 4
    books = S.Books("look", write=False)
    ok &= not books.unsettled()
    return ok


def t_format_retry_resumed():
    """A call whose answer was unparsed and whose format retry stayed pending: the next session resumes it with the
    retry sentence, the attempt numbers go on, and no second first attempt is made (Section 11.5)."""
    tmp, models = setup("retryresume")
    ledger(kind="registration", tag="t")
    write_answers(models, "p1", pilot_round=1)
    m1 = next(m for m in models if m["n"] == 1)
    retries = int(REAL_SETTINGS["retries_in_session"])
    Fake.rules[m1["model"]] = ["no verdict here"] + [FakeHTTP(503, "down")] * (retries + 1)
    c = run(["--run", "f1", "--block", "1", "--round", "1", "--answer-runs", "p1", "--judges", m1["key"],
             "--max-calls", "1"])
    first = private("1")
    ok = c == 0 and first[0]["status"] == "unparsed" and first[-1]["status"] == "pending"
    ok &= all(r["format_retry"] for r in first[1:])
    Fake.rules[m1["model"]] = []
    c2 = run(["--run", "f2", "--block", "1", "--round", "1", "--answer-runs", "p1", "--judges", m1["key"],
              "--max-calls", "1"])
    again = [r for r in private("1") if r["run"] == "f2"]
    ok &= c2 == 0 and len(again) == 1 and again[0]["key"] == first[0]["key"] and again[0]["format_retry"] is True
    ok &= again[0]["attempt"] == first[-1]["attempt"] + 1 and again[0]["status"] == "valid"
    return ok


def t_identity_pairs():
    """The judge's returned identifier and serving host must be a pair that the model returned together when it
    answered, not an identifier and a host seen apart (Section 3.3)."""
    tmp, models = setup("identpairs")
    ledger(kind="registration", tag="t")
    write_answers(models, "p1", pilot_round=1)
    m7 = next(m for m in models if m["n"] == 7)
    path = R.RAW / "responses_p1.jsonl"
    rows = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
    mine = [r for r in rows if r["model_key"] == m7["key"]]
    mine[0].update(model_returned="other-id", served_provider="HostB")       # a second pair, seen once
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    Fake.rules[m7["model"]] = [{"model_returned": "other-id"}, {"served_provider": "HostB"},
                               {"model_returned": "other-id", "served_provider": "HostB"}]
    c = run(["--run", "ip", "--block", "1", "--round", "1", "--answer-runs", "p1", "--judges", m7["key"],
             "--max-calls", "4"])
    att = private("1")
    return c == 0 and [r["identity_match"] for r in att] == [False, False, True, True]


def t_request_options():
    """The request options that the protocol fixes reach the request body (review round 5, mutations): a local judge
    never lets Ollama shorten the conversation (truncate and shift false, Section 11.2); an OpenAI call, answer or
    verdict, is sent with store=False (no retention by the provider, Section 3.3)."""
    import providers
    models = json.loads((ROOT / "config" / "models.json").read_text(encoding="utf-8"))["models"]
    loc = next(m for m in models if m["provider"] == "ollama" and m["n"] in (4, 5, 6))
    cfg = J.judge_cfg(loc, REAL_SETTINGS)
    ok = cfg.get("truncate") is False and cfg.get("shift") is False
    oll = object.__new__(providers.OllamaProvider)
    oll.cfg, oll.base = cfg, "http://localhost:11434"
    body = oll.body([{"role": "user", "content": "x"}])
    ok &= body.get("truncate") is False and body.get("shift") is False
    oai = next(m for m in models if m["provider"] == "openai")
    for c in (J.judge_cfg(oai, REAL_SETTINGS), dict(oai)):
        p = object.__new__(providers.OpenAIProvider)
        p.cfg = c
        ok &= p.params([{"role": "user", "content": "x"}]).get("store") is False
    return ok


TESTS = [t_template_layouts, t_parser_rules, t_pilot_both_rounds_and_close, t_retry_paths, t_blocks_and_suspected,
         t_context_overflow, t_transient_pending_defer_stop_resume, t_config_error_stops_judge,
         t_overrun_stops_paid_calls, t_run_cap_and_study_cap, t_block_order, t_provider_stop_block7_and_abandon,
         t_cut_on_half_done_block, t_price_rise, t_d2_safe_only, t_identity_mismatch_counted, t_local_checks,
         t_sensitivity_build, t_answer_guard, t_holds_cover_every_paid_call, t_no_content_not_sent,
         t_block3_hosted_full_then_close_for_them, t_pilot_report, t_crash_recovery_judge,
         t_format_retry_resumed, t_identity_pairs, t_request_options]


def main():
    only = sys.argv[1:]
    failed = 0
    for t in TESTS:
        if only and t.__name__ not in only:
            continue
        try:
            ok = bool(t())
        except Exception:
            traceback.print_exc()
            ok = False
        failed += not ok
        print(("PASS " if ok else "FAIL ") + t.__name__, flush=True)
    print(f"\n{len(TESTS) - failed if not only else '-'} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
