"""Offline test of analysis/analyze_v23.py: on synthetic files, the analysis computes the same numbers as the
simulations on the same data.

One replication of the study is drawn from the latent model of the simulations (sim_v23_registered.draw, the
twelve-model panel, the production control assignment). Answer files, a verdict file (with attempts that are not
final, later final attempts that must be ignored, final statuses other than valid, and identity mismatches) and a
locked label file are written to a temporary directory (AC_TEST_TMP chooses where; it is deleted afterwards), and
analyze_v23 reads them back. Checked number for number (exact equality):
  - the registered statistics, tests and sign-flip p-values against sim_v23_registered.statistics() on the drawn
    arrays, with the design of sim_v23_dgp.design();
  - the sensitivity analyses that drop answers (identity mismatches, truncated answers) and the ten local models
    with the local control assignment, against the same function;
  - the commercial panel against sim_v23_registered.statistics() and the safe side against sim_v23_safe.contrasts();
  - the label-conditioned quantities against sim_v23_labels.registered_interval() on sim_v23_labels.estimates();
  - a call that is not attempted: P1 to P3 are not declared (Section 10.4);
  - the plan at the lock (every planned call of blocks 3, 5, 6 and 7, label_blind, the challenge set, the reference
    subset and the repeat calls included) and its accounting;
  - blind accuracy against the labels (Section 9.4: exact binomial on the reference set, weighted with cluster
    intervals), the challenge set in both presentations, the comparisons between commercial judges, and
    repeatability (Section 11.6), against direct counts on the generated verdicts;
  - a synthetic ledger: cuts 1 and 3, abandonments, a provider stop (and one resumed), the closes of blocks 6 and 7
    as the judge runner writes them (counted again from the plan; a close with other counts is marked), a local
    call left, and decision D2 for one commercial model: the reasons of Section 10.3, the quantities that the cuts
    withdraw, the commercial tables without that model's answers, and P1 to P3 declared unless a hosted call on the harmful
    frame is missing outside a cut.
Nothing under results/ is read or written (the command is given a ledger of its own).
Run: python -B -I -X utf8 tests/test_sim_v23_analyze.py
"""
import csv
import hashlib
import json
import math
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "src"))
import analyze_v23 as AN  # noqa: E402
import inference_v23 as inf  # noqa: E402
import missing_labels_v23 as ML  # noqa: E402
import sim_v23_dgp as dgp  # noqa: E402
import sim_v23_labels as SL  # noqa: E402
import sim_v23_registered as SR  # noqa: E402
import sim_v23_safe as SS  # noqa: E402
import answers_v23  # noqa: E402
import frames_v23  # noqa: E402
import judge_v23 as J  # noqa: E402
import label_sample as LS  # noqa: E402
import plan_v23  # noqa: E402
import spend_v23  # noqa: E402

TMP = Path(tempfile.mkdtemp(prefix="ac_analyze_", dir=os.environ.get("AC_TEST_TMP")))
FLIPS, SIGN_SEED = 199, 7
LOCKED_COLUMNS = ("answer_id", "model", "model_key", "prompt_id", "source", "side", "screen", "weight", "cell_size",
                  "cell_labelled", "collapsed", "second", "h60", "api_ref", "first_status", "second_status", "label",
                  "state", "unknown_reason")
W = {}


def same(a, b):
    """Exact equality, None standing for NaN."""
    b = None if b is None or (isinstance(b, float) and math.isnan(b)) else b
    if isinstance(b, np.generic):
        b = b.item()
        b = None if isinstance(b, float) and math.isnan(b) else b
    return a == b


def check_stats(got, out, keys, where):
    """got: the analysis report of each statistic; out: sim_v23_registered.statistics() fields, replication 0."""
    for k in keys:
        for f in ("est", "se", "p", "lo", "hi"):
            assert same(got[k][f], out[f"{k}_{f}"][0]), (where, k, f, got[k][f], out[f"{k}_{f}"][0])
        if k in ("be", "beu"):
            assert same(got[k]["lb99"], out[f"{k}_lb99"][0]), (where, k)


def arrays_from(truth, panel, D, ids, answers, side, own, control):
    """Arrays [J, P] built from the generated verdicts, independently of analyze_v23.collect()."""
    nJ, P = len(D["judges"]), len(ids)
    S, F = np.zeros((nJ, P), np.int8), {a: np.zeros((nJ, P), np.int8) for a in AN.ARMS}
    matched = D.get("matched", P)
    for j, m in enumerate(D["judges"]):
        for p, pid in enumerate(ids):
            aid = plan_v23.aid(panel.key_of[m], pid)
            a = answers[aid]
            S[j, p] = a["screen"] == "positive"
            if not a["has_content"]:
                continue
            for arm, (role, pres) in AN.ARMS.items():
                if role == "control" and p >= matched:
                    continue
                judge = m if role == "own" else D["judges"][D["ctrl"][j, p]]
                for blk, part in (own if role == "own" else control):
                    k = f"{blk}|{part}|{panel.key_of[judge]}|{aid}|{pres}"
                    if k in truth:
                        F[arm][j, p] = truth[k][1]
                        break
                else:
                    raise AssertionError(f"no generated verdict for {k}")
    return S, F


def build_world():
    """Draws the data, writes the files, reads them with analyze_v23. Fills W."""
    t0 = time.time()
    rng = np.random.default_rng(20261125)
    design = json.loads(AN.DESIGN.read_text(encoding="utf-8"))
    panel = AN.load_panel(design, [22, 23])
    frames, (asg, _) = frames_v23.frames(), plan_v23.load_assignment()
    D = dgp.design()
    sc = dict(dgp.BASE, theta=-0.05, iota=-0.03, inv="10_15")
    q = dgp.panel_quality(D, sc)
    g, rho, _ = dgp.calibrate(np.random.default_rng(1), D, sc, q, 100)
    S, A1, A2, C1, C2, L = SR.draw(rng, 1, D, sc, q, g, rho)
    S, A1, A2, C1, C2 = (x[0].copy() for x in (S, A1, A2, C1, C2))
    Y = L["fail"][0].astype(np.float64)
    empty = (S == 0) & (rng.random(S.shape) < 0.05)              # answers without content: flags 0, no verdict
    for x in (A1, A2, C1, C2):
        x[empty] = 0
    truncated = (S == 1) & (rng.random(S.shape) < 0.04)
    key = panel.key_of

    # answers: primary panel on the harmful and safe frames, commercial panel on the common set and the safe frame
    recs = []

    def answer(m, pid, src, side, positive, no_content=False, status="ok"):
        text = "" if no_content else ("A synthetic answer." if positive else "I'm sorry, a synthetic refusal.")
        recs.append(dict(run="t1", model_key=key[m], prompt_id=pid, source=src, text=text, pilot=False,
                         expected="refuse" if side == "harmful" else "comply",
                         answer_status="empty" if no_content else status))

    hid, hsrc = frames["harmful"]
    for j, m in enumerate(D["judges"]):
        for p, pid in enumerate(hid):
            answer(m, pid, hsrc[pid], "harmful", S[j, p], empty[j, p], "truncated" if truncated[j, p] else "ok")
    sid, ssrc = frames["safe"]
    cid, csrc = frames["common"]
    for m in D["judges"] + panel.commercial:
        for pid in sid:
            answer(m, pid, ssrc[pid], "safe", rng.random() < 0.85, rng.random() < 0.03)
    for m in panel.commercial:
        for pid in cid:
            answer(m, pid, csrc[pid], "harmful", rng.random() < 0.5, rng.random() < 0.03)
    with open(TMP / "responses_t1.jsonl", "w", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r) + "\n")
    table = answers_v23.table(answers_v23.read_records(TMP / "responses_t1.jsonl"), number_of=panel.n_of)
    answers = {k: answers_v23.public(v) for k, v in table.items()}
    pos = {pid: i for i, pid in enumerate(hid)}
    idx = {m: i for i, m in enumerate(D["judges"])}
    for j, m in enumerate(D["judges"]):          # the screen of the files reproduces the drawn one
        assert all((answers[plan_v23.aid(key[m], pid)]["screen"] == "positive") == bool(S[j, pos[pid]])
                   for pid in hid)

    # the label sample of every model and side (as scripts/label_draw_v23.py draws it) and its locked file: complete
    # labels on the harmful side of the primary panel; elsewhere a few unknown and single labels
    ldesign = LS.load_design(without=[])
    lrecs = [dict(model=a["model"], prompt=a["prompt_id"], answer_id=aid, model_key=a["model_key"],
                  prompt_id=a["prompt_id"], source=a["source"], side=a["side"], screen=a["screen"])
             for aid, a in sorted(answers.items())]
    rows, _ = LS.select(lrecs, ldesign)
    (TMP / "labels").mkdir()
    lpath = TMP / "labels" / "labels_locked_v23.csv"
    with open(lpath, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=LOCKED_COLUMNS)
        w.writeheader()
        for r in rows:
            if r["side"] == "harmful" and r["model"] in idx:
                y, state = bool(Y[idx[r["model"]], pos[r["prompt_id"]]]), "labelled"
            else:
                y = bool(rng.random() < (0.4 if r["side"] == "harmful" else 0.08))
                u = rng.random()
                state = "unknown" if u < 0.05 else "labelled_once" if u < 0.1 else "labelled"
            w.writerow({**{c: r.get(c, "") for c in LOCKED_COLUMNS}, "collapsed": str(r["collapsed"]).lower(),
                        "second": str(r["second"]).lower(), "h60": str(r["h60"]).lower(),
                        "api_ref": str(r["api_ref"]).lower(), "label": "" if state == "unknown" else
                        "yes" if y else "no", "state": state,
                        "unknown_reason": "unresolved" if state == "unknown" else "", "first_status": "label",
                        "second_status": "label"})
    (TMP / "labels" / "labels_lock_v23.json").write_text(json.dumps(
        {"locked_file": {"name": lpath.name, "sha256": hashlib.sha256(lpath.read_bytes()).hexdigest(),
                         "answers": len(rows)}}), encoding="utf-8")
    locked = ML.load_locked(AN.check_lock(TMP / "labels")[0])

    # verdicts of every planned call of blocks 3, 5, 6 and 7; a repeat call mostly gives its original call's flag
    plan = plan_v23.Plan(panel, frames, asg, table, labels=locked)
    calls = plan.calls("3") + plan.calls("5") + plan.calls("6") + plan.calls("7")
    hosted = {key[22], key[23]}
    api = hosted | {key[m] for m in panel.commercial}
    truth, harm_of, lines = {}, {}, []
    for c in calls:
        k = f"{c['block']}|{c['part']}|{c['judge']}|{c['answer_id']}|{c['presentation']}"
        if c["block"] == "3":
            j, p = idx[panel.n_of[c["author"]]], pos[c["prompt_id"]]
            arm = ("A" if c["part"] == "own_harmful" else "C") + ("1" if c["presentation"] == "blind" else "2")
            flag = int({"A1": A1, "A2": A2, "C1": C1, "C2": C2}[arm][j, p])
        elif c["part"] == "repeat":
            first = truth[f"{'3|own_harmful' if c['block'] == '5' else '6|own'}|{c['judge']}|{c['answer_id']}|"
                          f"{c['presentation']}"][1]
            flag = first if rng.random() < 0.9 else 1 - first
        else:
            flag = int(rng.random() < 0.3)
        status = "valid" if flag or rng.random() < 0.93 else str(rng.choice(AN.NOT_DELIVERED))
        if c["side"] == "harmful":
            label, harm = str(rng.choice(J.LABELS)), bool(flag)
        else:
            label = str(rng.choice(AN.REFUSAL)) if flag else "full_compliance"
            harm = bool(rng.random() < 0.05)
        ident = None if c["judge"] not in api else not (c["judge"] in hosted and c["block"] == "3"
                                                         and rng.random() < 0.02)
        base = dict(protocol="2.3", run="t", key=k, block=c["block"], part=c["part"], judge=c["judge"],
                    judge_n=panel.n_of[c["judge"]], build="primary", answer_id=c["answer_id"], author=c["author"],
                    prompt_id=c["prompt_id"], side=c["side"], arm=c["arm"], presentation=c["presentation"],
                    pair=c["pair"], position=c["position"], format_retry=False)
        if rng.random() < 0.03:                                   # an attempt that is not final comes first
            lines.append(dict(base, attempt=1, final=False, status="failed", label=None, harmful_content=None,
                              identity_match=None))
        ok = status == "valid"
        lines.append(dict(base, attempt=2, final=True, status=status, label=label if ok else None,
                          harmful_content=harm if ok else None, identity_match=ident))
        truth[k] = (status, flag if ok else 0, ident)
        harm_of[k] = harm if ok else None
        if rng.random() < 0.02:                                   # a later final attempt: never canonical
            lines.append(dict(base, attempt=3, final=True, status="valid", label=label,
                              harmful_content=(not harm) if c["side"] == "harmful" else harm,
                              identity_match=ident))
    vpath = TMP / "verdicts_v23_main.jsonl"
    with open(vpath, "w", encoding="utf-8") as f:
        for r in lines:
            f.write(json.dumps(r) + "\n")
        f.write('{"protocol": "2.3", "key": "an interrupted wri')            # an interrupted write

    canon, info = AN.read_verdicts(vpath)
    res = AN.analyse(canon, answers, panel, frames, asg, label_rows=locked, label_design=ldesign, flips=FLIPS,
                     seed=SIGN_SEED, cats=AN.categories())
    json.dumps(AN.jsonable(res))                                  # the result can be written
    W.update(panel=panel, frames=frames, asg=asg, D=D, S=S, A1=A1, A2=A2, C1=C1, C2=C2, Y=Y, empty=empty,
             truncated=truncated, truth=truth, harm=harm_of, answers=answers, table=table, canon=canon, info=info,
             res=res, rows=rows, locked=locked, ldesign=ldesign, calls=calls, lines=lines,
             signs=AN.sign_matrix(FLIPS, D["P"], SIGN_SEED))
    print(f"  world: {len(calls)} planned calls, {len(lines)} attempts, {len(rows)} labelled answers "
          f"({sum(r['h60'] for r in rows)} in the challenge set, {sum(r['api_ref'] for r in rows)} in the reference "
          f"subset), {time.time() - t0:.1f} s")


def test_design_from_assignment():
    """analyze_v23.design_of() on the recorded assignment equals the designs of the simulations."""
    p, fr, asg = W["panel"], W["frames"], W["asg"]
    for drop, block in (((), "refusal_removed"), ((22, 23), "refusal_removed_local"), ((22,), None)):
        for frame in ("harmful", "safe"):
            ref = dgp.design(drop=drop, frame=frame)
            rem = [m for m in p.groups["refusal_removed"] if m not in drop]
            got = AN.design_of(fr, asg, frame, [("instruct_open", p.instruct, "i"),
                                                (block or ref["blocks"]["refusal_removed"].split("|")[0], rem, "r")])
            assert got["judges"] == ref["judges"] and np.array_equal(got["ctrl"], ref["ctrl"])
            assert np.array_equal(got["auth"], ref["auth"]) and np.array_equal(got["strata"], ref["strata"])
    ref = SS.commercial_design()
    got = AN.design_of(fr, asg, "safe", [("commercial", p.commercial, "c")], assign_frame="safe_commercial_controls",
                       matched=30)
    assert np.array_equal(got["ctrl"], ref["ctrl"]) and got["matched"] == ref["matched"]


def test_canonical_verdicts():
    """The first final attempt of a key is its verdict; later final attempts and unreadable lines are counted."""
    canon, info, truth = W["canon"], W["info"], W["truth"]
    assert len(canon) == len(W["calls"]) == len(truth)
    assert info["later_final_attempts"] > 0 and info["unreadable_lines"] == 1
    assert info["attempts"] == len(W["lines"])
    for k, (status, flag, ident) in truth.items():
        r = canon[k]
        assert r["status"] == status and r["identity_match"] == ident
        assert AN.flag_of(r, r["side"]) == flag


def test_registered_equals_simulation():
    """The registered statistics, tests and sign-flip p-values equal sim_v23_registered.statistics() exactly."""
    D, reg = W["D"], W["res"]["registered"]
    out, _ = SR.statistics(*(W[k][None] for k in ("S", "A1", "A2", "C1", "C2")), D, W["signs"])
    check_stats(reg["statistics"], out, SR.STATS, "registered")
    assert reg["declared"] and reg["calls"]["complete"]
    for p in ("p1", "p2", "p3"):
        assert reg["tests"][p]["rejected"] == bool(out[p][0])
    assert reg["signflip"]["th"] == float(out["th_sf"][0]) and reg["signflip"]["io"] == float(out["io_sf"][0])
    S = W["S"].astype(np.int64)
    thc = inf.cluster_ratio((S * (W["C2"] - W["C1"])).sum(0), S.sum(0), D["strata"])
    assert same(reg["statistics"]["thc"]["est"], float(thc["est"]))
    assert same(reg["statistics"]["thc"]["lo"], float(inf.interval(thc)[0]))
    assert reg["screen_positive"] == int(W["S"].sum())
    print(f"  theta_S {reg['statistics']['th']['est']:+.4f}, iota_S {reg['statistics']['io']['est']:+.4f}, "
          f"beta_S {reg['statistics']['be']['est']:+.4f}; claims {reg['claims']['P1']}, {reg['claims']['P2']}")


def test_sensitivity_analyses_equal_simulation():
    """Answers dropped for an identity mismatch or truncation, by group and the ten local models: the same function
    on the same arrays."""
    D, sec, truth, panel = W["D"], W["res"]["secondary"], W["truth"], W["panel"]
    arrays = [W[k][None] for k in ("S", "A1", "A2", "C1", "C2")]
    hid = W["frames"]["harmful"][0]
    mismatch = np.zeros(W["S"].shape, bool)
    for j, m in enumerate(D["judges"]):
        for p, pid in enumerate(hid):
            aid = plan_v23.aid(panel.key_of[m], pid)
            k = D["judges"][D["ctrl"][j, p]]
            for kk in (f"3|own_harmful|{panel.key_of[m]}|{aid}|", f"3|control_harmful|{panel.key_of[k]}|{aid}|"):
                for pres in ("blind", "context"):
                    if truth.get(kk + pres, (None, None, None))[2] is False:
                        mismatch[j, p] = True
    assert mismatch.any() and sec["identity_mismatch_dropped"]["answers_dropped"] == int(mismatch.sum())
    for name, drop in (("identity_mismatch_dropped", mismatch), ("truncated_dropped", W["truncated"])):
        out, _ = SR.statistics(*arrays, D, W["signs"], (~drop)[None].astype(np.int8))
        check_stats(sec[name]["statistics"], out, SR.STATS, name)
    for g in ("i", "r"):
        inc = np.repeat((D["group"] == g)[:, None], D["P"], 1)[None].astype(np.int8)
        out, _ = SR.statistics(*arrays, D, W["signs"][:1], inc)
        check_stats(sec[f"group_{g}"], out, ("th", "io", "be", "iw", "ic", "thu"), f"group {g}")
    Dl = dgp.design(drop=(22, 23))
    S, F = arrays_from(truth, panel, Dl, hid, W["answers"], "harmful", AN.OWN_H, AN.CTRL_LOCAL)
    out, _ = SR.statistics(S[None], *(F[a][None] for a in ("A1", "A2", "C1", "C2")), Dl, W["signs"])
    check_stats(sec["ten_local_models"]["statistics"], out, SR.STATS, "ten local models")
    assert sec["ten_local_models"]["calls"]["complete"]
    loco = sec["leave_one_category_out"]
    assert loco["range"]["th"][0] <= W["res"]["registered"]["statistics"]["th"]["est"] <= loco["range"]["th"][1] \
        or len(loco["by_category"]) == 1


def test_more_secondary_analyses():
    """By source, among screen-negative answers, under an initial screen and with the sensitivity build of model 6,
    against the simulation functions on the same arrays."""
    D, panel, truth, sec = W["D"], W["panel"], W["truth"], W["res"]["secondary"]
    arrays = {k: W[k] for k in ("S", "A1", "A2", "C1", "C2")}
    names = ("S", "A1", "A2", "C1", "C2")
    # Section 11.4: the change of the authors and of the controls by which presentation came first in the pair
    po, st = sec["presentation_order"], W["res"]["registered"]["statistics"]
    for k in ("th", "thc"):
        b, c = po[k]["blind_first"], po[k]["context_first"]
        assert b["answers"] + c["answers"] == int((W["S"] > 0).sum()) and min(b["answers"], c["answers"]) > 0, k
        assert abs(b["est"] * b["den"] + c["est"] * c["den"] - st[k]["est"] * st[k]["den"]) < 1e-9, k
    for k in ("io", "be"):                    # iota_S and beta_S by the four combinations of the two orders
        cells = po[k]
        assert len(cells) == 4 and sum(c["answers"] for c in cells.values()) == int((W["S"] > 0).sum()), k
        assert abs(sum(c["est"] * c["den"] for c in cells.values() if c["den"]) - st[k]["est"] * st[k]["den"]) \
            < 1e-9, k
    first = [J.first_presentation(panel.key_of[m], plan_v23.aid(panel.key_of[m], pid), plan_v23.SEED) == "blind"
             for m in D["judges"] for pid in W["frames"]["harmful"][0]]
    assert abs(sum(first) / len(first) - 0.5) < 0.05
    for h in (0, 1):
        cols = np.flatnonzero(D["strata"] == h)
        Dh = dict(D, P=len(cols), strata=D["strata"][cols], auth=D["auth"][:, cols], ctrl=D["ctrl"][:, cols])
        out, _ = SR.statistics(*(arrays[k][None][:, :, cols] for k in names), Dh, W["signs"][:1, cols])
        check_stats(sec[f"source_{h}"], out, ("th", "io", "be", "iw", "ic"), f"source {h}")
        assert sec[f"source_{h}"]["th"]["df"] == len(cols) - 1
    res = SS.contrasts(*(arrays[k][None] for k in names[1:]), (W["S"] == 0).astype(np.int8)[None], D, slice(None),
                       SS.CONTRASTS)
    for k in SS.CONTRASTS:
        assert same(sec["screen_negative"][k]["est"], res[k]["est"][0])
        assert same(sec["screen_negative"][k]["lo"], inf.interval(res[k])[0][0])
    hid = W["frames"]["harmful"][0]
    S0 = W["S"].copy()
    turn = (np.random.default_rng(3).random(S0.shape) < 0.1) & ~W["empty"]
    S0[turn] = 1 - S0[turn]
    initial = {plan_v23.aid(panel.key_of[m], pid): "positive" if S0[j, p] else "negative"
               for j, m in enumerate(D["judges"]) for p, pid in enumerate(hid)}
    k6 = panel.key_of[6]
    canon_m6 = {k: dict(r, harmful_content=not r["harmful_content"]) if r["status"] == "valid" else r
                for k, r in W["canon"].items() if r["judge"] == k6 and r["part"] in ("own_harmful", "control_harmful")}
    res = AN.analyse(W["canon"], W["answers"], panel, W["frames"], W["asg"], canon_m6=canon_m6, flips=FLIPS,
                     seed=SIGN_SEED, initial_screen=initial)
    out, _ = SR.statistics(S0[None], *(arrays[k][None] for k in names[1:]), D, W["signs"])
    check_stats(res["secondary"]["initial_screen"]["statistics"], out, SR.STATS, "initial screen")
    F = {a: arrays[a].copy() for a in names[1:]}
    j6 = D["judges"].index(6)
    for j, m in enumerate(D["judges"]):
        for p, pid in enumerate(hid):
            aid = plan_v23.aid(panel.key_of[m], pid)
            for arm, (role, pres) in AN.ARMS.items():
                if (j if role == "own" else D["ctrl"][j, p]) != j6:
                    continue
                part = "own_harmful" if role == "own" else "control_harmful"
                t = truth.get(f"3|{part}|{k6}|{aid}|{pres}")
                if t and t[0] == "valid":
                    F[arm][j, p] = 1 - F[arm][j, p]
    out, _ = SR.statistics(W["S"][None], *(F[a][None] for a in names[1:]), D, W["signs"])
    check_stats(res["secondary"]["model_6_q4_k_m"]["statistics"], out, SR.STATS, "model 6, Q4_K_M build")
    bm = sec["by_model"]["6"]
    j6_s = W["S"][j6].astype(np.int64)
    r = inf.cluster_ratio(j6_s * (W["A2"][j6] - W["A1"][j6]), j6_s, D["strata"])
    assert same(bm["th"]["est"], float(r["est"])) and bm["screen_positive_as_author"] == int(j6_s.sum())


def test_delivery_reports():
    """Section 10.2 from the statuses: complete pairs, fail-closed, bounds and the decomposition of theta_S."""
    D, dl, truth, panel = W["D"], W["res"]["delivery"], W["truth"], W["panel"]
    hid = W["frames"]["harmful"][0]
    st = {a: np.full(W["S"].shape, "", dtype=object) for a in AN.ARMS}
    for j, m in enumerate(D["judges"]):
        for p, pid in enumerate(hid):
            aid = plan_v23.aid(panel.key_of[m], pid)
            k = panel.key_of[D["judges"][D["ctrl"][j, p]]]
            for arm, (role, pres) in AN.ARMS.items():
                judge = panel.key_of[m] if role == "own" else k
                part = "own_harmful" if role == "own" else "control_harmful"
                st[arm][j, p] = truth.get(f"3|{part}|{judge}|{aid}|{pres}", ("no_content",))[0]
    S = W["S"].astype(bool)
    valid = {a: st[a] == "valid" for a in AN.ARMS}
    nd = {a: np.isin(st[a], AN.NOT_DELIVERED) for a in AN.ARMS}
    both = S & valid["A1"] & valid["A2"]
    d = (W["A2"] - W["A1"]).astype(np.int64)
    r = inf.cluster_ratio((both * d).sum(0), both.sum(0), D["strata"])
    assert same(dl["complete_pairs"]["th"]["est"], float(r["est"])) and same(dl["complete_pairs"]["th"]["hi"],
                                                                            float(inf.interval(r)[1]))
    fc = np.where(nd["A2"], 1, W["A2"]).astype(np.int64) - np.where(nd["A1"], 1, W["A1"])
    r = inf.cluster_ratio((S * fc).sum(0), S.sum(0), D["strata"])
    assert same(dl["fail_closed"]["th"]["est"], float(r["est"]))
    lo = np.where(nd["A2"], 0, W["A2"]).astype(np.int64) - np.where(nd["A1"], 1, W["A1"])
    assert same(dl["bounds"]["th"]["low"]["est"], float(inf.cluster_ratio((S * lo).sum(0), S.sum(0),
                                                                          D["strata"])["est"]))
    parts = dl["decomposition"]["th"]
    total = (parts["pairs_with_two_valid_verdicts"]["est"] + parts["context_flag_blind_not_delivered"]["est"]
             - parts["blind_flag_context_not_delivered"]["est"])
    assert abs(total - W["res"]["registered"]["statistics"]["th"]["est"]) < 1e-12
    assert nd["A1"].any() and dl["bounds"]["io"]["low"]["est"] <= W["res"]["registered"]["statistics"]["io"]["est"]


def commercial_arrays():
    """The commercial design of the common set, made by sim_v23_dgp.assign (not read from the recorded assignment),
    and its arrays from the generated verdicts."""
    panel, fr = W["panel"], W["frames"]
    yoke = dgp.yoking.load_panel()
    cid, cnames = fr["common"]
    members = panel.commercial
    ix = {m: i for i, m in enumerate(members)}
    asg = dgp.assign(cid, cnames, members, yoke, "commercial")
    ctrl = np.zeros((len(members), len(cid)), np.int64)
    for p, pid in enumerate(cid):
        for a, k in asg[pid].items():
            ctrl[ix[a], p] = ix[k]
    auth = np.zeros_like(ctrl)
    for p in range(len(cid)):
        auth[ctrl[:, p], p] = np.arange(len(members))
    src = sorted(set(cnames.values()))
    Dc = dict(judges=members, P=len(cid), strata=np.array([src.index(cnames[p]) for p in cid]), ctrl=ctrl, auth=auth)
    S, F = arrays_from(W["truth"], panel, Dc, cid, W["answers"], "harmful", AN.OWN_C, AN.CTRL_C)
    return Dc, S, F


def test_commercial_and_safe_equal_simulation():
    """The commercial panel against sim_v23_registered.statistics(); the safe side against sim_v23_safe.contrasts()."""
    panel, fr, truth, answers = W["panel"], W["frames"], W["truth"], W["answers"]
    Dc, S, F = commercial_arrays()
    cid, members, ctrl = fr["common"][0], panel.commercial, Dc["ctrl"]
    out, _ = SR.statistics(S[None], *(F[a][None] for a in ("A1", "A2", "C1", "C2")), Dc,
                           np.ones((1, len(cid)), np.int8))
    check_stats(W["res"]["commercial"]["tables"]["all"]["statistics"], out, ("th", "io", "be", "iw", "ic", "thu"),
                "commercial")
    j11 = members.index(11)                     # without model 11: its answers and the answers it controls
    inc = np.ones(S.shape, bool)
    inc[j11, :] = False
    inc &= ctrl != j11
    out, _ = SR.statistics(S[None], *(F[a][None] for a in ("A1", "A2", "C1", "C2")), Dc,
                           np.ones((1, len(cid)), np.int8), inc[None].astype(np.int8))
    check_stats(W["res"]["commercial"]["tables"]["without_11"]["statistics"], out, ("th", "io", "be", "iw"),
                "commercial without 11")
    Ds = dgp.design(frame="safe")
    sid = fr["safe"][0]
    S, F = arrays_from(truth, panel, Ds, sid, answers, "safe", AN.OWN_S, AN.CTRL_S)
    got = W["res"]["safe"]["primary"]["quantities"]
    for key, w, cols, k in SS.specs("primary", Ds):
        Wt = SS.weights(S.astype(bool)[None], w)
        r = SS.contrasts(*(F[a][None] for a in ("A1", "A2", "C1", "C2")), Wt, Ds, cols, [k])[k]
        lo, hi = inf.interval(r)
        if key in AN.SAFE_NO_INTERVAL:              # Appendix A.4: the estimate only
            assert same(got[key]["est"], r["est"][0]) and got[key]["lo"] is None and got[key]["hi"] is None, key
            assert got[key]["p"] is None and got[key]["no_interval"] == AN.SAFE_NO_INTERVAL_TEXT, key
            continue
        assert same(got[key]["est"], r["est"][0]) and same(got[key]["lo"], lo[0]) and same(got[key]["hi"], hi[0]), key
        assert "no_interval" not in got[key], key
    Dcs = SS.commercial_design()
    S, F = arrays_from(truth, panel, Dcs, sid, answers, "safe", AN.OWN_C, AN.CTRL_CS)
    got = W["res"]["safe"]["commercial"]["quantities"]
    for key, w, cols, k in SS.specs("commercial", Dcs):
        Wt = SS.weights(S.astype(bool)[None], w)
        r = SS.contrasts(*(F[a][None] for a in ("A1", "A2", "C1", "C2")), Wt, Dcs, cols, [k])[k]
        if key in AN.SAFE_NO_INTERVAL:
            assert same(got[key]["est"], r["est"][0]) and got[key]["hi"] is None, key
            assert got[key].get("lb99", None) is None and got[key]["no_interval"] == AN.SAFE_NO_INTERVAL_TEXT, key
            continue
        assert same(got[key]["est"], r["est"][0]) and same(got[key]["hi"], inf.interval(r)[1][0]), key
    # Sections 8.6 and 17.3: the commercial safe tables also without model 11 and without models 1 and 2
    wo = W["res"]["safe"]["commercial"]["quantities_without"]
    assert set(wo) == set(AN.CONFLICT)
    for name, drop in AN.CONFLICT.items():
        inc = np.ones(S.shape, bool)
        for m in drop:
            j = Dcs["judges"].index(m)
            inc[j, :] = False
            inc &= Dcs["ctrl"] != j
        assert 0 < inc.sum() < inc.size
        for key, w, cols, k in SS.specs("commercial", Dcs):
            Wt = (SS.weights(S.astype(bool)[None], w) * inc[None]).astype(np.int8)
            r = SS.contrasts(*(F[a][None] for a in ("A1", "A2", "C1", "C2")), Wt, Dcs, cols, [k])[k]
            g = wo[name][key]
            assert same(g["est"], r["est"][0]), (name, key)
            if key in AN.SAFE_NO_INTERVAL:
                assert g["hi"] is None and g["no_interval"] == AN.SAFE_NO_INTERVAL_TEXT, (name, key)
            else:
                assert same(g["hi"], inf.interval(r)[1][0]), (name, key)
        assert any(not same(wo[name][k]["est"], got[k]["est"]) for k in got if got[k]["est"] is not None), name
    assert W["res"]["safe"]["harmful_content_true_on_safe_answers"]


def test_labels_equal_simulation():
    """The label-conditioned quantities (complete labels) equal sim_v23_labels.registered_interval() on
    sim_v23_labels.estimates() of the same arrays, the computation of R-S3."""
    D, rows, lab = W["D"], W["rows"], W["res"]["labels"]["analysis"]
    hid = W["frames"]["harmful"][0]
    pos, idx = {pid: i for i, pid in enumerate(hid)}, {m: i for i, m in enumerate(D["judges"])}
    Wt = np.zeros(W["S"].shape)
    for r in rows:
        if r["side"] == "harmful" and r["model"] in idx:          # the primary panel on the harmful frame
            Wt[idx[r["model"]], pos[r["prompt_id"]]] = r["weight"]
    S = W["S"].astype(np.float64)
    F = [W[k].astype(np.float64) for k in ("A1", "A2", "C1", "C2")]
    Z = np.zeros(W["S"].shape)                       # answers without content: screen-negative, not harmful (7.2)
    for m, j in idx.items():
        for pid, i in pos.items():
            a = W["answers"].get(plan_v23.aid(W["panel"].key_of[m], pid))
            Z[j, i] = float(a is not None and a["screen"] == "none")
    assert Z.sum() > 0
    cells, _ = SL.estimates(Wt, S, W["Y"], *F, D, Z=Z)
    sup = SL.support(Wt, S, W["Y"], D)
    shares = all(sup["all"][c] >= SL.MIN_SUPPORT for c in ("pos", "neg"))
    assert lab["complete_labels"]
    seen = 0
    for stat in ML.REPORTED:
        e = lab["steps_1_2"][stat]
        if sup[stat.split("|")[1]][SL.support_class(stat)] < SL.MIN_SUPPORT:
            assert not e["reported"]
            continue
        reg = SL.registered_interval(cells, stat, D["strata"], shares)
        got = e["all_not_harmful"]
        assert same(got["est"], reg["est"]), stat
        withdrawn = stat in ML.NO_INTERVAL and reg["no_interval"] is None         # Appendix A.4: estimate only
        assert (got["lo"] is None) == (reg["no_interval"] is not None or withdrawn), stat
        if withdrawn:
            assert got["no_interval"] == ML.NO_INTERVAL[stat], stat
        if got["lo"] is not None:
            assert got["lo"] == reg["lo"] and got["hi"] == reg["hi"], stat
        assert e["all_harmful"] == got
        seen += 1
    assert seen >= 10
    assert set(W["res"]["registered"]["claims"]["detection_addition"]) == set(ML.GATED)


def test_call_not_attempted():
    """A call of a registered hosted judge without a final attempt: P1 to P3 are not declared (Section 10.4); the
    estimates are made over the answers whose calls were all made, with bounds over the call."""
    panel, canon = W["panel"], dict(W["canon"])
    victim = next(k for k, r in canon.items() if r["judge"] == panel.key_of[22] and r["part"] == "own_harmful")
    del canon[victim]
    res = AN.analyse(canon, W["answers"], panel, W["frames"], W["asg"], flips=FLIPS, seed=SIGN_SEED)
    reg = res["registered"]
    assert not reg["declared"] and reg["calls"]["hosted_concerned"] == [22]
    assert all(reg["claims"][p]["state"] == "not declared" for p in ("P1", "P2", "P3"))
    b = reg["bounds_not_attempted"]
    assert b["answers_with_a_call_not_attempted"] == 1 and b["scope"] == AN.BOUNDS_SCOPE
    assert b["answers_not_generated"] == sum(1 for m in W["D"]["judges"] for pid in W["frames"]["harmful"][0]
                                             if plan_v23.aid(panel.key_of[m], pid) not in W["answers"])
    assert b["th"]["low"]["est"] <= b["th"]["high"]["est"]
    D = W["D"]
    inc = np.ones(W["S"].shape, np.int8)
    aid = W["canon"][victim]["answer_id"]
    m, pid = panel.n_of[aid.split("|")[0]], aid.split("|", 1)[1]
    inc[D["judges"].index(m), W["frames"]["harmful"][0].index(pid)] = 0
    out, _ = SR.statistics(*(W[k][None] for k in ("S", "A1", "A2", "C1", "C2")), D, W["signs"], inc[None])
    check_stats(reg["statistics"], out, ("th", "io", "be"), "completed calls")


def test_command_line():
    """The command (main) on the synthetic files: the result file holds the numbers of analyse(); the registered
    panel comes from decision D13 of the panel file unless the files are synthetic and name it."""
    out = TMP / "analysis.json"
    # a ledger of its own (absent: no line) and the holds file: the command never reads the study's ledger here
    argv = ["--verdicts", str(TMP / "verdicts_v23_main.jsonl"), "--m6", str(TMP / "none.jsonl"), "--answer-runs",
            "t1", "--raw", str(TMP), "--labels", str(TMP / "labels"), "--flips", str(FLIPS), "--seed",
            str(SIGN_SEED), "--registered-hosted", "22,23", "--out", str(out),
            "--ledger", str(TMP / "no_ledger.jsonl"), "--holds", str(ROOT / "config" / "stage_holds.json")]
    # answers_v23.guard() compares the answer folder with results/raw by resolving both paths; a stand-in keeps the
    # test from touching results/ at all
    real_raw, answers_v23.RAW = answers_v23.RAW, TMP / "raw_stand_in"
    try:
        AN.main(argv)
    finally:
        answers_v23.RAW = real_raw
    got = json.loads(out.read_text(encoding="utf-8"))
    want = json.loads(json.dumps(AN.jsonable(W["res"])))
    assert got["registered"] == want["registered"] and got["labels"] == want["labels"]
    assert got["secondary"]["by_model"] == want["secondary"]["by_model"]
    for k in ("accuracy", "challenge_set", "reference_subset", "judge_comparisons", "repeatability",
              "calls_not_attempted", "commercial", "safe"):
        assert got[k] == want[k], k
    assert got["inputs"]["verdict_file"]["unreadable_lines"] == 1 and got["inputs"]["ledger_lines"] == 0
    for bad in (["--verdicts", str(TMP / "verdicts_v23_pilot.jsonl")],
                ["--verdicts", str(AN.VERDICTS), "--labels", str(TMP / "labels"), "--registered-hosted", "22"]):
        try:
            AN.main(bad)
        except SystemExit:
            pass
        else:
            raise AssertionError("a command that must be refused ran")


def test_refusals():
    """Inputs that the analysis refuses: a verdict file of another protocol, a final attempt with a status that is
    not final, a locked label file that differs from its lock record."""
    bad = TMP / "bad.jsonl"
    for content in (json.dumps({"protocol": "2.2", "key": "x"}),
                    json.dumps({"protocol": "2.3", "key": "x", "final": True, "status": "pending"})):
        bad.write_text(content + "\n", encoding="utf-8")
        try:
            AN.read_verdicts(bad)
        except ValueError:
            pass
        else:
            raise AssertionError("a verdict file that must be refused was read")
    lpath = TMP / "labels" / "labels_locked_v23.csv"
    lpath.write_bytes(lpath.read_bytes() + b"\n")
    try:
        AN.check_lock(TMP / "labels")
    except SystemExit:
        pass
    else:
        raise AssertionError("a changed label file passed the lock check")


# ------------------------------------------------------------------------------- Sections 9.4, 10.3 and 11.6
def ck(c):
    return f"{c['block']}|{c['part']}|{c['judge']}|{c['answer_id']}|{c['presentation']}"


def bump(d, k, n=1):
    d[k] = d.get(k, 0) + n


def relations():
    """Developer and close lineage of config/panel_v23.json, read here without src/yoking."""
    d = json.loads(AN.DESIGN.read_text(encoding="utf-8"))
    dev = {int(k): v for k, v in d["developer"].items()}
    close = {frozenset(int(x) for x in p) for p in d["close_lineage"]}
    return lambda a, k: a == k or dev[a] == dev[k] or frozenset((a, k)) in close


def generated(judge_key, aid, pres, parts):
    """Key of the generated verdict of a judge on an answer: the first of the parts (block, part) that holds one."""
    return next((k for k in (f"{b}|{p}|{judge_key}|{aid}|{pres}" for b, p in parts) if k in W["truth"]), None)


def clopper_pearson(x, n):
    return (stats.beta.ppf(0.025, x, n - x + 1) if x > 0 else 0.0,
            stats.beta.ppf(0.975, x + 1, n - x) if x < n else 1.0)


def check_rate(got, x, n, where):
    assert got["answers"] == n and got["flags"] == x, (where, got, x, n)
    if n:
        lo, hi = clopper_pearson(x, n)
        assert got["rate"] == x / n and abs(got["lo"] - lo) < 1e-9 and abs(got["hi"] - hi) < 1e-9, where
    else:
        assert got["rate"] is None and got["lo"] is None


def test_plan_and_accounting():
    """The plan at the lock is the plan of the runner: every planned call of blocks 3, 5, 6 and 7 (the label-dependent
    parts included) has its final verdict, counted by block and status; no call is not attempted, no verdict lies
    outside the plan, and every answer of blocks 2 and 4 exists."""
    na, calls, truth = W["res"]["calls_not_attempted"], W["calls"], W["truth"]
    want = {}
    for c in calls:
        bump(want.setdefault(c["block"], {}), truth[ck(c)][0])
    got = na["judging_by_block"]
    assert {b: v["final"] for b, v in got.items()} == want
    assert all(v["planned"] == sum(want[b].values()) and not v["not_attempted"] and v[AN.EXCLUDED] == 0
               for b, v in got.items())
    assert na["totals"] == {"not_attempted": {}, AN.EXCLUDED: 0, "answers_not_attempted": {},
                            "answers_excluded_d2": 0}
    assert na["verdicts_outside_plan"] == {} and na["label_parts_planned"] and na["local_calls_left"] == {}
    assert {("5", "label_blind"), ("5", "challenge_context"), ("5", "repeat"), ("6", "reference_h1"),
            ("6", "reference_h2"), ("6", "repeat"), ("7", "challenge_blind"),
            ("7", "challenge_context")} <= {(c["block"], c["part"]) for c in calls}
    n_answers = 0
    for sides in na["answers"].values():
        for cells in sides.values():
            for c in cells.values():
                assert c["made"] == c["planned"] and not c["not_attempted"]
                n_answers += c["planned"]
    fr = W["frames"]
    assert n_answers == (len(W["panel"].primary) * (len(fr["harmful"][0]) + len(fr["safe"][0]))
                         + len(W["panel"].commercial) * (len(fr["common"][0]) + len(fr["safe"][0])))
    assert W["res"]["registered"]["hosted_calls_on_harmful_frame_outside_block_3_not_attempted"] == {}


def test_accuracy():
    """Section 9.4: the blind accuracy of every judge equals direct counts on the generated verdicts: eligible answers
    without the judge's own, same-developer and close-lineage answers; rates among answers labelled harmful and not
    harmful with Clopper-Pearson intervals (primary judges on all labelled answers, commercial judges on the reference
    subset); for the primary panel, the weighted rates of cluster_ratio over the 390 prompts of both frames."""
    panel, rows, harm, fr, acc = W["panel"], W["locked"], W["harm"], W["frames"], W["res"]["accuracy"]
    related = relations()
    ids = list(fr["harmful"][0]) + list(fr["safe"][0])
    lab = [f"harmful|{fr['harmful'][1][p]}" for p in fr["harmful"][0]] + [f"safe|{fr['safe'][1][p]}"
                                                                         for p in fr["safe"][0]]
    names = sorted(set(lab))
    strata, col = np.array([names.index(x) for x in lab]), {p: i for i, p in enumerate(ids)}
    assert len(names) == 4 and len(ids) == 390
    ineligible = unknown = 0
    for m in panel.primary + panel.commercial:
        k, primary = panel.key_of[m], m in panel.primary
        scope = rows if primary else [r for r in rows if r["api_ref"]]
        parts = AN.BLIND_PRIMARY if primary else AN.BLIND_COMMERCIAL
        el = [r for r in scope if not related(r["model"], m)]
        x, n = {"yes": 0, "no": 0}, {"yes": 0, "no": 0}
        X, N = ({c: np.zeros(len(ids)) for c in ("yes", "no")} for _ in range(2))
        for r in el:
            kk = generated(k, r["answer_id"], "blind", parts)
            assert kk is not None, (m, r["answer_id"])
            if r["label"] == "":
                continue
            f = int(harm[kk] is True)
            n[r["label"]] += 1
            x[r["label"]] += f
            X[r["label"]][col[r["prompt_id"]]] += r["weight"] * f
            N[r["label"]][col[r["prompt_id"]]] += r["weight"]
        got = acc[str(m)]
        assert got["eligible"] == len(el) and got["ineligible"] == len(scope) - len(el)
        assert got["not_attempted"] == {} and got["not_planned"] == 0 and got["verdicts"] == len(el)
        ineligible += got["ineligible"]
        unknown += got["unknown_label"]
        for y, cls in (("yes", "harmful"), ("no", "not_harmful")):
            check_rate(got[cls], x[y], n[y], (m, cls))
            if primary:
                r = inf.cluster_ratio(X[y], N[y], strata)
                lo, hi = inf.interval(r)
                g = got["weighted"][cls]
                assert abs(g["est"] - float(r["est"])) < 1e-12 and abs(g["lo"] - float(lo)) < 1e-12, (m, cls)
                dom = sum(max(int((N[y][strata == h] > 0).sum()) - 1, 0) for h in np.unique(strata))
                assert abs(g["hi"] - float(hi)) < 1e-12 and g["df"] == max(dom, 1) and dom < 386   # Section 8.1
            else:
                assert "weighted" not in got
    assert ineligible > 0 and unknown > 0
    print(f"  judge 20 (refusal-removed): {acc['20']['eligible']} eligible of {len(rows)}; judge 1: "
          f"{acc['1']['eligible']} of {sum(r['api_ref'] for r in rows)}")


def test_challenge_set_and_comparisons():
    """Sections 8.6 and 9.4: the challenge set of every judge in both presentations and the change, against direct
    counts; the comparisons between commercial judges on the answers eligible and validly classified for every
    compared judge (all, without 11, without 1 and 2), on the challenge set and on the reference subset."""
    panel, rows, truth, res = W["panel"], W["locked"], W["truth"], W["res"]
    related = relations()
    ch = [r for r in rows if r["h60"]]
    cs = res["challenge_set"]
    assert cs["size"] == len(ch) == sum(cs["by_model"].values()) and set(cs["by_model"]) == {
        str(m) for m in panel.removed}
    assert sum(cs["labels"].values()) == len(ch)
    for m in panel.primary + panel.commercial:
        k, primary = panel.key_of[m], m in panel.primary
        el = [r for r in ch if not related(r["model"], m)]
        bp = AN.BLIND_PRIMARY if primary else (("7", "challenge_blind"),)
        cp = AN.CONTEXT_PRIMARY if primary else AN.CONTEXT_COMMERCIAL
        tb = [truth[generated(k, r["answer_id"], "blind", bp)] for r in el]
        tc = [truth[generated(k, r["answer_id"], "context", cp)] for r in el]
        got = cs["by_judge"][str(m)]
        assert got["eligible"] == len(el)
        check_rate(got["blind"], sum(t[1] for t in tb), len(el), (m, "blind"))
        check_rate(got["context"], sum(t[1] for t in tc), len(el), (m, "context"))
        g = sum(1 for b, c in zip(tb, tc) if c[1] > b[1])
        lost = sum(1 for b, c in zip(tb, tc) if c[1] < b[1])
        assert got["change"]["gained"] == g and got["change"]["lost"] == lost
        assert got["change"]["est"] == ((g - lost) / len(el) if el else None)
        if el:                                         # Section 8.2: the change has a 95% interval (cluster: prompt)
            per = {}
            for r, b, c in zip(el, tb, tc):
                a = per.setdefault(r["prompt_id"], [r["source"], 0, 0])
                a[1], a[2] = a[1] + c[1] - b[1], a[2] + 1
            want = ratio_interval_by_hand(per)
            iv = got["change"]["interval95"]
            assert (iv["lo"] is None and want is None) or (close(iv["lo"], want[0]) and close(iv["hi"], want[1])),                 (m, iv, want)
        vp = [(b, c) for b, c in zip(tb, tc) if b[0] == c[0] == "valid"]
        assert got["change"]["valid_pairs"]["answers"] == len(vp)
        if not primary:
            assert got["eligible"] == len(ch)          # none of these answers is a commercial judge's own
    assert cs["by_judge"]["20"]["eligible"] < len(ch)
    jc = res["judge_comparisons"]
    assert jc["challenge_presentations"] == ["blind", "context"] and jc["left_out"] == {}
    ref = [r for r in rows if r["api_ref"]]
    for name, drop in (("all", ()), ("without_11", (11,)), ("without_1_2", (1, 2))):
        js = [m for m in panel.commercial if m not in drop]
        keys = {m: panel.key_of[m] for m in js}
        common = [r for r in ch if all(truth[f"7|challenge_{p}|{keys[m]}|{r['answer_id']}|{p}"][0] == "valid"
                                       for m in js for p in ("blind", "context"))]
        got = jc[name]["challenge_set"]
        assert got["judges"] == js and got["answers"] == len(common), name
        for m in js:
            fb = [truth[f"7|challenge_blind|{keys[m]}|{r['answer_id']}|blind"][1] for r in common]
            fc = [truth[f"7|challenge_context|{keys[m]}|{r['answer_id']}|context"][1] for r in common]
            check_rate(got["by_judge"][str(m)]["blind"], sum(fb), len(common), (name, m))
            check_rate(got["by_judge"][str(m)]["context"], sum(fc), len(common), (name, m))
            assert got["by_judge"][str(m)]["change"]["est"] == ((sum(fc) - sum(fb)) / len(common) if common else None)
        common = [r for r in ref if all(truth[generated(keys[m], r["answer_id"], "blind", AN.BLIND_COMMERCIAL)][0]
                                        == "valid" for m in js)]
        got = jc[name]["reference_subset"]
        assert got["answers"] == len(common), name
        for m in js:              # the harm flag on both sides (on a safe answer the generated flag is a refusal)
            for y, cls in (("yes", "harmful"), ("no", "not_harmful")):
                f = [int(W["harm"][generated(keys[m], r["answer_id"], "blind", AN.BLIND_COMMERCIAL)] is True)
                     for r in common if r["label"] == y]
                check_rate(got["by_judge"][str(m)][cls], sum(f), len(f), (name, m, cls))
    assert 0 < jc["all"]["challenge_set"]["answers"] <= jc["without_1_2"]["challenge_set"]["answers"] <= len(ch)
    rs = res["reference_subset"]
    assert rs["size"] == len(ref) and rs["challenge_set"] == len(ch)
    assert rs["halves"]["first"] + rs["halves"]["second"] == len(ref) - len(ch)
    print(f"  challenge set {len(ch)}; compared: {jc['all']['challenge_set']['answers']} answers valid for all eleven "
          f"commercial judges in both presentations, {jc['all']['reference_subset']['answers']} of the reference "
          f"subset blind")


def test_repeatability():
    """Section 11.6: per judge and presentation, the pairs of an original call and its repeat, the share whose flag
    differs, and for local judges the mark to investigate, against direct counts."""
    panel, calls, truth, rep = W["panel"], W["calls"], W["truth"], W["res"]["repeatability"]
    differs = 0
    for m in panel.primary + panel.commercial:
        k = panel.key_of[m]
        orig = "3|own_harmful" if m in panel.primary else "6|own"
        mine = [c for c in calls if c["part"] == "repeat" and c["judge"] == k]
        assert len(mine) == 20, (m, len(mine))
        for pres in ("blind", "context"):
            pairs = [(truth[f"{orig}|{k}|{c['answer_id']}|{pres}"], truth[ck(c)]) for c in mine
                     if c["presentation"] == pres]
            d = sum(1 for a, b in pairs if a[1] != b[1])
            got = rep[str(m)][pres]
            assert got["pairs"] == len(pairs) == 10 and got["flag_differs"] == d and got["share"] == d / 10
            assert got["status_differs"] == sum(1 for a, b in pairs if a[0] != b[0])
            assert ("investigate" in got) == (m not in panel.hosted_all and m not in panel.commercial)
            assert got.get("investigate", d > 0) == (d > 0)
            differs += d
    assert differs > 0


def without(canon, drop):
    return {k: r for k, r in canon.items() if k not in drop}


def test_ledger_reasons():
    """A ledger at the lock: cuts 1 and 3, an abandonment of block 6 for model 13 (whose provider stop was resumed),
    a stop of model 12's serving host still in force (block 6 then abandoned for model 12 so that it could close),
    the closes of blocks 6 and 7 as the judge runner writes them, and calls left by model 16 (local) and model 22 on a
    safe answer. Every call without a final attempt gets its reason (Section 10.3; model 12's are 'provider_stop',
    where the close counted them as abandoned); the counts of each close are made again from the plan and agree, and
    a close with other counts is marked; the cuts withdraw the repeatability of the API judges and the commercial
    presentation change on the challenge set; the commercial safe controls of the stop are reported on the complete
    answers with bounds; P1 to P3 stay declared. A hosted call on the harmful frame left outside a cut then stops the
    declaration (Section 10.4)."""
    panel, canon0, calls = W["panel"], W["canon"], W["calls"]
    key = panel.key_of
    harm_ids = set(W["frames"]["harmful"][0])
    drop, want = set(), {}

    def take(cs, reason):
        for c in cs:
            drop.add(ck(c))
            bump(want, reason)

    ctx7 = [c for c in calls if c["part"] == "challenge_context" and c["block"] == "7"]
    take(ctx7[len(ctx7) // 5:], "budget_cut")                       # cut 3 after a fifth of the in-context half
    api = {key[m] for m in panel.commercial} | {key[22], key[23]}
    reps = [c for c in calls if c["part"] == "repeat" and c["judge"] in api]
    take(reps[len(reps) // 3:], "budget_cut")                       # cut 1
    take([c for c in calls if c["part"] == "reference_h1" and c["judge"] == key[13]][:7], "abandoned")
    take([c for c in calls if c["part"] == "control_safe" and c["judge"] == key[12] and c["block"] == "6"][:9],
         "provider_stop")
    take([next(c for c in calls if c["part"] == "label_blind" and c["judge"] == key[16] and c["side"] == "safe")],
         "unavailable")
    take([next(c for c in calls if c["part"] == "label_blind" and c["judge"] == key[22] and c["side"] == "safe")],
         "unavailable")
    canon = without(canon0, drop)

    def close_line(b, not_attempted):
        """The block_complete line of the judge runner for block b of the primary build (every judge)."""
        cs = [c for c in calls if c["block"] == b]
        fin = {}
        for c in cs:
            if ck(c) in canon:
                bump(fin, canon[ck(c)]["status"])
        assert len(cs) - sum(fin.values()) == sum(not_attempted.values()), b
        return {"kind": "block_complete", "block": b, "role": "judge", "build": "primary", "models": None,
                "spent_usd": 0.0, "planned": len(cs), "final_by_status": fin, "not_attempted": not_attempted,
                "not_sent": {}, "excluded_d2": {}, "reason": "every planned call counted"}

    cut6 = sum(1 for c in reps[len(reps) // 3:] if c["block"] == "6")
    ledger = [{"kind": "provider_stop", "account": "openrouter", "host": "xAI", "reason": "a synthetic warning"},
              {"kind": "provider_resume", "account": "openrouter", "host": "xAI", "reason": "a synthetic answer"},
              {"kind": "cut", "cut": 1, "before_block": "6"},
              {"kind": "block_abandon", "block": "6", "models": [key[13]], "reason": "a synthetic decision"},
              {"kind": "provider_stop", "account": "openrouter", "host": "Moonshot AI", "reason": "a synthetic stop"},
              {"kind": "block_abandon", "block": "6", "models": [key[12]], "reason": "a synthetic decision"},
              close_line("6", {"budget_cut": cut6, "abandoned": 7 + 9}),     # the runner: cut, then abandoned
              {"kind": "cut", "cut": 3, "before_block": "7"},
              close_line("7", {"budget_cut": len(ctx7) - len(ctx7) // 5})]
    holds = spend_v23.load_holds(ROOT / "config" / "stage_holds.json")
    res = AN.analyse(canon, W["answers"], panel, W["frames"], W["asg"], label_rows=W["locked"],
                     label_design=W["ldesign"], flips=FLIPS, seed=SIGN_SEED, ledger=ledger, holds=holds)
    json.dumps(AN.jsonable(res))
    na, reg, base = res["calls_not_attempted"], res["registered"], W["res"]
    assert na["totals"]["not_attempted"] == want, (na["totals"]["not_attempted"], want)
    assert na["local_calls_left"] == {"16": {"5|label_blind": 1}}
    assert reg["declared"] and reg["claims"] == base["registered"]["claims"]
    assert reg["statistics"] == base["registered"]["statistics"]
    led = na["ledger"]
    assert set(led["cuts_in_force"]) == {"1", "3"}
    assert {(a["block"], a["model"]) for a in led["abandoned"]} == {("6", 12), ("6", 13)}
    assert [(s["account"], s["host"]) for s in led["provider_stops_in_force"]] == [("openrouter", "Moonshot AI")]
    for close, b in zip(led["block_complete"], ("6", "7")):
        assert close["block"] == b and close["same_counts"], close
        assert {f: close["here"][f] for f in ("planned", "final_by_status", "not_attempted", AN.EXCLUDED)} == {
            f: close[f] for f in ("planned", "final_by_status", "not_attempted", AN.EXCLUDED)}
    # a close whose counts differ from the plan and the verdicts is marked
    bad = [dict(e, final_by_status=dict(e["final_by_status"], valid=e["final_by_status"]["valid"] + 1))
           if e["kind"] == "block_complete" and e["block"] == "6" else e for e in ledger]
    L2 = AN.ledger_state(bad, holds)
    P2 = AN.planned(panel, W["frames"], W["asg"], W["answers"], W["locked"], J.load_settings())
    acc2 = AN.accounting(P2, AN.reasons(P2, canon, W["answers"], L2, panel), canon, W["answers"], L2, panel)
    assert [c["same_counts"] for c in acc2["ledger"]["block_complete"]] == [False, True]
    # cut 3: no commercial presentation change on the challenge set; the in-context calls made are counted
    for m in panel.commercial:
        made = sum(1 for c in ctx7 if c["judge"] == key[m] and ck(c) in canon)
        assert res["challenge_set"]["by_judge"][str(m)]["change"] == {"not_reported": AN.CUT_TEXT[3],
                                                                       "in_context_calls_made": made}
    for m in panel.primary:
        assert res["challenge_set"]["by_judge"][str(m)] == base["challenge_set"]["by_judge"][str(m)]
    jc = res["judge_comparisons"]
    assert jc["challenge_presentations"] == ["blind"] and jc["presentation_change"] == AN.CUT_TEXT[3]
    assert jc["all"]["challenge_set"]["answers"] >= base["judge_comparisons"]["all"]["challenge_set"]["answers"]
    assert all("change" not in e for e in jc["all"]["challenge_set"]["by_judge"].values())
    # cut 1: the repeatability of the API judges is not reported; the local judges' is
    for m in panel.primary + panel.commercial:
        r = res["repeatability"][str(m)]
        if m in panel.commercial or m in (22, 23):
            made = sum(1 for c in reps if c["judge"] == key[m] and ck(c) in canon)
            assert r == {"not_reported": AN.CUT_TEXT[1], "planned": 20, "repeat_calls_made": made}
        else:
            assert r == base["repeatability"][str(m)]
    # the stop of model 12: its safe controls are missing; the author-versus-control quantities are reported on the
    # complete answers, with bounds over those calls
    sc = res["safe"]["commercial"]
    assert sc["calls"]["not_attempted_by_reason"] == {"provider_stop": 9} and not sc["control_verdicts_complete"]
    assert "bounds_not_attempted" in sc and "author_versus_control" not in sc
    assert set(sc["quantities"]) == set(base["safe"]["commercial"]["quantities"])
    for key_, lim in sc["bounds_not_attempted"].items():
        assert lim["low"]["est"] <= lim["high"]["est"], key_
        if key_ in AN.SAFE_NO_INTERVAL:                  # Appendix A.4: no interval on the bounds either
            assert all(lim[t]["lo"] is None and lim[t]["p"] is None and lim[t].get("lb99") is None
                       and lim[t]["no_interval"] == AN.SAFE_NO_INTERVAL_TEXT for t in ("low", "high")), key_
    assert set(sc["bounds_not_attempted"]) & set(AN.SAFE_NO_INTERVAL)
    # the abandonment of model 13: fewer answers, with bounds over the calls
    a13 = res["accuracy"]["13"]
    assert a13["not_attempted"] == {"abandoned": 7}
    assert sum(a13[c].get("bounds_not_attempted", {}).get("calls", 0) for c in ("harmful", "not_harmful")) <= 7
    assert a13["verdicts"] == base["accuracy"]["13"]["verdicts"] - 7

    # a scheduled call of model 22 on the harmful frame, outside block 3 and outside a cut: not declared
    hosted = next(c for c in calls if c["part"] == "label_blind" and c["judge"] == key[22]
                  and c["prompt_id"] in harm_ids)
    res2 = AN.analyse(without(canon, {ck(hosted)}), W["answers"], panel, W["frames"], W["asg"],
                      label_rows=W["locked"], label_design=W["ldesign"], flips=FLIPS, seed=SIGN_SEED, ledger=ledger,
                      holds=holds)
    reg2 = res2["registered"]
    assert not reg2["declared"] and all(reg2["claims"][p]["state"] == "not declared" for p in ("P1", "P2", "P3"))
    assert reg2["hosted_calls_on_harmful_frame_outside_block_3_not_attempted"] == {"22": {"5|label_blind":
                                                                                            {"unavailable": 1}}}
    assert reg2["statistics"] == base["registered"]["statistics"] and "bounds_not_attempted" not in reg2
    assert "analysis" in res2["labels"] and "detection_addition" not in reg2["claims"]
    print(f"  reasons: {na['totals']['not_attempted']}")


D2M = 10          # the example of decision D2 in this test (model 14 until decision D17)


def test_decision_d2():
    """Decision D2 for model D2M (its latest preflight admits its endpoint for safe prompts only): it writes no answer to
    the common set and classifies no harmful-side answer. These calls are excluded, not 'not attempted': P1 to P3 stay
    declared, the commercial tables leave out its answers and the answers it would control (no bounds), and its
    harmful-side quantities are not available; its safe side is untouched."""
    panel, key = W["panel"], W["panel"].key_of
    k14 = key[D2M]
    gone = {aid for aid, a in W["answers"].items() if a["model_key"] == k14 and a["side"] == "harmful"}
    answers = {aid: a for aid, a in W["answers"].items() if aid not in gone}
    rows = [r for r in W["locked"] if r["answer_id"] not in gone]       # drawn from the answers that exist
    canon = {k: r for k, r in W["canon"].items()
             if r["answer_id"] not in gone and not (r["judge"] == k14 and r["side"] == "harmful")}
    pl = plan_v23.Plan(panel, W["frames"], W["asg"], answers, labels=rows)
    pcalls, skipped = {}, {}
    for b in ("3", "5", "6", "7"):
        before = len(pl.skipped)
        pcalls[b] = pl.calls(b)
        skipped[b] = {}
        for e in pl.skipped[before:]:
            bump(skipped[b], e["state"])
    fin6, ex6 = {}, 0                    # the close of block 6 as the judge runner writes it under D2
    for c in pcalls["6"]:
        if ck(c) in canon:
            bump(fin6, canon[ck(c)]["status"])
        else:
            assert c["judge"] == k14 and c["side"] == "harmful"
            ex6 += 1
    ledger = [{"kind": "preflight", "model_key": key[13], "ok": True, "safe_only": True, "spent_usd": 0.0},
              {"kind": "preflight", "model_key": key[13], "ok": True, "safe_only": False, "spent_usd": 0.0},
              {"kind": "preflight", "model_key": k14, "ok": True, "safe_only": True, "spent_usd": 0.0},
              {"kind": "block_complete", "block": "6", "role": "judge", "build": "primary", "models": None,
               "spent_usd": 0.0, "planned": len(pcalls["6"]), "final_by_status": fin6, "not_attempted": {},
               "not_sent": skipped["6"], "excluded_d2": {k14: ex6},
               "reason": f"answers of model {D2M} on harmful prompts never made (decision D2)"}]
    holds = spend_v23.load_holds(ROOT / "config" / "stage_holds.json")
    res = AN.analyse(canon, answers, panel, W["frames"], W["asg"], label_rows=rows, label_design=W["ldesign"],
                     flips=FLIPS, seed=SIGN_SEED, ledger=ledger, holds=holds)
    json.dumps(AN.jsonable(res))
    base, reg, com = W["res"], res["registered"], res["commercial"]
    assert reg["declared"] and reg["claims"] == base["registered"]["claims"]
    assert com["calls"]["complete"] and com["calls"]["excluded_d2"]["models"] == [D2M]
    assert com["calls"]["excluded_d2"]["answers_not_written"] == len(gone) == 60
    assert "bounds_not_attempted" not in com
    for name in ("all", "without_11", "without_1_2"):
        assert com["tables"][name]["by_model"][str(D2M)] == {"not_available": AN.D2_TEXT}
    Dc, S, F = commercial_arrays()                    # the answers of D2M and those it controls are left out
    j14 = panel.commercial.index(D2M)
    inc = np.ones(S.shape, bool)
    inc[j14, :] = False
    inc &= Dc["ctrl"] != j14
    out, _ = SR.statistics(S[None], *(F[a][None] for a in ("A1", "A2", "C1", "C2")), Dc,
                           np.ones((1, Dc["P"]), np.int8), inc[None].astype(np.int8))
    check_stats(com["tables"]["all"]["statistics"], out, ("th", "io", "be", "iw"), "commercial under D2")
    excluded = sum(1 for cs in pcalls.values() for c in cs if c["judge"] == k14 and c["side"] == "harmful")
    na = res["calls_not_attempted"]
    assert na["totals"] == {"not_attempted": {}, AN.EXCLUDED: excluded, "answers_not_attempted": {},
                            "answers_excluded_d2": 60}
    assert excluded > ex6 > 0 and na["verdicts_outside_plan"] == {}
    assert na["ledger"]["d2_safe_prompts_only"] == [D2M]                          # 13's latest preflight is not
    close = na["ledger"]["block_complete"][0]
    assert close["same_counts"] and close["here"][AN.EXCLUDED] == close[AN.EXCLUDED] == {str(D2M): ex6}
    assert na["not_sent"]["6"] == skipped["6"] and skipped["6"].get("missing", 0) > 0   # on answers never made
    assert res["accuracy"][str(D2M)]["not_available"] == AN.D2_TEXT
    assert res["accuracy"][str(D2M)]["verdicts_on_safe_side_answers"] > 0
    assert res["challenge_set"]["by_judge"][str(D2M)]["not_available"] == AN.D2_TEXT
    assert res["repeatability"][str(D2M)] == {"not_available": AN.D2_TEXT}
    assert res["common_set_all_models"][str(D2M)] == {"not_available": AN.D2_TEXT}
    jc = res["judge_comparisons"]
    assert jc["left_out"] == {str(D2M): AN.D2_TEXT} and D2M not in jc["all"]["challenge_set"]["judges"]
    assert D2M not in jc["all"]["reference_subset"]["judges"]
    assert res["safe"] == base["safe"]
    for m in panel.commercial:
        if m != D2M:
            assert res["accuracy"][str(m)] == base["accuracy"][str(m)]
    print(f"  model {D2M} under D2: {excluded} judging calls and 60 answers excluded; P1 to P3 declared")


def test_safe_no_interval():
    """Appendix A.4, run (d): analyze_v23.SAFE_NO_INTERVAL_D19 is exactly the set of safe-side intervals that failed
    check 6 in the first run (seed 20261121, SS.BASE_SEED) and again in the second run (seed 20261124, 40,000
    replications) of the stored files, in at least one setting. Both runs have the same number of reference clusters.
    SAFE_NO_INTERVAL adds the intervals that failed twice only with the registered code (kept until the PI decides on
    amendment D19)."""
    out = ROOT / "analysis" / "output"
    first = json.loads((out / "sim_v23_safe.json").read_text(encoding="utf-8"))
    second = json.loads((out / "sim_v23_safe_rerun.json").read_text(encoding="utf-8"))
    failed_twice = set()
    for name, sc in first.items():
        assert sc["seed"] == SS.BASE_SEED and sc["reps"] == 10000, name
        sc2 = second[name]
        assert sc2["seed"] == 20261124 and sc2["reps"] == 40000 and sc2["clusters"] == sc["clusters"], name
        for k, st in sc["stats"].items():
            c = st.get("check6") or {}
            if c.get("made") and not c["passed"]:
                c2 = sc2["stats"][k]["check6"]
                assert c2["made"], (name, k)
                if not c2["passed"]:
                    failed_twice.add(k)
    assert failed_twice == set(AN.SAFE_NO_INTERVAL_D19), sorted(failed_twice ^ set(AN.SAFE_NO_INTERVAL_D19))
    assert set(AN.SAFE_NO_INTERVAL) == failed_twice | set(AN.SAFE_NO_INTERVAL_REGISTERED_ONLY)
    assert not failed_twice & set(AN.SAFE_NO_INTERVAL_REGISTERED_ONLY)
    keys = {s[0] for s in SS.specs("primary", dgp.design(frame="safe"))} | {
        s[0] for s in SS.specs("commercial", SS.commercial_design())}
    assert set(AN.SAFE_NO_INTERVAL) <= keys
    print(f"  {len(failed_twice)} safe-side intervals failed check 6 twice: {sorted(failed_twice)}")


def test_power_table_quantile():
    """Section 8.3 (review round 5, mutations): the approximate power of P3 in table A.1 is the normal approximation
    with the simulated standard error of beta_S and the 99% quantile of Student's t with 298 degrees of freedom; a
    table made with another quantile does not match."""
    import json as _json
    from scipy import stats
    sys.path.insert(0, str(ROOT / "analysis"))
    import tables_v23 as TB
    rows = {r["name"]: r for r in _json.loads((ROOT / "analysis" / "output" / "sim_v23_rs1.json")
                                              .read_text(encoding="utf-8"))["rows"]}
    TB.LINES.clear()
    TB.rs1()                                  # the generator itself, not the stored table (review round 6)
    text = "\n".join(TB.LINES)
    TB.LINES.clear()
    stored = (ROOT / "analysis" / "output" / "tables_v23.md").read_text(encoding="utf-8")
    block = text.split("**Approximate power of the bound P3 for other margins.**")[1].split("###")[0]
    assert block.strip() in stored                           # the stored table is the generated one
    got = {}
    for line in block.splitlines():
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(c) == 11 and c[0] in {n.split("|")[0] for n in rows}:
            got[c[0]] = c[2:]
    assert got and TB.APPROX_DF == 298
    margins = ((0.03, (0, -0.01)), (0.05, (0, -0.01, -0.02)), (0.07, (0, -0.01, -0.02, -0.03)))
    for z, should_match in ((stats.t.ppf(0.99, 298), True), (stats.norm.ppf(0.95), False)):
        same_all = True
        for c, cells in got.items():
            se = rows[f"{c}|null"]["summary"]["be"]["mean_se"]
            want = [f"{100 * stats.norm.cdf((m + b) / se - z):.0f}" for m, bs in margins for b in bs]
            same_all &= want == cells
        assert same_all == should_match, z


def close(a, b):
    """Equal up to rounding (a formula written out by hand against the production code)."""
    return a is not None and b is not None and abs(a - b) < 1e-9


def ratio_interval_by_hand(per):
    """Section 8.1 written out, independently of analysis/inference_v23.py: per {prompt: [source, X_p, N_p]}.
    R = sum X / sum N; e_p = X_p - R N_p centred in each source; V = sum_h n_h/(n_h - 1) sum (e_p - mean_h)^2
    / (sum N)^2; Student's t with sum_h (m_h - 1) df, m_h the prompts of h with N_p != 0, at least 1. None when a
    source has one prompt, the denominator is zero or the variance is zero."""
    from scipy import stats
    srcs = {}
    for s, x, n in per.values():
        srcs.setdefault(s, []).append((x, n))
    if any(len(v) < 2 for v in srcs.values()):
        return None
    tx, tn = sum(x for v in srcs.values() for x, _ in v), sum(n for v in srcs.values() for _, n in v)
    if tn == 0:
        return None
    r = tx / tn
    var, df = 0.0, 0
    for v in srcs.values():
        e = [x - r * n for x, n in v]
        mu = sum(e) / len(e)
        var += len(e) / (len(e) - 1) * sum((y - mu) ** 2 for y in e)
        df += max(sum(1 for _, n in v if n != 0) - 1, 0)
    if var <= 1e-12 * max(1.0, max(abs(x - r * n) for v in srcs.values() for x, n in v)) ** 2:
        return None
    se = var ** 0.5 / abs(tn)
    q = stats.t.ppf(0.975, max(df, 1))
    return r - q * se, r + q * se


def test_change_interval_support():
    """Section 9.4 (review round 6): every prompt of the eligible answers stays in the variance, with a zero
    contribution where none of its answers enters; a source with one prompt gives no interval and does not stop the
    analysis; the estimate and the counts stay."""
    one = [dict(answer_id="a", prompt_id="p", source="s")]
    got = AN.change(one, {("a", "blind"): (0, "valid"), ("a", "context"): (1, "valid")})
    assert got["est"] == 1.0 and got["gained"] == 1 and got["interval95"]["available"] is False
    assert got["interval95"]["reason"] == "source with one prompt" and got["interval95"]["lo"] is None
    el = [dict(answer_id=f"a{i}", prompt_id=f"p{i // 2}", source=f"s{(i // 2) % 2}") for i in range(16)]
    flags = {}
    for i, r in enumerate(el):
        flags[(r["answer_id"], "blind")] = (int(i % 3 == 0), "valid")
        flags[(r["answer_id"], "context")] = (int(i % 2 == 0), "valid" if i % 5 else "invalid_json")
    for a in ("a6", "a7"):                    # prompt p3: no answer enters the change; it stays in the variance
        flags[(a, "context")] = ("free", "budget_stop")
    got = AN.change(el, flags)
    for cell, valid_only in ((got, False), (got["valid_pairs"], True)):
        per = {}
        for r in el:
            per.setdefault(r["prompt_id"], [r["source"], 0, 0])
        for r in el:
            b, c = flags[(r["answer_id"], "blind")], flags[(r["answer_id"], "context")]
            if "free" in (b[0], c[0]) or (valid_only and not b[1] == c[1] == "valid"):
                continue
            per[r["prompt_id"]][1] += c[0] - b[0]
            per[r["prompt_id"]][2] += 1
        assert per["p3"][2] == 0
        want = ratio_interval_by_hand(per)
        assert want is not None and close(cell["interval95"]["lo"], want[0]) and close(cell["interval95"]["hi"],
                                                                                      want[1]), (valid_only, want)
        short = {p: v for p, v in per.items() if v[2]}          # the domain without p3 gives another interval
        other = ratio_interval_by_hand(short)
        assert other is None or not close(other[0], want[0])
    assert got["bounds_not_attempted"]["answers"] == 2


TESTS = [test_design_from_assignment, test_canonical_verdicts, test_registered_equals_simulation,
         test_more_secondary_analyses,
         test_sensitivity_analyses_equal_simulation, test_delivery_reports, test_commercial_and_safe_equal_simulation,
         test_labels_equal_simulation, test_call_not_attempted, test_plan_and_accounting, test_accuracy,
         test_challenge_set_and_comparisons, test_repeatability, test_ledger_reasons, test_decision_d2,
         test_command_line, test_refusals, test_safe_no_interval, test_power_table_quantile,
         test_change_interval_support]

if __name__ == "__main__":
    try:
        build_world()
        for t in TESTS:
            t0 = time.time()
            t()
            print(f"ok {t.__name__} ({time.time() - t0:.1f} s)")
        print("all analysis tests passed")
    finally:
        shutil.rmtree(TMP, ignore_errors=True)
