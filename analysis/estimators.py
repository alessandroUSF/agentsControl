"""Estimators for the confirmatory and secondary analyses (protocol v2.2, Section 9).

Pure functions on numpy arrays, shared by the real analysis and by the power
simulation (analysis/power_sim.py). Nothing here reads data files.

Conventions
- F: 1 if the verdict flags the item's failure (Section 7.1), NaN if invalid.
- cluster: base_prompt_id codes (integers); bootstrap and robust SEs cluster on it.
"""
import math

import numpy as np
from scipy import stats


# ---------- fixed-effects linear probability model (T1a) ----------

def demean_two_way(v, g1, g2, iters=200, tol=1e-10):
    """Remove two sets of fixed effects by alternating projections."""
    v = np.asarray(v, dtype=float).copy()
    n1, n2 = g1.max() + 1, g2.max() + 1
    c1 = np.bincount(g1, minlength=n1)
    c2 = np.bincount(g2, minlength=n2)
    for _ in range(iters):
        old = v.copy()
        v -= (np.bincount(g1, weights=v, minlength=n1) / np.maximum(c1, 1))[g1]
        v -= (np.bincount(g2, weights=v, minlength=n2) / np.maximum(c2, 1))[g2]
        if np.max(np.abs(v - old)) < tol:
            break
    return v


def fe_lpm(y, X, fe1, fe2, cluster):
    """OLS of y on X with two sets of fixed effects; CR1 cluster-robust SEs.

    Returns (beta, se, resid, Xd) where Xd is the demeaned design (for the wild bootstrap).
    Degrees-of-freedom correction uses the number of clusters (Stata-style CR1).
    """
    y = np.asarray(y, dtype=float)
    X = np.atleast_2d(np.asarray(X, dtype=float).T).T
    yd = demean_two_way(y, fe1, fe2)
    Xd = np.column_stack([demean_two_way(X[:, k], fe1, fe2) for k in range(X.shape[1])])
    XtX_inv = np.linalg.pinv(Xd.T @ Xd)
    beta = XtX_inv @ Xd.T @ yd
    resid = yd - Xd @ beta
    G = cluster.max() + 1
    scores = np.zeros((G, Xd.shape[1]))
    np.add.at(scores, cluster, Xd * resid[:, None])
    meat = scores.T @ scores
    n, k = Xd.shape
    n_fe = len(np.unique(fe1)) + len(np.unique(fe2)) - 1
    g_used = len(np.unique(cluster))
    adj = g_used / (g_used - 1) * (n - 1) / max(n - k - n_fe, 1)
    V = adj * XtX_inv @ meat @ XtX_inv
    return beta, np.sqrt(np.diag(V)), resid, Xd


def wild_cluster_bootstrap_p(y, X, fe1, fe2, cluster, coef=0, B=9999, seed=20261114):
    """Wild cluster bootstrap-t p-value for H0: beta[coef] = 0 (null imposed, Rademacher).

    Cameron, Gelbach & Miller (2008). Two-sided, symmetric.
    """
    rng = np.random.default_rng(seed)
    X = np.atleast_2d(np.asarray(X, dtype=float).T).T
    beta, se, _, _ = fe_lpm(y, X, fe1, fe2, cluster)
    t_obs = beta[coef] / se[coef]
    others = [k for k in range(X.shape[1]) if k != coef]
    yd = demean_two_way(np.asarray(y, float), fe1, fe2)
    Xd = np.column_stack([demean_two_way(X[:, k], fe1, fe2) for k in range(X.shape[1])])
    if others:
        Xo = Xd[:, others]
        b0 = np.linalg.lstsq(Xo, yd, rcond=None)[0]
        fit0, res0 = Xo @ b0, yd - Xo @ b0
    else:
        fit0, res0 = np.zeros_like(yd), yd
    G = cluster.max() + 1
    XtX_inv = np.linalg.pinv(Xd.T @ Xd)
    n, k = Xd.shape
    g_used = len(np.unique(cluster))
    n_fe = len(np.unique(fe1)) + len(np.unique(fe2)) - 1
    adj = g_used / (g_used - 1) * (n - 1) / max(n - k - n_fe, 1)     # same factor as fe_lpm (round-3 A3-M4)
    count = 0
    for _ in range(B):
        w = rng.choice([-1.0, 1.0], size=G)[cluster]
        ys = demean_two_way(fit0 + res0 * w, fe1, fe2)                  # re-project onto the FE complement
        bs = XtX_inv @ Xd.T @ ys
        r = ys - Xd @ bs
        sc = np.zeros((G, k))
        np.add.at(sc, cluster, Xd * r[:, None])
        V = adj * XtX_inv @ (sc.T @ sc) @ XtX_inv
        t = bs[coef] / math.sqrt(max(V[coef, coef], 1e-300))
        count += abs(t) >= abs(t_obs)
    return (1 + count) / (B + 1), t_obs, beta, se


# ---------- weighted means with cluster-robust SEs (T1b, T4) ----------

def weighted_mean_cluster_se(values, weights, cluster):
    """theta = sum w v / sum w; SE from cluster sums of linearised scores."""
    v = np.asarray(values, float)
    w = np.asarray(weights, float)
    W = w.sum()
    theta = (w * v).sum() / W
    G = cluster.max() + 1
    s = np.bincount(cluster, weights=w * (v - theta) / W, minlength=G)
    g_used = len(np.unique(cluster))
    var = g_used / max(g_used - 1, 1) * (s ** 2).sum()
    return theta, math.sqrt(var)


def theta_on(D, judge, cluster):
    """T1b: mean over judges of each judge's mean paired difference (equal judge weights).

    D: F_ctx - F_blind for each (judge, own item) pair with valid verdicts in both.
    """
    D = np.asarray(D, float)
    ok = ~np.isnan(D)
    D, judge, cluster = D[ok], judge[ok], cluster[ok]
    n_j = np.bincount(judge)
    J = (n_j > 0).sum()
    w = 1.0 / (J * n_j[judge])
    return weighted_mean_cluster_se(D, w, cluster)


def theta_on_signflip_p(D, judge, cluster, B=9999, seed=20261114):
    """T1b confirmatory test (Section 9.1): cluster sign-flip test of the studentised theta_on.

    Under the sharp null that the presentation has no effect, F_ctx and F_blind are exchangeable within each
    judge-item pair, so the signs of D are exchangeable; signs are flipped jointly within each base_prompt_id
    cluster (one cluster can hold several judges' pairs and several framings). The test is exact under that
    sharp null. Under the weak null theta_on = 0 it is a Rademacher wild cluster bootstrap-t with the null
    imposed, valid asymptotically (studentising about the pooled mean is conservative there).
    Two-sided p = (1 + #{|t*| >= |t_obs|}) / (B + 1).
    """
    rng = np.random.default_rng(seed)
    D = np.asarray(D, float)
    ok = ~np.isnan(D)
    D, judge, cluster = D[ok], np.asarray(judge)[ok], np.asarray(cluster)[ok]
    th, se = theta_on(D, judge, cluster)
    t_obs = th / se if se > 0 else 0.0
    G = cluster.max() + 1
    count = 0
    for _ in range(B):
        s = rng.choice([-1.0, 1.0], size=G)[cluster]
        tb, sb = theta_on(D * s, judge, cluster)
        count += abs(tb / sb if sb > 0 else 0.0) >= abs(t_obs)
    return (1 + count) / (B + 1), th, se


def pooled_pair_difference(diff, pair, cluster):
    """T4: Delta = (1/K) sum_k mean_{i in I_k} (F_abl - F_base)."""
    diff = np.asarray(diff, float)
    ok = ~np.isnan(diff)
    diff, pair, cluster = diff[ok], pair[ok], cluster[ok]
    n_k = np.bincount(pair)
    K = (n_k > 0).sum()
    w = 1.0 / (K * n_k[pair])
    return weighted_mean_cluster_se(diff, w, cluster)


def tango_null_variance(base, abl, delta0):
    """Variance of the paired difference (abl - base) under H0: Delta = delta0 (Tango, 1998).

    base, abl: 0/1 flags on the same items. Uses the restricted MLE of the discordant cells, so
    the variance does not shrink with the observed difference (Wald tests on few discordant
    pairs are anti-conservative at a non-inferiority boundary).
    """
    base, abl = np.asarray(base, int), np.asarray(abl, int)
    n = len(base)
    b = int(((base == 1) & (abl == 0)).sum())      # base flags, abliterated misses
    c = int(((base == 0) & (abl == 1)).sum())
    r = n - b - c
    s = 1 - delta0
    A, B, C = 2 * n, (b + c) * s - 2 * delta0 * (b + r), -b * delta0 * s
    disc = max(B * B - 4 * A * C, 0.0)   # A x^2 - B x + C = 0
    roots = [(B + math.sqrt(disc)) / (2 * A), (B - math.sqrt(disc)) / (2 * A)]
    lo = max(0.0, -delta0)
    ok = [x for x in roots if lo - 1e-12 <= x <= (1 - delta0) / 2 + 1e-12]
    x = ok[0] if ok else lo
    p12, p21 = x, x + delta0
    return max(p12 + p21 - (p21 - p12) ** 2, 1e-12) / n


def t4_test(base, abl, pair, cluster, delta0=-0.10, variance="max"):
    """T4: pooled Delta, a conservative SE = max(cluster-robust, null-restricted), one-sided p.

    Returns (Delta, se_used, p_one_sided). The real analysis also reports the bootstrap p.
    """
    base, abl = np.asarray(base, float), np.asarray(abl, float)
    ok = ~(np.isnan(base) | np.isnan(abl))
    base, abl, pair, cluster = base[ok], abl[ok], pair[ok], cluster[ok]
    delta, se_cr = pooled_pair_difference(abl - base, pair, cluster)
    ks = [k for k in np.unique(pair)]
    var0 = sum(tango_null_variance(base[pair == k], abl[pair == k], delta0) for k in ks) / len(ks) ** 2
    se = math.sqrt(var0) if variance == "null" else max(se_cr, math.sqrt(var0))
    p1 = 1 - stats.norm.cdf((delta - delta0) / se)
    return delta, se, p1


# ---------- bootstrap p-values (Section 9.1) ----------

def boot_p_two_sided(theta_hat, boot, theta0=0.0):
    boot = np.asarray(boot, float)
    return (1 + np.sum(np.abs(boot - theta_hat) >= abs(theta_hat - theta0))) / (len(boot) + 1)


def boot_p_one_sided_greater(theta_hat, boot, theta0):
    """p for H0: theta <= theta0 against theta > theta0 (T4 with theta0 = -0.10)."""
    boot = np.asarray(boot, float)
    return (1 + np.sum(boot - theta_hat >= theta_hat - theta0)) / (len(boot) + 1)


def cluster_bootstrap_indices(cluster, strata, rng):
    """One stratified cluster-bootstrap draw. Returns (row indices, new cluster ids)."""
    rows_by_cluster = {}
    for i, c in enumerate(cluster):
        rows_by_cluster.setdefault(c, []).append(i)
    clusters_by_stratum = {}
    for c, rows in rows_by_cluster.items():
        if len({strata[i] for i in rows}) != 1:
            raise ValueError(f"stratum varies within cluster {c}; stratify on a prompt-level variable")
        clusters_by_stratum.setdefault(strata[rows[0]], []).append(c)
    idx, new_ids, nid = [], [], 0
    for s in sorted(clusters_by_stratum):
        cs = clusters_by_stratum[s]
        for c in rng.choice(cs, size=len(cs), replace=True):
            rows = rows_by_cluster[c]
            idx.extend(rows)
            new_ids.extend([nid] * len(rows))
            nid += 1
    return np.array(idx), np.array(new_ids)


def holm(pvals, alpha=0.05):
    """Holm step-down. Returns adjusted p-values and reject flags, in input order."""
    p = np.asarray(pvals, float)
    order = np.argsort(p)
    m = len(p)
    adj = np.empty(m)
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, (m - rank) * p[i])
        adj[i] = min(1.0, running)
    return adj, adj < alpha


# ---------- proportions and agreement (H1, RQ1) ----------

def clopper_pearson(x, n, level=0.95):
    a = 1 - level
    lo = 0.0 if x == 0 else stats.beta.ppf(a / 2, x, n - x + 1)
    hi = 1.0 if x == n else stats.beta.ppf(1 - a / 2, x + 1, n - x)
    return lo, hi


def kish_neff(w):
    w = np.asarray(w, float)
    return w.sum() ** 2 / (w ** 2).sum()


def korn_graubard(p_hat, n_eff, level=0.95, n=None):
    """Korn-Graubard-type interval (Korn & Graubard, 1998): Clopper-Pearson at the Kish effective sample size.

    Simplified: no degrees-of-freedom adjustment and no clustering term; n_eff is capped at the actual n.
    """
    if n is not None:
        n_eff = min(n_eff, n)
    x = p_hat * n_eff
    a = 1 - level
    lo = 0.0 if x <= 0 else stats.beta.ppf(a / 2, x, n_eff - x + 1)
    hi = 1.0 if x >= n_eff else stats.beta.ppf(1 - a / 2, x + 1, n_eff - x)
    return lo, hi


def weighted_confusion(gold, pred, w, k, k_pred=None):
    """Weighted confusion matrix, gold (k classes) x prediction (k_pred columns, e.g. 3 labels + invalid)."""
    P = np.zeros((k, k_pred or k))
    np.add.at(P, (gold, pred), w)
    return P / P.sum()


def kappa_from_confusion(P):
    """Cohen's kappa. A k x (k+1) matrix (extra 'invalid' column) is padded with an empty gold row,
    so invalid verdicts count as disagreement."""
    P = np.asarray(P, float)
    m = max(P.shape)
    if P.shape != (m, m):
        Q = np.zeros((m, m))
        Q[:P.shape[0], :P.shape[1]] = P
        P = Q
    po = np.trace(P)
    pe = (P.sum(1) * P.sum(0)).sum()
    return (po - pe) / (1 - pe)


# ---------- design (Section 7.2) ----------

def pi_keyword_enriched(N, K, unflagged):
    """Inclusion probabilities for '2 keyword-unflagged + 2 at random' from a stratum frame of N answers.

    N = frame count (status ok or truncated, excluding G1 and pilot items); K = answers the keyword baseline does
    not flag. The 2 random items are a simple random sample of the N - 2 answers not yet drawn.
    If K < 2, all K unflagged answers are taken and 4 - K are drawn at random from the other N - K.
    """
    if K < 2:
        return 1.0 if unflagged else (4 - K) / (N - K)
    if unflagged:
        return 2 / K + (1 - 2 / K) * 2 / (N - 2)
    return 2 / (N - 2)


def pi_g3(pi_prev, n_g3_m, R_m):
    """Inclusion probability after G3 for EVERY unit of model m's G3 frame, whichever stage drew it.

    pi_prev: the unit's G1/G2 inclusion probability; n_g3_m: realised G3 draws from model m (treated as fixed);
    R_m: model m's frame remaining after G1, G2 and pilot items (= N_m - n_prev,m).
    pi = pi_prev + (1 - pi_prev) * n_g3_m / R_m   (round-3 audits A3-M1, B3-m3)
    """
    return pi_prev + (1 - pi_prev) * n_g3_m / R_m


def pi_own_cell(n_h, N_h):
    """Inclusion probability for a unit of a fixed-quota own-prompt stratum drawn by fractional-interval
    systematic sampling (Section 7.2; A5-M1). The `comply x uso_indevido = yes` guarantee is implemented as
    such a stratum (12 per framing, nested into a code-capability sub-stratum covering d19/d27/d50a/d51 and a
    physical sub-stratum), NOT as a post-hoc minimum-count top-up, so pi stays exactly n_h/N_h with no
    augmentation term (contrast pi_g3). Each (framing x capability) sub-stratum uses its own n_h, N_h."""
    return n_h / N_h


# ---------- misclassification correction (RQ4) ----------

def rogan_gladen(q, se, sp):
    j = se + sp - 1
    if j <= 0:
        return float("nan")
    return float(np.clip((q + sp - 1) / j, 0, 1))
