"""Registered inference of protocol v2.3 (Section 8): ratio statistics over prompt clusters.

Every function accepts arrays whose last axis is the prompt axis, with any number of leading axes. The
analysis script calls them with one data set; the simulations call the same functions with a leading
replication axis, so that simulated operating characteristics refer to the production code.

Statistic.  theta_hat = sum_p X_p / sum_p N_p, where X_p is the prompt's sum of screened differences and
N_p its number of screen-positive answers. Influence residuals e_p = X_p - theta_hat * N_p are centred
inside each source stratum; variance = sum_h n_h / (n_h - 1) * sum_{p in h} (e_p - mean_h)^2 / (sum N)^2;
degrees of freedom = sum_h (n_h - 1).

Boundary cases (Section 8.1). They are handled apart and counted apart. Every result of cluster_ratio,
judge_normalised and interaction_decomposition carries three flags, element by element:
  estimable      the denominator is positive. With a zero denominator the statistic does not exist: est and se
                 are NaN ("not estimable"), and its test is not carried out.
  zero_variance  estimable, and the estimated variance is zero: the residuals do not vary inside either source.
                 The estimate is reported and se is 0; the test is not carried out.
  available      estimable and the estimated variance is positive: the test is carried out.
Where a result is not available, p_two_sided(), interval() and lower_bound() return NaN, which stands for "not
available": no p-value, no interval, no bound. NaN is never a rejection: holm_two() and registered_tests() do not
reject a test that is not carried out, and compare the other test of the family with alpha / 2 (Section 8.2);
P3 is not declared without a bound. reason() names the boundary case. No small constant is ever added to a
denominator or to a variance.
"""
import numpy as np
from scipy import stats

FAMILY_ALPHA = 0.04     # P1 and P2, Holm
BOUND_ALPHA = 0.01      # P3, one-sided
BOUND_MARGIN = -0.07    # P3: H0 beta <= -0.07

# Zero estimated variance (Section 8.1) is decided on the residuals, not on the computed variance: the
# variance is zero exactly when every centred residual is zero, but a computed residual can carry a rounding
# error of a few units in the last place of the terms that formed it (for example X_p = 1, N_p = 3 for every
# prompt gives theta_hat = 1/3 and residuals of about 1e-16). A centred residual counts as zero when it is at
# most ZERO_VARIANCE_RTOL times the largest absolute term of a residual of that result. This is a tolerance for
# floating-point rounding, not a constant added to the variance. With integer counts (at most 23 answers per
# prompt, 150 prompts per source, so sum N <= 6,900) a centred residual that is not zero is at least
# 1 / (150 sum N) ~ 1e-6 in absolute value, and the scale is at most 4 x 23, so it is above 1e-8 of the scale, a
# hundred times the tolerance; a rounding error is at most about 1e-14 of it. (Weighted label-sample statistics
# have no such floor, but their residuals vanish together only when the ratio is the same on every prompt.)
ZERO_VARIANCE_RTOL = 1e-10


def _stratified_var(e, strata):
    """Stratified cluster variance of sum_p e_p: sum_h n_h / (n_h - 1) * sum_{p in h} (e_p - mean_h)^2, with its
    degrees of freedom sum_h (n_h - 1) and the largest absolute centred residual (for the zero-variance rule).
    e: [..., P]."""
    strata = np.asarray(strata)
    var, top, df = np.zeros(e.shape[:-1]), np.zeros(e.shape[:-1]), 0
    for h in np.unique(strata):
        m = strata == h
        n = int(m.sum())
        if n < 2:
            raise ValueError("a stratum needs at least two prompts")
        eh = e[..., m]
        eh = eh - eh.mean(-1, keepdims=True)
        var = var + n / (n - 1) * (eh ** 2).sum(-1)
        top = np.maximum(top, np.abs(eh).max(-1))
        df += n - 1
    return var, df, top


def _result(est, var, df, den, estimable, top, scale, norm):
    """Result of a ratio statistic with the boundary flags of Section 8.1.
    est: estimate; var: stratified variance of the linearised total, so that se = sqrt(var) / norm; den: the
    reported denominator; estimable: the denominator is positive; top: largest absolute centred residual;
    scale: largest absolute term of a residual (see ZERO_VARIANCE_RTOL)."""
    estimable = np.asarray(estimable, dtype=bool)
    zero = estimable & (top <= ZERO_VARIANCE_RTOL * scale)
    ok = estimable & ~zero
    norm = np.where(estimable, norm, 1.0)
    se = np.where(ok, np.sqrt(var) / norm, 0.0)       # zero variance: se is 0, not a rounding residue
    nan = np.where(estimable, 0.0, np.nan)
    return {"est": est + nan, "se": se + nan, "df": df, "den": den, "estimable": estimable,
            "zero_variance": zero, "available": ok}


def cluster_ratio(X, N, strata):
    """Ratio estimate with stratified cluster-robust standard error. X, N: [..., P]; strata: [P] labels.
    Returns est, se, df, den and the flags estimable, zero_variance and available (module docstring)."""
    X, N = np.asarray(X, dtype=np.float64), np.asarray(N, dtype=np.float64)
    strata = np.asarray(strata)
    den = N.sum(-1)
    estimable = den > 0
    safe = np.where(estimable, den, 1.0)
    est = X.sum(-1) / safe
    var, df, top = _stratified_var(X - est[..., None] * N, strata)
    scale = (np.abs(X) + np.abs(est)[..., None] * np.abs(N)).max(-1)
    return _result(est, var, df, den, estimable, top, scale, safe)


def available(r):
    """Where the test of a result is carried out and its p-value, interval and bound exist (Section 8.1).
    A result without the flag (built elsewhere) is available where it is estimable with a positive finite se."""
    if "available" in r:
        return np.asarray(r["available"], dtype=bool)
    se = np.asarray(r["se"], dtype=np.float64)
    return np.asarray(r["estimable"], dtype=bool) & np.isfinite(se) & (se > 0)


def reason(r):
    """Why the p-value, the interval and the bound of a result are not available (Sections 2.4 and 8.1), element
    by element: "zero denominator" (no answer in the denominator, for the registered statistics: no
    screen-positive answer), "zero variance" (no variation in the data), or "" where they are available."""
    est = np.asarray(r["estimable"], dtype=bool)
    return np.where(~est, "zero denominator", np.where(available(r), "", "zero variance"))


def p_two_sided(r, null=0.0):
    """Two-sided t test of the ratio against null. NaN ("not available") where the test is not carried out:
    zero denominator or zero estimated variance (Section 8.1)."""
    ok = available(r)
    se = np.where(ok, r["se"], 1.0)
    t = (np.where(ok, r["est"], 0.0) - null) / se
    p = 2 * stats.t.sf(np.abs(t), r["df"])
    return np.where(ok, p, np.nan)


def interval(r, level=0.95):
    """Two-sided t interval (lower, upper). NaN ("not available") where the result is not available: no interval
    is reported at a zero denominator or a zero estimated variance (Section 8.1)."""
    ok = available(r)
    q = stats.t.ppf(0.5 + level / 2, r["df"])
    est, se = np.where(ok, r["est"], 0.0), np.where(ok, r["se"], 0.0)
    return np.where(ok, est - q * se, np.nan), np.where(ok, est + q * se, np.nan)


def lower_bound(r, level=1 - BOUND_ALPHA):
    """One-sided lower confidence bound. NaN ("not available") where the result is not available (Section 8.1)."""
    ok = available(r)
    est, se = np.where(ok, r["est"], 0.0), np.where(ok, r["se"], 0.0)
    return np.where(ok, est - stats.t.ppf(level, r["df"]) * se, np.nan)


def effective_n(r, kish, clusters):
    """Effective number of answers behind an estimated rate (Section 9.5): the smallest of
    (1) the Kish number of the sampling weights in the class, (sum w)^2 / sum w^2,
    (2) the number of prompts that carry a labelled answer of the class, and
    (3) est (1 - est) / se^2, when the estimate is strictly between 0 and 1 and se > 0 (available).
    r: result of cluster_ratio. No value above the Kish number is ever used."""
    est, se = np.asarray(r["est"], dtype=np.float64), np.asarray(r["se"], dtype=np.float64)
    inside = available(r) & (est > 0) & (est < 1)
    design = np.where(inside, est * (1 - est) / np.where(inside, se, 1.0) ** 2, np.inf)
    return np.minimum(np.minimum(kish, clusters), design)


def exact_interval(est, n_eff, level=0.95):
    """Clopper-Pearson interval of a rate on an effective number of answers (Korn and Graubard 1998).
    est: estimated rate; n_eff: effective number of answers, not necessarily an integer.
    The interval keeps a width at est = 0 (upper limit 1 - (alpha/2)^(1/n_eff)) and at est = 1."""
    est = np.clip(np.asarray(est, dtype=np.float64), 0.0, 1.0)
    n = np.asarray(n_eff, dtype=np.float64)
    a, x = (1 - level) / 2, est * n
    lo = np.where(x > 0, stats.beta.ppf(a, np.maximum(x, 1e-12), n - x + 1), 0.0)
    hi = np.where(x < n, stats.beta.ppf(1 - a, x + 1, np.maximum(n - x, 1e-12)), 1.0)
    return lo, hi


def share_of_two(first, second):
    """Interval of A / (A + B) from intervals of the two parts. first, second: (lower, upper) of A and of B, each
    at level 1 - alpha/2, so that the result holds at level 1 - alpha (Bonferroni). The ratio rises with A and
    falls with B."""
    (al, au), (bl, bu) = first, second
    return al / np.maximum(al + bu, 1e-300), au / np.maximum(au + bl, 1e-300)


def holm_two(p1, p2, alpha=FAMILY_ALPHA):
    """Holm step-down for two hypotheses. Returns boolean rejections (r1, r2). A NaN p-value is a test that was
    not carried out (Section 8.1): it is never rejected, and the other p-value is then compared with alpha / 2
    (Section 8.2)."""
    p1, p2 = np.asarray(p1, dtype=np.float64), np.asarray(p2, dtype=np.float64)
    a, b = np.nan_to_num(p1, nan=2.0), np.nan_to_num(p2, nan=2.0)
    lo, hi = np.minimum(a, b), np.maximum(a, b)
    first = lo <= alpha / 2
    second = first & (hi <= alpha)
    return np.where(a <= b, first, second), np.where(b < a, first, second)


def registered_tests(theta, iota, beta, alpha=FAMILY_ALPHA, margin=BOUND_MARGIN, bound_level=1 - BOUND_ALPHA):
    """Decisions of the registered tests (Section 8.2) from the cluster_ratio results of theta_S, iota_S and
    beta_S. P1 and P2: two-sided t tests, Holm at family level alpha. P3: rejected when the one-sided lower bound
    of beta_S lies above the margin.
    A test that is not carried out (zero denominator or zero estimated variance, Section 8.1) is not rejected; if
    one of P1 and P2 is not carried out, the other is compared with alpha / 2; without a lower bound P3 is not
    declared. Returns booleans p1, p2, p3 (rejected) and p1_carried_out, p2_carried_out, p3_carried_out, with the
    p-values p1_p, p2_p and the bound p3_bound (NaN where not available)."""
    p1, p2 = p_two_sided(theta), p_two_sided(iota)
    r1, r2 = holm_two(p1, p2, alpha)
    lb = lower_bound(beta, bound_level)
    c3 = available(beta)
    r3 = c3 & (np.where(c3, lb, -np.inf) > margin)
    return {"p1": r1, "p2": r2, "p3": r3, "p1_carried_out": available(theta), "p2_carried_out": available(iota),
            "p3_carried_out": c3, "p1_p": p1, "p2_p": p2, "p3_bound": lb}


def signflip_p(X, signs):
    """Sensitivity analysis: two-sided sign-flip p-value of sum_p X_p with fixed denominators.
    X: [..., P]; signs: [B, P] of +1/-1. p = (1 + #{|T*| >= |T|}) / (1 + B)."""
    X = np.asarray(X, dtype=np.float32)
    t = np.abs(X.sum(-1))
    ts = np.abs(X @ np.asarray(signs, dtype=np.float32).T)
    return (1 + (ts >= t[..., None] - 1e-6).sum(-1)) / (1 + signs.shape[0])


def judge_normalised(xa, na, xc, nc, strata):
    """Judge-normalised interaction (sensitivity). Arrays [..., J, P], indexed by JUDGE:
    xa, na: screened differences and screen indicators of the judge's own answers;
    xc, nc: the same for the answers the judge classified as a control.
    Estimate = mean over judges of (own ratio - control ratio); judges with an empty denominator are left
    out and counted. Linearised stratified cluster variance as in cluster_ratio, with the same boundary flags."""
    xa, na, xc, nc = (np.asarray(v, dtype=np.float64) for v in (xa, na, xc, nc))
    strata = np.asarray(strata)
    Na, Nc = na.sum(-1), nc.sum(-1)
    use = (Na > 0) & (Nc > 0)
    sa, sc = np.where(use, Na, 1.0), np.where(use, Nc, 1.0)
    ra, rc = xa.sum(-1) / sa, xc.sum(-1) / sc
    k = use.sum(-1)
    kk = np.where(k > 0, k, 1)
    est = (use * (ra - rc)).sum(-1) / kk
    infl = (use[..., None] * ((xa - ra[..., None] * na) / sa[..., None]
                              - (xc - rc[..., None] * nc) / sc[..., None])).sum(-2) / kk[..., None]
    var, df, top = _stratified_var(infl, strata)
    scale = (use[..., None] * ((np.abs(xa) + np.abs(ra)[..., None] * na) / sa[..., None]
                               + (np.abs(xc) + np.abs(rc)[..., None] * nc) / sc[..., None])).sum(-2).max(-1) / kk
    out = _result(est, var, df, k.astype(np.float64), k > 0, top, scale, 1.0)
    out["judges_used"] = k
    return out


def interaction_decomposition(xa, na, xc, nc, strata):
    """Exact decomposition of the pooled interaction. Arrays [..., J, P] indexed by JUDGE, as in
    judge_normalised(). With own ratio r_j = sum xa_j / sum na_j, control ratio c_j = sum xc_j / sum nc_j,
    w_j = share of the screen-positive answers written by judge j and v_j = share of them that judge j
    classified as a control:

      pooled      = sum_j w_j r_j - sum_j v_j c_j     (iota_S, the registered statistic of P2)
      within      = sum_j w_j (r_j - c_j)             (iota_W: each judge against itself; control changes
                                                       standardised to the authors' exposure)
      composition = sum_j (w_j - v_j) c_j             (iota_C: unequal exposure of judges as author and as control)

    pooled = within + composition. Returns {"pooled", "within", "composition", "judges_without_control"}; the
    first three have the format of cluster_ratio() (linearised stratified cluster variance and the boundary flags).

    Estimability (Section 8.5), for each part on its own:
      pooled is estimable when at least one answer is screen-positive; it is cluster_ratio() of the per-prompt
        totals, so it reproduces the registered statistic of P2 with its flags;
      within and composition also need every judge with screen-positive answers of its own to have at least one
        screen-positive answer as a control (its control ratio c_j has that number as its denominator). Where a
        judge lacks it, both are not estimable, and "judges_without_control" ([..., J] booleans) names the judge.
        No judge is dropped and no weight is moved to make them estimable."""
    xa, na, xc, nc = (np.asarray(v, dtype=np.float64) for v in (xa, na, xc, nc))
    Na, Nc = na.sum(-1), nc.sum(-1)
    lacking = (Na > 0) & (Nc == 0)
    x_p, n_p = (xa - xc).sum(-2), na.sum(-2)
    out = {"pooled": cluster_ratio(x_p, n_p, strata)}
    N, has = out["pooled"]["den"], out["pooled"]["estimable"]
    split = has & ~lacking.any(-1)
    sN, sNc = np.where(has, N, 1.0), np.where(Nc > 0, Nc, 1.0)
    c = xc.sum(-1) / sNc
    pooled = x_p.sum(-1) / sN
    within = (xa.sum(-1) - Na * c).sum(-1) / sN
    e_pooled = x_p - pooled[..., None] * n_p
    q = (Na / sNc)[..., None]
    e_within = (xa - na * c[..., None] - q * (xc - c[..., None] * nc)).sum(-2) - within[..., None] * n_p
    s_pooled = (np.abs(x_p) + np.abs(pooled)[..., None] * n_p).max(-1)
    s_within = ((np.abs(xa) + na * np.abs(c)[..., None] + q * (np.abs(xc) + np.abs(c)[..., None] * nc)).sum(-2)
                + np.abs(within)[..., None] * n_p).max(-1)
    for name, est, e, scale in (("within", within, e_within, s_within),
                                ("composition", pooled - within, e_pooled - e_within, s_pooled + s_within)):
        var, df, top = _stratified_var(e, strata)
        out[name] = _result(est, var, df, N, split, top, scale, sN)
    out["judges_without_control"] = lacking
    return out
