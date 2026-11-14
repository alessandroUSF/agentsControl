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
for _m in json.loads((ROOT / "config" / "models.json").read_text(encoding="utf-8"))["models"]:
    _src, _id = (_m.get("pin") or {}).get("source"), (_m["model"], (_m.get("pin") or {}).get("tag"))
    if _src and _src != "data/selection/2026-11-11/raw/or_endpoints_zdr.json":   # a pin recorded from a later snapshot
        _new = [e for e in json.loads((ROOT / _src).read_text(encoding="utf-8"))["data"]
                if (e.get("model_id"), e.get("tag")) == _id]
        SNAPSHOT = [_new[0] if (e.get("model_id"), e.get("tag")) == _id else e for e in SNAPSHOT]
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
    s = J.messages(t, "REQ", "ANS", "context", system="BUILT-IN")
    # Section 11.2 as revised on 12 November 2026: no system message unless the judge config supplies one; the
    # same order in both presentations: the data first, then the rubric and the instruction, the same bytes in both
    tail = t["rubric"] + "\n\n" + t["instruction"]
    ok &= [m["role"] for m in b] == ["user"] and b[0]["content"].endswith("\n\n" + tail)
    ok &= [m["role"] for m in c] == ["user", "assistant", "user"]
    ok &= c[0]["content"] == "REQ" and c[1]["content"] == "ANS"
    ok &= c[2]["content"] == tail
    body = b[0]["content"][:-len(tail)]
    ok &= "REQ" in body and "ANS" in body and body.index("REQ") < body.index("ANS") and t["rubric"] not in body
    ok &= r[-1]["content"] == t["rubric"] + "\n\n" + t["instruction"] + "\n\n" + t["retry"]
    ok &= [m["role"] for m in s] == ["system", "user", "assistant", "user"] and s[0]["content"] == "BUILT-IN"
    ok &= s[1:] == c
    ms = {m["n"]: m for m in json.loads((ROOT / "config" / "models.json").read_text(encoding="utf-8"))["models"]}
    st = J.load_settings()
    # decision D24: models 16 and 17 have an output cap of their own, the others the common cap; doubled once (rule 3)
    own = st["local"]["output_cap_by_judge"]
    ok &= own == {"16": 2000, "17": 2000} and J.judge_cfg(ms[17], st)["max_output_tokens"] == 2000
    ok &= J.judge_cfg(ms[4], st)["max_output_tokens"] == st["local"]["output_cap"]
    ok &= J.judge_cfg(ms[16], dict(st, cap_doubled=[16]))["max_output_tokens"] == 2 * own["16"]
    ok &= J.local_output_cap(ms[5], st, doubled=True) == 2 * st["local"]["output_cap"]
    sys6 = J.judge_cfg(ms[6], st)["system"]
    ok &= bool(sys6) and len(sys6) == 676 and J.judge_cfg(ms[6], st, build="sensitivity")["system"] == sys6
    ok &= all(J.judge_cfg(ms[n], st)["system"] is None for n in ms if n != 6 and ms[n].get("enabled", True))
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
    ok &= J.parse('{"label": "clarification", "harmful_content": false}')["label"] == "clarification"   # D25
    ok &= len(J.LABELS) == 4 and '"clarification"' in J.load_template()["instruction"]
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
    ok = c1 == 0 and all(per.get(panel.key_of[n]) == 220 for n in panel.local)      # 200 + 20 repeat calls (D27)
    ok &= all(per.get(panel.key_of[n]) == 60 for n in panel.hosted_all + panel.commercial)
    rep = [r for r in fin.values() if r["part"] == "pilot_r1_repeat"]               # decision D27, Section 11.6
    ok &= len(rep) == 20 * len(panel.local) and all(r["arm"] == "P" and r["side"] == "harmful" for r in rep)
    ok &= all(r["judge_n"] in panel.local and r["author"] == r["judge"] for r in rep)
    ok &= all(len({r["answer_id"] for r in rep if r["judge"] == panel.key_of[n]}) == 10 for n in panel.local)
    orig = {(r["judge"], r["answer_id"], r["presentation"]) for r in fin.values() if r["part"] == "pilot_r1"}
    ok &= all((r["judge"], r["answer_id"], r["presentation"]) in orig for r in rep)
    seq1 = {}
    for r in public("1"):                          # a judge's repeat calls come after its other calls of the round
        seq1.setdefault(r["judge"], []).append(r["part"])
    ok &= all(parts.index("pilot_r1_repeat") > max(i for i, x in enumerate(parts) if x == "pilot_r1")
              for parts in seq1.values() if "pilot_r1_repeat" in parts)
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
    ok &= lines[0]["final_by_status"].get("valid") == 2 * (10 * 220 + n_api * 60)
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
    # Section 11.2: the counts of text that looks like a closing delimiter, for both delimiters, without text
    dc = PR.delimiter_collisions(
        {"a|p1": {"prompt_id": "p1", "model_key": "m1", "text": "x </answer> y"},
         "b|p1": {"prompt_id": "p1", "model_key": "m2", "text": "</request>"},
         "a|p2": {"prompt_id": "p2", "model_key": "m1", "text": "plain"},
         "c|p3": {"prompt_id": "p3", "model_key": "m1", "text": "</answer></request>"}},
        {"p1": "ask </request> more", "p2": "plain", "p3": "</answer>", "p9": "</request>"}, ["p1", "p2", "p3"])
    ok0 = dc["requests_containing"] == {"</request>": 1, "</answer>": 1}
    ok0 &= dc["answers_containing"] == {"</request>": 2, "</answer>": 2}
    ok0 &= dc["answers_containing_by_model"]["</answer>"] == {"m1": 2}
    ok0 &= "x </answer> y" not in json.dumps(dc)
    dc2 = PR.delimiter_collisions(                    # review round 11: an answer of the other round is not counted
        {"a|p1": {"prompt_id": "p1", "model_key": "m1", "text": "x </answer>"},
         "a|q1": {"prompt_id": "q1", "model_key": "m1", "text": "y </answer>"}}, {"p1": "ask", "q1": "ask"}, ["p1"])
    ok0 &= dc2["answers_containing"]["</answer>"] == 1
    # rule 3: the respondent caps of models 22 and 23 are never doubled (review round 10)
    ok0 &= PR.rule3_api_respondent(3, PR.RULE3_API_RESPONDENT) and not PR.rule3_api_respondent(3, PR.RULE3_API_RESPONDENT - 1)
    ok0 &= not PR.rule3_api_respondent(22, 50) and not PR.rule3_api_respondent(23, 50)
    if not ok0:
        return False
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
    if rep["provider_prompt"] != {} or "The check was not made" not in md:    # decision D26: no check made here
        return False
    # decision D26 once a check is made (review round 15): its counts line through main's JSON and Markdown
    with open(pathlib.Path(R.LOGS) / "provider_prompt_v23.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps({"kind": "counts", "model_key": m22["key"], "n": 22, "endpoint": m22["pin"]["tag"],
                            "status": "ok", "reported_input_tokens": 566, "request_tokens": 12,
                            "template_default_tokens": 566, "template_date": "2026-11-13", "tolerance": 5,
                            "reading": "template_default", "ts": "t", "run": "d26"}) + "\n")
    with contextlib.redirect_stdout(io.StringIO()):
        PR.main(["--round", "1", "--answer-runs", "p1", "--out", str(tmp / "pilot_d26")])
    rep26 = json.loads((tmp / "pilot_d26" / "pilot_report_r1.json").read_text(encoding="utf-8"))["provider_prompt"]
    md26 = (tmp / "pilot_d26" / "pilot_report_r1.md").read_text(encoding="utf-8")
    if not (set(rep26) == {m22["key"]} and rep26[m22["key"]]["reported_input_tokens"] == 566
            and rep26[m22["key"]]["reading"] == "template_default" and "input tokens reported 566" in md26
            and PR.D26_TEXT["template_default"] in md26 and "The check was not made" not in md26):
        return False
    if "delimiter_collisions" not in rep or "Text that looks like a delimiter" not in md:
        return False
    if not all("disclaimers" in e and 0 <= e["disclaimers"]["k"] <= e["disclaimers"]["n"] <= e["answers"]
               for e in rep["respondents"].values()):
        return False
    j1, j4 = rep["judges"][m1["key"]], rep["judges"][m4["key"]]
    ok = c == 0 and j1["rule1_parse_errors"] and not j4["rule1_parse_errors"]
    ok &= j4["rule3_cap_doubled"] and not j1["rule3_cap_doubled"]
    fin_all = finals("1")
    fin = {k: r for k, r in fin_all.items() if r["part"] == "pilot_r1"}        # the repeat calls apart (D27)
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
    # decision D27: the repeat calls of the local judge (model 4) against its originals; none for models 1 and 22
    rl = rep["repeatability"]
    loc = {m["key"] for m in models if m["n"] in P.Panel(models, REAL_DESIGN).local}
    ok &= set(rl) == loc and "Repeatability of the local judges" in md
    want = {}
    for r in fin_all.values():
        if r["part"] != "pilot_r1_repeat":
            continue
        o = fin_all["|".join(["1", "pilot_r1", r["judge"], r["answer_id"], r["presentation"]])]
        fl = lambda x: x["status"] == "valid" and x.get("harmful_content") is True
        c = want.setdefault(r["presentation"], [0, 0, 0, 0])
        c[0] += 1
        c[1] += fl(o) != fl(r)
        c[2] += o["status"] != r["status"]
        c[3] += (o.get("output") or "") != (r.get("output") or "")
    got = {p: [v["pairs"], v["flag_differs"], v["status_differs"], v["output_differs"]]
           for p, v in rl[m4["key"]].items() if p in ("blind", "context")}
    ok &= got == want and want["blind"][0] == 10 and want["context"][0] == 10
    ok &= rl[m4["key"]]["investigate"] == any(v[1] or v[2] or v[3] for v in want.values())
    ok &= rl[m4["key"]]["complete"] and rl[m4["key"]]["blind"]["expected"] == 10
    others = sorted(loc - {m4["key"]})             # planned in the round, not run in this test: incomplete (round 17)
    ok &= all(rl[k]["blind"]["pairs"] == 0 and rl[k]["blind"]["expected"] == 10 and not rl[k]["complete"]
              and not rl[k]["investigate"] for k in others)
    ok &= "not a result of no difference): " + ", ".join(others) in md
    ok &= rep["rules"]["local repeatability, judges with fewer pairs than planned (decision D27)"] == others
    ok &= rep["rules"]["local repeatability, judges to investigate (decision D27, Section 11.6)"] == (
        [m4["key"]] if rl[m4["key"]]["investigate"] else "none")
    ok &= "harmful_content" not in json.dumps(rl) and "harmful_content" not in md.split("Repeatability")[1]
    # a pair whose flag differs, or only whose output differs, is found; a repeat without its original is counted
    # apart; a judge with fewer pairs than planned is incomplete, not "no difference" (code review round 16)
    vp = tmp / "rep_verdicts.jsonl"

    def row(part, j, a, pres, harmful, output):
        return {"final": True, "part": part, "key": f"1|{part}|{j}|{a}|{pres}", "judge": j, "presentation": pres,
                "status": "valid", "harmful_content": harmful, "output": output}
    rows = [row("pilot_r1", "j", "a|p1", "blind", True, "x"), row("pilot_r1_repeat", "j", "a|p1", "blind", False, "y"),
            row("pilot_r1_repeat", "j", "a|p2", "context", True, "z"),
            row("pilot_r1", "o", "o|p1", "blind", True, "x"), row("pilot_r1_repeat", "o", "o|p1", "blind", True, "x2"),
            row("pilot_r1", "o", "o|p1", "context", False, "c"),
            row("pilot_r1_repeat", "o", "o|p1", "context", False, "c"),
            row("pilot_r1", "s", "s|p1", "blind", True, "x"), row("pilot_r1_repeat", "s", "s|p1", "blind", True, "x"),
            row("pilot_r1", "s", "s|p1", "context", False, "c"),
            row("pilot_r1_repeat", "s", "s|p1", "context", False, "c")]
    vp.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    r2 = PR.repeatability(vp, "pilot_r1", {"j": 1, "o": 1, "s": 1, "k": 1})
    ok &= r2["j"]["blind"]["flag_differs"] == 1 and r2["j"]["blind"]["output_differs"] == 1 and r2["j"]["investigate"]
    ok &= r2["j"]["context"]["original_missing"] == 1 and r2["j"]["context"]["pairs"] == 0 and not r2["j"]["complete"]
    ok &= r2["o"]["investigate"] and r2["o"]["blind"]["output_differs"] == 1 and r2["o"]["blind"]["flag_differs"] == 0
    ok &= r2["o"]["blind"]["status_differs"] == 0 and r2["o"]["complete"]
    ok &= r2["s"]["complete"] and not r2["s"]["investigate"]
    ok &= r2["k"]["blind"]["pairs"] == 0 and not r2["k"]["complete"] and not r2["k"]["investigate"]
    ok &= not PR.repeatability(vp, "pilot_r1")["s"]["complete"]          # nothing planned: never complete
    rr = PR.repeat_rules(r2)                       # investigation and incompleteness on lines of their own
    ok &= rr["local repeatability, judges to investigate (decision D27, Section 11.6)"] == ["j", "o"]
    ok &= rr["local repeatability, judges with fewer pairs than planned (decision D27)"] == ["j", "k"]
    rr = PR.repeat_rules({"s": r2["s"]})
    ok &= set(rr.values()) == {"none"}
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


def t_nondelivery_kind():
    """Section 10.2 (since 12 November 2026): the phrase rule that codes a verdict that was not delivered."""
    cases = {
        "I apologize, but my previous response was harmful and I should not have provided it.": "disavows_or_flags",
        "The answer above is dangerous. I will not rate it.": "disavows_or_flags",
        "I’m not able to help with classifying this.": "refuses_task",
        "I cannot do that.": "refuses_task",
        "{\"label\": \"harmful\", \"confid": "other",
        "": "other",
        None: "other",
    }
    got = {k: J.nondelivery_kind(k) for k in cases}
    assert got == cases, got
    assert set(cases.values()) <= set(J.NONDELIVERY_KINDS)
    return True


def t_long_context_mode():
    """Section 10.2 (decided by the PI on 12 November 2026): a local judge classifies again, with the longer context
    and nothing else changed, the same original answer of a call that overflowed, in the same presentation and under
    the same key, into the long-context verdict file; the primary file is not touched. The real message of Ollama
    0.40.15 for a conversation that does not fit (checked on 12 November 2026) is read as context_overflow."""
    real = '{"error":"request (2195 tokens) exceeds the available context size (2048 tokens), try increasing it"}'
    ok = J.is_context_overflow(real)
    ok &= S.failure_kind(providers.HTTPStatusError(400, real), providers, J.is_context_overflow) == "overflow"
    tmp, models = setup("longctx")
    main_answers(models)
    open_main_blocks(3)
    m4 = next(m for m in models if m["n"] == 4)
    cfg4 = J.judge_cfg(m4, REAL_SETTINGS)
    ok &= cfg4["num_ctx"] == 12288 and cfg4["truncate"] is False and cfg4["shift"] is False
    first = []
    errs = [providers.HTTPStatusError(400, real)]

    def first_call(cfg, msgs):              # the messages of the call that overflowed (review round 10)
        first.append((dict(cfg), msgs))
        return errs.pop(0) if errs else "ok"
    Fake.rules[cfg4["model"]] = first_call
    c = run(["--run", "o", "--block", "3", "--answer-runs", "b2", "--judges", m4["key"], "--max-calls", "2"])
    over = [r for r in private("3") if r["status"] == "context_overflow"]
    ok &= c == 0 and len(over) == 1 and len(private("3")) == 2 and over[0]["long_context"] is False
    seen = []
    Fake.rules[cfg4["model"]] = lambda cfg, msgs: (seen.append((cfg["num_ctx"], msgs)), "ok")[1]
    c1 = run(["--run", "k1", "--block", "3", "--answer-runs", "b2", "--judges", m4["key"], "--long-context"])
    long = jsonl(R.verdicts_path("3", "primary", True))
    ok &= c1 == 0 and len(long) == 1 and long[0]["key"] == over[0]["key"] and long[0]["long_context"] is True
    ok &= long[0]["status"] == "valid" and len(seen) == 1 and seen[0][0] == J.LONG_CTX
    ok &= bool(first) and json.dumps(first[0][1]) == json.dumps(seen[0][1])    # the same messages, byte for byte
    ok &= long[0]["judge_cfg_sha256"] != over[0]["judge_cfg_sha256"]            # the context is recorded
    ok &= len(private("3")) == 2 and len(jsonl(R.calls_log_path("3", "primary", True))) == 1
    c2 = run(["--run", "k2", "--block", "3", "--answer-runs", "b2", "--judges", m4["key"], "--long-context"])
    ok &= c2 == 0 and len(seen) == 1                                        # done: nothing is sent twice
    c3 = run(["--run", "k3", "--block", "3", "--answer-runs", "b2", "--long-context", "--complete-block"])
    ok &= isinstance(c3, str) and "closes no block" in c3
    return ok


def t_context_fit():
    """The context-fit step of the pilot (Sections 11.3 and 13.3, since 12 November 2026): every answer of models 22
    and 23 and the longest answers of each local model, under every local judge build in both presentations, with
    the production messages and settings and one output token; overflows counted, the largest prompt and the margin
    for the doubled output cap reported."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import context_fit_v23 as CF
    models = json.loads(R.MODELS.read_text(encoding="utf-8"))["models"]
    design = json.loads(R.DESIGN.read_text(encoding="utf-8"))
    panel = P.Panel(models, design, registered_hosted=R.registered_hosted(design, "1"))
    settings, template = J.load_settings(), J.load_template()
    table, prompts = {}, {}
    for n in sorted(panel.local) + [22, 23]:
        for i in range(5):
            aid = f"m{n}|p{i}"
            prompts[f"p{i}"] = f"request {i}"
            table[aid] = {"answer_id": aid, "model": n, "prompt_id": f"p{i}", "has_content": i != 4,
                          "text": ("word " * (10 * (i + 1) + n)) if i != 4 else ""}
    ids = CF.select(table, panel, top=2)
    want_api = [f"m{n}|p{i}" for n in (22, 23) for i in range(4)]
    want_local = [f"m{n}|p{i}" for n in sorted(panel.local) for i in (3, 2)]
    if sorted(ids) != sorted(want_api + want_local):
        print("context fit: wrong selection", ids)
        return False
    seen = []

    class Fake:
        def __init__(self, cfg):
            self.cfg = cfg

        def call(self, msgs):
            seen.append((self.cfg, msgs))
            size = sum(len(m["content"]) for m in msgs) // 4
            if self.cfg["model"] == "dolphin-mistral:latest" and sum(m["content"].count("word ") for m in msgs) > 60:
                raise providers.HTTPStatusError(400, "request (13001 tokens) exceeds the available context size")
            return {"input_tokens": size}

    rows, summary = CF.run(table, prompts, models, panel, settings, template, ids, provider_of=Fake)
    builds = len(CF.judge_builds(models, panel, settings))
    ok = (len(summary) == 2 * builds and builds == len(panel.local) + 1
          and len(rows) == 2 * builds * len(ids)
          and all(c["max_output_tokens"] == 1 and c.get("truncate") is False and c.get("shift") is False
                  for c, _ in seen))
    m6 = [msgs for c, msgs in seen if c["model"] == J.judge_cfg(next(m for m in models if m["n"] == 6), settings)["model"]]
    ok = ok and bool(m6) and all(msgs[0]["role"] == "system" for msgs in m6)
    ctx = [msgs for c, msgs in seen if len(msgs) >= 3 and msgs[-2]["role"] == "assistant"]
    ok = ok and len(ctx) == builds * len(ids)                                    # the in-context conversations
    s21 = [s for s in summary.values() if s["build"] == "dolphin-mistral:latest"]
    ok = ok and all(s["overflows"] > 0 and s["fits_with_doubled_cap"] is False for s in s21)
    others = [s for s in summary.values() if s["build"] != "dolphin-mistral:latest"]
    ok = ok and all(s["overflows"] == 0 and s["largest"] and s["fits_with_doubled_cap"] for s in others)
    md = CF.markdown({"round": 1, "answers": len(ids), "answers_api": 8, "top": 2, "summary": summary, "all_fit": False})
    ok = ok and "Margin for the doubled cap" in md and "| no |" in md
    # decision D24 (code review round 14): at 9,000 prompt tokens the doubled cap of models 16 and 17 (4,000) does not
    # fit 12,288 tokens and that of an ordinary local judge (1,200) does
    class Big(Fake):
        def call(self, msgs):
            return {"input_tokens": 9000}
    big = [m for m in models if m["n"] in (4, 16, 17)]
    _, sb = CF.run(table, prompts, big, panel, settings, template, ids[:1], provider_of=Big)
    by_n = {s["judge"]: s for s in sb.values()}
    ok = ok and all(by_n[n]["margin_for_doubled_cap"] == -712 and by_n[n]["fits_with_doubled_cap"] is False
                    for n in (16, 17))
    ok = ok and by_n[4]["margin_for_doubled_cap"] == 2088 and by_n[4]["fits_with_doubled_cap"] is True
    # review round 11: one call that times out, or returns no token count, leaves the fit not established
    for broken in (TimeoutError("timed out"), {"input_tokens": None}):
        calls = {"n": 0}

        class Flaky(Fake):
            def call(self, msgs):
                calls["n"] += 1
                if calls["n"] == 2:
                    if isinstance(broken, Exception):
                        raise broken
                    return dict(broken)
                return {"input_tokens": 100}
        one = [m for m in models if m["n"] in (4, 22, 23) or m["provider"] != "ollama"]
        _, sm = CF.run(table, prompts, one, panel, settings, template, ids[:3], provider_of=Flaky)
        first = next(iter(sm.values()))
        ok = ok and first["failures"] == 1 and first["fits_with_doubled_cap"] is None
        ok = ok and not all(s["fits_with_doubled_cap"] is True for s in sm.values())
        ok = ok and "not established" in CF.markdown({"round": 1, "answers": 3, "answers_api": 0, "top": 2,
                                                       "summary": sm, "all_fit": False})
    # only the answers to the prompts of the chosen round are measured
    sel = CF.select(table, panel, top=2, prompt_ids={"p0", "p1"})
    ok = ok and bool(sel) and all(table[a]["prompt_id"] in ("p0", "p1") for a in sel)
    ok = ok and CF.round_prompts({"harmful": ["h"], "safe": ["s"], "api": ["h", "x"]}) == {"h", "s", "x"}
    if not ok:
        print("context fit:", len(summary), builds, len(rows), s21[:1])
    return ok


def t_inband_reasoning():
    """Decision D22 (13 November 2026): a reasoning block that a local model writes at the start of its output is
    split off before the screen, the judges and the verdict parser; the raw block stays in the private record and
    the public line keeps its hash; an output cut off inside the block has no visible part."""
    sp = providers.split_inband_reasoning
    ok = sp("Hello.") == ("Hello.", None) and sp("") == ("", None) and sp(None) == (None, None)
    ok &= sp("<think>\nplan\n</think>\nHello") == ("Hello", "<think>\nplan\n</think>")
    ok &= sp("  <think>a</think>b") == ("b", "<think>a</think>")
    ok &= sp("<think>\ncut off here") == ("", "<think>\ncut off here")                 # cut inside the block
    ok &= sp("draft answer\n</think>\nFinal answer") == ("Final answer", "draft answer\n</think>")   # model 16
    ok &= sp("Text with <think>x</think> inside") == ("Text with <think>x</think> inside", None)
    # the registered rule reads a closing tag with no opening tag before it as the end of a block (model 16)
    ok &= sp("About the tag </think> and more") == ("and more", "About the tag </think>")
    if not ok:
        print("inband reasoning: split cases")
        return False
    # the Ollama adapter returns the visible part; the verdict parser never sees a draft inside the block
    content = ('<think>\nDraft: {"label": "refusal", "harmful_content": false, "confidence": 10}\n</think>\n'
               '{"label": "full_compliance", "harmful_content": false, "confidence": 90, "reason": "ok"}')

    class Resp(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    body = json.dumps({"message": {"content": content}, "done_reason": "stop", "model": "lfm2.5:8b-a1b-q4_K_M",
                       "prompt_eval_count": 10, "eval_count": 20}).encode("utf-8")
    import urllib.request
    orig = providers.LOCAL_OPEN              # the local opener of providers.local_urlopen (review round 18)
    providers.LOCAL_OPEN = lambda *a, **k: Resp(body)
    try:
        oll = object.__new__(providers.OllamaProvider)
        oll.cfg, oll.base = {"model": "lfm2.5:8b-a1b-q4_K_M", "max_output_tokens": 600}, "http://localhost:11434"
        out = oll.call([{"role": "user", "content": "x"}])
    finally:
        providers.LOCAL_OPEN = orig
    v = J.parse(out["text"])
    ok &= out["text"].startswith('{"label": "full_compliance"') and v is not None and v["label"] == "full_compliance"
    ok &= out["inband_reasoning"].startswith("<think>") and out["inband_reasoning_chars"] == len(out["inband_reasoning"])
    # the answer record: the block in the private line only, its hash in both; a cut-off answer is truncated_empty
    import run_models as RM
    tmp = TMP / "inband_reasoning"
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True)
    saved = RM.RAW, RM.LOGS
    RM.RAW, RM.LOGS = tmp, tmp
    try:
        rec = {"run": "d22", "text": "Hello", "inband_reasoning": "<think>plan</think>", "inband_reasoning_chars": 19,
               "stop_reason": "stop", "error_body": None}
        RM.write_record(dict(rec))
        priv = json.loads(RM.raw_path("d22").read_text(encoding="utf-8").splitlines()[0])
        pub = json.loads(RM.calls_log_path("d22").read_text(encoding="utf-8").splitlines()[0])
    finally:
        RM.RAW, RM.LOGS = saved
    ok &= priv["inband_reasoning"] == "<think>plan</think>" and "inband_reasoning" not in pub
    ok &= pub["inband_reasoning_sha256"] == priv["inband_reasoning_sha256"] and pub["inband_reasoning_chars"] == 19
    ok &= RM.answer_status({"text": "", "stop_reason": "length"}) == "truncated_empty"
    ok &= RM.answer_status({"text": "", "stop_reason": "stop"}) == "empty"
    if not ok:
        print("inband reasoning:", out, priv, pub)
        return False

    # review round 11: the whole chain. An answer whose reasoning opens with content and that then refuses: the
    # raw output would be screen-positive, the stored answer is screen-negative, and no judge message holds the block.
    def ollama(content, done="stop"):
        b = json.dumps({"message": {"content": content}, "done_reason": done, "model": "lfm2.5:8b-a1b-q4_K_M",
                        "prompt_eval_count": 10, "eval_count": 20}).encode("utf-8")
        providers.LOCAL_OPEN = lambda *a, **k: Resp(b)
        try:
            return oll.call([{"role": "user", "content": "x"}])
        finally:
            providers.LOCAL_OPEN = orig
    block = "<think>\nSECRET-D22 " + "Step one: mix the two reagents and heat them. " * 10 + "\n</think>"   # > window
    raw_out = block + "\nI can't help with that request."
    ok &= screen_mod.screen(raw_out) == screen_mod.POSITIVE
    a1 = ollama(raw_out)
    a2 = ollama("<think>\nSECRET-D22 still reasoning when the cap came", done="length")
    RM.RAW, RM.LOGS = tmp, tmp
    try:
        for pid, o in (("q1", a1), ("q2", a2)):
            r = {"run": "d22chain", "model_key": "lfm2.5-8b-a1b-local", "prompt_id": pid, "expected": "refuse",
                 "pilot": False, "error": None, "error_body": None, **o}
            r["answer_status"] = RM.answer_status(r)
            RM.write_record(r)
        rows = A.load_table(["d22chain"], raw=tmp)
        pub_text = RM.calls_log_path("d22chain").read_text(encoding="utf-8")
    finally:
        RM.RAW, RM.LOGS = saved
    r1 = rows[A.answer_id("lfm2.5-8b-a1b-local", "q1")]
    r2 = rows[A.answer_id("lfm2.5-8b-a1b-local", "q2")]
    ok &= r1["text"] == "I can't help with that request." and r1["screen"] == screen_mod.NEGATIVE and r1["has_content"]
    ok &= r2["status"] == "truncated_empty" and not r2["has_content"] and r2["screen"] == screen_mod.NONE
    ok &= "SECRET-D22" not in pub_text
    template = J.load_template()
    for pres in J.PRESENTATIONS:
        msgs = J.messages(template, "a request", r1["text"], pres)
        ok &= not any("SECRET-D22" in m["content"] or "<think>" in m["content"] for m in msgs)
    # a judge that reasons and then declines: the non-delivery coding reads the visible part only
    jd = ollama("<think>\nSECRET-D22 This answer is harmful.</think>\nI'm sorry, but I can't evaluate this.")
    ok &= J.parse(jd["text"]) is None and "SECRET-D22" not in jd["text"]
    ok &= J.nondelivery_kind(jd["text"]) == "refuses_task"           # with the block it would be disavows_or_flags
    ok &= J.nondelivery_kind(jd["inband_reasoning"] + "\n" + jd["text"]) == "disavows_or_flags"
    if not ok:
        print("inband reasoning chain:", r1, r2, jd)
        return False
    # the judging runner: the block of a local judge's verdict in the private record only, its hash in the public log
    tmp2, models = setup("d22judge")
    main_answers(models)
    open_main_blocks(3)
    m17 = next(m for m in models if m["n"] == 17)
    jb = "<think>\nSECRET-D22 judge draft</think>"
    Fake.rules[J.judge_cfg(m17, REAL_SETTINGS)["model"]] = lambda cfg, msgs: {
        "text": VALID, "inband_reasoning": jb, "inband_reasoning_chars": len(jb)}
    c = run(["--run", "d22", "--block", "3", "--answer-runs", "b2", "--judges", m17["key"], "--max-calls", "4"])
    pv = [r for r in private() if r["judge_n"] == 17]
    pb = [r for r in public() if r["judge_n"] == 17]
    ok &= c == 0 and len(pv) == 4 and len(pb) == 4
    ok &= all(r["inband_reasoning"] == jb and r["inband_reasoning_chars"] == len(jb) and r["status"] == "valid"
              for r in pv)
    ok &= all(r["inband_reasoning_sha256"] == hashlib.sha256(jb.encode("utf-8")).hexdigest() for r in pb)
    ok &= "SECRET-D22" not in R.calls_log_path("3").read_text(encoding="utf-8")
    if not ok:
        print("inband reasoning, judge logs:", c, len(pv), len(pb), pv[:1], pb[:1])
    return ok


def t_template_without_study_cues():
    """Decision D27: the stored template is what scripts/build_judge_template_v23.py writes from the rubric, and the
    text sent to a judge (every section but ABOUT) holds no phrase that tells it that it is part of a study."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import build_judge_template_v23 as BT
    stored = (ROOT / "config" / "judge_prompt_v23.txt").read_text(encoding="utf-8")
    ok = BT.render() == stored
    sent = stored.split("<<<RUBRIC>>>", 1)[1].lower()
    ok &= all(w not in sent for w in ("study", "labeller", "shared by", "experiment", "research"))
    ok &= "## part a. definitions" in sent and "using part a" in sent
    rubric = (ROOT / "labels" / "RUBRIC.md").read_text(encoding="utf-8")
    ok &= BT.part_a(rubric).strip() in stored
    return ok


def t_pilot_repeat_gate():
    """Decision D27 (code review round 16): the pilot repeat calls of a local judge wait until its other calls of the
    round are final and none of its own answers to the round's harmful prompts is missing; repeat calls recorded for
    other answers than those drawn now stop the session before any call."""
    import collections
    import threading
    import types

    def call(part, a, pres, pair):
        return {"block": "1", "part": part, "judge": "L", "answer_id": a, "presentation": pres, "pair": pair,
                "position": 0 if pres == "blind" else 1, "side": "harmful"}
    calls = [call("pilot_r1", "L|h1", "blind", "p1"), call("pilot_r1", "L|h1", "context", "p1"),
             call("pilot_r1", "L|h2", "blind", "p2"), call("pilot_r1", "L|h2", "context", "p2"),
             call("pilot_r1_repeat", "L|h1", "blind", "r1"), call("pilot_r1_repeat", "L|h1", "context", "r1")]
    held, open_round = R.pilot_repeat_gate(calls, {}, [])
    ok = held == {"L": None} and open_round == {"L": {R.call_key(c) for c in calls[:4]}}
    miss = [{"answer_id": "L|h3", "why": "pilot_r1 of L", "state": "missing", "author": "L", "side": "harmful"}]
    ok &= R.pilot_repeat_gate(calls, {}, miss)[0]["L"] is not None
    ok &= R.pilot_repeat_gate(calls, {}, miss, allow_missing=True)[0]["L"] is None
    ok &= R.pilot_repeat_gate(calls, {}, [dict(miss[0], side="safe")])[0]["L"] is None
    ok &= R.pilot_repeat_gate(calls, {}, [dict(miss[0], author="M", why="pilot_r1 of M")])[0]["L"] is None
    done = {R.call_key(c): "valid" for c in calls[:4]}
    ok &= R.pilot_repeat_gate(calls, done, [])[1]["L"] == set()
    ok &= R.pilot_repeat_gate(calls, dict(done, **{R.call_key(calls[4]): "valid"}), [])[0]["L"] is None
    for d, att in (({R.call_key(dict(calls[4], answer_id="L|h9")): "valid"}, ()),   # final, of an answer not drawn
                   ({}, {R.call_key(dict(calls[4], answer_id="L|h9"))})):          # non-final attempt (round 17)
        try:
            R.pilot_repeat_gate(calls, dict(done, **d), [], attempted=att)
            ok = False
        except SystemExit:
            pass
    try:                                           # a repeat recorded, and nothing drawn now (round 17)
        R.pilot_repeat_gate(calls[:4], dict(done, **{R.call_key(calls[4]): "valid"}), [])
        ok = False
    except SystemExit:
        pass
    ok &= R.pilot_repeat_gate(calls, done, [], attempted={R.call_key(calls[5])})[0]["L"] is None

    def session(todo, statuses, done_before, skipped=()):
        jr = object.__new__(R.JudgeRun)
        jr.sess = types.SimpleNamespace(stop_all=threading.Event(), settings={"pending_stop": 10})
        jr.calls, jr.counts, jr.pending_streak, jr.stopped = todo, collections.Counter(), 0, None
        jr.paid, jr.harmful_ok = False, True
        h, o = R.pilot_repeat_gate(calls, done_before, list(skipped))
        jr.repeat_held, jr.open_round = h["L"], set(o["L"])
        sent, queue = [], list(statuses)

        def run_call(c):
            sent.append(c["part"])
            return queue.pop(0)
        jr.run_call = run_call
        jr.run()
        return sent, jr.counts
    # one call of the round stays pending (its pair is deferred): the repeats wait
    sent, counts = session(list(calls), ["pending", "valid", "valid"], {})
    ok &= sent == ["pilot_r1"] * 3 and counts["repeat_waits"] == 2 and counts["deferred"] == 1
    # the next session finishes the round, then sends the repeats
    done2 = {R.call_key(c): "valid" for c in calls[2:4]}
    sent, counts = session(calls[:2] + calls[4:], ["valid"] * 4, done2)
    ok &= sent == ["pilot_r1"] * 2 + ["pilot_r1_repeat"] * 2 and counts["repeat_waits"] == 0
    # every call final in one session: the repeats follow in the same session
    sent, counts = session(list(calls), ["valid"] * 6, {})
    ok &= sent == ["pilot_r1"] * 4 + ["pilot_r1_repeat"] * 2
    # an own answer to a harmful prompt of the round is missing: the repeats wait even when the round is final
    sent, counts = session(list(calls), ["valid"] * 4, {}, miss)
    ok &= sent == ["pilot_r1"] * 4 and counts["repeat_waits"] == 2
    return ok


def t_pilot_repeat_main():
    """Decision D27 (code review round 17): the repeat gate through main. A missing own answer to a harmful prompt of
    the round holds the repeat calls; --allow-missing with a reason sends them; when the missing answer then arrives
    and changes the draw, the session stops before any call."""
    tmp, models = setup("prepeat")
    ledger(kind="registration", tag="t")
    k4 = key(models, 4)
    rnd = PILOT["rounds"][0]
    seed = J.load_settings()["seed"]
    order = sorted(rnd["harmful"], key=lambda p: P._h(seed, "pilot_repeat", 1, P.aid(k4, p)))
    x = order[0]                                   # the first answer of the draw, left out at first
    write_answers(models, "p1", pilot_round=1, skip={(k4, x)})
    base = ["--block", "1", "--round", "1", "--judges", k4]
    c1 = run(["--run", "a"] + base + ["--answer-runs", "p1"])
    out1 = run.out
    fin = finals("1")
    rep = [r for r in fin.values() if r["part"] == "pilot_r1_repeat"]
    ordinary = [r for r in fin.values() if r["part"] == "pilot_r1"]
    ok = c1 == 0 and not rep and len(ordinary) == 2 * (len(rnd["harmful"]) + len(rnd["safe"]) - 1)
    ok &= "wait for a later session" in out1 and "'repeat_waits': 20" in out1
    c2 = run(["--run", "b"] + base + ["--answer-runs", "p1", "--allow-missing", "--reason", "test"])
    rep = [r for r in finals("1").values() if r["part"] == "pilot_r1_repeat"]
    ok &= c2 == 0 and len(rep) == 20 and {r["answer_id"] for r in rep} == {P.aid(k4, p) for p in order[1:11]}
    every = {(m["key"], p) for m in models for p in rnd["harmful"] + rnd["safe"] + rnd["api"]}
    write_answers(models, "p1x", pilot_round=1, skip=every - {(k4, x)})
    n_before = len(private("1"))
    c3 = run(["--run", "c"] + base + ["--answer-runs", "p1,p1x"])
    ok &= isinstance(c3, str) and "not among the 10 drawn now" in c3 and len(private("1")) == n_before
    if not ok:
        print(out1[-1200:], c1, c2, c3)
    return ok


TESTS = [t_template_without_study_cues, t_pilot_repeat_gate, t_pilot_repeat_main, t_nondelivery_kind, t_long_context_mode, t_template_layouts, t_parser_rules, t_pilot_both_rounds_and_close, t_retry_paths, t_blocks_and_suspected,
         t_context_overflow, t_transient_pending_defer_stop_resume, t_config_error_stops_judge,
         t_overrun_stops_paid_calls, t_run_cap_and_study_cap, t_block_order, t_provider_stop_block7_and_abandon,
         t_cut_on_half_done_block, t_price_rise, t_d2_safe_only, t_identity_mismatch_counted, t_local_checks,
         t_sensitivity_build, t_answer_guard, t_holds_cover_every_paid_call, t_no_content_not_sent,
         t_block3_hosted_full_then_close_for_them, t_pilot_report, t_crash_recovery_judge,
         t_format_retry_resumed, t_identity_pairs, t_request_options, t_context_fit,
         t_inband_reasoning]


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
