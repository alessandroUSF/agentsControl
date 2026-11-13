"""Run (k) of Appendix A.4 (protocol v2.3, since 13 November 2026): the cases of the fourth round of fresh readings
(Section 17.1), measured with the production code (inference_v23, density_v23; sim_v23_registered.draw, not changed).

Part 1, P3 at the boundary of its null with concentrated deficits (GPT-6.1 Sol). Every prompt has N_p = 6
screen-positive answers. With probability pi a prompt carries a deficit of m answers (the author does not flag, the
control flags: a total of -m), otherwise 0, with pi * m / 6 = 0.07, so beta_S = -0.07, the boundary of the null of
P3. Optionally a symmetric background change of +1 or -1, each with probability bg / 2; the deficit and the background
change are disjoint outcomes of the prompt, so that |X_p| <= N_p and the mean stays -0.07 * 6 (since code review round
12; the first run of 13 November 2026 added the background change to the deficit, which could give a total of -7).
Printed: the rate at which P3 rejects (nominal .01) and its Monte Carlo standard error.

Part 2, P1 and P2 with rare large rises among many small changes, dense enough for D20 (GPT-6.1 Sol). Every prompt
has N_p = n screen-positive answers. The author's total is +s with probability lam / 300, -1 with probability a,
+1 with probability b, and 0 otherwise, with a - b = s * lam / 300 so that its mean is zero; the controls' totals are
zero, so theta_S and iota_S have the same totals and Holm rejects both or neither, when p <= .02 (nominal family
rate .02 here; .04 is the level of the family). Printed: the rate of the registered decision, the rate under the
condition of D20, and the mean share of prompts with a nonzero total.

Part 3, the condition of D20 when the background discordance is low (Claude Opus 5.5). Rows of R-S1 (Appendix A.1)
drawn with the registered model at q0 = 0, 0.025 and 0.05 (0.10 in the baseline), under the null and with
theta = -0.05 or iota = -0.05. The baseline shocks (sd_common = sd_own = 0.3) put a floor of about 0.041 under the
discordance that the coupling rho can reach, so the rows at q0 = 0 and 0.025 use smaller shocks (0 and 0.1; floors 0
and about 0.014; RS1_SD). Every row records its calibration (rho, the floor, the discordance with independent draws,
and any target not reached), and the run stops if a target is not reached (since code review round 12: the first run
used the baseline shocks at every q0 and so ran the rows at 0 and 0.025 at the floor). Printed: the share of
replications in which each test is carried out under D20 (dense, and a positive estimated variance), the share that
is dense, and the rate of each test with and without the condition.
Since 13 November 2026 (the PI's answer to the fifth round of fresh readings), Part 3 also has the rows of effects of
-2 and -3 points (theta or iota = -0.02, -0.03) at each q0, and the rows of the baseline q0 = 0.10 (baseline shocks).
Every row draws from its own named stream, so the rows of the first run are unchanged; --add-to computes only the rows
of Part 3 that a stored output does not hold and writes the stored output with them added (Parts 1 and 2 are kept).

Usage (from the repository root):
  python -I analysis/sim_v23_tails.py --out sim_v23_tails.json
  python -I analysis/sim_v23_tails.py --add-to sim_v23_tails.json --out sim_v23_tails.json   (missing Part 3 rows)
  python -I analysis/sim_v23_tails.py --reps 2000 --rs1-reps 100            (a small run, nothing written)"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent / "src")]
import density_v23 as DN  # noqa: E402
import inference_v23 as inf  # noqa: E402
import sim_v23_dgp as dgp  # noqa: E402
import sim_v23_registered as SR  # noqa: E402

SEED = 20261113
P3_ROWS = [dict(m=6, bg=0.0), dict(m=6, bg=0.1), dict(m=6, bg=0.2), dict(m=3, bg=0.0), dict(m=3, bg=0.1),
           dict(m=2, bg=0.0)]
P12_ROWS = [dict(n=12, s=12, lam=2.0, b=0.20), dict(n=12, s=12, lam=1.0, b=0.20), dict(n=12, s=12, lam=4.0, b=0.20),
            dict(n=12, s=12, lam=2.0, b=0.10), dict(n=6, s=6, lam=2.0, b=0.20), dict(n=6, s=6, lam=4.0, b=0.20)]
RS1_SD = {0.0: 0.0, 0.025: 0.1, 0.05: 0.3, 0.10: 0.3}   # target q0 -> sd_common = sd_own that reaches it (0.10: base)
RS1 = {}
for _q, _sd in RS1_SD.items():
    _base = dict(q0=_q, sd_common=_sd, sd_own=_sd)
    RS1[f"q0_{_q}|null"] = dict(_base)
    RS1[f"q0_{_q}|theta"] = dict(_base, theta=-0.05)
    RS1[f"q0_{_q}|iota"] = dict(_base, iota=-0.05)
    for _e in (0.02, 0.03):                  # since 13 November 2026: effects of -2 and -3 points
        RS1[f"q0_{_q}|theta_{_e}"] = dict(_base, theta=-_e)
        RS1[f"q0_{_q}|iota_{_e}"] = dict(_base, iota=-_e)


def mcse(p, n):
    return float(np.sqrt(max(p * (1 - p), 1e-12) / n))


def p3_draw(rng, R, P, m, bg):
    """Totals X of R replications of P prompts with N_p = 6: -m with probability pi = 0.07 * 6 / m, +1 and -1 with
    probability bg / 2 each, 0 otherwise (disjoint outcomes, so |X_p| <= 6 and the mean is -0.42)."""
    pi = 0.07 * 6 / m
    if not 0 < m <= 6 or pi + bg > 1:
        raise ValueError(f"m={m}, bg={bg}: not a distribution with |X_p| <= 6")
    u = rng.random((R, P))
    X = np.where(u < pi, -float(m), np.where(u < pi + bg / 2, 1.0, np.where(u < pi + bg, -1.0, 0.0)))
    assert np.abs(X).max() <= 6
    return X


def d20_counts(d):
    """Of the output of density_v23.decide, for P1 and P2: the replications in which the test is carried out
    (dense and a positive estimated variance), those that are dense, and the summed share of nonzero totals."""
    return {k: (int(np.asarray(d[k + "_carried_out"]).sum()), int(np.asarray(d[k + "_dense"]).sum()),
                float(np.asarray(d[k + "_share"]).sum())) for k in ("p1", "p2")}


def calibrated(D, name, rng, reps=1000):
    """Scenario, panel quality, shifts, coupling and calibration record of one row of Part 3. Raises when a
    target (q0, theta or theta - iota) cannot be reached, so that no row runs silently at another value."""
    sc = dict(dgp.BASE, **RS1[name])
    q = dgp.panel_quality(D, sc)
    g, rho, diag = dgp.calibrate(rng, D, sc, q, reps)
    if diag["unreached"]:
        raise ValueError(f"{name}: target not reached: {diag['unreached']} (q0 floor {diag['q0_floor']:.4f})")
    cal = dict(q0_target=sc["q0"], sd_common=sc["sd_common"], sd_own=sc["sd_own"], rho=rho,
               q0_floor=diag["q0_floor"], q0_independent=diag["q0_independent"], unreached=diag["unreached"])
    return sc, q, g, rho, cal


def p3_boundary(rng, D, reps, chunk=20000):
    strata, P = np.asarray(D["strata"]), D["P"]
    rows = []
    for row in P3_ROWS:
        m, bg = row["m"], row["bg"]
        pi = 0.07 * 6 / m
        rej = done = 0
        while done < reps:
            R = min(chunk, reps - done)
            done += R
            X = p3_draw(rng, R, P, m, bg)
            N = np.full((R, P), 6.0)
            r = inf.cluster_ratio(X, N, strata)
            zero = inf.cluster_ratio(np.zeros((R, P)), N, strata)
            rej += int(np.asarray(inf.registered_tests(zero, zero, r)["p3"]).sum())
        rate = rej / reps
        rows.append(dict(row, pi=pi, beta=-0.07, reps=reps, rate=rate, mcse=mcse(rate, reps), nominal=0.01))
        print(f"P3 m={m} pi={pi:.4f} bg={bg}: rate {rate:.4f} (MCSE {mcse(rate, reps):.4f}; nominal .01)", flush=True)
    return rows


def p12_heavy(rng, D, reps, chunk=20000):
    strata, P = np.asarray(D["strata"]), D["P"]
    rows = []
    for row in P12_ROWS:
        n, s, lam, b = row["n"], row["s"], row["lam"], row["b"]
        q = lam / P
        a = b + s * q
        reg = d20 = 0
        share = 0.0
        done = 0
        while done < reps:
            R = min(chunk, reps - done)
            done += R
            u = rng.random((R, P))
            X = np.where(u < q, float(s), np.where(u < q + a, -1.0, np.where(u < q + a + b, 1.0, 0.0)))
            N = np.full((R, P), float(n))
            r = inf.cluster_ratio(X, N, strata)
            zero = inf.cluster_ratio(np.zeros((R, P)), N, strata)
            t = inf.registered_tests(r, r, zero)
            reg += int((np.asarray(t["p1"]) | np.asarray(t["p2"])).sum())
            d = DN.decide(r, r, zero, X, X, N)
            d20 += int((np.asarray(d["p1"]) | np.asarray(d["p2"])).sum())
            share += float(np.asarray(d["p1_share"]).sum())
        out = dict(row, a=a, reps=reps, rate_registered=reg / reps, mcse_registered=mcse(reg / reps, reps),
                   rate_d20=d20 / reps, mcse_d20=mcse(d20 / reps, reps), mean_share_nonzero=share / reps,
                   nominal=0.02)
        rows.append(out)
        print(f"P1/P2 n={n} s={s} lam={lam} b={b} a={a:.4f}: registered {out['rate_registered']:.4f}, with D20 "
              f"{out['rate_d20']:.4f} (MCSE {out['mcse_d20']:.4f}), share {out['mean_share_nonzero']:.2f}; "
              f"nominal .02", flush=True)
    return rows


def rs1(D, reps, chunk=250, skip=()):
    rows = []
    strata = np.asarray(D["strata"])
    for name, kw in RS1.items():
        if name in skip:
            continue
        t0 = time.time()
        r_cal, _, r_sim = SR.streams("tails_" + name, SEED)
        sc, q, g, rho, cal = calibrated(D, name, r_cal)
        reg = {t: 0 for t in ("p1", "p2", "p3")}
        d20 = {t: 0 for t in ("p1", "p2", "p3")}
        carried = {t: 0 for t in ("p1", "p2")}
        dense = {t: 0 for t in ("p1", "p2")}
        share = {t: 0.0 for t in ("p1", "p2")}
        done = 0
        while done < reps:
            R = min(chunk, reps - done)
            done += R
            S, A1, A2, C1, C2, _ = SR.draw(r_sim, R, D, sc, q, g, rho)
            dA, dC = (A2 - A1).astype(np.int32), (C2 - C1).astype(np.int32)
            X = {"th": (S * dA).sum(1), "io": (S * (dA - dC)).sum(1), "be": (S * (A1 - C1).astype(np.int32)).sum(1)}
            N = S.sum(1, dtype=np.int32)
            r = {k: inf.cluster_ratio(X[k], N, strata) for k in ("th", "io", "be")}
            t = inf.registered_tests(r["th"], r["io"], r["be"])
            d = DN.decide(r["th"], r["io"], r["be"], X["th"], X["io"], N)
            for k in reg:
                reg[k] += int(np.asarray(t[k]).sum())
                d20[k] += int(np.asarray(d[k]).sum())
            for k, (c, n_dense, s) in d20_counts(d).items():
                carried[k] += c
                dense[k] += n_dense
                share[k] += s
        row = {"row": name, "reps": reps, "seconds": round(time.time() - t0, 1), "calibration": cal}
        for k in reg:
            row[k] = {"rejected": reg[k] / reps, "rejected_d20": d20[k] / reps}
            if k in dense:
                row[k]["carried_out_share_d20"] = carried[k] / reps
                row[k]["dense_share_d20"] = dense[k] / reps
                row[k]["mean_share_nonzero"] = share[k] / reps
        rows.append(row)
        print(f"R-S1 {name:18s} sd {cal['sd_common']} rho {rho:.4f} floor {cal['q0_floor']:.4f} | " + " | ".join(
            f"{k} {row[k]['rejected']:.3f} D20 {row[k]['rejected_d20']:.3f}"
            + (f" carried {row[k]['carried_out_share_d20']:.3f} share {row[k]['mean_share_nonzero']:.2f}"
               if k in dense else "") for k in reg) + f" | {row['seconds']}s", flush=True)
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=200000)
    ap.add_argument("--rs1-reps", type=int, default=2000)
    ap.add_argument("--out", default="")
    ap.add_argument("--add-to", default="", help="a stored output: compute only the Part 3 rows it does not hold")
    a = ap.parse_args(argv)
    D = dgp.design()
    t0 = time.time()
    if a.add_to:
        old = json.loads((HERE / "output" / a.add_to).read_text(encoding="utf-8"))
        if old.get("seed") != SEED or old.get("d20_threshold") != DN.THRESHOLD:
            raise SystemExit("the stored output was made with another seed or threshold")
        have = [r["row"] for r in old["rs1_low_discordance"]]
        new = rs1(D, a.rs1_reps, skip=set(have))
        if any(r["reps"] != a.rs1_reps for r in old["rs1_low_discordance"]):
            raise SystemExit("the stored rows have another number of replications")
        order = list(RS1)
        old["rs1_low_discordance"] = sorted(old["rs1_low_discordance"] + new, key=lambda r: order.index(r["row"]))
        print(f"added {len(new)} rows in {time.time() - t0:.0f}s")
        if a.out:
            path = HERE / "output" / a.out
            path.write_text(json.dumps(old, indent=1), encoding="utf-8")
            print("written", path)
        return
    rng = np.random.default_rng(SEED)
    p3 = p3_boundary(rng, D, a.reps)
    p12 = p12_heavy(rng, D, a.reps)
    rs = rs1(D, a.rs1_reps)
    print(f"done in {time.time() - t0:.0f}s")
    if a.out:
        path = HERE / "output" / a.out
        path.write_text(json.dumps({"run": "tails (run k)", "seed": SEED, "p3_boundary": p3, "p12_heavy": p12,
                                    "rs1_low_discordance": rs, "d20_threshold": DN.THRESHOLD}, indent=1),
                        encoding="utf-8")
        print("written", path)


if __name__ == "__main__":
    main()
