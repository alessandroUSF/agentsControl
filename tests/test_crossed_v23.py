"""Offline tests of the crossed subset of protocol v2.3 (Section 8.8): the choice of the prompts, the judging plan
(src/plan_v23.Plan, part 'crossed' of block 5), the estimator and its variance (analysis/crossed_v23.py) against a
hand-computed case and against an explicit dummy-variable fit, the cells read from canonical verdicts, and a short
run of the coverage check of the intervals (Appendix A.4, check 5 in spirit). Nothing here calls a model.

Usage: python -I -X utf8 tests/test_crossed_v23.py
"""
import hashlib
import json
import math
import random
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "analysis"))
import crossed_v23 as X  # noqa: E402
import frames_v23  # noqa: E402
import plan_v23  # noqa: E402

FRAMES = frames_v23.frames()


def sha(p):
    return hashlib.sha256(p.encode("utf-8")).hexdigest()


def panel():
    models = json.loads((ROOT / "config" / "models.json").read_text(encoding="utf-8"))["models"]
    design = json.loads((ROOT / "config" / "panel_v23.json").read_text(encoding="utf-8"))
    return plan_v23.Panel(models, design, registered_hosted=[22, 23])


# ------------------------------------------------------------------------------------------------ the prompts
def test_selection():
    """100 prompts of the harmful frame, 50 per source, the first in SHA-256 order of their identifiers in each
    source; the same whatever the order of the frame, and the same on every call."""
    ids = plan_v23.crossed_prompts(FRAMES)
    hid, src = FRAMES["harmful"]
    assert len(ids) == len(set(ids)) == 100 and set(ids) <= set(hid)
    for s in set(src.values()):
        chosen = [p for p in ids if src[p] == s]
        rest = [p for p in hid if src[p] == s and p not in chosen]
        assert len(chosen) == 50 and max(map(sha, chosen)) < min(map(sha, rest))
    assert ids == sorted(ids, key=sha) == plan_v23.crossed_prompts(FRAMES)
    shuffled = list(hid)
    random.Random(5).shuffle(shuffled)
    assert plan_v23.crossed_prompts({"harmful": (shuffled, src)}) == ids
    small = {"harmful": (["a", "b", "c"], {"a": "x", "b": "y", "c": "x"})}
    assert sorted(plan_v23.crossed_prompts(small, per_source=1)) == sorted([min("a", "c", key=sha), "b"])


# ---------------------------------------------------------------------------------------------- the judging plan
def world(seed=3):
    """A synthetic answer table of the primary panel on the harmful frame, screen-positive with the shares of the
    simulation, and a label sample with a few labelled and challenge answers among the crossed ones."""
    p, rng = panel(), random.Random(seed)
    answers = {}
    for pid in FRAMES["harmful"][0]:
        for n in p.primary:
            k = plan_v23.aid(p.key_of[n], pid)
            pos = rng.random() < X.SIM_AUTHORS[n]
            answers[k] = {"answer_id": k, "model_key": p.key_of[n], "model": n, "prompt_id": pid,
                          "source": FRAMES["harmful"][1][pid], "side": "harmful", "status": "ok",
                          "screen": "positive" if pos else "negative", "has_content": rng.random() > 0.02}
    crossed = set(plan_v23.crossed_prompts(FRAMES))
    sp = [a for a in answers.values() if a["prompt_id"] in crossed and a["screen"] == "positive" and a["has_content"]]
    rng.shuffle(sp)
    labels = ([{"answer_id": a["answer_id"], "h60": False, "api_ref": False} for a in sp[:40]]
              + [{"answer_id": a["answer_id"], "h60": True, "api_ref": False} for a in sp[40:60]])
    asg, _ = plan_v23.load_assignment()
    return p, answers, labels, asg


def test_plan():
    """Part 'crossed' of block 5: the ten local judges, every screen-positive answer of the primary panel to the
    crossed prompts (models 22 and 23 included as authors), in the presentations that blocks 3 and 5 do not give;
    pairs in the order of Section 11.4, last for each judge; nothing without a label sample or with crossed=False."""
    p, answers, labels, asg = world()
    pl = plan_v23.Plan(p, FRAMES, asg, answers, labels=labels)
    assert pl.crossed_judges() == [4, 5, 6, 15, 16, 17, 18, 19, 20, 21]
    xa = pl.crossed_answers()
    crossed = set(plan_v23.crossed_prompts(FRAMES))
    assert all(a["prompt_id"] in crossed and a["screen"] == "positive" and a["has_content"] for a in xa)
    assert {a["model"] for a in xa} >= {22, 23}
    want = sum(1 for a in answers.values() if a["prompt_id"] in crossed and a["screen"] == "positive"
               and a["has_content"])
    assert len(xa) == want
    calls = pl.calls("5")
    main = {}                    # (judge, answer) -> presentations that blocks 3 and 5 already plan
    for c in pl.calls("3") + [c for c in calls if c["part"] != "crossed"]:
        if c["part"] in ("own_harmful", "control_harmful", "control_local", "label_blind", "challenge_context"):
            main.setdefault((c["judge"], c["answer_id"]), set()).add(c["presentation"])
    cx = [c for c in calls if c["part"] == "crossed"]
    assert cx and all(c["block"] == "5" and c["arm"] == "M" and c["side"] == "harmful" for c in cx)
    got = {}
    for c in cx:
        got.setdefault((c["judge"], c["answer_id"]), set()).add(c["presentation"])
    expected_calls = 0
    for jn in pl.crossed_judges():
        key = p.key_of[jn]
        for a in xa:
            have = main.get((key, a["answer_id"]), set())
            need = {"blind", "context"} - have
            expected_calls += len(need)
            assert got.get((key, a["answer_id"]), set()) == need, (key, a["answer_id"], have)
    assert len(cx) == expected_calls
    assert all(p.n_of[c["judge"]] in pl.crossed_judges() for c in cx)
    # pairs: hash order, next to each other; single calls only where the blind verdict exists (label_blind)
    by_pair = {}
    for c in cx:
        by_pair.setdefault(c["pair"], []).append(c)
    for pair, cs in by_pair.items():
        if pair is None:
            assert all(c["presentation"] == "context" and c["position"] == 0 for c in cs)
            continue
        assert len(cs) == 2 and cs[0]["presentation"] == plan_v23.J.first_presentation(
            cs[0]["judge"], cs[0]["answer_id"], pl.seed)
    for i, c in enumerate(calls):
        if c["pair"] is not None and c["position"] == 1:
            assert calls[i - 1]["pair"] == c["pair"]
    # last for each judge
    for key in {c["judge"] for c in cx}:
        parts = [c["part"] for c in calls if c["judge"] == key]
        first = parts.index("crossed")
        assert all(x == "crossed" for x in parts[first:])
    # the labelled answers: blind exists, so only the context call; challenge answers: none
    lab = {r["answer_id"]: r for r in labels}
    for c in cx:
        r = lab.get(c["answer_id"])
        if r is not None:
            assert not r["h60"], c                     # a challenge answer has both presentations in block 5
            assert c["presentation"] == "context" and c["pair"] is None
    assert not [c for c in plan_v23.Plan(p, FRAMES, asg, answers, labels=[]).calls("5") if c["part"] == "crossed"]
    assert not [c for c in plan_v23.Plan(p, FRAMES, asg, answers, labels=labels, crossed=False).calls("5")
                if c["part"] == "crossed"]
    # the size of the design: about 640 answers and 12,800 cells under the shares of Appendix A.1
    n_cells = 20 * len(xa)
    reused = n_cells - len(cx)
    print(f"  plan: {len(xa)} answers, {n_cells} cells, {reused} from blocks 3 and 5, {len(cx)} crossed calls")
    assert 550 <= len(xa) <= 740


# -------------------------------------------------------------------------------------------------- the estimator
def test_hand_case():
    """Two unrelated judges (16 and 17), one answer each, two presentations. The double difference gives delta:
    F(16,a) - F(16,b) - F(17,a) + F(17,b) = 2 delta. Blind 0, 1, 1, 0: delta = -1; in context 1, 1, 1, 0: delta =
    -0.5; delta_change = 0.5. The fit is exact (zero variance); sigma has no sibling cell (not identified)."""
    judge = [16, 16, 17, 17] * 2
    author = [16, 17, 16, 17] * 2
    answer = ["a", "b", "a", "b"] * 2
    prompt = [0, 2, 0, 2] * 2
    pres = ["blind"] * 4 + ["context"] * 4
    y = [0, 1, 1, 0] + [1, 1, 1, 0]
    r = X.fit(judge, author, answer, prompt, pres, y, 4, ["s0", "s0", "s1", "s1"])
    q = r["quantities"]
    assert abs(q["delta_blind"]["est"] + 1) < 1e-12 and abs(q["delta_ctx"]["est"] + 0.5) < 1e-12
    assert abs(q["delta_change"]["est"] - 0.5) < 1e-12
    assert all(q[k]["reason"] == "zero variance" and q[k]["se"] == 0 for k in ("delta_blind", "delta_change"))
    assert q["sigma_blind"]["reason"] == "not identified" and q["sigma_change"]["est"] is None
    assert r["df"] == 1 and r["own_cells"] == {"blind": 2, "context": 2}
    # one more judge (4, unrelated to 16 and 17) and noise: no longer exact, an interval with domain df
    judge2 = judge + [4] * 4
    author2 = author + [16, 17, 16, 17]
    r2 = X.fit(judge2, author2, answer + ["a", "b", "a", "b"], prompt + [0, 2, 0, 2],
               pres + ["blind", "blind", "context", "context"], y + [1, 0, 0, 0], 4, ["s0", "s0", "s1", "s1"])
    assert r2["df"] == 1 and r2["quantities"]["delta_blind"]["est"] is not None


def dense_fit(judge, author, answer, prompt, pres, y, n_prompts, strata):
    """The same model by explicit dummy variables: for each presentation, answer dummies, judge dummies (all but the
    first) and own and sib; the stacked sandwich with the stratified meat by prompt."""
    judge, author, answer = np.asarray(judge), np.asarray(author), np.asarray(answer)
    prompt, pres, y = np.asarray(prompt), np.asarray(pres), np.asarray(y, dtype=float)
    blocks, cols_of = [], {}
    n = len(y)
    width = 0
    designs = []
    for p in X.PRESENTATIONS:
        m = pres == p
        ua, uj = np.unique(answer[m]), np.unique(judge[m])
        D = [np.where(m, (judge == j), 0).astype(float) for j in uj[1:]] + \
            [np.where(m, (answer == a), 0).astype(float) for a in ua]
        own = np.where(m, judge == author, 0).astype(float)
        sib = np.where(m, X.sib_indicator(judge, author), 0)
        designs.append((p, [own, sib] + D))
    cols = []
    for p, ds in designs:
        cols_of[p] = (len(cols), len(cols) + 1)
        cols += ds
    Xm = np.column_stack(cols)
    bread = np.linalg.inv(Xm.T @ Xm)
    b = bread @ Xm.T @ y
    e = y - Xm @ b
    S = np.zeros((n_prompts, Xm.shape[1]))
    np.add.at(S, prompt, Xm * e[:, None])
    strata = np.asarray(strata)
    M = np.zeros((Xm.shape[1], Xm.shape[1]))
    for h in np.unique(strata):
        Sh = S[strata == h]
        Sh = Sh - Sh.mean(0)
        M += len(Sh) / (len(Sh) - 1) * Sh.T @ Sh
    V = bread @ M @ bread
    return b, V, cols_of


def test_against_dummy_variables():
    """On random unbalanced data: the coefficients and the standard errors of fit() equal those of the explicit
    dummy-variable least squares with the stratified cluster sandwich."""
    rng = np.random.default_rng(11)
    rows, P, strata, _ = X.simulate_once(rng, X.SIM_SCENARIOS["effect"], n_per_source=6, missing=0.1)
    r = X.fit(rows["judge"], rows["author"], rows["answer"], rows["prompt"], rows["presentation"], rows["y"], P, strata)
    unrelated = X.sib_indicator(rows["judge"], rows["author"], X.related_pairs()) == 0      # the cells that enter
    assert r["related_cells_left_out"] == int((~unrelated).sum()) > 0
    rows = {k: np.asarray(v)[unrelated] for k, v in rows.items()}
    b, V, cols = dense_fit(rows["judge"], rows["author"], rows["answer"], rows["prompt"], rows["presentation"],
                           rows["y"], P, strata)
    db, sb = cols["blind"]
    dc, sc = cols["context"]
    q = r["quantities"]
    assert abs(q["delta_blind"]["est"] - b[db]) < 1e-9 and abs(q["sigma_ctx"]["est"] - b[sc]) < 1e-9
    assert abs(q["delta_change"]["est"] - (b[dc] - b[db])) < 1e-9
    c = np.zeros(len(b))
    c[dc], c[db] = 1, -1
    assert abs(q["delta_change"]["se"] - math.sqrt(c @ V @ c)) < 1e-9
    c = np.zeros(len(b))
    c[sc], c[sb] = 1, -1
    assert abs(q["sigma_change"]["se"] - math.sqrt(c @ V @ c)) < 1e-9
    assert abs(q["delta_blind"]["se"] - math.sqrt(V[db, db])) < 1e-9
    t = X.stats.t.ppf(0.975, r["df"])
    assert abs(q["delta_change"]["hi"] - q["delta_change"]["est"] - t * q["delta_change"]["se"]) < 1e-12
    assert r["df"] == sum(len(set(np.asarray(rows["prompt"])[np.asarray(strata)[rows["prompt"]] == h])) - 1
                          for h in set(strata))


def test_related_left_out():
    """Fourth round of fresh readings (13 November 2026): the cells of related judge-author pairs that are not
    siblings are left out, so that own and sib are measured against unrelated judges."""
    rel = X.related_pairs()
    for p in ((4, 20), (6, 20), (5, 15), (5, 19), (15, 18), (18, 19), (20, 21), (20, 22), (21, 22), (21, 23), (1, 2)):
        assert p in rel, p
    assert not {(4, 6), (5, 18), (15, 19), (4, 16), (16, 17)} & set(rel)
    rng = np.random.default_rng(5)
    rows, P, strata, _ = X.simulate_once(rng, X.SIM_SCENARIOS["effect"], n_per_source=8, missing=0.05)
    full = X.fit(rows["judge"], rows["author"], rows["answer"], rows["prompt"], rows["presentation"], rows["y"], P,
                 strata)
    keep = X.sib_indicator(rows["judge"], rows["author"], rel) == 0
    sub = {k: np.asarray(v)[keep] for k, v in rows.items()}
    alone = X.fit(sub["judge"], sub["author"], sub["answer"], sub["prompt"], sub["presentation"], sub["y"], P, strata,
                  related=())
    assert alone["related_cells_left_out"] == 0 and full["related_cells_left_out"] == int((~keep).sum()) > 0
    for q, v in full["quantities"].items():
        assert v["est"] == alone["quantities"][q]["est"] and v["se"] == alone["quantities"][q]["se"], q
    with_rel = X.fit(rows["judge"], rows["author"], rows["answer"], rows["prompt"], rows["presentation"], rows["y"],
                     P, strata, related=())
    assert with_rel["quantities"]["delta_blind"]["est"] != full["quantities"]["delta_blind"]["est"]


def test_sib_and_order():
    assert X.sib_indicator([4, 6, 5, 18, 15, 19, 4, 6], [6, 4, 18, 5, 19, 15, 18, 6]).tolist() == [1] * 6 + [0, 0]
    assert X.is_sib(6, 4) and not X.is_sib(4, 4)
    r = X.fit([4, 4, 6, 6, 16, 16] * 2, [4, 6, 4, 6, 4, 6] * 2, ["a", "b", "a", "b", "a", "b"] * 2,
              [0, 2, 0, 2, 0, 2] * 2, ["blind"] * 6 + ["context"] * 6,
              [0, 0, 1, 1, 1, 1] + [0, 1, 1, 1, 1, 1], 4, ["s0", "s0", "s1", "s1"])
    o = r["order_described"]
    assert set(o) == {"blind", "context"} and all(v in (True, False, None) for d in o.values() for v in d.values())


def test_collinear_not_identified():
    """Review round 10, M1: when own and sib are collinear after the fixed effects (here own + sib = 1 in every cell),
    only their difference is identified. Neither coefficient may be reported; the quantities that use them are not
    identified. Undoing the fix (dropping sib and keeping own) gives an estimate near -0.5 with an interval."""
    r = X.fit([4, 6] * 4, [4, 4, 6, 6] * 2, ["a", "a", "b", "b", "c", "c", "d", "d"], [0, 0, 1, 1, 2, 2, 3, 3],
              ["blind"] * 8, [0, 1, 1, 0, 1, 1, 0, 0], 4, [0, 1, 0, 1])
    for name in ("delta_blind", "sigma_blind"):
        d = r["quantities"][name]
        assert d["est"] is None and not d["available"] and d["reason"] == "not identified", (name, d)
    assert r["coefficients"]["delta_blind"] is None and r["coefficients"]["sigma_blind"] is None
    # own varies alone (no sibling cell): delta is identified, sigma is not
    r2 = X.fit([4, 16] * 4, [4, 4, 16, 16] * 2, ["a", "a", "b", "b", "c", "c", "d", "d"], [0, 0, 1, 1, 2, 2, 3, 3],
               ["blind"] * 8, [0, 1, 1, 0, 1, 1, 0, 0], 4, [0, 1, 0, 1])
    assert r2["coefficients"]["delta_blind"] is not None and r2["coefficients"]["sigma_blind"] is None


def test_withhold():
    rows, P, strata, _ = X.simulate_once(np.random.default_rng(4), X.SIM_SCENARIOS["effect"], n_per_source=8)
    r = X.fit(rows["judge"], rows["author"], rows["answer"], rows["prompt"], rows["presentation"], rows["y"], P, strata)
    assert r["quantities"]["delta_change"]["available"]
    X.withhold(r, ("delta_change",))
    d = r["quantities"]["delta_change"]
    assert d["lo"] is None and d["hi"] is None and not d["available"] and "check 5" in d["reason"]
    assert d["est"] is not None and r["quantities"]["delta_blind"]["available"]


# ------------------------------------------------------------------------------------------- canonical verdicts
def test_matrix_rows():
    """Cells read from canonical verdicts: the first of PARTS that holds a final verdict; delivered and fail-closed
    flags; cells without a final verdict counted; judges 22 and 23 never a cell; their answers are."""
    p, answers, labels, asg = world(seed=8)
    pl = plan_v23.Plan(p, FRAMES, asg, answers, labels=labels)
    calls = pl.calls("3") + pl.calls("5")
    rng = random.Random(2)
    canon, skipped = {}, 0
    for c in calls:
        if rng.random() < 0.01:
            skipped += 1
            continue
        st = "valid" if rng.random() < 0.9 else "parse_error"
        canon[f"{c['block']}|{c['part']}|{c['judge']}|{c['answer_id']}|{c['presentation']}"] = {
            "status": st, "harmful_content": (rng.random() < 0.4) if st == "valid" else None}
    pub = {k: dict(v) for k, v in answers.items()}
    rows, counts, ids = X.matrix_rows(canon, pub, p, FRAMES)
    xa = pl.crossed_answers()
    assert counts["answers"] == len(xa) and counts["cells"] == 20 * len(xa) and len(ids) == 100
    assert counts["verdicts"] + counts["cells_without_final_verdict"] == counts["cells"]
    assert {r["judge"] for r in rows} <= {4, 5, 6, 15, 16, 17, 18, 19, 20, 21}
    assert {22, 23} <= {r["author"] for r in rows}
    assert all(r["fail_closed"] == (1 if r["status"] != "valid" else r["delivered"]) for r in rows)
    assert set(counts["verdicts_by_part"]) <= {f"{b}|{q}" for v in X.PARTS.values() for b, q in v}
    assert "5|crossed" in counts["verdicts_by_part"] and "3|own_harmful" in counts["verdicts_by_part"]
    res = X.analyse(rows, ids, FRAMES["harmful"][1])
    assert set(res) == {"delivered", "fail_closed"}
    for sc in res.values():
        assert sc["df"] == 98 and set(sc["quantities"]) == set(X.QUANTITIES)
    print(f"  matrix: {counts['answers']} answers, {counts['verdicts']} verdicts, by part {counts['verdicts_by_part']}")


# ------------------------------------------------------------------------------------------ the coverage check
def test_coverage_short_run():
    """A short run of the check of Appendix A.4 (check 5 in spirit): in both scenarios every 95% interval covers the
    true value at least 0.95 - 3 SE(0.95) of the time, and the estimates are unbiased within sampling error."""
    reps = 400
    res = X.simulate(reps=reps, seed=X.SIM_SEED)
    for name, s in res.items():
        assert 550 <= s["mean_answers"] <= 740
        for q, v in s["quantities"].items():
            assert v["replications_with_interval"] >= reps * 0.99, (name, q, v)
            assert v["coverage"] >= v["threshold"], (name, q, v)
            assert abs(v["mean_estimate"] - v["true"]) < 0.01, (name, q, v)
        print(f"  coverage ({name}, R = {reps}): " + ", ".join(f"{q} {v['coverage']:.3f}"
                                                               for q, v in s["quantities"].items()))


TESTS = [test_selection, test_plan, test_hand_case, test_against_dummy_variables, test_related_left_out, test_sib_and_order, test_collinear_not_identified, test_withhold,
         test_matrix_rows, test_coverage_short_run]

if __name__ == "__main__":
    for fn in TESTS:
        t0 = time.time()
        fn()
        print(f"ok {fn.__name__} ({time.time() - t0:.1f} s)")
    print("all crossed-subset tests passed")
