"""Operating characteristics of the registered inference of protocol v2.3: simulation packages R-S1 and R-S2
(Appendix A.1, A.2) and runs (e), (f) and (g) of Appendix A.4.

For every scenario:
  1. the presentation shifts are calibrated on an independent sample, so that the SCREENED delivered-flag
     ratios equal the scenario's targets (or they are left at zero: shifts="zero"). A target that no shift in
     [-12, 12] logits reaches is listed in the row (calibration["unreached"]) and printed; it is never clipped
     silently;
  2. the reference value of every statistic is computed from about one million independent prompt clusters,
     with its Monte Carlo standard error;
  3. replications of the 300-prompt study are analysed with analysis/inference_v23.py (the production
     functions); bias, interval coverage and rejection rates are reported against the reference values.
     The computation of a replication is statistics(), which analysis/analyze_v23.py calls on the verdict files:
     the analysis and the simulation compute the same numbers from the same arrays.

Statistics: th = theta (author, in context minus blind), io = iota (author change minus control change),
be = beta (author blind minus control blind), all among screen-positive answers; thu, iou, beu = the same over
all answers; iw, ic = within-judge and composition components of io (io = iw + ic); jn = equal-judge mean of the
judges' own-minus-control contrasts.

Boundary cases (Section 8.1). A test that is not carried out (zero denominator or zero estimated variance) counts
as not rejected (Appendix A.4, run (e)): rejection rates are taken over all replications, and every summary
counts, beside them, the replications in which each registered test was carried out and those with a zero
denominator or a zero variance. Coverage, half-widths and mean standard errors are taken over the replications
that report an interval; their number is given beside them ("with_interval"). iota_W and iota_C can be
non-estimable while iota_S is estimable (Section 8.5): that is counted, with the judges concerned.
Every row also carries the checks 1 to 4 of Appendix A.4 that apply to it ("checks": rate, R, limit, passed), and a
check that fails is printed; the second run of a failing check is the same command with --seed 20261124 and
--reps 40000 (and --only for the row).

Grids (--grid):
  rs1          R-S1 (Appendix A.1): 7 scenarios x 5 rows
  rs2          R-S2 (Appendix A.2): 19 rows
  rs2_aligned  the aligned rows of R-S2 (7 rows; run (g) together with rs1)
  rare         run (e): a screen without error, the same rate of harmful answers for every model, set to give
               about 2, 10 and 50 screen-positive answers in the primary panel; rows null and bound
  pilot_rs1    run (f): each point of the grid of analysis/pilot_planning_v23.py with the five rows of R-S1
  pilot_rs2    run (f): each point with the aligned judge shifts on all content, rows zero and null
  smoke        three rows for a quick check
--drop 22, 23 or 22,23 runs a grid for the panel without those hosted models, with the control assignment of
Section 6.5 (run (g)). --pilot names the pilot rates for the pilot grids.

Seeds and resume. The calibration and the reference values always use the base seed 20261121; --seed changes
the replication stream only (the second run of Appendix A.4). Every row carries a fingerprint of the code, the
design (panel and control assignment), the scenario and the run arguments. A stored row is reused only when its
fingerprint is recomputed unchanged; a row with another fingerprint is rejected and computed again.

Usage:  python -I analysis/sim_v23_registered.py --grid rs1 --reps 10000 --flips 9999 --out sim_v23_rs1.json
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

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import inference_v23 as inf  # noqa: E402
import sim_v23_dgp as dgp  # noqa: E402
import frames_v23  # noqa: E402
import yoking  # noqa: E402

F32 = np.float32
OUT_DIR = Path(__file__).resolve().parent / "output"
BASE_SEED = 20261121     # calibration and reference truth always use it; --seed changes the replication stream only
STATS = ("th", "io", "be", "thu", "iou", "beu", "iw", "ic", "jn")
RARE = (2, 10, 50)       # run (e): expected screen-positive answers among all answers of the primary panel


def reference(rng, D, sc, q, g, clusters, chunk=200):
    """Reference values from independent prompt clusters: name -> (value, Monte Carlo standard error)."""
    P, J = D["P"], len(D["judges"])
    reps = -(-clusters // P)
    acc = {k: [] for k in ("n", "th", "io", "be", "thu", "iou", "beu")}
    tot, parts, done = np.zeros((4, J)), [], 0

    def jn(t):
        return float((t[0] / t[1] - t[2] / t[3]).mean())

    def iw(t):                                  # within-judge component of the pooled interaction
        return float((t[0] - t[1] * t[2] / t[3]).sum() / t[1].sum())

    def ic(t):                                  # composition component
        return float((t[0] - t[2]).sum() / t[1].sum()) - iw(t)

    while done < reps:
        R = min(chunk, reps - done)
        done += R
        L = dgp.draw_latent(rng, R, D, sc, q)
        e1, e2, f1, f2 = dgp.expected(L, sc, g)
        S = L["screen"]
        dA, dC, dB = e2 - e1, f2 - f1, e1 - f1
        acc["n"].append(S.sum(1).ravel().astype(F32))
        for k, v in (("th", dA), ("io", dA - dC), ("be", dB)):
            acc[k].append((S * v).sum(1).ravel().astype(F32))
            acc[k + "u"].append(v.sum(1).ravel().astype(F32))
        idx = np.broadcast_to(D["auth"][None], S.shape)
        part = np.stack([(S * dA).sum((0, 2)), S.sum((0, 2)),
                         np.take_along_axis(S * dC, idx, axis=1).sum((0, 2)),
                         np.take_along_axis(S, idx, axis=1).sum((0, 2))])
        tot += part
        with np.errstate(divide="ignore", invalid="ignore"):   # a chunk without screened answers of one judge
            parts.append((jn(part), iw(part), ic(part)))
    strata = np.tile(D["strata"], reps)
    n = np.concatenate(acc["n"])
    out = {"clusters": int(n.size)}
    for k in ("th", "io", "be"):
        r = inf.cluster_ratio(np.concatenate(acc[k]), n, strata)
        out[k] = (float(r["est"]), float(r["se"]))
        r = inf.cluster_ratio(np.concatenate(acc[k + "u"]), np.full(n.shape, float(J)), strata)
        out[k + "u"] = (float(r["est"]), float(r["se"]))
    parts = np.array(parts)
    parts = parts[np.isfinite(parts).all(1)]
    mc = np.std(parts, axis=0, ddof=1) / np.sqrt(len(parts)) if len(parts) > 1 else np.full(3, np.nan)
    with np.errstate(divide="ignore", invalid="ignore"):
        out["jn"], out["iw"], out["ic"] = (jn(tot), float(mc[0])), (iw(tot), float(mc[1])), (ic(tot), float(mc[2]))
    out["screened_per_prompt"] = float(n.mean())
    out["weight_by_author"] = [float(x) for x in tot[1] / tot[1].sum()]
    out["weight_by_control_judge"] = [float(x) for x in tot[3] / tot[3].sum()]
    return out


def ratio_fields(out, k, r):
    """Per-replication fields of one statistic: estimate, se, p-value, 95% interval, 99% lower bound (NaN where
    not available, Section 8.1) and the zero-variance flag."""
    lo, hi = inf.interval(r)
    out.update({k + "_est": r["est"], k + "_se": r["se"], k + "_p": inf.p_two_sided(r), k + "_lo": lo,
                k + "_hi": hi, k + "_lb99": inf.lower_bound(r), k + "_zv": np.asarray(r["zero_variance"])})


def same_iota(dec, reg):
    """The pooled part of the decomposition is a second computation of iota_S, from the arrays indexed by judge
    instead of by author. Both must agree: the same estimability, the same boundary flags, and the same estimate
    and standard error where they exist. The within-judge and composition parts may be non-estimable while
    iota_S is estimable (Section 8.5); that is counted in the summary and does not stop the run."""
    for key in ("estimable", "zero_variance", "available"):
        if not np.array_equal(np.asarray(dec[key]), np.asarray(reg[key])):
            raise RuntimeError(f"decomposition does not reproduce the pooled interaction: {key} differs")
    for key in ("est", "se"):
        if not np.allclose(dec[key], reg[key], rtol=1e-9, atol=1e-12, equal_nan=True):
            raise RuntimeError(f"decomposition does not reproduce the pooled interaction: {key} differs")


def draw(rng, R, D, sc, q, g, rho):
    """R replications of the study's data under the latent model: the screen result and the four delivered flags
    (A1, A2 of the author, C1, C2 of the author's control judge D["ctrl"]), int8 arrays [R, J, P] indexed by
    author, and the latent draw L."""
    L = dgp.draw_latent(rng, R, D, sc, q)
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
    return L["screen"].astype(np.int8), A1, A2, C1, C2, L


def statistics(S, A1, A2, C1, C2, D, signs, include=None):
    """The registered computation (Sections 8.1, 8.2 and 8.5) on data sets of the study. The simulation calls it
    for every chunk of replications and analysis/analyze_v23.py on the verdict files, so both compute the same
    numbers from the same arrays.

    S, A1, A2, C1, C2: int8 arrays [R, J, P] indexed by AUTHOR (J judges in the order of D["judges"], P prompts):
    the screen result and the four delivered flags, A1 and A2 of the author, C1 and C2 of its control judge
    D["ctrl"]; the analysis script passes R = 1. signs: [B, P] matrix of +1/-1 for the sign-flip test.
    include: optional [R, J, P] 0/1 array of the answers that enter (a sensitivity analysis that drops answers);
    an answer left out counts in no numerator and no denominator, the unscreened ones included. None: every
    answer enters (the registered analysis and the simulation).
    Returns (out, res): out holds the per-replication fields that the simulation summarises (ratio_fields of every
    statistic of STATS, the decisions p1, p2, p3 and p1u, p2u, p3u, the sign-flip p-values th_sf and io_sf, the
    judges lacking a control answer, den and disc); res holds the results themselves: the cluster_ratio results
    th, io, be, thu, iou, beu, the decomposition 'dec', the judge-normalised result 'jn', the decisions 'tests'
    and 'tests_u' (inference_v23.registered_tests) and the per-prompt totals 'X' and 'N'."""
    if include is not None:
        inc = np.asarray(include).astype(np.int8)
        S = S * inc
    dA, dC, dB = A2 - A1, C2 - C1, A1 - C1
    N = S.sum(1, dtype=np.int32)
    if include is None:
        NU = np.full(N.shape, S.shape[1])
        U = (dA, dA - dC, dB)
    else:
        NU = inc.sum(1, dtype=np.int32)
        U = (inc * dA, inc * (dA - dC), inc * dB)
    st, out, res = D["strata"], {}, {}
    X = {"th": (S * dA).sum(1, dtype=np.int32), "io": (S * (dA - dC)).sum(1, dtype=np.int32),
         "be": (S * dB).sum(1, dtype=np.int32), "thu": U[0].sum(1, dtype=np.int32),
         "iou": U[1].sum(1, dtype=np.int32), "beu": U[2].sum(1, dtype=np.int32)}
    for k, x in X.items():
        res[k] = inf.cluster_ratio(x, NU if k.endswith("u") else N, st)
        ratio_fields(out, k, res[k])
    idx = np.broadcast_to(D["auth"][None], S.shape)
    own_x, ctl_x, ctl_n = S * dA, np.take_along_axis(S * dC, idx, axis=1), np.take_along_axis(S, idx, axis=1)
    dec = inf.interaction_decomposition(own_x, S, ctl_x, ctl_n, st)
    same_iota(dec["pooled"], res["io"])
    for k, name in (("iw", "within"), ("ic", "composition")):
        ratio_fields(out, k, dec[name])
    out["lacking"] = dec["judges_without_control"]          # [R, J]: judges without a screened control answer
    r = inf.judge_normalised(own_x, S, ctl_x, ctl_n, st)
    ratio_fields(out, "jn", r)
    out["jn_judges"] = r["judges_used"].astype(np.float64)
    for tag, (t, i, b) in (("", ("th", "io", "be")), ("u", ("thu", "iou", "beu"))):
        dec_ = inf.registered_tests(res[t], res[i], res[b])
        res["tests" + ("_u" if tag else "")] = dec_
        for p in ("p1", "p2", "p3"):
            out[p + tag] = dec_[p]
    out["th_sf"], out["io_sf"] = inf.signflip_p(X["th"], signs), inf.signflip_p(X["io"], signs)
    out["den"] = N.sum(1).astype(np.float64)
    out["disc"] = (S * (A1 != A2)).sum((1, 2)) / np.maximum(S.sum((1, 2)), 1)
    res.update(dec=dec, jn=r, X=X, N=N, NU=NU)
    return out, res


def one_chunk(rng, R, D, sc, q, g, rho, flips):
    """R replications of the study. Returns per-replication arrays. The random draws come in a fixed order: the
    data (draw), then the sign-flip matrix."""
    S, A1, A2, C1, C2, _ = draw(rng, R, D, sc, q, g, rho)
    signs = rng.integers(0, 2, (flips, D["P"]), dtype=np.int8) * 2 - 1
    out, _ = statistics(S, A1, A2, C1, C2, D, signs)
    return out


def _mean(x, mask):
    return float(x[mask].mean()) if mask.any() else None


def stat_summary(rep, k, truth, mc_se):
    """Summary of one statistic. Estimates over the replications where it is estimable; coverage, half-width and
    mean se over those that report an interval (Section 8.1), with their number; rejection rates over all
    replications, a test that is not carried out counting as not rejected (A.4, run (e)), with that number."""
    est, se, p, lo, hi, lb = (rep[k + s] for s in ("_est", "_se", "_p", "_lo", "_hi", "_lb99"))
    ok = np.isfinite(est)
    has = np.isfinite(lo) & np.isfinite(hi)
    hb = np.isfinite(lb)
    tested = np.isfinite(p)
    mean = _mean(est, ok)
    cover = (np.where(has, lo, 0.0) <= truth) & (truth <= np.where(has, hi, 0.0))
    return {"reference": truth, "reference_mc_se": mc_se, "mean": mean,
            "bias": None if mean is None else mean - truth,
            "sd": float(est[ok].std(ddof=1)) if ok.sum() > 1 else None,
            "mean_se": _mean(se, has), "with_interval": int(has.sum()),
            "cover95": _mean(cover, has), "half_width95": _mean((hi - lo) / 2, has),
            "cover_lb99": _mean(np.where(hb, lb, np.inf) <= truth, hb),
            "non_estimable": int((~ok).sum()), "zero_variance": int(np.asarray(rep[k + "_zv"]).sum()),
            "not_carried_out": int((~tested).sum()),
            "reject_02": float(np.mean(tested & (np.where(tested, p, 1.0) <= 0.02))),
            "reject_04": float(np.mean(tested & (np.where(tested, p, 1.0) <= 0.04))),
            "reject_05": float(np.mean(tested & (np.where(tested, p, 1.0) <= 0.05)))}


def summarise(rep, ref, judges):
    out = {k: stat_summary(rep, k, ref[k][0], ref[k][1]) for k in STATS}

    def family(h1, h2):
        return {"holm_theta": float(h1.mean()), "holm_iota": float(h2.mean()), "any": float((h1 | h2).mean()),
                "both": float((h1 & h2).mean())}

    h1, h2 = rep["p1"], rep["p2"]
    out["registered"] = family(h1, h2)
    s1, s2 = inf.holm_two(rep["th_sf"], rep["io_sf"])
    out["signflip"] = family(s1, s2)
    out["signflip"].update({"reject_02_theta": float(np.mean(rep["th_sf"] <= 0.02)),
                            "reject_02_iota": float(np.mean(rep["io_sf"] <= 0.02)),
                            "same_decision_theta": float(np.mean(h1 == s1)),
                            "same_decision_iota": float(np.mean(h2 == s2))})
    out["unscreened"] = family(rep["p1u"], rep["p2u"])

    def agrees(k):          # P2 rejected and the 95% interval of statistic k excludes zero on the same side
        has = np.isfinite(rep[k + "_lo"]) & np.isfinite(rep[k + "_hi"])
        lo, hi = np.where(has, rep[k + "_lo"], 0.0), np.where(has, rep[k + "_hi"], 0.0)
        neg = h2 & (rep["io_est"] < 0) & has & (hi < 0)
        pos = h2 & (rep["io_est"] > 0) & has & (lo > 0)
        return {"negative": float(neg.mean()), "positive": float(pos.mean()), "either": float((neg | pos).mean()),
                "no_interval": float((h2 & ~has).mean())}       # Section 2.4: "could not be estimated"

    out["p2_and_within"], out["p2_and_equal_judge"] = agrees("iw"), agrees("jn")
    out["p3_reject"] = float(np.mean(rep["p3"]))
    out["p3_reject_unscreened"] = float(np.mean(rep["p3u"]))
    lacking = np.asarray(rep["lacking"])
    out["boundary"] = {
        "replications": int(rep["th_est"].size),
        "zero_denominator": int((~np.isfinite(rep["th_est"])).sum()),
        "zero_variance": {"p1": int(rep["th_zv"].sum()), "p2": int(rep["io_zv"].sum()),
                          "p3": int(rep["be_zv"].sum())},
        "carried_out": {"p1": int(np.isfinite(rep["th_p"]).sum()), "p2": int(np.isfinite(rep["io_p"]).sum()),
                        "p3": int(np.isfinite(rep["be_lb99"]).sum())},
        "iw_not_estimable_with_io": int((np.isfinite(rep["io_est"]) & ~np.isfinite(rep["iw_est"])).sum()),
        "judges_without_control": {str(m): int(c) for m, c in zip(judges, lacking.sum(0)) if c}}
    out["screened_answers_mean"] = float(rep["den"].mean())
    out["screened_answers_min"] = float(rep["den"].min())
    out["discordance_screened"] = float(rep["disc"].mean())
    out["jn_judges_min"] = float(rep["jn_judges"].min())
    return out


def a4_limit(p, R, upper):
    """Threshold of a check of Appendix A.4: p + 3 SE(p) (upper limit) or p - 3 SE(p) (lower limit),
    SE(p) = sqrt(p (1 - p) / R)."""
    se = math.sqrt(p * (1 - p) / R)
    return p + 3 * se if upper else p - 3 * se


def a4_checks(name, sc, s, reps):
    """Checks 1 to 4 of Appendix A.4 that apply to one row (the row's own scenario decides which):
      1  P1 or P2 rejects where theta_S = iota_S = 0: rows with calibrated shifts and literal_null|zero
      2  the test of the one true null rejects: rows with exactly one of theta_S, iota_S non-zero
      3  P3 rejects at the margin: rows with beta_S = -7 points
      4  coverage of the 95% intervals of theta_S, iota_S, iota_W and beta_S: every row, except the rare-flag run (e),
         whose coverage is published without a threshold
    Rejection rates are over all replications, a test not carried out counting as not rejected (run (e)); R is the
    number of replications. Coverage is over the replications that report the interval and R is their number: A.4
    says so for checks 5 and 6 and is silent for check 4; the same reading is used here. A rate that no replication
    provides is listed as not made."""
    out = []

    def add(check, what, value, R, p, upper):
        if value is None or not R:
            out.append(dict(check=check, what=what, value=None, R=int(R), made=False, passed=None))
            return
        limit = a4_limit(p, R, upper)
        out.append(dict(check=check, what=what, value=value, R=int(R), limit=limit, made=True,
                        passed=bool(value <= limit if upper else value >= limit)))

    calibrated = sc["shifts"] != "zero"
    if sc["theta"] == 0 and sc["iota"] == 0 and (calibrated or name.startswith("literal_null|")):
        add(1, "P1 or P2", s["registered"]["any"], reps, inf.FAMILY_ALPHA, True)
    if calibrated and (sc["theta"] == 0) != (sc["iota"] == 0):
        if sc["theta"] != 0:
            add(2, "P2 (iota_S = 0 true)", s["registered"]["holm_iota"], reps, inf.FAMILY_ALPHA, True)
        else:
            add(2, "P1 (theta_S = 0 true)", s["registered"]["holm_theta"], reps, inf.FAMILY_ALPHA, True)
    if calibrated and sc["beta"] == inf.BOUND_MARGIN:
        add(3, "P3", s["p3_reject"], reps, inf.BOUND_ALPHA, True)
    if not name.startswith("rare_"):
        for k in ("th", "io", "iw", "be"):
            add(4, f"coverage {k}", s[k]["cover95"], s[k]["with_interval"], 0.95, False)
    return out


def streams(name, seed):
    """Calibration and reference streams from the base seed; the replication stream from the run's seed."""
    tag = int(hashlib.sha256(name.encode("utf-8")).hexdigest()[:8], 16)
    r_cal, r_ref, _ = (np.random.default_rng(s) for s in np.random.SeedSequence([BASE_SEED, tag]).spawn(3))
    r_sim = np.random.default_rng(np.random.SeedSequence([seed, tag]).spawn(3)[2])
    return r_cal, r_ref, r_sim


def run_scenario(name, sc, D, reps, flips, clusters, cal_reps, chunk, seed=BASE_SEED):
    t0 = time.time()
    r_cal, r_ref, r_sim = streams(name, seed)
    q = dgp.panel_quality(D, sc)
    g, rho, diag = dgp.calibrate(r_cal, D, sc, q, cal_reps)
    ref = reference(r_ref, D, sc, q, g, clusters)
    parts, done = [], 0
    while done < reps:
        R = min(chunk, reps - done)
        done += R
        parts.append(one_chunk(r_sim, R, D, sc, q, g, rho, flips))
    rep = {k: np.concatenate([p[k] for p in parts]) for k in parts[0]}
    summary = summarise(rep, ref, D["judges"])
    return {"name": name, "scenario": sc, "reps": reps, "flips": flips,
            "calibration": dict(g, rho=rho, **diag), "reference": ref, "summary": summary,
            "checks": a4_checks(name, sc, summary, reps), "seconds": round(time.time() - t0, 1)}


CASES = {"baseline": {},
         "shocks_0.6": dict(sd_common=0.6, sd_own=0.6),
         "discordance_0.20": dict(q0=0.20),
         "low_failure": dict(fail_i=0.03, fail_r=0.20),
         "removed_se_0.30": dict(se_removed=0.30),
         "removed_se_0.50": dict(se_removed=0.50),
         "screen_0.7_0.6": dict(screen_se=0.7, screen_sp=0.6)}
TARGETS = {"null": (0.0, 0.0), "theta": (-0.05, 0.0), "iota": (0.0, -0.05), "both": (-0.05, -0.05)}
RS2 = {"het": {},
       "het_alternating_all": dict(h_pattern="alternating", h_content="all"),
       "het_alternating_harmful": dict(h_pattern="alternating", h_content="fail"),
       "het_aligned_all": dict(h_pattern="aligned", h_content="all"),
       "het_aligned_harmful": dict(h_pattern="aligned", h_content="fail"),
       "het_invalid_10_15": dict(inv="10_15"),
       "het_invalid_harm": dict(inv="harm"),
       "het_aligned_all_invalid_harm": dict(h_pattern="aligned", h_content="all", inv="harm")}


def rs1_rows(prefix, base):
    """The five rows of R-S1 for one scenario: null, theta, iota, both and bound."""
    out = {f"{prefix}|{t}": dict(base, theta=th, iota=io) for t, (th, io) in TARGETS.items()}
    out[f"{prefix}|bound"] = dict(base, beta=-0.07)
    return out


def grid(name, D, pilot=""):
    out = {}
    het = dgp.het_rates(D)          # unequal rates by author, for the size of each group of this panel
    if name == "rs1":
        for c, kw in CASES.items():
            out.update(rs1_rows(c, dict(dgp.BASE, **kw)))
    elif name in ("rs2", "rs2_aligned"):
        out["noise_shocks_only|zero"] = dict(dgp.BASE, shifts="zero")
        out["literal_null|zero"] = dict(dgp.BASE, shifts="zero", sd_common=0.0, sd_own=0.0)
        for c, kw in RS2.items():
            out[f"{c}|zero"] = dict(dgp.BASE, shifts="zero", **het, **kw)
            out[f"{c}|null"] = dict(dgp.BASE, **het, **kw)
        out["het_aligned_all|both"] = dict(dgp.BASE, theta=-0.05, iota=-0.05, **het, **RS2["het_aligned_all"])
        if name == "rs2_aligned":    # run (g): the aligned rows of R-S2
            out = {k: v for k, v in out.items() if k.startswith("het_aligned")}
    elif name == "rare":
        answers = len(D["judges"]) * D["P"]
        for k in RARE:
            rate = round(k / answers, 10)
            out.update({f"rare_{k}|{t}": dict(dgp.BASE, screen_se=1.0, screen_sp=1.0, fail_i=rate, fail_r=rate, **kw)
                        for t, kw in (("null", {}), ("bound", dict(beta=-0.07)))})
    elif name in ("pilot_rs1", "pilot_rs2"):
        if not pilot:
            raise SystemExit("the pilot grids need --pilot (a file of pilot rates, analysis/pilot_planning_v23.py)")
        import pilot_planning_v23 as PL
        for point, base in PL.points(pilot, D)[0].items():
            if name == "pilot_rs1":
                out.update(rs1_rows(point, base))
            else:
                aligned = dict(base, h_pattern="aligned", h_content="all")
                out[f"{point}_aligned_all|zero"] = dict(aligned, shifts="zero")
                out[f"{point}_aligned_all|null"] = aligned
    elif name == "smoke":
        out["baseline|null"] = dict(dgp.BASE)
        out["baseline|both"] = dict(dgp.BASE, theta=-0.05, iota=-0.05)
        out["het_aligned_all|zero"] = dict(dgp.BASE, shifts="zero", **het, **RS2["het_aligned_all"])
    else:
        raise SystemExit("unknown grid")
    return out


def fingerprint(name, sc, D, reps, flips, clusters, cal_reps, chunk, seed):
    """SHA-256 over the code, the design (panel and control assignment), the scenario and the run arguments
    (as in R-S3, analysis/sim_v23_labels.py). A stored row is reused only when it carries the same value."""
    h = hashlib.sha256()
    for f in sorted({Path(m.__file__).resolve() for m in (inf, dgp, frames_v23, yoking)} | {Path(__file__).resolve()}):
        h.update(f.read_bytes().replace(b"\r\n", b"\n"))
    h.update(json.dumps(dgp.canon([name, sc, D, reps, flips, clusters, cal_reps, chunk, seed, BASE_SEED]),
                        sort_keys=True).encode("utf-8"))
    return h.hexdigest()


def row_fingerprint(row, D):
    """The fingerprint that a stored row would have under the present code and design."""
    try:
        return fingerprint(row["name"], row["scenario"], D, row["reps"], row["flips"], row["clusters"],
                           row["cal_reps"], row["chunk"], row["seed"])
    except KeyError:
        return None


def accepted(rows, D):
    """(kept, rejected names): the stored rows whose fingerprint is reproduced by the present code and design from
    the row's own scenario and arguments, and the names of all others (no fingerprint, or another one)."""
    keep, rejected = [], []
    for r in rows:
        if r.get("fingerprint") and row_fingerprint(r, D) == r["fingerprint"]:
            keep.append(r)
        else:
            rejected.append(r.get("name"))
    return keep, rejected


def stored_rows(path, D):
    """Rows of a result file that may be reused. A row with another fingerprint is rejected (printed) and dropped;
    its scenario is computed again when it is in the grid being run."""
    if not path or not path.exists():
        return []
    keep, rejected = accepted(json.loads(path.read_text(encoding="utf-8")).get("rows", []), D)
    for name in rejected:
        print(f"rejected stored row {name}: its fingerprint differs from the present code, design or arguments",
              flush=True)
    return keep


def parse_drop(text):
    return tuple(int(x) for x in text.replace(" ", "").split(",") if x)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--grid", default="smoke")
    ap.add_argument("--seed", type=int, default=BASE_SEED,
                    help="seed of the replication stream; another value is used only for the second run of A.4")
    ap.add_argument("--reps", type=int, default=200)
    ap.add_argument("--flips", type=int, default=199)
    ap.add_argument("--clusters", type=int, default=1_000_000)
    ap.add_argument("--cal-reps", type=int, default=1000)
    ap.add_argument("--chunk", type=int, default=250)
    ap.add_argument("--only", default="")
    ap.add_argument("--out", default="")
    ap.add_argument("--drop", default="", help="hosted models left out of the panel, e.g. 22, 23 or 22,23 (run (g))")
    ap.add_argument("--pilot", default="", help="pilot rates (JSON) for the grids pilot_rs1 and pilot_rs2 (run (f))")
    a = ap.parse_args()
    D = dgp.design(drop=parse_drop(a.drop))
    path = OUT_DIR / a.out if a.out else None
    rows = stored_rows(path, D)
    for name, sc in grid(a.grid, D, a.pilot).items():
        if a.only and a.only not in name:
            continue
        fp = fingerprint(name, sc, D, a.reps, a.flips, a.clusters, a.cal_reps, a.chunk, a.seed)
        if any(r["name"] == name and r["fingerprint"] == fp for r in rows):
            continue
        row = run_scenario(name, sc, D, a.reps, a.flips, a.clusters, a.cal_reps, a.chunk, a.seed)
        row.update(seed=a.seed, clusters=a.clusters, cal_reps=a.cal_reps, chunk=a.chunk, fingerprint=fp)
        rows = [r for r in rows if r["name"] != name] + [row]
        s, b = row["summary"], row["summary"]["boundary"]
        print("%-34s th %+.4f (ref %+.4f) cov %s | io %+.4f (ref %+.4f) cov %s | iw %s (ref %+.4f) cov %s "
              "| holm th %.3f io %.3f any %.3f both %.3f | io&iw %.3f | p3 %.3f | %.0fs"
              % (name, s["th"]["mean"] if s["th"]["mean"] is not None else float("nan"), s["th"]["reference"],
                 _fmt(s["th"]["cover95"]), s["io"]["mean"] if s["io"]["mean"] is not None else float("nan"),
                 s["io"]["reference"], _fmt(s["io"]["cover95"]), _fmt(s["iw"]["mean"], "+.4f"),
                 s["iw"]["reference"], _fmt(s["iw"]["cover95"]),
                 s["registered"]["holm_theta"], s["registered"]["holm_iota"],
                 s["registered"]["any"], s["registered"]["both"], s["p2_and_within"]["either"], s["p3_reject"],
                 row["seconds"]), flush=True)
        if b["zero_denominator"] or any(b["zero_variance"].values()) or b["iw_not_estimable_with_io"]:
            print(f"    boundary cases in {b['replications']} replications: zero denominator {b['zero_denominator']}, "
                  f"zero variance {b['zero_variance']}, tests carried out {b['carried_out']}, iota_W not estimable "
                  f"with iota_S estimable {b['iw_not_estimable_with_io']}", flush=True)
        for u in row["calibration"]["unreached"]:
            print(f"    TARGET NOT REACHED: {u['name']} = {u['target']}; nearest value {u['nearest']} "
                  f"(shift {u['shift']})", flush=True)
        for c in row["checks"]:
            if c["made"] and not c["passed"]:
                print(f"    CHECK {c['check']} FAILS: {c['what']} {c['value']:.4f} against {c['limit']:.4f} "
                      f"(R {c['R']})", flush=True)
        if sc.get("target_not_reproduced"):
            print("    pilot planning scenario: target not reproduced (analysis/pilot_planning_v23.py report)", flush=True)
        if path:
            path.write_text(json.dumps({"grid": a.grid, "judges": D["judges"], "dropped": D["dropped"],
                                        "blocks": D["blocks"], "rows": rows}, indent=1), encoding="utf-8")


def _fmt(x, spec=".3f"):
    return " n/a " if x is None else format(x, spec)


if __name__ == "__main__":
    main()
