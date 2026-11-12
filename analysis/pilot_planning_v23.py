"""Run (f) of Appendix A.4: the pilot planning scenarios (the mapping, its grid and the report of targets that
cannot be reached). Fixed with the pilot registration, before any pilot call.

Rule (A.4): pilot planning scenarios reproduce observable screen and blind-flag marginals where feasible. Harm
prevalence, screen accuracy and sensitivity remain assumed nuisance parameters varied over a registered grid.
Unattainable targets are reported explicitly and never silently clipped.

What the pilot gives (Section 13.3, rule 6), both without labels:
  s_m  for each model m of the primary panel: the share of screen-positive answers among its pilot answers to
       harmful prompts;
  f_j  for each judge j: the blind flag rate on its own screen-positive pilot answers (delivered flags: a verdict
       that was not delivered counts as no flag, Section 10.2).
Small counts: a model with fewer than 30 pilot answers to harmful prompts takes the share of its group, and a
judge with fewer than 20 screen-positive pilot answers takes the flag rate of its group. The group's value is
pooled over the models of the group in the panel: total screen-positive answers over total answers, total
flags over total screen-positive answers.

The grid: three assumptions about the screen, (a, b) = (0.9, 0.2), (1, 0) and (0.7, 0.4), where a is the share of
answers with harmful content that are screen-positive and b the same share for the other answers.

The mapping, at each point (a, b):
  1. The rate r_m of harmful answers of model m solves s_m = a r_m + b (1 - r_m), r_m = (s_m - b) / (a - b). A
     solution exists only when b <= s_m <= a; the model needs a rate strictly between 0 and 1, so a solution below
     1% or above 99% also counts as not reached.
  2. The sensitivity of judge j is the value at which its expected blind flag rate on its own screen-positive
     answers equals f_j. Its specificity keeps the baseline value (sim_v23_dgp.judge_accuracy). Under the latent
     model of sim_v23_dgp.py, with no presentation shift:
         rate(Se) = (1 - i_b) [pi_j E expit(logit Se + Z) + (1 - pi_j) E expit(logit(1 - Sp_j) + Z)],
         pi_j = a r_j / (a r_j + b (1 - r_j))   (share of harmful answers among its screen-positive answers),
         Z ~ N(0, 0.6^2 + 0.6^2 + 0.4^2)        (prompt, answer and call effects of the blind logit),
         i_b = 3%                                (invalid blind verdicts of the baseline).
     A solution exists only when f_j lies between the rates at the lowest and at the highest sensitivity. As for
     the rates, the sensitivity is kept between 1% and 99% (A.4 states the 1%-99% range for rates; this module
     applies it to sensitivities too, and says so in the report).
  3. Everything else is as in the baseline of A.1.
Targets that cannot be reached: every case is listed (model or judge, the target, the nearest value that can be
reached), the nearest value is used, and the scenario is marked "target not reproduced". No value is replaced
without this record. With the pair (1, 0) every share between 1% and 99% is reached, because r_m = s_m.

Where the scenarios run: each point of the grid gives one scenario in each package, named pilot_<a>_<b>:
  R-S1 with its five rows             sim_v23_registered.py --grid pilot_rs1 --pilot FILE
  R-S2 with the aligned judge shifts on all content, rows zero and null
                                      sim_v23_registered.py --grid pilot_rs2 --pilot FILE
  R-S3 with no effect and with theta_S = iota_S = -5 points
                                      sim_v23_labels.py --grid pilot --pilot FILE
The power table of Section 8.4 is computed again from the rows of R-S1 and shown as a range over the grid.

Input (written from counts by the pilot report; no answer text):
  {"models": {"<model number>": {"answers": <pilot answers to harmful prompts>,
                                 "screen_positive": <screen-positive answers among them>}, ...},
   "judges": {"<model number>": {"screen_positive": <own screen-positive pilot answers judged blind>,
                                 "blind_flags": <delivered blind flags on them>}, ...}}
A model of the panel without a record counts as one with no pilot answer (it takes its group's value). Records of
models outside the panel (a hosted model that is not registered, Section 10.4) are not used.

Usage: python -I analysis/pilot_planning_v23.py --pilot PILOT.json [--drop 22] [--out pilot_planning_v23.json]
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import brentq
from scipy.special import expit, logit

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import sim_v23_dgp as dgp  # noqa: E402

GRID = ((0.9, 0.2), (1.0, 0.0), (0.7, 0.4))
RATE_MIN, RATE_MAX = 0.01, 0.99
MIN_ANSWERS, MIN_POSITIVE = 30, 20
GROUP_NAMES = {"i": "instruction-tuned", "r": "refusal-removed"}
_X, _W = np.polynomial.hermite_e.hermegauss(80)
_W = _W / _W.sum()
SD_BLIND = float(np.sqrt(dgp.SD_PROMPT ** 2 + dgp.SD_ANSWER ** 2 + dgp.SD_CALL ** 2))


def point_name(a, b):
    return f"pilot_{a:g}_{b:g}"


def _mean_expit(p):
    """E expit(logit(p) + Z), Z ~ N(0, SD_BLIND), by Gauss-Hermite quadrature."""
    return float((_W * expit(logit(p) + SD_BLIND * _X)).sum())


def blind_rate(se, sp, rate, a, b, inv_blind):
    """Expected delivered blind flag rate of a judge on its own screen-positive answers (step 2 of the mapping)."""
    pos_h, pos_o = a * rate, b * (1 - rate)
    pi = pos_h / (pos_h + pos_o)
    return (1 - inv_blind) * (pi * _mean_expit(se) + (1 - pi) * _mean_expit(1 - sp))


def observed(pilot, D):
    """s_m and f_j for the models of D (in panel order), with the small-count rule. Returns arrays and the notes
    of every value that was taken from the group."""
    models = {int(k): v for k, v in pilot.get("models", {}).items()}
    judges = {int(k): v for k, v in pilot.get("judges", {}).items()}
    J = len(D["judges"])
    share, flag, notes = np.zeros(J), np.zeros(J), []
    for g in sorted(set(D["group"])):
        members = [m for m, gg in zip(D["judges"], D["group"]) if gg == g]
        n_ans = sum(int(models.get(m, {}).get("answers", 0)) for m in members)
        n_pos = sum(int(models.get(m, {}).get("screen_positive", 0)) for m in members)
        n_own = sum(int(judges.get(m, {}).get("screen_positive", 0)) for m in members)
        n_flag = sum(int(judges.get(m, {}).get("blind_flags", 0)) for m in members)
        if n_ans == 0 or n_own == 0:
            raise ValueError(f"group {GROUP_NAMES[g]}: no pilot answer or no screen-positive answer judged blind")
        g_share, g_flag = n_pos / n_ans, n_flag / n_own
        for m in members:
            j = D["judges"].index(m)
            rec, jr = models.get(m, {}), judges.get(m, {})
            n, k = int(rec.get("answers", 0)), int(rec.get("screen_positive", 0))
            if not 0 <= k <= n:
                raise ValueError(f"model {m}: {k} screen-positive answers out of {n}")
            if n >= MIN_ANSWERS:
                share[j] = k / n
            else:
                share[j] = g_share
                notes.append({"kind": "share", "model": m, "answers": n,
                              "rule": f"fewer than {MIN_ANSWERS} pilot answers: share of its group",
                              "group_value": g_share})
            n, k = int(jr.get("screen_positive", 0)), int(jr.get("blind_flags", 0))
            if not 0 <= k <= n:
                raise ValueError(f"judge {m}: {k} blind flags on {n} screen-positive answers")
            if n >= MIN_POSITIVE:
                flag[j] = k / n
            else:
                flag[j] = g_flag
                notes.append({"kind": "flag", "judge": m, "screen_positive": n,
                              "rule": f"fewer than {MIN_POSITIVE} screen-positive pilot answers: flag rate of its group",
                              "group_value": g_flag})
    return share, flag, notes


def mapping(share, flag, D, a, b):
    """Rates of harmful answers and sensitivities at one point (a, b) of the grid, with the record of every target
    that cannot be reached (step 1: the screen-positive share of a model; step 2: the blind flag rate of a judge)."""
    sp = dgp.judge_accuracy(D)[1]
    inv_blind = float(dgp.invalid_probs(dgp.BASE["inv"], False)[0])
    J = len(D["judges"])
    rates, se, unreached = np.zeros(J), np.zeros(J), []
    for j, m in enumerate(D["judges"]):
        r = (share[j] - b) / (a - b)
        if not RATE_MIN <= r <= RATE_MAX:
            near = min(max(r, RATE_MIN), RATE_MAX)
            unreached.append({"what": "screen-positive share", "model": m, "target": float(share[j]),
                              "nearest": float(a * near + b * (1 - near)), "rate_used": float(near),
                              "why": "the rate of harmful answers would be "
                                     + (f"{r:.4f}, outside 1% to 99%" if b <= share[j] <= a
                                        else f"{r:.4f}: the share lies outside [{b}, {a}]")})
            r = near
        rates[j] = r
    for j, m in enumerate(D["judges"]):
        def gap(x, j=j):
            return blind_rate(x, sp[j], rates[j], a, b, inv_blind) - flag[j]
        lo, hi = gap(RATE_MIN), gap(RATE_MAX)
        if lo > 0 or hi < 0:
            end = RATE_MIN if lo > 0 else RATE_MAX
            unreached.append({"what": "blind flag rate", "judge": m, "target": float(flag[j]),
                              "nearest": float(flag[j] + (lo if lo > 0 else hi)), "sensitivity_used": end,
                              "why": "no sensitivity between 1% and 99% gives this rate"})
            se[j] = end
        else:
            se[j] = RATE_MIN if lo == 0 else RATE_MAX if hi == 0 else float(brentq(gap, RATE_MIN, RATE_MAX,
                                                                                   xtol=1e-10))
    return rates, se, unreached


def points(pilot, D):
    """One base scenario per point of the grid (overrides of dgp.BASE, complete), and the report.
    pilot: the file of pilot rates or its parsed content."""
    if not isinstance(pilot, dict):
        pilot = json.loads(Path(pilot).read_text(encoding="utf-8"))
    share, flag, notes = observed(pilot, D)
    out, report = {}, {"panel": list(D["judges"]), "dropped": list(D.get("dropped", [])), "small_counts": notes,
                       "observed": {"share": {str(m): float(s) for m, s in zip(D["judges"], share)},
                                    "flag": {str(m): float(f) for m, f in zip(D["judges"], flag)}},
                       "points": {}}
    gi, gr = D["group"] == "i", D["group"] == "r"
    for a, b in GRID:
        rates, se, unreached = mapping(share, flag, D, a, b)
        name = point_name(a, b)
        out[name] = dict(dgp.BASE, screen_se=float(a), screen_sp=float(1 - b),
                         fail_i=[float(x) for x in rates[gi]], fail_r=[float(x) for x in rates[gr]],
                         se_judge=[float(x) for x in se], target_not_reproduced=bool(unreached))
        report["points"][name] = {"screen": [a, b], "target_not_reproduced": bool(unreached),
                                  "unreached": unreached,
                                  "rates": {str(m): float(r) for m, r in zip(D["judges"], rates)},
                                  "sensitivity": {str(m): float(s) for m, s in zip(D["judges"], se)}}
    return out, report


def show(report):
    print(f"panel {report['panel']}" + (f" (without {report['dropped']})" if report["dropped"] else ""))
    for n in report["small_counts"]:
        who = f"model {n['model']}" if n["kind"] == "share" else f"judge {n['judge']}"
        print(f"  small count: {who}: {n['rule']} ({n['group_value']:.4f})")
    for name, p in report["points"].items():
        state = "TARGET NOT REPRODUCED" if p["target_not_reproduced"] else "all targets reproduced"
        print(f"{name}: screen (a, b) = ({p['screen'][0]}, {p['screen'][1]}): {state}")
        for u in p["unreached"]:
            who = f"model {u['model']}" if "model" in u else f"judge {u['judge']}"
            print(f"  not reached: {u['what']} of {who}: target {u['target']:.4f}, nearest {u['nearest']:.4f} "
                  f"({u['why']})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", required=True, help="pilot rates (JSON, format in the module docstring)")
    ap.add_argument("--drop", default="", help="hosted models left out of the panel, e.g. 22, 23 or 22,23")
    ap.add_argument("--out", default="pilot_planning_v23.json", help="file under analysis/output")
    a = ap.parse_args()
    D = dgp.design(drop=tuple(int(x) for x in a.drop.replace(" ", "").split(",") if x))
    scen, report = points(a.pilot, D)
    report["scenarios"] = scen
    show(report)
    out = HERE / "output" / a.out
    out.write_text(json.dumps(report, indent=1), encoding="utf-8")
    print("written", out)


if __name__ == "__main__":
    main()
