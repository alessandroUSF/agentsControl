"""Run (h) of Appendix A.4 (protocol v2.3, since 12 November 2026): rare, asymmetric changes concentrated on few
prompts.

The registered t test of Section 8.1 refers the prompt-clustered ratio to Student's t. Its level is nominal: no test
of a mean controls its size for every distribution of the per-prompt totals (Bahadur and Savage, 1956). A sample can
miss rare, large changes that carry the mean, and then any test of the mean rejects too often. This run measures how
far the registered tests are from their nominal level when the in-context change is concentrated on few prompts.

Scenario. The baseline of R-S1 (Appendix A.1), with one more per-prompt term in the in-context logit: with
probability p a prompt receives a shift of L logits on every in-context verdict of the arm(s) named, and none
otherwise. 'own' adds it to the author arm only (it moves theta_S and iota_S); 'common' adds it to the author and the
control arm (it moves theta_S and theta_S of the controls, not iota_S). The calibrated fixed shifts of Appendix A.1
then set theta_S = iota_S = 0 (rows '|null'): the changes are rare and large on few prompts, small and of the other
sign on all the rest, and their mean is zero. Rows and checks:
  skew_own_p0.0067_L6    on average 2 of the 300 prompts carry the shift (none in about 13% of the samples)
  skew_own_p0.02_L6      on average 6 prompts
  skew_own_p0.02_L3
  skew_own_p0.05_L3      on average 15 prompts
  skew_own_p0.02_L-6     the same concentration, in the other direction
  skew_common_p0.02_L6   the shift in both arms
Checks 1 and 4 of Appendix A.4, as for R-S1. The rows are published whether they pass or not; a failure is a
documented limit of the nominal level (Section 8.1), not a reason to change the test after the fact.

The code of the other runs is not changed: this module wraps sim_v23_dgp.draw_latent and calls
sim_v23_registered.run_scenario, so the fingerprints of the stored rows of runs (a) to (g) stay valid. The
fingerprint of a row here adds this file.

Usage (from the repository root):
  python -I analysis/sim_v23_skew.py --reps 10000 --flips 9999 --out sim_v23_skew.json
  python -I analysis/sim_v23_skew.py --reps 200 --flips 199                     (a small run, nothing written)
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "src"))
import frames_v23  # noqa: E402
import inference_v23 as inf  # noqa: E402
import sim_v23_dgp as dgp  # noqa: E402
import sim_v23_registered as SR  # noqa: E402
import yoking  # noqa: E402

ROWS = {
    "skew_own_p0.0067_L6": dict(rare_own=(1 / 150, 6.0)),
    "skew_own_p0.02_L6": dict(rare_own=(0.02, 6.0)),
    "skew_own_p0.02_L3": dict(rare_own=(0.02, 3.0)),
    "skew_own_p0.05_L3": dict(rare_own=(0.05, 3.0)),
    "skew_own_p0.02_L-6": dict(rare_own=(0.02, -6.0)),
    "skew_common_p0.02_L6": dict(rare_common=(0.02, 6.0)),
}
_DRAW = dgp.draw_latent


def draw_latent(rng, R, D, sc, q):
    """sim_v23_dgp.draw_latent, then the rare per-prompt shift of the scenario (see the module text)."""
    L = _DRAW(rng, R, D, sc, q)
    for key, arms in (("rare_own", ("a",)), ("rare_common", ("a", "c"))):
        spec = sc.get(key)
        if not spec:
            continue
        p, shift = spec
        spike = np.where(rng.random((R, 1, D["P"])) < p, shift, 0.0).astype(dgp.F32)
        for arm in arms:
            L["shock_" + arm] = (L["shock_" + arm] + spike).astype(dgp.F32)
    return L


dgp.draw_latent = draw_latent       # read at call time by sim_v23_dgp.calibrate and sim_v23_registered


def grid():
    return {f"{name}|null": dict(dgp.BASE, **kw) for name, kw in ROWS.items()}


def fingerprint(name, sc, D, reps, flips, clusters, cal_reps, chunk, seed):
    h = hashlib.sha256()
    files = {Path(m.__file__).resolve() for m in (inf, dgp, frames_v23, yoking, SR)} | {Path(__file__).resolve()}
    for f in sorted(files):
        h.update(f.read_bytes().replace(b"\r\n", b"\n"))
    h.update(json.dumps(dgp.canon([name, sc, D, reps, flips, clusters, cal_reps, chunk, seed, SR.BASE_SEED]),
                        sort_keys=True).encode("utf-8"))
    return h.hexdigest()


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=SR.BASE_SEED)
    ap.add_argument("--reps", type=int, default=200)
    ap.add_argument("--flips", type=int, default=199)
    ap.add_argument("--clusters", type=int, default=1_000_000)
    ap.add_argument("--cal-reps", type=int, default=1000)
    ap.add_argument("--chunk", type=int, default=250)
    ap.add_argument("--only", default="")
    ap.add_argument("--out", default="")
    a = ap.parse_args(argv)
    D = dgp.design()
    path = SR.OUT_DIR / a.out if a.out else None
    rows = json.loads(path.read_text(encoding="utf-8")).get("rows", []) if path and path.exists() else []
    for name, sc in grid().items():
        if a.only and a.only not in name:
            continue
        fp = fingerprint(name, sc, D, a.reps, a.flips, a.clusters, a.cal_reps, a.chunk, a.seed)
        if any(r["name"] == name and r.get("fingerprint") == fp for r in rows):
            continue
        row = SR.run_scenario(name, sc, D, a.reps, a.flips, a.clusters, a.cal_reps, a.chunk, a.seed)
        row.update(seed=a.seed, clusters=a.clusters, cal_reps=a.cal_reps, chunk=a.chunk, fingerprint=fp)
        rows = [r for r in rows if r["name"] != name] + [row]
        s = row["summary"]
        print("%-28s th %+.4f (ref %+.4f) cov %s | io %+.4f (ref %+.4f) cov %s | P1 %.4f P2 %.4f any %.4f "
              "| p3 %.3f | %.0fs"
              % (name, s["th"]["mean"], s["th"]["reference"], SR._fmt(s["th"]["cover95"]), s["io"]["mean"],
                 s["io"]["reference"], SR._fmt(s["io"]["cover95"]), s["registered"]["holm_theta"],
                 s["registered"]["holm_iota"], s["registered"]["any"], s["p3_reject"], row["seconds"]), flush=True)
        for u in row["calibration"]["unreached"]:
            print(f"    TARGET NOT REACHED: {u['name']} = {u['target']}; nearest {u['nearest']}", flush=True)
        for c in row["checks"]:
            if c["made"] and not c["passed"]:
                print(f"    CHECK {c['check']} FAILS: {c['what']} {c['value']:.4f} against {c['limit']:.4f} "
                      f"(R {c['R']})", flush=True)
        if path:
            path.write_text(json.dumps({"grid": "skew (run h)", "judges": D["judges"], "rows": rows}, indent=1),
                            encoding="utf-8")


if __name__ == "__main__":
    main()
