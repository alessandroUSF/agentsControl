"""Self-checks of analysis/estimators.py on synthetic data only (protocol v2.2, Sections 7.2 and 9.1).

Each check compares a function with a hand computation, a Monte Carlo or a null-rejection rate.
It reads no study data. Output: analysis/output/selfcheck_estimators.json.
Round 4 (audits A4-m2, B4): the G3 check is a real stratified two-stage draw without replacement with a
Horvitz-Thompson total; the T1b null check uses the design's judge sizes, shared clusters and a weak null
with heterogeneous judges, B = 999, at alpha 0.05/3 and 0.05; T4 size is checked with heterogeneous pairs.
The runner's ledger and batch path are checked separately (tests/test_runner_offline.py).

Usage: python -I analysis/selfcheck_estimators.py [--sims 1000]
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import estimators as E  # noqa: E402

OUT = Path(__file__).resolve().parent / "output" / "selfcheck_estimators.json"


def check_kappa_rectangular():
    """3 gold classes x 4 prediction columns (the 4th = invalid) must give a kappa, not an error."""
    gold = np.array([0, 0, 1, 1, 2, 2, 0, 1, 2, 2])
    pred = np.array([0, 0, 1, 3, 2, 2, 1, 1, 2, 3])
    P = E.weighted_confusion(gold, pred, np.ones(10), 3, k_pred=4)
    return {"kappa_3x4": round(float(E.kappa_from_confusion(P)), 4)}


def check_pi_keyword(rng, reps=200000):
    """Inclusion probabilities of '2 unflagged + 2 at random', including K < 2, against Monte Carlo."""
    out = {}
    for N, K in ((30, 6), (30, 1)):
        flags = np.array([0] * K + [1] * (N - K))      # 0 = unflagged by the keyword baseline
        hit = np.zeros(N)
        for _ in range(reps // 10):
            unfl = np.where(flags == 0)[0]
            take = list(unfl) if K < 2 else list(rng.choice(unfl, 2, replace=False))
            rest = np.setdiff1d(np.arange(N), take)
            take += list(rng.choice(rest, 4 - len(take), replace=False))
            hit[take] += 1
        mc = hit / (reps // 10)
        out[f"N={N},K={K}"] = {"mc_unflagged": round(float(mc[0]), 4), "formula_unflagged": round(E.pi_keyword_enriched(N, K, True), 4),
                               "mc_flagged": round(float(mc[-1]), 4), "formula_flagged": round(E.pi_keyword_enriched(N, K, False), 4)}
    return out


def check_pi_g3(rng, reps=40000):
    """Model m's frame has two sources (G2 strata) A (40 units) and B (20); G2 draws 4 from A and 4 from B
    without replacement; G3 then draws 12 from the 52 left, pooled over sources. Monte Carlo inclusion
    probabilities against pi_g3, and the Horvitz-Thompson estimate of N (= 60) from the realised sample."""
    NA, NB, nA, nB, n3 = 40, 20, 4, 4, 12
    N, R = NA + NB, NA + NB - nA - nB
    pi = np.r_[np.full(NA, E.pi_g3(nA / NA, n3, R)), np.full(NB, E.pi_g3(nB / NB, n3, R))]
    hit, ht = np.zeros(N), []
    for _ in range(reps):
        g2 = np.r_[rng.choice(NA, nA, replace=False), NA + rng.choice(NB, nB, replace=False)]
        rest = np.setdiff1d(np.arange(N), g2)
        smp = np.r_[g2, rng.choice(rest, n3, replace=False)]
        hit[smp] += 1
        ht.append((1 / pi[smp]).sum())
    mc = hit / reps
    return {"mc_A": round(float(mc[:NA].mean()), 4), "formula_A": round(float(pi[0]), 4),
            "mc_B": round(float(mc[NA:].mean()), 4), "formula_B": round(float(pi[-1]), 4),
            "ht_total_mean": round(float(np.mean(ht)), 3), "N": N}


def check_pi_own_comply_yes(rng, reps=40000):
    """`comply x uso_indevido = yes` own cell, one framing block, as a fixed-quota stratum (v2.2 addition 2,
    RULING C). A code-capability sub-stratum (answers to d19/d27/d50a/d51 -> N_code) and a physical
    sub-stratum (the other comply-yes bases -> N_phys); the guarantee draws a fixed quota from each by
    systematic sampling, i.e. a fixed-size without-replacement draw with first-order inclusion pi = n/N.
    This is a stratum, not a post-hoc top-up, so pi_i = n_sub/N_sub with no augmentation. Monte Carlo
    inclusion probabilities against pi_own_cell, and the Horvitz-Thompson total of the cell frame N."""
    N_code, N_phys, n_code, n_phys = 24, 54, 6, 6       # 12 per framing = 6 code + 6 physical
    N = N_code + N_phys
    pi = np.r_[np.full(N_code, E.pi_own_cell(n_code, N_code)), np.full(N_phys, E.pi_own_cell(n_phys, N_phys))]
    hit, ht = np.zeros(N), []
    for _ in range(reps):
        smp = np.r_[rng.choice(N_code, n_code, replace=False), N_code + rng.choice(N_phys, n_phys, replace=False)]
        hit[smp] += 1
        ht.append((1 / pi[smp]).sum())
    mc = hit / reps
    return {"mc_code": round(float(mc[:N_code].mean()), 4), "formula_code": round(float(pi[0]), 4),
            "mc_phys": round(float(mc[N_code:].mean()), 4), "formula_phys": round(float(pi[-1]), 4),
            "ht_total_mean": round(float(np.mean(ht)), 3), "N_cell": N, "n_per_framing": int(n_code + n_phys)}


def synth_t1a(rng, G=40, J=6, per=3):
    """Judge x item flags with judge x stratum and item effects, no self effect (the null)."""
    items = G * per
    cluster = np.repeat(np.arange(G), per)
    stratum = rng.integers(0, 3, G)[cluster]
    u = rng.normal(0, 0.6, G)[cluster]
    rows = []
    for j in range(J):
        for i in range(items):
            p = 1 / (1 + np.exp(-(0.3 * j - 0.5 + u[i] + rng.normal(0, 0.3))))
            rows.append((j, i, cluster[i], stratum[i], float(rng.random() < p), float(i % J == j)))
    a = np.array(rows)
    fe1 = np.unique(a[:, 0] * 10 + a[:, 3], return_inverse=True)[1]
    return a[:, 4], a[:, 5], fe1, a[:, 1].astype(int), a[:, 2].astype(int)


def synth_t1b(rng, weak):
    """T1b pairs with the design's sizes: judges 4, 5, 6 own 44/43/63 G1+G2 items, 19 other judges 12 each;
    items come from a pool of 150 base prompts, so a cluster holds several judges' pairs. Discordance about
    10%, with a cluster effect. weak=False: sharp null (symmetric signs). weak=True: judge effects of +/-0.04
    that average to zero (theta_on = 0, signs not symmetric within judges)."""
    sizes = [44, 43, 63] + [12] * 19
    judge = np.repeat(np.arange(len(sizes)), sizes)
    cluster = rng.integers(0, 150, judge.size)
    q = np.clip(0.10 + rng.normal(0, 0.04, 150)[cluster], 0.01, 0.4)
    theta = np.where(np.arange(len(sizes)) % 2 == 0, 0.04, -0.04) if weak else np.zeros(len(sizes))
    theta = theta - theta.mean()
    discord = rng.random(judge.size) < q
    p_plus = np.clip(0.5 + theta[judge] / (2 * q), 0, 1)
    D = np.where(discord, np.where(rng.random(judge.size) < p_plus, 1.0, -1.0), 0.0)
    return D, judge, np.unique(cluster, return_inverse=True)[1]


def check_null_rejection(rng, sims, B_wild=199, B_flip=999):
    a1, a = 0.05 / 3, 0.05
    wild, flip = [], {"sharp": [], "weak": []}
    for s in range(sims):
        y, x, fe1, fe2, cl = synth_t1a(rng)
        wild.append(E.wild_cluster_bootstrap_p(y, x, fe1, fe2, cl, B=B_wild, seed=s)[0])
        for kind in flip:
            D, judge, cluster = synth_t1b(rng, kind == "weak")
            flip[kind].append(E.theta_on_signflip_p(D, judge, cluster, B=B_flip, seed=s)[0])
    rate = lambda ps, lev: round(float(np.mean(np.array(ps) < lev)), 3)
    return {"sims": sims, "B_wild": B_wild, "B_signflip": B_flip,
            "wild_bootstrap_reject": {"0.05": rate(wild, a)},
            "signflip_sharp_null_reject": {"0.0167": rate(flip["sharp"], a1), "0.05": rate(flip["sharp"], a)},
            "signflip_weak_null_reject": {"0.0167": rate(flip["weak"], a1), "0.05": rate(flip["weak"], a)}}


def check_t4_size(rng, sims):
    """Size of the T4 test at the margin (mean Delta = -0.10) with heterogeneous pairs, comonotone and weakly
    coupled members; rejection at one-sided 0.025 (2 p1 < 0.05)."""
    out = {}
    for name, deltas in (("equal", (-0.10, -0.10, -0.10)), ("spread", (0.0, -0.10, -0.20)),
                         ("skewed", (0.05, -0.05, -0.30))):
        for rho in (1.0, 0.4):
            rej = 0
            for _ in range(sims):
                base, abl, pair, cl = [], [], [], []
                for k, d in enumerate(deltas):
                    n = 110
                    u = rng.random(n)
                    ua = np.where(rng.random(n) < rho, u, rng.random(n))
                    base += list((u < 0.85).astype(float)); abl += list((ua < 0.85 + d).astype(float))
                    pair += [k] * n; cl += list(rng.integers(0, 80, n))
                _, _, p1 = E.t4_test(np.array(base), np.array(abl), np.array(pair), np.array(cl), -0.10)
                rej += 2 * p1 < 0.05
            out[f"{name},rho={rho}"] = round(rej / sims, 4)
    return out


def check_strata_constant():
    try:
        E.cluster_bootstrap_indices(np.array([0, 0, 1]), np.array([0, 1, 1]), np.random.default_rng(1))
        return {"raises_on_varying_stratum": False}
    except ValueError:
        return {"raises_on_varying_stratum": True}


def check_clopper_pearson():
    """H1 thresholds (Section 7.2): one-sided 95% upper limits (two-sided 90% interval) at the smallest n that
    passes with 0, 1 and 2 misses, and at one item fewer; equivalence with the exact binomial test; and the
    two-sided limits of the round-3 rule for comparison."""
    from scipy import stats
    out = {}
    for x, n in ((0, 59), (1, 93), (2, 124)):
        for k in (n - 1, n):
            up = E.clopper_pearson(x, k, level=0.90)[1]
            out[f"one_sided_upper_{x}_of_{k}"] = round(up, 5)
            out[f"exact_test_agrees_{x}_of_{k}"] = bool((up < 0.05) == (stats.binom.cdf(x, k, 0.05) <= 0.05))
    out["two_sided_upper_1_of_110"] = round(E.clopper_pearson(1, 110)[1], 5)
    out["two_sided_upper_0_of_72"] = round(E.clopper_pearson(0, 72)[1], 5)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sims", type=int, default=1000)
    a = ap.parse_args()
    rng = np.random.default_rng(20261120)
    out = {"kappa": check_kappa_rectangular(), "pi_keyword": check_pi_keyword(rng), "pi_g3": check_pi_g3(rng),
           "pi_own_comply_yes": check_pi_own_comply_yes(rng),
           "strata": check_strata_constant(), "clopper_pearson": check_clopper_pearson(),
           "null_rejection": check_null_rejection(rng, a.sims), "t4_size_at_margin": check_t4_size(rng, 2000)}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
