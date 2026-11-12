"""Run (d) of Appendix A.4: the safe-side simulation. It checks the intervals of Section 8.7 (check 6).

Frame and judges. The 90 prompts of the safe frame. The primary panel (twelve models, or fewer with --drop) with
its control assignment on the safe frame; the commercial models (ten since decision D17), each classifying its own 90 answers, with
control verdicts on the 30 commercial safe controls only (Section 8.7). The assignments are the production ones
(src/yoking.py) with the block labels of scripts/control_assignment_v23.py ("<block>|safe", "commercial|safe").

Flag. The verdict classifies the answer as a refusal. The latent model of sim_v23_dgp.py is used with "contains a
refusal" in the place of "has harmful content":
  an answer contains a refusal with probability 15% (instruction-tuned models), 2% (refusal-removed models) and
  10% (commercial models); it is screen-negative with probability 0.8 if it contains a refusal and 0.05 otherwise;
  judges: sensitivity, specificity and the dependence of the two verdicts as in the baseline of A.1 (Se ~
  U(0.70, 0.95), Sp ~ U(0.85, 0.98), 10% of the author's verdict pairs differ under no effect). The commercial
  judges draw theirs with their own seed.
Invalid verdicts: two settings, safe|inv_3 (3% in each presentation) and safe|inv_10_15 (10% blind, 15% in context).
No presentation effect: every presentation shift is zero. In A.1 the in-context shift has three parts, a fixed
amount, a shock of the prompt shared by all judges and a second shock in the author arm; all three are zero here
(as in literal_null|zero of R-S2), and the dependence of the two verdicts is calibrated to the baseline's 10%
discordance without them. (Reading of A.4: "Every presentation shift is zero" and "no presentation effect in the
simulated data", Section 8.7.) The invalid verdicts still differ between the presentations in safe|inv_10_15, so
the true values are computed, from about one million independent prompt clusters for every statistic.

What is checked: the 95% intervals over all answers ("all") and among screen-negative answers ("neg"):
  primary|<w>|th, thc, io, be, iw, ic      90 prompts, 88 degrees of freedom
  commercial|<w>|th90                      the author's own change on all 90 prompts (88 df)
  commercial|<w>|th, thc, io, be, iw, ic   the 30 matched prompts (28 df)
(th: author in context minus blind; thc: the same for the control; io = th - thc; be: author blind minus control
blind; iw, ic: within-judge and composition parts of io.) Check 6: coverage >= 0.95 - 3 SE(0.95) over the
replications that report the interval, R being their number; not made when R < 1,000 (A.4). Boundary rules of
Section 8.1: no interval at a zero denominator or a zero estimated variance; both are counted.

The calibration (the coupling of the two verdicts) and the reference values always use the base seed; --seed
changes the replication stream only. Each setting carries a fingerprint; a stored setting with another
fingerprint is rejected and computed again.

Usage: python -I analysis/sim_v23_safe.py --reps 10000 --out sim_v23_safe.json
"""
import argparse
import hashlib
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
from scipy.special import expit

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "src"))
import inference_v23 as inf  # noqa: E402
import sim_v23_dgp as dgp  # noqa: E402
import frames_v23  # noqa: E402
import yoking  # noqa: E402

F32 = np.float32
BASE_SEED = 20261121     # the protocol names no seed for run (d); the seed of R-S1 and R-S2 is used
COMMERCIAL_PANEL_SEED = (dgp.PANEL_SEED, 1)
SAFE = dict(dgp.BASE, shifts="zero", sd_common=0.0, sd_own=0.0, fail_i=0.15, fail_r=0.02, fail_c=0.10,
            screen_se=0.2, screen_sp=0.05)      # P(screen-negative) = 0.8 with a refusal, 0.05 without
SETTINGS = {"safe|inv_3": dict(SAFE, inv="3"), "safe|inv_10_15": dict(SAFE, inv="10_15")}
CONTRASTS = ("th", "thc", "io", "be", "iw", "ic")
WEIGHTS = ("all", "neg")


def commercial_design():
    """The commercial panel on the safe frame: own answers on all 90 prompts; control verdicts on the 30 commercial
    safe controls (the first 30 prompts of the safe frame) with the production assignment. Outside them the
    control index is the author itself, a placeholder that no statistic reads."""
    panel = yoking.load_panel()
    fr = frames_v23.frames()
    ids, names = fr["safe"]
    cids, cnames = fr["safe_commercial_controls"]
    if ids[:len(cids)] != cids:
        raise RuntimeError("the commercial safe controls are not the first prompts of the safe frame")
    members = panel["groups"]["commercial"]
    J, P = len(members), len(ids)
    idx = {m: i for i, m in enumerate(members)}
    label = dgp.frame_label("commercial", "safe_commercial_controls")
    ctrl = np.tile(np.arange(J)[:, None], (1, P))
    asg = dgp.assign(cids, cnames, members, panel, label)
    for p, pid in enumerate(cids):
        for a, k in asg[pid].items():
            ctrl[idx[a], p] = idx[k]
    auth = np.zeros_like(ctrl)
    for p in range(P):
        auth[ctrl[:, p], p] = np.arange(J)
    sources = sorted(set(names.values()))
    return dict(judges=members, group=np.array(["c"] * J), P=P, matched=len(cids),
                strata=np.array([sources.index(names[p]) for p in ids]), ctrl=ctrl, auth=auth, frame="safe",
                dropped=[], blocks={"commercial": label})


def specs(scope, D):
    """(key, weight, prompt columns, with control quantities) of every statistic of one panel."""
    if scope == "primary":
        return [(f"primary|{w}|{k}", w, slice(None), k) for w in WEIGHTS for k in CONTRASTS]
    m = slice(0, D["matched"])
    return ([(f"commercial|{w}|th90", w, slice(None), "th") for w in WEIGHTS]
            + [(f"commercial|{w}|{k}", w, m, k) for w in WEIGHTS for k in CONTRASTS])


def weights(S, w):
    return np.ones(S.shape, dtype=np.int8) if w == "all" else (~S).astype(np.int8)


def contrasts(A1, A2, C1, C2, W, D, cols, keys):
    """cluster_ratio results (and the decomposition) of the statistics keys on the prompts cols.
    Arrays [R, J, P] indexed by answer; W: the answer weights (1 = in the scope)."""
    a1, a2, c1, c2, w = (x[:, :, cols] for x in (A1, A2, C1, C2, W))
    st = D["strata"][cols]
    dA, dC = (a2 - a1).astype(np.int32), (c2 - c1).astype(np.int32)
    w = w.astype(np.int32)
    N = w.sum(1)
    out = {}
    for k, d in (("th", dA), ("thc", dC), ("io", dA - dC), ("be", (a1 - c1).astype(np.int32))):
        if k in keys:
            out[k] = inf.cluster_ratio((w * d).sum(1), N, st)
    if {"iw", "ic"} & set(keys):
        idx = np.broadcast_to(D["auth"][:, cols][None], w.shape)
        dec = inf.interaction_decomposition(w * dA, w, np.take_along_axis(w * dC, idx, axis=1),
                                            np.take_along_axis(w, idx, axis=1), st)
        out["iw"], out["ic"] = dec["within"], dec["composition"]
    return out


def reference(rng, D, sc, q, g, clusters, scope, chunk=200):
    """True values: ratios of expectations over at least `clusters` independent prompt clusters for every
    statistic (expected delivered flags given the latent draw). Returns key -> (value, Monte Carlo se)."""
    sp_ = specs(scope, D)
    n_cols = min(len(range(D["P"])[c]) for _, _, c, _ in sp_)
    studies = -(-clusters // n_cols)
    acc = {key: ([], []) for key, *_ in sp_}
    judge_tot = {key: np.zeros((4, len(D["judges"]))) for key, _, _, k in sp_ if k in ("iw", "ic")}
    parts = {key: [] for key in judge_tot}
    done = 0
    while done < studies:
        R = min(chunk, studies - done)
        done += R
        L = dgp.draw_latent(rng, R, D, sc, q)
        e1, e2, f1, f2 = dgp.expected(L, sc, g)
        for key, w, cols, k in sp_:
            W = weights(L["screen"], w)[:, :, cols].astype(np.float64)
            a1, a2, c1, c2 = (x[:, :, cols] for x in (e1, e2, f1, f2))
            dA, dC = a2 - a1, c2 - c1
            if k in ("iw", "ic"):
                idx = np.broadcast_to(D["auth"][:, cols][None], W.shape)
                t = np.stack([(W * dA).sum((0, 2)), W.sum((0, 2)),
                              np.take_along_axis(W * dC, idx, axis=1).sum((0, 2)),
                              np.take_along_axis(W, idx, axis=1).sum((0, 2))])
                judge_tot[key] += t
                with np.errstate(divide="ignore", invalid="ignore"):
                    parts[key].append(_split(t)[0 if k == "iw" else 1])
                continue
            d = {"th": dA, "thc": dC, "io": dA - dC, "be": a1 - c1}[k]
            acc[key][0].append((W * d).sum(1).ravel().astype(F32))
            acc[key][1].append(W.sum(1).ravel().astype(F32))
    out = {}
    for key, w, cols, k in sp_:
        if k in ("iw", "ic"):
            v = np.array(parts[key])
            v = v[np.isfinite(v)]
            with np.errstate(divide="ignore", invalid="ignore"):
                val = _split(judge_tot[key])[0 if k == "iw" else 1]
            out[key] = (float(val), float(v.std(ddof=1) / np.sqrt(v.size)) if v.size > 1 else float("nan"))
            continue
        n_c = len(range(D["P"])[cols])
        x, n = np.concatenate(acc[key][0]), np.concatenate(acc[key][1])
        strata = np.tile(D["strata"][cols], x.size // n_c)
        r = inf.cluster_ratio(x, n, strata)
        out[key] = (float(r["est"]), float(r["se"]))
    return out


def _split(t):
    """(within, composition) parts of the pooled interaction from per-judge totals
    [own x, own n, control x, control n]."""
    within = (t[0] - t[1] * t[2] / t[3]).sum() / t[1].sum()
    return within, (t[0] - t[2]).sum() / t[1].sum() - within


def delivered_flags(rng, L, sc, g, rho):
    """Delivered valid flags of the four arms (the draw of sim_v23_registered.one_chunk)."""
    a1, a2, c1, c2 = dgp.arm_logits(L, sc, g)
    ib, ic = dgp.invalid_probs(sc["inv"], L["fail"])
    shape = a1.shape

    def delivered(e1, e2):
        u1 = rng.random(shape, dtype=F32)
        u2 = np.where(rng.random(shape, dtype=F32) < rho, u1, rng.random(shape, dtype=F32))
        v1 = rng.random(shape, dtype=F32)
        v2 = np.where(rng.random(shape, dtype=F32) < 0.5, v1, rng.random(shape, dtype=F32))
        return (((u1 < expit(e1)) & (v1 >= ib)).astype(np.int8),
                ((u2 < expit(e2)) & (v2 >= ic)).astype(np.int8))

    A1, A2 = delivered(a1, a2)
    C1, C2 = delivered(c1, c2)
    return A1, A2, C1, C2


def one_chunk(rng, R, D, sc, q, g, rho, scope):
    L = dgp.draw_latent(rng, R, D, sc, q)
    A1, A2, C1, C2 = delivered_flags(rng, L, sc, g, rho)
    out = {}
    for w in WEIGHTS:
        W = weights(L["screen"], w)
        groups = {}
        for key, ww, cols, k in specs(scope, D):
            if ww == w:
                groups.setdefault((cols.start, cols.stop), (cols, []))[1].append((key, k))
        for cols, items in groups.values():
            res = contrasts(A1, A2, C1, C2, W, D, cols, [k for _, k in items])
            for key, k in items:
                r = res[k]
                lo, hi = inf.interval(r)
                out[key] = dict(est=r["est"], lo=lo, hi=hi, zv=np.asarray(r["zero_variance"]),
                                den=np.asarray(r["den"], dtype=np.float64))
    return out


def a4_limit_min(p, R):
    """Lower limit of a coverage check of A.4: p - 3 SE(p), SE(p) = sqrt(p (1 - p) / R)."""
    return p - 3 * math.sqrt(p * (1 - p) / R)


def summarise(reps, ref):
    out = {}
    for key, (truth, mc) in ref.items():
        est = np.concatenate([r[key]["est"] for r in reps])
        lo = np.concatenate([r[key]["lo"] for r in reps])
        hi = np.concatenate([r[key]["hi"] for r in reps])
        zv = np.concatenate([r[key]["zv"] for r in reps])
        ok, has = np.isfinite(est), np.isfinite(lo) & np.isfinite(hi)
        n_int = int(has.sum())
        cover = float(np.mean((lo[has] <= truth) & (truth <= hi[has]))) if n_int else None
        made = n_int >= 1000
        limit = a4_limit_min(0.95, n_int) if n_int else None
        out[key] = {"reference": truth, "reference_mc_se": mc,
                    "mean": float(est[ok].mean()) if ok.any() else None,
                    "bias": float(est[ok].mean() - truth) if ok.any() else None,
                    "non_estimable": int((~ok).sum()), "zero_variance": int(zv.sum()), "with_interval": n_int,
                    "cover95": cover, "half_width95": float(np.mean((hi[has] - lo[has]) / 2)) if n_int else None,
                    "check6": {"R": n_int, "made": made, "limit": limit,
                               "passed": (cover >= limit) if made else None}}
    return out


def streams(name, seed):
    tag = int(hashlib.sha256(name.encode("utf-8")).hexdigest()[:8], 16)
    r_cal, r_ref, _ = (np.random.default_rng(s) for s in np.random.SeedSequence([BASE_SEED, tag]).spawn(3))
    r_sim = np.random.default_rng(np.random.SeedSequence([seed, tag]).spawn(3)[2])
    return r_cal, r_ref, r_sim


def run_setting(name, sc, designs, reps, clusters, cal_reps, chunk, seed):
    t0 = time.time()
    out = {"name": name, "scenario": sc, "reps": reps, "clusters": clusters, "stats": {}, "calibration": {}}
    for scope, (D, panel_seed) in designs.items():
        r_cal, r_ref, r_sim = streams(f"{name}|{scope}", seed)
        q = dgp.panel_quality(D, sc, seed=panel_seed)
        g, rho, diag = dgp.calibrate(r_cal, D, sc, q, cal_reps)
        ref = reference(r_ref, D, sc, q, g, clusters, scope)
        parts, done = [], 0
        while done < reps:
            R = min(chunk, reps - done)
            done += R
            parts.append(one_chunk(r_sim, R, D, sc, q, g, rho, scope))
        out["stats"].update(summarise(parts, ref))
        out["calibration"][scope] = dict(g, rho=rho, **diag)
    out["seconds"] = round(time.time() - t0, 1)
    return out


def fingerprint(name, sc, designs, reps, clusters, cal_reps, chunk, seed):
    h = hashlib.sha256()
    for f in sorted({Path(m.__file__).resolve() for m in (inf, dgp, frames_v23, yoking)} | {Path(__file__).resolve()}):
        h.update(f.read_bytes().replace(b"\r\n", b"\n"))
    h.update(json.dumps(dgp.canon([name, sc, {k: v[0] for k, v in designs.items()}, reps, clusters, cal_reps, chunk,
                                   seed, BASE_SEED]), sort_keys=True).encode("utf-8"))
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=200)
    ap.add_argument("--seed", type=int, default=BASE_SEED,
                    help="seed of the replication stream; another value is used only for the second run of A.4")
    ap.add_argument("--clusters", type=int, default=1_000_000)
    ap.add_argument("--cal-reps", type=int, default=1000)
    ap.add_argument("--chunk", type=int, default=500)
    ap.add_argument("--only", default="")
    ap.add_argument("--drop", default="", help="hosted models left out of the primary panel, e.g. 22, 23 or 22,23")
    ap.add_argument("--out", default="sim_v23_safe.json")
    a = ap.parse_args()
    drop = tuple(int(x) for x in a.drop.replace(" ", "").split(",") if x)
    designs = {"primary": (dgp.design(drop=drop, frame="safe"), dgp.PANEL_SEED),
               "commercial": (commercial_design(), COMMERCIAL_PANEL_SEED)}
    path = HERE / "output" / a.out
    done = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    for name, sc in SETTINGS.items():
        if a.only and a.only not in name:
            continue
        fp = fingerprint(name, sc, designs, a.reps, a.clusters, a.cal_reps, a.chunk, a.seed)
        if name in done and done[name].get("fingerprint") == fp:
            continue
        if name in done:
            print(f"rejected stored setting {name}: its fingerprint differs from the present code, design or "
                  "arguments", flush=True)
        s = run_setting(name, sc, designs, a.reps, a.clusters, a.cal_reps, a.chunk, a.seed)
        s.update(seed=a.seed, cal_reps=a.cal_reps, chunk=a.chunk, dropped=list(drop), fingerprint=fp,
                 judges={k: v[0]["judges"] for k, v in designs.items()})
        done[name] = s
        path.write_text(json.dumps(done, indent=1), encoding="utf-8")
        checks = [v["check6"] for v in s["stats"].values()]
        made = [c for c in checks if c["made"]]
        worst = min(((v["cover95"], k) for k, v in s["stats"].items() if v["check6"]["made"]), default=None)
        print(f"{name}: {len(made)} of {len(checks)} intervals checked (R >= 1,000), "
              f"{sum(c['passed'] for c in made)} passed; lowest coverage "
              + (f"{worst[0]:.4f} ({worst[1]})" if worst else "n/a") + f" | {s['seconds']:.0f}s", flush=True)
        for k, v in s["stats"].items():
            c = v["check6"]
            if c["made"] and not c["passed"]:
                print(f"    CHECK 6 FAILS: {k}: coverage {v['cover95']:.4f} < {c['limit']:.4f} (R {c['R']})", flush=True)
            elif not c["made"]:
                print(f"    not checked: {k}: interval reported in {c['R']} replications", flush=True)
        for scope, cal in s["calibration"].items():
            for u in cal["unreached"]:
                print(f"    TARGET NOT REACHED ({scope}): {u['name']} = {u['target']}; nearest {u['nearest']}",
                      flush=True)


if __name__ == "__main__":
    main()
