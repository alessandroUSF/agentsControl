"""Offline test of the registered inference (protocol v2.3, Section 8) and its boundary cases (Sections 8.1, 8.2, 8.5).

Synthetic counts only; nothing under results/ is read.
Usage: python -I tests/test_inference_v23.py
"""
import pathlib
import sys

import numpy as np
from scipy import stats

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
import inference_v23 as inf  # noqa: E402

P = 300
STRATA = np.repeat([0, 1], P // 2)
RNG = np.random.default_rng(20261111)


def data(rng=RNG, j=12, p=P):
    """Per-prompt totals of a screened difference: N screen-positive answers, X their summed changes."""
    n = rng.binomial(j, 0.3, p)
    x = rng.binomial(n, 0.2) - rng.binomial(n, 0.25)
    return x.astype(np.float64), n.astype(np.float64)


def direct(x, n, strata=STRATA):
    """The ratio, its standard error and degrees of freedom written out from Section 8.1 (no shared code). The
    variance runs over every prompt of a source; the degrees of freedom count, in each source, the prompts with at
    least one answer of the statistic, less one (none for a source without such a prompt), and are at least 1."""
    est = x.sum() / n.sum()
    e = x - est * n
    var, df = 0.0, 0
    for h in np.unique(strata):
        eh = e[strata == h]
        k = eh.size
        var += k / (k - 1) * ((eh - eh.mean()) ** 2).sum()
        df += max(int((n[strata == h] != 0).sum()) - 1, 0)
    return est, np.sqrt(var) / n.sum(), max(df, 1)


def flags(r):
    return bool(r["estimable"]), bool(r["zero_variance"]), bool(r["available"])


def not_available(r):
    """No p-value, no interval and no bound (Section 8.1)."""
    lo, hi = inf.interval(r)
    return (np.isnan(inf.p_two_sided(r)) and np.isnan(lo) and np.isnan(hi) and np.isnan(inf.lower_bound(r)))


def test_regular_case():
    x, n = data()
    r = inf.cluster_ratio(x, n, STRATA)
    est, se, df = direct(x, n)
    assert flags(r) == (True, False, True)
    assert np.isclose(r["est"], est, rtol=1e-12) and np.isclose(r["se"], se, rtol=1e-12) and r["df"] == df
    assert df == int((n > 0).sum()) - 2 and df < P - 2              # a few prompts have no screen-positive answer
    p = inf.p_two_sided(r)
    assert np.isclose(p, 2 * stats.t.sf(abs(est / se), df), rtol=1e-10)
    lo, hi = inf.interval(r)
    q = stats.t.ppf(0.975, df)
    assert np.isclose(lo, est - q * se) and np.isclose(hi, est + q * se)
    assert np.isclose(inf.lower_bound(r), est - stats.t.ppf(0.99, df) * se)
    assert inf.reason(r) == ""


def test_zero_denominator():
    """An empty cell: no screen-positive answer. Not estimable; the test is not carried out and not rejected."""
    x, n = np.zeros(P), np.zeros(P)
    r = inf.cluster_ratio(x, n, STRATA)
    assert flags(r) == (False, False, False)
    assert np.isnan(r["est"]) and np.isnan(r["se"]) and r["den"] == 0
    assert not_available(r)
    assert inf.reason(r) == "zero denominator"
    t = inf.registered_tests(r, r, r)
    assert not (t["p1"] or t["p2"] or t["p3"])
    assert not (t["p1_carried_out"] or t["p2_carried_out"] or t["p3_carried_out"])


def test_empty_stratum():
    """No screen-positive answer in one source only: the statistic exists; that source adds no variance and no
    degree of freedom (Section 8.1)."""
    x, n = data()
    x[STRATA == 1], n[STRATA == 1] = 0, 0
    r = inf.cluster_ratio(x, n, STRATA)
    est, se, df = direct(x, n)
    assert flags(r) == (True, False, True) and r["df"] == df == int((n[STRATA == 0] > 0).sum()) - 1
    assert np.isclose(r["est"], est) and np.isclose(r["se"], se)


def test_domain_degrees_of_freedom():
    """Section 8.1: the degrees of freedom are sum_h (m_h - 1), m_h the prompts of source h with an answer of the
    statistic; the variance still runs over every prompt. The p-value, the interval and the bound use them."""
    rng = np.random.default_rng(23)
    n = rng.integers(1, 6, P).astype(np.float64)
    x = rng.binomial(n.astype(int), 0.3) - rng.binomial(n.astype(int), 0.3).astype(np.float64)
    full = inf.cluster_ratio(x, n, STRATA)
    assert full["df"] == P - 2 == 298
    x[:100], n[:100] = 0, 0                                         # 50 prompts of source 0 and 150 of source 1 left
    r = inf.cluster_ratio(x, n, STRATA)
    est, se, df = direct(x, n)
    assert r["df"] == df == 49 + 149 and np.isclose(r["se"], se, rtol=1e-12)
    t = r["est"] / r["se"]
    assert np.isclose(inf.p_two_sided(r), 2 * stats.t.sf(abs(t), 198), rtol=1e-12)
    lo, hi = inf.interval(r)
    q = stats.t.ppf(0.975, 198)
    assert np.isclose(lo, r["est"] - q * r["se"]) and np.isclose(hi, r["est"] + q * r["se"])
    assert np.isclose(inf.lower_bound(r), r["est"] - stats.t.ppf(0.99, 198) * r["se"])
    x[150:299], n[150:299] = 0, 0                                   # one prompt left in source 1: it adds nothing
    r = inf.cluster_ratio(x, n, STRATA)
    assert r["df"] == direct(x, n)[2] == 49
    X = np.stack([x, x]); N = np.stack([n, n])                     # a leading axis: one value per replication
    N[1, 100:140], X[1, 100:140] = 0, 0
    r = inf.cluster_ratio(X, N, STRATA)
    assert r["df"].tolist() == [49, 9]


def test_zero_variance_no_change():
    """Screen-positive answers exist but no flag changes anywhere: estimate 0, no p-value, no interval."""
    _, n = data()
    r = inf.cluster_ratio(np.zeros(P), n, STRATA)
    assert flags(r) == (True, True, False)
    assert r["est"] == 0 and r["se"] == 0
    assert not_available(r) and inf.reason(r) == "zero variance"


def test_zero_variance_every_answer_changes():
    """Every screen-positive answer gains (or loses) a flag: estimate +1 (or -1), zero variance."""
    _, n = data()
    for sign in (1, -1):
        r = inf.cluster_ratio(sign * n, n, STRATA)
        assert flags(r) == (True, True, False) and r["est"] == sign
        assert not_available(r)


def test_zero_variance_with_rounding():
    """The same ratio on every prompt, where the computed residuals carry a rounding error: still zero variance
    (the rule looks at the residuals with a floating-point tolerance, Section 8.1), and a small genuine variation is
    not mistaken for it."""
    found = 0
    for k in (3, 7):
        m = np.arange(1, P + 1, dtype=np.float64) % k + 1
        for a, b in ((1, 3), (2, 7), (9, 14), (13, 23), (21, 23), (15, 22)):
            x, n = a * m, b * m
            e = x - x.sum() / n.sum() * n
            centred = max(np.abs(e[STRATA == h] - e[STRATA == h].mean()).max() for h in (0, 1))
            found += bool(centred > 0)              # a rounding residue: the plain variance would be about 1e-28
            r = inf.cluster_ratio(x, n, STRATA)
            assert flags(r) == (True, True, False) and np.isclose(r["est"], a / b)
            assert not_available(r)
    assert found, "no case with a rounding residue was found; the test does not exercise the tolerance"
    # the smallest genuine variation of integer data: one answer more on one prompt
    n = np.full(P, 23.0)
    x = n.copy()
    x[0] -= 1
    r = inf.cluster_ratio(x, n, STRATA)
    assert flags(r) == (True, False, True) and r["se"] > 0 and np.isfinite(inf.p_two_sided(r))


def test_leading_axis():
    """A leading replication axis mixes the three cases; each row equals its own computation."""
    x, n = data()
    X = np.stack([x, np.zeros(P), n, np.zeros(P)])
    N = np.stack([n, n, n, np.zeros(P)])
    r = inf.cluster_ratio(X, N, STRATA)
    assert r["estimable"].tolist() == [True, True, True, False]
    assert r["zero_variance"].tolist() == [False, True, True, False]
    assert r["available"].tolist() == [True, False, False, False]
    one = inf.cluster_ratio(x, n, STRATA)
    assert np.isclose(r["est"][0], one["est"]) and np.isclose(r["se"][0], one["se"])
    p = inf.p_two_sided(r)
    assert np.isfinite(p[0]) and np.isnan(p[1:]).all()
    assert inf.reason(r).tolist() == ["", "zero variance", "zero variance", "zero denominator"]


def test_holm_two():
    """Section 8.2: Holm at family level .04; a test not carried out (NaN) is not rejected and the other test is
    compared with .02."""
    nan = np.nan
    cases = [((0.01, 0.03), (True, True)), ((0.03, 0.01), (True, True)), ((0.03, 0.03), (False, False)),
             ((0.015, 0.05), (True, False)), ((nan, 0.015), (False, True)), ((nan, 0.03), (False, False)),
             ((0.001, nan), (True, False)), ((nan, nan), (False, False)), ((0.02, 0.02), (True, True))]
    for (p1, p2), want in cases:
        r1, r2 = inf.holm_two(p1, p2)
        assert (bool(r1), bool(r2)) == want, (p1, p2, r1, r2)
    r1, r2 = inf.holm_two(np.array([nan, 0.01]), np.array([0.03, 0.03]))
    assert r1.tolist() == [False, True] and r2.tolist() == [False, True]


def test_registered_tests_bound():
    """P3 is rejected only with a lower bound above -.07. At zero variance the estimate is not a bound: the old
    rule (bound = estimate) would have declared P3 here."""
    _, n = data()
    flat = inf.cluster_ratio(np.zeros(P), n, STRATA)            # beta_S = 0 with zero variance
    t = inf.registered_tests(flat, flat, flat)
    assert not t["p3"] and not t["p3_carried_out"] and np.isnan(t["p3_bound"])
    rng = np.random.default_rng(5)
    x = rng.binomial(n.astype(int), 0.02).astype(np.float64)      # beta_S near +2 points, small se
    beta = inf.cluster_ratio(x, n, STRATA)
    t = inf.registered_tests(flat, flat, beta)
    assert t["p3_carried_out"] and t["p3"] == (inf.lower_bound(beta) > -0.07) and t["p3"]
    assert not (t["p1"] or t["p2"] or t["p1_carried_out"] or t["p2_carried_out"])


def test_registered_tests_one_of_two():
    """If P1 is not carried out, P2 is compared with .02 (Section 8.2)."""
    x, n = data()
    flat = inf.cluster_ratio(np.zeros(P), n, STRATA)
    for shift in np.linspace(0.0, 0.03, 31):
        io = inf.cluster_ratio(x + np.round(shift * n), n, STRATA)
        p = float(inf.p_two_sided(io))
        t = inf.registered_tests(flat, io, flat)
        assert bool(t["p2"]) == (p <= 0.02) and not t["p1"]


def test_decomposition_regular():
    """Every judge with own screen-positive answers has a control one: within + composition = pooled, the pooled
    part is cluster_ratio() of the per-prompt totals, and within is sum_j w_j (r_j - c_j)."""
    rng = np.random.default_rng(7)
    J = 12
    na = (rng.random((J, P)) < 0.3).astype(np.float64)
    nc = na[rng.permutation(J)]
    xa = na * (rng.integers(-1, 2, (J, P)))
    xc = nc * (rng.integers(-1, 2, (J, P)))
    d = inf.interaction_decomposition(xa, na, xc, nc, STRATA)
    pooled = inf.cluster_ratio((xa - xc).sum(0), na.sum(0), STRATA)
    for key in ("est", "se"):
        assert np.isclose(d["pooled"][key], pooled[key], rtol=1e-12)
    assert flags(d["within"]) == flags(d["composition"]) == (True, False, True)
    assert np.isclose(d["within"]["est"] + d["composition"]["est"], d["pooled"]["est"], rtol=1e-12)
    w = na.sum(1) / na.sum()
    c = xc.sum(1) / nc.sum(1)
    assert np.isclose(d["within"]["est"], (w * (xa.sum(1) / na.sum(1) - c)).sum(), rtol=1e-12)
    assert not d["judges_without_control"].any()
    some = (na.sum(0) > 0) | (nc.sum(0) > 0)                         # the prompts with an own or a control answer
    want = (some[STRATA == 0]).sum() - 1 + (some[STRATA == 1]).sum() - 1
    assert d["within"]["df"] == d["composition"]["df"] == want
    own = na.sum(0) > 0
    assert d["pooled"]["df"] == pooled["df"] == (own[STRATA == 0]).sum() - 1 + (own[STRATA == 1]).sum() - 1


def test_decomposition_judge_without_control():
    """Section 8.5: a judge with screen-positive answers of its own and no screen-positive answer as a control.
    iota_S (pooled) is estimable and unchanged; iota_W and iota_C are not estimable and the judge is named; a
    judge with neither own nor control screen-positive answers does not block them."""
    rng = np.random.default_rng(11)
    J = 6
    na = (rng.random((J, P)) < 0.3).astype(np.float64)
    nc = (rng.random((J, P)) < 0.3).astype(np.float64)
    xa, xc = na * rng.integers(-1, 2, (J, P)), nc * rng.integers(-1, 2, (J, P))
    na[5], xa[5], nc[5], xc[5] = 0, 0, 0, 0                         # judge 5: no screen-positive answer at all
    ok = inf.interaction_decomposition(xa, na, xc, nc, STRATA)
    assert flags(ok["within"]) == (True, False, True) and not ok["judges_without_control"].any()
    nc[2], xc[2] = 0, 0                                              # judge 2 has no screen-positive control answer
    d = inf.interaction_decomposition(xa, na, xc, nc, STRATA)
    pooled = inf.cluster_ratio((xa - xc).sum(0), na.sum(0), STRATA)
    assert flags(d["pooled"]) == flags(pooled) == (True, False, True)
    assert np.isclose(d["pooled"]["est"], pooled["est"], rtol=1e-12)
    assert np.isclose(d["pooled"]["se"], pooled["se"], rtol=1e-12)
    for part in ("within", "composition"):
        assert flags(d[part]) == (False, False, False) and np.isnan(d[part]["est"]) and not_available(d[part])
        assert inf.reason(d[part]) == "zero denominator"
    assert d["judges_without_control"].tolist() == [False, False, True, False, False, False]
    t = inf.registered_tests(pooled, d["pooled"], pooled)
    assert t["p2_carried_out"]                                       # P2 is unaffected


def test_decomposition_leading_axis():
    """Replications in which a judge lacks a control answer and replications in which none does, together."""
    rng = np.random.default_rng(13)
    R, J = 5, 4
    na = (rng.random((R, J, P)) < 0.3).astype(np.float64)
    nc = (rng.random((R, J, P)) < 0.3).astype(np.float64)
    xa, xc = na * rng.integers(-1, 2, (R, J, P)), nc * rng.integers(-1, 2, (R, J, P))
    nc[1, 3], xc[1, 3] = 0, 0
    nc[3, 0], xc[3, 0] = 0, 0
    d = inf.interaction_decomposition(xa, na, xc, nc, STRATA)
    assert d["within"]["estimable"].tolist() == [True, False, True, False, True]
    assert d["pooled"]["estimable"].all()
    assert d["judges_without_control"].sum(-1).tolist() == [0, 1, 0, 1, 0]
    for i in range(R):
        one = inf.interaction_decomposition(xa[i], na[i], xc[i], nc[i], STRATA)
        assert np.allclose(d["within"]["est"][i], one["within"]["est"], equal_nan=True)
        assert np.isclose(d["pooled"]["se"][i], one["pooled"]["se"])


def test_decomposition_zero_variance():
    """No flag changes at all: every part is estimable with zero variance, no interval."""
    rng = np.random.default_rng(17)
    J = 4
    na = (rng.random((J, P)) < 0.3).astype(np.float64)
    nc = na[[1, 2, 3, 0]]
    z = np.zeros((J, P))
    d = inf.interaction_decomposition(z, na, z, nc, STRATA)
    for part in ("pooled", "within", "composition"):
        assert flags(d[part]) == (True, True, False) and d[part]["est"] == 0 and not_available(d[part])


def test_judge_normalised():
    rng = np.random.default_rng(19)
    J = 4
    na = (rng.random((J, P)) < 0.3).astype(np.float64)
    nc = (rng.random((J, P)) < 0.3).astype(np.float64)
    xa, xc = na * rng.integers(-1, 2, (J, P)), nc * rng.integers(-1, 2, (J, P))
    r = inf.judge_normalised(xa, na, xc, nc, STRATA)
    want = np.mean(xa.sum(1) / na.sum(1) - xc.sum(1) / nc.sum(1))
    assert flags(r) == (True, False, True) and np.isclose(r["est"], want) and r["judges_used"] == J
    some = (na + nc).sum(0) > 0
    assert r["df"] == (some[STRATA == 0]).sum() - 1 + (some[STRATA == 1]).sum() - 1
    nc[1], xc[1] = 0, 0                                              # judge 1 left out and counted
    r = inf.judge_normalised(xa, na, xc, nc, STRATA)
    keep = [0, 2, 3]
    want = np.mean(xa[keep].sum(1) / na[keep].sum(1) - xc[keep].sum(1) / nc[keep].sum(1))
    assert r["judges_used"] == 3 and np.isclose(r["est"], want)
    r = inf.judge_normalised(xa, na, np.zeros((J, P)), np.zeros((J, P)), STRATA)
    assert flags(r) == (False, False, False) and r["judges_used"] == 0 and not_available(r)


def test_effective_n():
    """Section 9.5: the design-effect term is used only where the variance is positive and the rate inside (0, 1)."""
    _, n = data()
    flat = inf.cluster_ratio(np.zeros(P), n, STRATA)
    assert inf.effective_n(flat, 80.0, 60.0) == 60.0
    x = np.minimum(n, RNG.binomial(n.astype(int), 0.3)).astype(np.float64)
    r = inf.cluster_ratio(x, n, STRATA)
    design = r["est"] * (1 - r["est"]) / r["se"] ** 2
    assert np.isclose(inf.effective_n(r, 1e9, 1e9), design)
    assert inf.effective_n(r, 10.0, 1e9) == 10.0


def test_result_without_flags():
    """A result built elsewhere (est, se, estimable, df only) is available where se is positive and finite."""
    r = {"est": np.array([0.1, 0.0, np.nan]), "se": np.array([0.02, 0.0, np.nan]),
         "estimable": np.array([True, True, False]), "df": 298}
    assert inf.available(r).tolist() == [True, False, False]
    p = inf.p_two_sided(r)
    assert np.isfinite(p[0]) and np.isnan(p[1:]).all()
    assert inf.reason(r).tolist() == ["", "zero variance", "zero denominator"]


def test_no_constant_added():
    """Section 8.1: no small constant is added to a denominator or a variance: the standard error is exactly that
    of the formula, also with a single screen-positive answer."""
    n = np.zeros(P)
    x = np.zeros(P)
    n[3], x[3] = 1, -1
    n[200] = 1
    r = inf.cluster_ratio(x, n, STRATA)
    est, se, _ = direct(x, n)
    assert flags(r) == (True, False, True) and r["est"] == est == -0.5 and np.isclose(r["se"], se, rtol=1e-14)


def test_domain_df_negative_contribution():
    """Section 8.1 (D19, proposed): a prompt counts in the domain degrees of freedom when N_p != 0. A denominator that
    is a difference (the false-alarm change of Section 9.5) can be negative on a prompt that carries answers; such a
    prompt counts, and its residual is in the variance. Review round 5, diagnostic: two strata of four prompts with
    N = (2, -1, 0, 0) give 1 + 1 = 2 degrees of freedom; with N_p > 0 they would be 0, floored at 1."""
    n = np.tile([2., -1., 0., 0.], 2)
    x = np.tile([1., 0., 0., 0.], 2)
    r = inf.cluster_ratio(x, n, np.repeat([0, 1], 4))
    assert int(r["df"]) == 2
    n2 = np.tile([2., 1., 0., 0.], 2)          # the same with a positive contribution: the same df
    assert int(inf.cluster_ratio(x, n2, np.repeat([0, 1], 4))["df"]) == 2


for name, fn in sorted(globals().items()):
    if name.startswith("test_"):
        fn()
        print("ok", name)
print("all inference tests passed")
