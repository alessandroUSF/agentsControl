"""Run (j) of Appendix A.4 (protocol v2.3, since 12 November 2026): sparse, clustered changes with no background
discordance, the counterexample of the second round of fresh readings (Section 17.1).

Part 1, the family. Every prompt of the registered design has N_p = 6 screen-positive answers. The author's total of
each prompt is +s with probability lambda / P, -1 with probability s lambda / P, and 0 otherwise, so its mean is zero:
on average lambda prompts carry a large rise and s lambda prompts a small fall. The controls' totals are zero, so the
totals of theta_S and iota_S are the same, and Holm rejects both or neither, when p <= .02: the nominal rate of the
event 'P1 or P2 rejects' is .02 here. With probability 0.1 a prompt also gets a symmetric background term of +1 or
-1 (rows bg = 0.1). Printed: the rate of the registered decision, the rate of a rejection whose fragility count
(analysis/fragility_v23.py) is at least 2 (it survives one added prompt at its bound), and the probability that the
sample has no prompt with a large rise, exp(-lambda). Since decision D20 (12 November 2026): also the rate of a
rejection under the registered condition of analysis/density_v23.py (the test is carried out only when at least 30% of
the prompts with N_p > 0 have a nonzero total), and the mean share of such prompts; the background rows go up to 0.4,
where the condition starts to hold.

Part 2, the cost of the same requirement as a gate. Rows of R-S1 (Appendix A.1) drawn with the registered model
(sim_v23_registered.draw, not changed), fewer replications: the rate of each registered test, and the rate with
fragility counts of at least 2, 3 and 6. Since decision D20: the rate of each test under the condition of D20, and
the share of replications where its test is carried out.

The t tests themselves (inference_v23) do not change: this run measures their size where the level is not
controlled, with and without the condition of decision D20, and what the fragility count shows.

Usage (from the repository root):
  python -I analysis/sim_v23_sparse.py --out sim_v23_sparse.json
  python -I analysis/sim_v23_sparse.py --reps 500 --rs1-reps 100            (a small run, nothing written)"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent / "src")]
import density_v23 as DN  # noqa: E402
import fragility_v23 as FR  # noqa: E402
import inference_v23 as inf  # noqa: E402
import sim_v23_dgp as dgp  # noqa: E402
import sim_v23_registered as SR  # noqa: E402

SEED = 20261112
SPIKES = (2, 3, 6)
LAMBDAS = (0.5, 1, 2, 3, 5, 10)
BACKGROUND = (0.0, 0.1, 0.2, 0.3, 0.4)
RS1 = {"baseline|null": {}, "baseline|theta": dict(theta=-0.05), "baseline|iota": dict(iota=-0.05),
       "baseline|both": dict(theta=-0.05, iota=-0.05), "baseline|bound": dict(beta=-0.07),
       "baseline|beta0": dict(beta=0.0), "discordance_0.20|iota": dict(q0=0.20, iota=-0.05),
       "low_failure|iota": dict(fail_i=0.03, fail_r=0.20, iota=-0.05),
       "removed_se_0.30|iota": dict(se_removed=0.30, iota=-0.05)}


def family(rng, D, reps, chunk=5000):
    strata, P = np.asarray(D["strata"]), D["P"]
    rows = []
    for s in SPIKES:
        for lam in LAMBDAS:
            for bg in BACKGROUND:
                reg = robust = d20 = 0
                share = 0.0
                done = 0
                while done < reps:
                    R = min(chunk, reps - done)
                    done += R
                    q = lam / P
                    u = rng.random((R, P))
                    X = np.where(u < q, float(s), np.where(u < q + s * q, -1.0, 0.0))
                    if bg:
                        v = rng.random((R, P))
                        X = X + np.where(v < bg / 2, 1.0, np.where(v < bg, -1.0, 0.0))
                    N = np.full((R, P), 6.0)
                    c = FR.counts({"th": X, "io": X, "be": np.zeros((R, P))}, N, strata, kmax=1,
                                  tests=FR.TESTS[:2], rule="registered")
                    reg += int(((c["p1"] > 0) | (c["p2"] > 0)).sum())
                    robust += int(((c["p1"] > 1) | (c["p2"] > 1)).sum())
                    r = inf.cluster_ratio(X, N, strata)
                    rb = inf.cluster_ratio(np.zeros((R, P)), N, strata)
                    d = DN.decide(r, r, rb, X, X, N)
                    d20 += int((np.asarray(d["p1"]) | np.asarray(d["p2"])).sum())
                    share += float(np.asarray(d["p1_share"]).sum())
                rows.append({"spike": s, "lambda": lam, "background": bg, "reps": reps,
                             "rate_registered": reg / reps, "rate_fragility_2": robust / reps,
                             "rate_d20": d20 / reps, "mean_share_nonzero": share / reps,
                             "no_spike_probability": float(np.exp(-lam)), "nominal": 0.02})
                print(f"family s={s} lambda={lam:<4} bg={bg}: registered {reg / reps:.4f}, "
                      f"surviving one bound prompt {robust / reps:.4f}, with D20 {d20 / reps:.4f} "
                      f"(share {share / reps:.2f}), P(no spike) {np.exp(-lam):.3f}", flush=True)
    return rows


def rs1(D, reps, chunk=250):
    rows = []
    strata = np.asarray(D["strata"])
    for name, kw in RS1.items():
        t0 = time.time()
        sc = dict(dgp.BASE, **kw)
        r_cal, _, r_sim = SR.streams("sparse_" + name, SEED)
        q = dgp.panel_quality(D, sc)
        g, rho, _ = dgp.calibrate(r_cal, D, sc, q, 1000)
        hist = {t: np.zeros(FR.KMAX + 2, np.int64) for t, _ in FR.TESTS}
        d20 = {t: 0 for t in ("p1", "p2", "p3")}
        dense = {t: 0 for t in ("p1", "p2")}
        done = 0
        while done < reps:
            R = min(chunk, reps - done)
            done += R
            S, A1, A2, C1, C2, _ = SR.draw(r_sim, R, D, sc, q, g, rho)
            dA, dC = (A2 - A1).astype(np.int32), (C2 - C1).astype(np.int32)
            X = {"th": (S * dA).sum(1), "io": (S * (dA - dC)).sum(1), "be": (S * (A1 - C1).astype(np.int32)).sum(1)}
            N = S.sum(1, dtype=np.int32)
            c = FR.counts(X, N, strata, rule="registered")
            for t in hist:
                hist[t] += np.bincount(c[t], minlength=FR.KMAX + 2)
            r = {k: inf.cluster_ratio(X[k], N, strata) for k in ("th", "io", "be")}
            d = DN.decide(r["th"], r["io"], r["be"], X["th"], X["io"], N)
            for t in d20:
                d20[t] += int(np.asarray(d[t]).sum())
            for t in dense:
                dense[t] += int(np.asarray(d[t + "_dense"]).sum())
        row = {"row": name, "reps": reps, "seconds": round(time.time() - t0, 1)}
        for t, h in hist.items():
            row[t] = {"rejected": float(h[1:].sum() / reps), "fragility_at_least_2": float(h[2:].sum() / reps),
                      "fragility_at_least_3": float(h[3:].sum() / reps),
                      "fragility_at_least_6": float(h[6:].sum() / reps), "counts": h.tolist(),
                      "rejected_d20": d20[t] / reps}
            if t in dense:
                row[t]["carried_out_share_d20"] = dense[t] / reps
        rows.append(row)
        print(f"R-S1 {name:24s} " + " | ".join(f"{t} {row[t]['rejected']:.3f} D20 {row[t]['rejected_d20']:.3f}"
                                               f" >=2 {row[t]['fragility_at_least_2']:.3f}" for t in hist)
              + " | carried out " + " ".join(f"{t} {row[t]['carried_out_share_d20']:.3f}" for t in dense)
              + f" | {row['seconds']}s", flush=True)
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=20000)
    ap.add_argument("--rs1-reps", type=int, default=2000)
    ap.add_argument("--out", default="")
    a = ap.parse_args(argv)
    D = dgp.design()
    t0 = time.time()
    fam = family(np.random.default_rng(SEED), D, a.reps)
    rs = rs1(D, a.rs1_reps)
    worst = max(fam, key=lambda r: r["rate_registered"])
    print(f"largest rate of the registered decision in the family: {worst['rate_registered']:.4f} "
          f"(s={worst['spike']}, lambda={worst['lambda']}, bg={worst['background']}; nominal .02); "
          f"{time.time() - t0:.0f}s")
    w20 = max(fam, key=lambda r: r["rate_d20"])
    print(f"largest rate with the condition of D20: {w20['rate_d20']:.4f} (s={w20['spike']}, lambda={w20['lambda']}, "
          f"bg={w20['background']}, mean share {w20['mean_share_nonzero']:.2f})")
    if a.out:
        path = HERE / "output" / a.out
        path.write_text(json.dumps({"run": "sparse (run j)", "seed": SEED, "family": fam, "rs1": rs,
                                    "kmax": FR.KMAX, "d20_threshold": DN.THRESHOLD}, indent=1), encoding="utf-8")
        print("written", path)


if __name__ == "__main__":
    main()
