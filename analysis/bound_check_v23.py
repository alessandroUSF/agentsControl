"""Blind bound among screened answers: observed rejection rates against a normal approximation.

Reads the simulation outputs analysis/output/power_sim_v23_alts_bound*.json (statistic "h11scr": on-policy panel,
answers that pass the refusal screen). For each scenario it prints the mean estimate of the blind gap among
screened answers (which estimates the true gap; Monte Carlo error = SE / sqrt(replications)), the within-panel
standard error, the share of replications in which H0: gap <= -margin was rejected at the one-sided level 0.01,
and the rejection rate that a normal statistic with that mean and standard error would give at the 7-pp margin.

Files named "bound1panel" were simulated with one fixed judge panel; the others redraw 20 panels, so the true
gap differs between panels and the observed rate is a mixture.

Usage: python -I analysis/bound_check_v23.py
"""
import json
from pathlib import Path
from statistics import NormalDist

OUT = Path(__file__).resolve().parent / "output"
Z = NormalDist().inv_cdf(0.99)


def main():
    files = sorted(OUT.glob("power_sim_v23_alts_bound*.json"))
    for f in files:
        rows = json.loads(f.read_text(encoding="utf-8"))["rows"]
        print(f"{f.name}: {rows[0]['reps']} replications, {rows[0]['panels']} panel(s), "
              f"{rows[0]['flips']} sign vectors")
        print("  mean gap (pp) | SE (pp) | rejected at margin 5 / 7 / 10 pp (%) | normal approximation, margin 7 (%)")
        obs, approx = [], []
        for r in rows:
            a = r["alt"]["h11scr"]
            gap, se = 100 * a["ratio_blind"], 100 * a["se_ratio_blind"]
            b = a["bound_reject"]
            n7 = 100 * NormalDist().cdf(-Z + (gap + 7.0) / se)
            obs.append(100 * b["0.07"])
            approx.append(n7)
            print(f"  {gap:+.2f} | {se:.2f} | {100 * b['0.05']:.2f} / {100 * b['0.07']:.2f} / {100 * b['0.1']:.2f} | {n7:.2f}")
        print(f"  average over scenarios, margin 7: observed {sum(obs) / len(obs):.2f}%, "
              f"approximation {sum(approx) / len(approx):.2f}%")
        print()


if __name__ == "__main__":
    main()
