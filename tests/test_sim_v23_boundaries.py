"""Offline test of the simulation code of protocol v2.3 (Appendix A): the twelve-model panel and the panels without
hosted models, unreachable targets, the pilot planning mapping, fingerprints and seeds, informative screening, the
boundary cases inside a simulated study, and the safe-side design.

Synthetic data only; identifiers and sources of the frames are read, nothing under results/.
Usage: python -I tests/test_sim_v23_boundaries.py      (about 40 seconds)
"""
import pathlib
import sys
import time

import numpy as np
from scipy.special import expit, logit

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
import control_assignment_v23 as CA  # noqa: E402  (production assignment script, read-only use)
import density_v23 as DN  # noqa: E402
import inference_v23 as inf  # noqa: E402
import pilot_planning_v23 as PL  # noqa: E402
import sim_v23_dgp as dgp  # noqa: E402
import sim_v23_labels as SL  # noqa: E402
import sim_v23_registered as SR  # noqa: E402
import sim_v23_safe as SS  # noqa: E402
import sim_v23_tails as TL  # noqa: E402
import yoking  # noqa: E402

PANEL = yoking.load_panel()
D = dgp.design()
DROPS = ((), (22,), (23,), (22, 23))


def test_twelve_model_panel():
    """Sections 6.3 and 6.5 (decision D15): five instruction-tuned and seven refusal-removed models."""
    assert D["judges"] == PANEL["groups"]["instruct_open"] + PANEL["groups"]["refusal_removed"]
    assert len(D["judges"]) == 12 and (D["group"] == "i").sum() == 5 and (D["group"] == "r").sum() == 7
    assert D["P"] == 300 and np.bincount(D["strata"]).tolist() == [150, 150]
    for p in range(D["P"]):                     # every answer has one control judge, of its group, not itself
        assert sorted(D["ctrl"][:, p]) == list(range(12))
        assert (D["group"][D["ctrl"][:, p]] == D["group"]).all() and (D["ctrl"][:, p] != np.arange(12)).all()
        assert (D["ctrl"][D["auth"][:, p], p] == np.arange(12)).all()


def test_design_matches_production_assignment():
    """design(drop, frame) reproduces scripts/control_assignment_v23.py block by block (Section 6.5)."""
    blocks = {(b["group"], b["frame"]): b["assignment"] for b in CA.build()["blocks"]}
    frames = dgp.frames_v23.frames()
    for drop in DROPS:
        for frame in ("harmful", "safe"):
            Dd = dgp.design(drop=drop, frame=frame)
            assert Dd["judges"] == [m for m in D["judges"] if m not in drop]
            for group in ("instruct_open", "refusal_removed"):
                block = dgp.block_label(group, list(drop), PANEL["hosted_primary"])
                asg = blocks[(block, frame)]
                for p, pid in enumerate(frames[frame][0]):
                    for a, k in asg[pid].items():
                        assert Dd["judges"][Dd["ctrl"][Dd["judges"].index(int(a)), p]] == int(k)
    C = SS.commercial_design()
    asg = blocks[("commercial", "safe_commercial_controls")]
    ids = frames["safe_commercial_controls"][0]
    assert C["matched"] == len(ids) == 30 and C["P"] == 90
    for p, pid in enumerate(ids):
        for a, k in asg[pid].items():
            assert C["judges"][C["ctrl"][C["judges"].index(int(a)), p]] == int(k)
    assert (C["ctrl"][:, 30:] == np.arange(len(C["judges"]))[:, None]).all()      # placeholder, never read


def test_drop_only_hosted():
    try:
        dgp.design(drop=(4,))
    except ValueError:
        pass
    else:
        raise AssertionError("a model that is not hosted was left out")


def test_het_rates():
    """A.2's rates for six refusal-removed models; the same range and mean for seven (and five)."""
    assert dgp.het_rates(dgp.design(drop=(22,))) == {"fail_i": [0.05, 0.1, 0.15, 0.2, 0.25],
                                                     "fail_r": [0.45, 0.55, 0.65, 0.75, 0.85, 0.95]}
    r = dgp.het_rates(D)
    assert len(r["fail_r"]) == 7 and r["fail_r"][0] == 0.45 and r["fail_r"][-1] == 0.95
    assert abs(np.mean(r["fail_r"]) - 0.70) < 1e-9
    q = dgp.panel_quality(D, dict(dgp.BASE, **r, h_pattern="aligned"))
    assert np.allclose(q["rates"], r["fail_i"] + r["fail_r"])
    assert (np.sign(q["h"][5:]) == -np.sign(np.array(r["fail_r"]) - 0.70)).all()


def test_root_reports_unreachable():
    x, miss = dgp._root(lambda v: v - 1.0, 1.0)
    assert miss is None and abs(x - 1.0) < 1e-5
    x, miss = dgp._root(lambda v: v - 20.0, 20.0)
    assert x == 12.0 and miss == {"target": 20.0, "nearest": 12.0, "shift": 12.0}
    x, miss = dgp._root(lambda v: v + 30.0, -30.0)
    assert x == -12.0 and miss["nearest"] == -12.0


def test_fail_intercept_raises():
    for target in (0.0, 1.0):
        try:
            dgp.fail_intercept(target)
        except ValueError:
            pass
        else:
            raise AssertionError("an unreachable rate was clipped silently")
    assert abs(np.mean(expit(dgp.fail_intercept(0.3) + np.random.default_rng(1).normal(0, 0.8, 200000))) - 0.3) < 1e-6


def test_calibrate_reports_unreachable():
    """A beta of -0.9 and a discordance of 90% cannot be reached: both are listed with the nearest value."""
    sc = dict(dgp.BASE, beta=-0.9, q0=0.9)
    q = dgp.panel_quality(D, sc)
    g, rho, diag = dgp.calibrate(np.random.default_rng(3), D, sc, q, reps=20)
    names = {u["name"]: u for u in diag["unreached"]}
    assert set(names) == {"beta", "q0"}
    assert names["beta"]["target"] == -0.9 and names["beta"]["nearest"] > -0.9 and g["blind"] == -12.0
    assert rho == 0.0 and names["q0"]["nearest"] < 0.9
    g, rho, diag = dgp.calibrate(np.random.default_rng(3), D, dict(dgp.BASE), q, reps=20)
    assert diag["unreached"] == [] and 0 < rho < 1


def test_calibrate_same_as_expected():
    """calibrate() writes out the expected flags of expected() for speed; the shifts it finds are those that the
    plain use of expected() gives, for every kind of target and invalid-verdict setting."""
    for over in ({}, dict(theta=-0.05, iota=-0.05, inv="harm"), dict(beta=-0.07, mode="all", inv="10_15"),
                 dict(beta=-0.9)):
        sc = dict(dgp.BASE, **over)
        q = dgp.panel_quality(D, sc)
        g, _, diag = dgp.calibrate(np.random.default_rng(12), D, sc, q, reps=10)
        L = dgp.draw_latent(np.random.default_rng(12), 10, D, sc, q)
        S, den = L["screen"], float(L["screen"].sum())
        plain = dict(blind=0.0, on=0.0, ctrl=0.0)

        def f(key, target, pick):
            def fn(x):
                e = dgp.expected(L, sc, dict(plain, **{key: x}))
                return float((S * pick(e)).sum()) / den - target
            return fn

        plain["blind"] = dgp._root(f("blind", sc["beta"], lambda e: e[0] - e[2]), sc["beta"])[0]
        plain["on"] = dgp._root(f("on", sc["theta"], lambda e: e[1] - e[0]), sc["theta"])[0]
        plain["ctrl"] = dgp._root(f("ctrl", sc["theta"] - sc["iota"], lambda e: e[3] - e[2]),
                                  sc["theta"] - sc["iota"])[0]
        assert g == plain, (over, g, plain)


def test_informative_screen():
    """Run (b): P(S = 1) = expit(a_Y + v) with average shares 0.9 and 0.2, and the screen follows the answer
    effect v, which also enters every blind verdict."""
    a0, a1 = dgp.screen_intercepts(0.9, 0.2)
    v = np.random.default_rng(2).normal(0, dgp.SD_ANSWER, 2_000_000)
    assert abs(expit(a1 + v).mean() - 0.9) < 1e-3 and abs(expit(a0 + v).mean() - 0.2) < 1e-3
    out = {}
    for mode in ("independent", "informative"):
        sc = dict(dgp.BASE, screen_mode=mode)
        L = dgp.draw_latent(np.random.default_rng(4), 6, D, sc, dgp.panel_quality(D, sc))
        f, s = L["fail"], L["screen"]
        assert abs(s[f].mean() - 0.9) < 0.02 and abs(s[~f].mean() - 0.2) < 0.02
        out[mode] = np.corrcoef(s[~f], L["eta_a"][~f])[0, 1]
    assert out["informative"] > 0.08 and abs(out["independent"]) < 0.04


def pilot_counts(share, flag, answers=150, positive=60):
    return {"models": {str(m): {"answers": answers, "screen_positive": int(round(s * answers))}
                       for m, s in zip(D["judges"], share)},
            "judges": {str(m): {"screen_positive": positive, "blind_flags": int(round(f * positive))}
                       for m, f in zip(D["judges"], flag)}}


def test_pilot_mapping():
    share = [0.10, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.95, 0.60, 0.70, 0.50]
    flag = [0.50, 0.60, 0.70, 0.80, 0.85, 0.60, 0.70, 0.75, 0.80, 0.65, 1.00, 0.70]
    pilot = pilot_counts(share, flag)
    scen, report = PL.points(pilot, D)
    assert list(scen) == ["pilot_0.9_0.2", "pilot_1_0", "pilot_0.7_0.4"]
    s, f, notes = PL.observed(pilot, D)
    assert notes == [] and np.allclose(s, np.round(np.array(share) * 150) / 150)
    # (a, b) = (1, 0): the rate is the share; every share in [1%, 99%] is reached
    one = report["points"]["pilot_1_0"]
    assert np.allclose([one["rates"][str(m)] for m in D["judges"]], s)
    assert not [u for u in one["unreached"] if u["what"] == "screen-positive share"]
    # (0.9, 0.2): a share of 0.10 lies below b; it is listed with the nearest share reached, 0.9 x 1% + 0.2 x 99%
    low = [u for u in report["points"]["pilot_0.9_0.2"]["unreached"] if u.get("model") == 4][0]
    assert low["rate_used"] == 0.01 and abs(low["nearest"] - (0.9 * 0.01 + 0.2 * 0.99)) < 1e-12
    assert scen["pilot_0.9_0.2"]["target_not_reproduced"] and scen["pilot_0.9_0.2"]["fail_i"][0] == 0.01
    # a blind flag rate of 100% is above what any sensitivity gives: listed, the highest sensitivity used
    top = [u for u in one["unreached"] if u.get("judge") == 22][0]
    assert top["sensitivity_used"] == 0.99 and top["nearest"] < 1.0
    # the sensitivities found reproduce the blind flag rates (the model of the mapping)
    sp = dgp.judge_accuracy(D)[1]
    for name, (a, b) in zip(scen, PL.GRID):
        sc, rep = scen[name], report["points"][name]
        missed = {u.get("judge") for u in rep["unreached"] if u["what"] == "blind flag rate"}
        rates = np.array(sc["fail_i"] + sc["fail_r"])
        for j, m in enumerate(D["judges"]):
            if m not in missed:
                got = PL.blind_rate(sc["se_judge"][j], sp[j], rates[j], a, b, 0.03)
                assert abs(got - f[j]) < 1e-8, (name, m, got, f[j])
        assert sc["screen_se"] == a and sc["screen_sp"] == 1 - b and len(sc["se_judge"]) == 12


def test_pilot_small_counts():
    share, flag = [0.5] * 12, [0.7] * 12
    pilot = pilot_counts(share, flag)
    pilot["models"]["5"] = {"answers": 29, "screen_positive": 29}            # fewer than 30: group share
    pilot["judges"]["18"] = {"screen_positive": 19, "blind_flags": 0}        # fewer than 20: group flag rate
    del pilot["models"]["23"]                                                # no record: no pilot answer
    s, f, notes = PL.observed(pilot, D)
    group_i = (75 * 4 + 29) / (150 * 4 + 29)
    assert abs(s[D["judges"].index(5)] - group_i) < 1e-12
    assert abs(s[D["judges"].index(23)] - 0.5) < 1e-12
    group_r = (42 * 6 + 0) / (60 * 6 + 19)
    assert abs(f[D["judges"].index(18)] - group_r) < 1e-12
    assert {(n["kind"], n.get("model", n.get("judge"))) for n in notes} == {("share", 5), ("share", 23), ("flag", 18)}


def test_pilot_quadrature():
    z = np.random.default_rng(6).normal(0, PL.SD_BLIND, 2_000_000)
    for p in (0.05, 0.3, 0.8, 0.97):
        assert abs(PL._mean_expit(p) - expit(logit(p) + z).mean()) < 1e-3


def test_pilot_grids():
    pilot = pilot_counts([0.5] * 12, [0.7] * 12)
    rs1 = SR.grid("pilot_rs1", D, pilot)
    rs2 = SR.grid("pilot_rs2", D, pilot)
    rs3 = SL.grid("pilot", D, pilot)
    assert len(rs1) == 15 and len(rs2) == 6 and len(rs3) == 6
    assert rs1["pilot_1_0|bound"]["beta"] == -0.07 and rs1["pilot_1_0|both"]["iota"] == -0.05
    assert rs2["pilot_0.7_0.4_aligned_all|zero"]["shifts"] == "zero"
    q = dgp.panel_quality(D, rs1["pilot_1_0|null"])
    assert np.allclose(q["se"], rs1["pilot_1_0|null"]["se_judge"])


def test_grid_sizes():
    assert len(SR.grid("rs1", D)) == 35 and len(SR.grid("rs2", D)) == 19
    aligned = SR.grid("rs2_aligned", D)
    assert sorted(aligned) == sorted(k for k in SR.grid("rs2", D) if k.startswith("het_aligned")) and len(aligned) == 7
    rare = SR.grid("rare", D)
    assert len(rare) == 6
    for k in SR.RARE:
        sc = rare[f"rare_{k}|null"]
        assert sc["screen_se"] == sc["screen_sp"] == 1.0 and sc["fail_i"] == sc["fail_r"]
        assert abs(sc["fail_i"] * 12 * 300 - k) < 1e-6 and rare[f"rare_{k}|bound"]["beta"] == -0.07
    assert len(SL.grid("informative", D)) == 8 and len(SL.grid("rs3", D)) == 7
    assert all(v["screen_mode"] == "informative" and len(v["fail_r"]) == 7 for v in SL.grid("informative", D).values())


def test_streams():
    """A second run keeps the calibration and the reference streams and changes only the replication stream."""
    a, b = SR.streams("baseline|null", SR.BASE_SEED), SR.streams("baseline|null", 20261124)
    draws = [[r.random(4).tolist() for r in s] for s in (a, b)]
    assert draws[0][0] == draws[1][0] and draws[0][1] == draws[1][1] and draws[0][2] != draws[1][2]
    c = SR.streams("baseline|both", SR.BASE_SEED)
    assert c[0].random(4).tolist() != SR.streams("baseline|null", SR.BASE_SEED)[0].random(4).tolist()


def test_fingerprint_rejects():
    sc = SR.grid("smoke", D)["baseline|null"]
    args = dict(reps=10, flips=9, clusters=1000, cal_reps=10, chunk=10, seed=SR.BASE_SEED)
    row = dict(name="baseline|null", scenario=sc, **args)
    row["fingerprint"] = SR.fingerprint(row["name"], sc, D, **args)
    keep, rejected = SR.accepted([row], D)
    assert keep == [row] and rejected == []
    for change in (dict(scenario=dict(sc, theta=-0.05)), dict(seed=20261124), dict(fingerprint=None),
                   dict(reps=11)):
        keep, rejected = SR.accepted([dict(row, **change)], D)
        assert keep == [] and rejected == ["baseline|null"], change
    keep, rejected = SR.accepted([row], dgp.design(drop=(22,)))      # another panel: another fingerprint
    assert keep == [] and rejected == ["baseline|null"]
    other = SR.fingerprint(row["name"], sc, D, **dict(args, seed=20261124))
    assert other != row["fingerprint"]
    old = dict(row)
    del old["chunk"]                                                 # a row written before fingerprints
    assert SR.accepted([old], D) == ([], ["baseline|null"])


def test_same_iota_check():
    rng = np.random.default_rng(8)
    st = np.repeat([0, 1], 150)
    n = rng.binomial(5, 0.3, (3, 300)).astype(float)
    x = rng.binomial(n.astype(int), 0.2) - rng.binomial(n.astype(int), 0.2)
    r = inf.cluster_ratio(x, n, st)
    SR.same_iota(r, r)
    bad = dict(r, est=r["est"] + np.array([0, 1e-6, 0]))
    try:
        SR.same_iota(bad, r)
    except RuntimeError:
        pass
    else:
        raise AssertionError("a differing second computation of iota_S was accepted")
    flags = dict(r, available=~r["available"])
    try:
        SR.same_iota(flags, r)
    except RuntimeError:
        pass
    else:
        raise AssertionError("differing boundary flags were accepted")


def test_rare_flag_study():
    """Run (e): about two screen-positive answers per study. Replications with a zero denominator, a zero variance
    and judges without a control answer are counted, never rejected, and do not stop the run."""
    sc = SR.grid("rare", D)["rare_2|null"]
    q = dgp.panel_quality(D, sc)
    g = dict(blind=0.0, on=0.0, ctrl=0.0)
    rep = SR.one_chunk(np.random.default_rng(9), 300, D, sc, q, g, 0.5, 9)
    zero_den = ~np.isfinite(rep["th_est"])
    assert 10 < zero_den.sum() < 90                       # P(no screen-positive answer) = exp(-2), about 14%
    assert rep["th_zv"].sum() > 0 and rep["lacking"].any()
    for t, k in (("p1", "th"), ("p2", "io"), ("p3", "be")):
        assert not rep[t][~np.isfinite(rep[k + "_p" if t != "p3" else k + "_lb99"])].any()
    ref = {k: (0.0, 0.0) for k in SR.STATS}
    s = SR.summarise(rep, ref, D["judges"])
    b = s["boundary"]
    assert b["zero_denominator"] == int(zero_den.sum()) and b["replications"] == 300
    for t in ("p1", "p2", "p3"):
        assert b["carried_out"][t] + b["zero_variance"][t] + b["zero_denominator"] == 300
    assert b["iw_not_estimable_with_io"] > 0 and b["judges_without_control"]
    assert s["th"]["with_interval"] == b["carried_out"]["p1"]
    assert s["registered"]["any"] <= (b["carried_out"]["p1"] + b["carried_out"]["p2"]) / 300


def test_safe_side_chunk():
    """Run (d): statistics over all answers and among screen-negative answers for both panels; no interval where
    the variance is zero or the denominator empty."""
    sc = SS.SETTINGS["safe|inv_3"]
    for scope, Dd, seed in (("primary", dgp.design(frame="safe"), dgp.PANEL_SEED),
                            ("commercial", SS.commercial_design(), SS.COMMERCIAL_PANEL_SEED)):
        q = dgp.panel_quality(Dd, sc, seed=seed)
        out = SS.one_chunk(np.random.default_rng(10), 40, Dd, sc, q, dict(blind=0.0, on=0.0, ctrl=0.0), 0.5, scope)
        keys = [k for k, *_ in SS.specs(scope, Dd)]
        assert sorted(out) == sorted(keys) and len(keys) == (12 if scope == "primary" else 14)
        for k, v in out.items():
            has = np.isfinite(v["lo"])
            assert not (has & v["zv"]).any() and not (has & ~np.isfinite(v["est"])).any()
            if not k.endswith(("|iw", "|ic")):      # iota_W, iota_C: also not estimable when a judge lacks a control
                assert (np.isfinite(v["est"]) | (v["den"] == 0)).all()


def test_label_design_drop():
    full, small = SL.label_design(), SL.label_design((22, 23))
    assert 22 in full["primary"] and 23 in full["group_of"]
    assert 22 not in small["primary"] and 23 not in small["group_of"]
    assert small["groups"]["refusal_removed"] == [6, 18, 19, 20, 21]
    assert small["groups"]["commercial"] == full["groups"]["commercial"]


def test_a4_checks():
    """Which checks of Appendix A.4 a row carries, and the thresholds of the table (R = 10,000 and 40,000)."""
    s = {"registered": {"any": 0.03, "holm_theta": 0.02, "holm_iota": 0.05}, "p3_reject": 0.02,
         **{k: {"cover95": 0.95, "with_interval": 10000} for k in ("th", "io", "iw", "be")}}
    base = dgp.BASE

    def kinds(name, sc):
        return sorted({c["check"] for c in SR.a4_checks(name, sc, s, 10000)})

    assert kinds("baseline|null", dict(base)) == [1, 4]
    assert kinds("baseline|bound", dict(base, beta=-0.07)) == [1, 3, 4]
    assert kinds("baseline|theta", dict(base, theta=-0.05)) == [2, 4]
    assert kinds("baseline|iota", dict(base, iota=-0.05)) == [2, 4]
    assert kinds("baseline|both", dict(base, theta=-0.05, iota=-0.05)) == [4]
    assert kinds("het|zero", dict(base, shifts="zero")) == [4]
    assert kinds("literal_null|zero", dict(base, shifts="zero", sd_common=0.0, sd_own=0.0)) == [1, 4]
    assert kinds("rare_2|bound", dict(base, beta=-0.07)) == [1, 3]       # run (e): coverage without threshold
    c = {x["check"]: x for x in SR.a4_checks("baseline|theta", dict(base, theta=-0.05), s, 10000)}
    assert c[2]["what"].startswith("P2") and c[2]["made"] and not c[2]["passed"]      # 5.0% > 4.59%
    c = {x["check"]: x for x in SR.a4_checks("baseline|iota", dict(base, iota=-0.05), s, 10000)}
    assert c[2]["what"].startswith("P1") and c[2]["passed"]
    for p, R, upper, want in ((0.04, 10000, True, 0.0459), (0.01, 10000, True, 0.0130), (0.95, 10000, False, 0.9435),
                              (0.04, 40000, True, 0.0429), (0.01, 40000, True, 0.0115), (0.95, 40000, False, 0.9467)):
        assert round(SR.a4_limit(p, R, upper), 4) == want, (p, R)
    rs3 = {k: {"reportable": 999, "cover95": 0.90, "exact": {"reportable": 5000, "cover95": 0.951}} for k in SL.STATS}
    checks = {x["what"]: x for x in SL.check5(rs3)}
    assert set(checks) == set(SL.CHECKED) and "det_change_own|all" not in checks
    assert checks["harm_share_pos|all"]["made"] and checks["harm_share_pos|all"]["passed"]
    assert not checks["det_change_own_reg|all"]["made"] and checks["det_change_own_reg|all"]["R"] == 999


def test_registered_interval():
    """sim_v23_labels.registered_interval(), the one rule of the Section 9.5 intervals (run_scenario and
    missing_labels_v23 call it): each kind of interval against its formula, and each case without an interval."""
    rng = np.random.default_rng(5)
    D = dgp.design()
    J, P = len(D["judges"]), D["P"]
    S = (rng.random((J, P)) < 0.6).astype(float)
    Y = (rng.random((J, P)) < 0.5).astype(float)
    Wt = np.where(rng.random((J, P)) < 0.3, 1.0 + rng.random((J, P)) * 4, 0.0)
    A1, A2, C1, C2 = ((rng.random((J, P)) < 0.4).astype(float) for _ in range(4))
    cells, _ = SL.estimates(Wt, S, Y, A1, A2, C1, C2, D)
    st = D["strata"]
    x, n, kish, ncl = cells["det_blind_own|all"]
    c = inf.cluster_ratio(x, n, st)
    r = SL.registered_interval(cells, "det_blind_own|all", st)
    lo, hi = inf.exact_interval(c["est"], inf.effective_n(c, kish, ncl))
    assert r["kind"] == "effective-n Clopper-Pearson" and (r["lo"], r["hi"]) == (float(lo), float(hi))
    x, n, _, _ = cells["det_change_own_reg|all"]
    c = inf.cluster_ratio(x, n, st)
    r = SL.registered_interval(cells, "det_change_own_reg|all", st)
    assert r["kind"] == "cluster ratio t" and (r["lo"], r["hi"]) == tuple(float(v) for v in inf.interval(c))
    wide = []
    for k in ("harm_share_pos|all", "harm_share_neg|all"):
        x, n, kish, ncl = cells[k]
        ck = inf.cluster_ratio(x, n, st)
        w_lo, w_hi = inf.exact_interval(ck["est"], inf.effective_n(ck, kish, ncl), level=0.975)
        wide.append((n.sum() * w_lo, n.sum() * w_hi))
    r = SL.registered_interval(cells, "screen_pass_harm|all", st)
    assert r["kind"].startswith("propagated") and np.allclose((r["lo"], r["hi"]), inf.share_of_two(*wide),
                                                               rtol=0, atol=1e-15)
    r = SL.registered_interval(cells, "screen_pass_harm|all", st, shares_reported=False)
    assert np.isnan(r["lo"]) and r["no_interval"] == "a harmful share is not reported" and np.isfinite(r["est"])
    r = SL.registered_interval(cells, "det_change_own|all", st)               # a direct estimator
    assert r["kind"] is None and np.isnan(r["hi"]) and r["no_interval"].startswith("direct estimator")
    flat = SL.estimates(Wt, S, Y, A1, A1, C1, C1, D)[0]                         # no flag changes: zero variance
    r = SL.registered_interval(flat, "det_change_own_reg|all", st)
    assert r["est"] == 0.0 and np.isnan(r["lo"]) and r["no_interval"].startswith("zero estimated variance")
    none = SL.estimates(Wt, np.zeros_like(S), Y, A1, A2, C1, C2, D)[0]          # no screen-positive answer
    r = SL.registered_interval(none, "det_blind_own|all", st)
    assert np.isnan(r["est"]) and np.isnan(r["lo"]) and r["no_interval"].startswith("not estimable")


def test_tails_p3_support():
    """Run (k), part 1 (code review round 12): in every row the totals stay within |X_p| <= N_p = 6 and have mean
    -0.42 (beta_S = -0.07); the background change is disjoint from the deficit, so -7 cannot occur; a row that is not
    a distribution is refused."""
    rng = np.random.default_rng(12)
    for row in TL.P3_ROWS:
        X = TL.p3_draw(rng, 400, 300, row["m"], row["bg"])
        assert np.abs(X).max() <= 6 and abs(X.mean() + 0.42) < 0.02, (row, X.min(), X.mean())
        if row["bg"]:
            assert set(np.unique(X)) == {-float(row["m"]), -1.0, 0.0, 1.0}
    try:
        TL.p3_draw(rng, 2, 300, 1, 0.7)
        raise AssertionError("pi + bg > 1 accepted")
    except ValueError:
        pass


def test_tails_carried_out_not_dense():
    """Run (k), part 3 (code review round 12): constant totals X = 1 with N = 6 on every prompt are dense (share of
    nonzero totals 1) but have no variance, so P1 and P2 are not carried out; the count of carried-out tests reads
    p*_carried_out, not p*_dense."""
    st = np.asarray(D["strata"])
    X, N = np.ones((1, D["P"])), np.full((1, D["P"]), 6.0)
    r = inf.cluster_ratio(X, N, st)
    zero = inf.cluster_ratio(np.zeros((1, D["P"])), N, st)
    c = TL.d20_counts(DN.decide(r, r, zero, X, X, N))
    assert c == {"p1": (0, 1, 1.0), "p2": (0, 1, 1.0)}, c


def test_tails_rs1_targets_reached():
    """Run (k), part 3 (code review round 12): with the shocks of RS1_SD the target discordance is reached (floor 0
    at q0 = 0, below 0.025 at q0 = 0.025), and a row at the baseline shocks with q0 = 0 is refused instead of running
    at the floor."""
    for name in ("q0_0.0|theta", "q0_0.025|null"):
        sc, q, g, rho, cal = TL.calibrated(D, name, np.random.default_rng(3), reps=200)
        assert cal["unreached"] == [] and cal["q0_floor"] <= cal["q0_target"] and 0 <= rho <= 1, (name, cal)
        if cal["q0_target"] == 0:
            assert cal["q0_floor"] == 0 and rho == 1
    TL.RS1["_baseline_q0_0"] = dict(q0=0.0)
    try:
        TL.calibrated(D, "_baseline_q0_0", np.random.default_rng(3), reps=200)
        raise AssertionError("an unreached q0 was accepted")
    except ValueError as e:
        assert "q0" in str(e)
    finally:
        del TL.RS1["_baseline_q0_0"]


for name, fn in sorted(globals().items()):
    if name.startswith("test_"):
        t0 = time.time()
        fn()
        print("ok", name, f"({time.time() - t0:.1f} s)", flush=True)
print("all simulation tests passed")
