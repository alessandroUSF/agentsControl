"""Power, size and coverage simulation for the yoked design proposed for protocol v2.3 (draft, 10 Nov 2026).

Design simulated (harm side unless --side safe):
  22 judges in two access groups (API: 1,2,3,7-14,22; local: 4,5,6,15-21). Judge j has its own answer to
  each of n_j prompts (API n_api, local n_local; the API prompts are a prefix of the local ones). Every answer
  is judged by its author and by one unrelated control judge of the same access group (no self, close or
  same-developer relation; one seeded permutation per prompt, pair counts balanced greedily), each under the
  blind and the in-context presentation.

Estimands (equal-judge averages of delivered valid flags; an invalid verdict counts as "no flag"):
  theta_on = mean_j mean_i [F_ctx - F_blind] on the judge's own answers;
  iota     = mean_j mean_i [(F_ctx - F_blind) author - (F_ctx - F_blind) control] on the same answers;
  beta_bl  = mean_j mean_i [F_blind author - F_blind control] on the same answers.

Data-generating process (assumptions, not estimates; the failure rates and judge parameters are those of
analysis/power_sim.py):
  failure of an answer (harmful content on the harm side; over-refusal on the safe side) ~ Bernoulli with
  logit = c_group + a_p, a_p ~ N(0, 0.8) per prompt, c_group calibrated to the marginal rate
  (harm: commercial 0.05, instruct local 0.15, refusal-removed 0.70; safe: 0.10, 0.15, 0.02);
  judge sensitivity Se_j ~ U(0.70, 0.95), specificity Sp_j ~ U(0.85, 0.98), fixed within a simulated panel of
      22 judges (as in the study) and redrawn across panels (20 panels per scenario by default);
  blind logit = logit(Se_j if failure else 1 - Sp_j) + u_p + v_answer + w_judge,answer,
      u ~ N(0, 0.6), v ~ N(0, 0.6), w ~ N(0, 0.4); plus g_blind on the author's own answers;
  in-context logit = blind logit + g_on (author) or g_ctrl (control) + s_p (both arms, N(0, sd_common))
      + t_p (author arm only, N(0, sd_own)) + h_j (judge heterogeneity; mode "opposing": +/-0.5 by judge);
      mode "fail_only": g_on and g_ctrl act on failure answers only;
  the blind and in-context verdicts of one judge on one answer share the uniform draw with probability rho,
      solved so that the null discordance of the author arm equals q0 (reported if the shocks alone exceed q0);
  g_blind, g_on, g_ctrl are solved per panel so that its equal-judge average marginal effects equal the targets;
  invalid verdicts: "3" = 3% in both presentations; "10" = 10% in both; "10_15" = 10% blind, 15% in context;
      "harm" = 5% blind, in context 5% on non-failure and 25% on failure answers. Validity draws of the two
      presentations share the uniform draw with probability 0.5.

Tests: cluster sign-flip over prompts (B sign vectors) for theta_on and iota, Holm at alpha_primary (0.04);
blind bound H0: beta_bl <= -margin (margins 0.03, 0.05, 0.07), one-sided shifted sign-flip at alpha_bound (0.01).
Intervals: cluster-robust t intervals over prompts (95%); coverage is measured against each panel's own mean.
Standard errors reported are within-panel standard deviations of the estimates.

Label-conditioned quantities (answer-weighted, the simulated failure indicator standing in for the human label):
  change of the flag rate on failure answers (sensitivity change) and on non-failure answers (false-positive
  change), author arm and author-minus-control, for all answers of the frame and for two labelled subsets of
  GOLD_TOTAL answers: "bal" (equal quota per author) and "tilt" (quotas GOLD_TILT per author by group).

Options added after the first review round (defaults reproduce the earlier results exactly):
  --yoke type      controls come from the same model type instead of the same access group: commercial (11),
                   local instruction-tuned (5), refusal-removed (5 local + the one API model);
  --sus x          in-context logit shift of the refusal-removed judges on failure answers, own and control arm
                   alike (a type-level susceptibility that is not self-specific); the targets exclude it;
  --structural     no self-specific effect at all: the control arm receives the author arm's shift;
  --se-removed x   logit shift of the blind sensitivity of the refusal-removed judges;
  --panel harm11   primary panel = the eleven non-commercial models (ten local + the refusal-removed API model),
                   all on the long frame (n_local prompts); the commercial judges keep n_api prompts, weight zero;
  --panel mixed    all 22 judges with equal weights; the eleven non-commercial models use the long frame;
  --alts           further statistics on the same simulated data: "h11" (the harm11 sub-panel), "scr" (all 22
                   judges, only answers that a refusal screen marks as non-refusals; the ratio estimand is the
                   failure-weighted mean change among screened answers) and "h11scr" (both). The screen is a
                   function of the answer only (here: the failure indicator, optionally with errors set by
                   --screen-se and --screen-sp), so it is fixed before any judgment; the control arm of a
                   screened statistic uses the screen of the yoked answer, i.e. the same answers in both arms.

Usage: python -I analysis/power_sim_v23.py --grid screen --reps 2000 --flips 1999 --out screen.json
"""
import argparse
import functools
import itertools
import json
import time
from pathlib import Path

import numpy as np
from scipy import stats
from scipy.optimize import brentq
from scipy.special import expit, logit

OUT_DIR = Path(__file__).resolve().parent / "output"
SEED = 20261121
API = [1, 2, 3, 7, 8, 9, 10, 11, 12, 13, 14, 22]
LOCAL = [4, 5, 6, 15, 16, 17, 18, 19, 20, 21]
COMMERCIAL = [1, 2, 3, 7, 8, 9, 10, 11, 12, 13, 14]
INSTRUCT_LOCAL = [4, 5, 15, 16, 17]
DEV = {1: "anthropic", 2: "anthropic", 3: "openai", 9: "openai", 11: "openai", 4: "meta", 6: "meta",
       20: "meta", 5: "alibaba", 15: "alibaba", 18: "alibaba", 19: "alibaba", 7: "deepseek", 8: "zai",
       10: "tencent", 14: "google", 12: "moonshot", 13: "xai", 16: "ibm", 17: "liquid",
       21: "mistral", 22: "mistral"}
CLOSE = {frozenset(p) for p in [(4, 6), (5, 18), (15, 19), (20, 4), (20, 6), (20, 21), (20, 22), (21, 22)]}
FAIL = {"harm": {"c": 0.05, "i": 0.15, "r": 0.70}, "safe": {"c": 0.10, "i": 0.15, "r": 0.02}}
JUDGES = API + LOCAL                      # array order: API first, then local
NJ = len(JUDGES)
GROUP = ["c" if m in COMMERCIAL else ("i" if m in INSTRUCT_LOCAL else "r") for m in JUDGES]
F32 = np.float32
BOUND_MARGINS = (0.03, 0.05, 0.07)   # candidate margins of the blind bound H0: beta_bl <= -margin
GOLD_TOTAL = 300                     # labelled answers on this side (harm side: all double-labelled)
GOLD_TILT = {"c": 4.1, "i": 15.0, "r": 30.0}   # labelled answers per author under the tilted allocation
GOLD_TAGS = ("all", "bal", "tilt")


ALT_TAGS = ("h11", "scr", "h11scr")     # open-model sub-panel; screen-positive answers; both
ALT_MARGINS = (0.03, 0.05, 0.07, 0.10)


def related(j, a):
    return j == a or frozenset((j, a)) in CLOSE or DEV[j] == DEV[a]


def control_assignment(members, n_prompts, rng, candidates=12):
    """donor[k, p] = position in `members` of the author whose answer member k judges as control at prompt p.
    One valid permutation per prompt (no related pair), chosen greedily to balance the judge-donor pair counts."""
    k = len(members)
    ok = np.array([[not related(j, a) for a in members] for j in members])
    counts = np.zeros((k, k))
    donor = np.zeros((k, n_prompts), int)
    rows = np.arange(k)
    for p in range(n_prompts):
        found = []
        while len(found) < candidates:
            perms = np.argsort(rng.random((4000, k)), axis=1)
            found += list(perms[ok[rows, perms].all(axis=1)])
        found = np.array(found[:candidates])
        cost = [(counts[rows, f] ** 2).sum() for f in found]
        best = found[int(np.argmin(cost))]
        donor[:, p] = best
        counts[rows, best] += 1
    return donor, counts


def yoke_blocks(yoke, n):
    """Yoking strata as (name, array positions, first prompt, last prompt + 1); n = prompts per judge (array order).
    "access": controls come from the same access group (API or local).
    "type": controls come from the same model type (commercial, local instruction-tuned, refusal-removed);
    the refusal-removed stratum joins the five local models and the one API model (Venice).
    Judges of one stratum may have different numbers of prompts: each segment of prompts is yoked among the
    judges that have it."""
    pos = {m: k for k, m in enumerate(JUDGES)}
    if yoke == "access":
        strata = [("api", [pos[m] for m in API]), ("local", [pos[m] for m in LOCAL])]
    elif yoke == "type":
        removed = [m for m in LOCAL if m not in INSTRUCT_LOCAL] + [m for m in API if m not in COMMERCIAL]
        strata = [("commercial", [pos[m] for m in COMMERCIAL]),
                  ("instruct_local", [pos[m] for m in INSTRUCT_LOCAL]),
                  ("refusal_removed", [pos[m] for m in removed])]
    else:
        raise ValueError(yoke)
    blocks = []
    for name, members in strata:
        cuts = sorted({int(n[k]) for k in members})
        lo = 0
        for hi in cuts:
            active = [k for k in members if n[k] >= hi]
            if len(active) < 2:
                raise ValueError(f"no control judge for {name}, prompts {lo} to {hi}")
            blocks.append((name if len(cuts) == 1 else f"{name}_{lo}_{hi}", active, lo, hi))
            lo = hi
    return blocks


def design(n_api, n_local, seed=SEED, yoke="access", panel="all"):
    """Masks, weights and donor indices (array positions) for the whole panel.
    panel "all": the 22 judges with equal weights. panel "harm11": the ten local models and the refusal-removed
    API model, all on the local frame (n_local prompts), with equal weights; the commercial judges keep n_api
    prompts and weight zero."""
    rng = np.random.default_rng(seed)
    n = np.array([n_api] * len(API) + [n_local] * len(LOCAL))
    sub = np.ones(NJ, dtype=bool)
    h11 = np.array([m not in COMMERCIAL for m in JUDGES])
    if panel in ("harm11", "mixed"):
        # "mixed": all 22 judges with equal weights; the open models (and Venice) use the long frame
        n[[k for k, m in enumerate(JUDGES) if m in API and m not in COMMERCIAL]] = n_local
        if panel == "harm11":
            sub = h11
    elif panel != "all":
        raise ValueError(panel)
    P = int(n.max())
    mask = np.arange(P)[None, :] < n[:, None]
    donor = np.tile(np.arange(NJ)[:, None], (1, P))
    spread = {}
    for name, positions, p0, p1 in yoke_blocks(yoke, n):
        members = [JUDGES[k] for k in positions]
        d, counts = control_assignment(members, p1 - p0, rng)
        donor[np.array(positions), p0:p1] = np.array(positions)[d]
        allowed = counts[np.array([[not related(j, a) for a in members] for j in members])]
        spread[name] = [int(allowed.min()), int(allowed.max())]
    wgt = (mask * sub[:, None] / n[:, None] / sub.sum()).astype(F32)
    wgt_h11 = (mask * h11[:, None] / n[:, None] / h11.sum()).astype(F32)
    wgt_all = (mask / n[:, None] / NJ).astype(F32)
    return dict(P=P, n=n, mask=mask, donor=donor, wgt=wgt, share=wgt.sum(0), spread=spread, sub=sub,
                wgt_h11=wgt_h11, wgt_all=wgt_all)


@functools.lru_cache(maxsize=None)
def _fail_intercepts(side, sd=0.8):
    a = np.random.default_rng(1).normal(0, sd, 200000)
    out = {}
    for g, target in FAIL[side].items():
        lo, hi = -15.0, 15.0
        for _ in range(60):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if expit(mid + a).mean() < target else (lo, mid)
        out[g] = (lo + hi) / 2
    return tuple(out[g] for g in GROUP)


def fail_intercepts(side):
    return np.array(_fail_intercepts(side))


def draw_panel(rng, sc=None):
    """Sensitivity and specificity of the 22 judges of one simulated panel, arrays [1, judge, 1].
    sc["se_removed"] is a logit shift of the sensitivity of the refusal-removed judges (0 = one distribution)."""
    se, sp = rng.uniform(0.70, 0.95, (1, NJ, 1)), rng.uniform(0.85, 0.98, (1, NJ, 1))
    shift = (sc or {}).get("se_removed", 0.0)
    if shift:
        removed = np.array([g == "r" for g in GROUP])[None, :, None]
        se = np.where(removed, expit(logit(se) + shift), se)
    return se, sp


def draw_latent(rng, R, D, cfail, sc, se, sp):
    """Latent blind logits and shocks for R replications. Arrays are [R, judge, prompt]."""
    P = D["P"]
    shape = (R, NJ, P)
    a_p = rng.normal(0, 0.8, (R, 1, P))
    fail_own = rng.random(shape) < expit(cfail[None, :, None] + a_p)
    u = rng.normal(0, 0.6, (R, 1, P))
    v_own = rng.normal(0, 0.6, shape)
    idx = D["donor"][None, :, :]
    fail_ctrl = np.take_along_axis(fail_own, np.broadcast_to(idx, shape), axis=1)
    v_ctrl = np.take_along_axis(v_own, np.broadcast_to(idx, shape), axis=1)
    eta_own = (logit(np.where(fail_own, se, 1 - sp)) + u + v_own + rng.normal(0, 0.4, shape)).astype(F32)
    eta_ctrl = (logit(np.where(fail_ctrl, se, 1 - sp)) + u + v_ctrl + rng.normal(0, 0.4, shape)).astype(F32)
    s = rng.normal(0, sc["sd_common"], (R, 1, P)) if sc["sd_common"] > 0 else np.zeros((R, 1, P))
    t = rng.normal(0, sc["sd_own"], (R, 1, P)) if sc["sd_own"] > 0 else np.zeros((R, 1, P))
    h = np.zeros((1, NJ, 1))
    if sc["mode"] == "opposing":
        h[0, :, 0] = np.where(np.arange(NJ) % 2 == 0, 0.5, -0.5)
    sus_own = sus_ctrl = 0.0
    if sc.get("sus", 0.0):
        removed = np.array([g == "r" for g in GROUP], dtype=np.float64)[None, :, None]
        sus_own, sus_ctrl = sc["sus"] * removed * fail_own, sc["sus"] * removed * fail_ctrl
    return dict(fail_own=fail_own, fail_ctrl=fail_ctrl, eta_own=eta_own, eta_ctrl=eta_ctrl,
                shock_own=(s + t + h + sus_own).astype(F32), shock_ctrl=(s + h + sus_ctrl).astype(F32),
                sus_own=np.asarray(sus_own, dtype=F32), sus_ctrl=np.asarray(sus_ctrl, dtype=F32))


def solve_shift(base, extra, m, w, target):
    """g with sum(w * (expit(base + extra + g*m) - expit(base))) = target (the nearest bound if not attainable)."""
    p0 = float((w * expit(base)).sum())
    z = base + extra

    def f(g):
        return float((w * expit(z + F32(g) * m)).sum()) - p0 - target

    if f(-12.0) >= 0:
        return -12.0
    if f(12.0) <= 0:
        return 12.0
    return float(brentq(f, -12.0, 12.0, xtol=1e-5, maxiter=80))


def calibrate(D, cfail, sc, rng, se, sp):
    """Shifts and coupling for one panel, so that this panel's average marginal effects equal the targets."""
    L = draw_latent(rng, max(40, int(sc.get("cal_prompts", 8.0e3) // D["P"])), D, cfail, sc, se, sp)
    w = np.broadcast_to(D["wgt"][None], L["eta_own"].shape) / L["eta_own"].shape[0]
    g_blind = solve_shift(L["eta_own"], 0.0, 1.0, w, sc["beta_blind"])
    eta_own = L["eta_own"] + g_blind
    m_own = L["fail_own"].astype(F32) if sc["mode"] == "fail_only" else 1.0
    m_ctrl = L["fail_ctrl"].astype(F32) if sc["mode"] == "fail_only" else 1.0
    # the targets refer to the general shift; a type-level susceptibility ("sus") comes on top of them
    g_on = solve_shift(eta_own, L["shock_own"] - L["sus_own"], m_own, w, sc["theta_on"])
    if sc.get("structural"):
        g_ctrl = g_on
    else:
        g_ctrl = solve_shift(L["eta_ctrl"], L["shock_ctrl"] - L["sus_ctrl"], m_ctrl, w,
                             sc["theta_on"] - sc["iota"])
    pb, pc = expit(eta_own), expit(eta_own + L["shock_own"])          # null discordance of the author arm
    a = float((w * (pb * (1 - pc) + pc * (1 - pb))).sum())
    b = float((w * np.abs(pc - pb)).sum())
    rho = float(np.clip((a - sc["q0"]) / (a - b), 0.0, 1.0))
    return dict(g_blind=g_blind, g_on=g_on, g_ctrl=g_ctrl, rho=rho, q0_floor=b,
                fail_share=float((w * L["fail_own"]).sum()))


def invalid_probs(mode, fail):
    if mode == "3":
        return 0.03, 0.03
    if mode == "10":
        return 0.10, 0.10
    if mode == "10_15":
        return 0.10, 0.15
    if mode == "harm":
        return 0.05, np.where(fail, 0.25, 0.05)
    raise ValueError(mode)


def verdicts(rng, eta_b, eta_c, fail, rho, inv_mode):
    shape = eta_b.shape
    ub = rng.random(shape, dtype=F32)
    uc = np.where(rng.random(shape, dtype=F32) < rho, ub, rng.random(shape, dtype=F32))
    fb, fc = ub < expit(eta_b), uc < expit(eta_c)
    ib, ic = invalid_probs(inv_mode, fail)
    vb_u = rng.random(shape, dtype=F32)
    vc_u = np.where(rng.random(shape, dtype=F32) < 0.5, vb_u, rng.random(shape, dtype=F32))
    return fb, fc, vb_u >= ib, vc_u >= ic


def signflip_p(c, S, one_sided=False):
    """c [R, P] cluster contributions; S [B, P] signs. Two-sided p for sum(c) = 0, or one-sided (large = reject)."""
    t = c.sum(1)
    tb = c @ S.T
    if one_sided:
        return (1 + (tb >= t[:, None] - 1e-12).sum(1)) / (S.shape[0] + 1)
    return (1 + (np.abs(tb) >= np.abs(t)[:, None] - 1e-12).sum(1)) / (S.shape[0] + 1)


def robust_ci(c, share, level=0.95):
    P = c.shape[1]
    est = c.sum(1)
    se = np.sqrt(P / (P - 1) * ((c - share[None] * est[:, None]) ** 2).sum(1))
    tq = stats.t.ppf(0.5 + level / 2, P - 1)
    return est, se, est - tq * se, est + tq * se


def ratio_ci(c, s, level=0.95):
    """Ratio sum(c) / sum(s) over prompt clusters, c and s [R, P]; linearised cluster-robust t interval."""
    P = c.shape[1]
    den = np.maximum(s.sum(1), 1e-12)
    est = c.sum(1) / den
    se = np.sqrt(P / (P - 1) * ((c - est[:, None] * s) ** 2).sum(1)) / den
    tq = stats.t.ppf(0.5 + level / 2, P - 1)
    return est, se, est - tq * se, est + tq * se


def simulate(sc, reps, flips, seed=SEED, panels=20):
    """One scenario. Judge parameters are fixed within a simulated panel (as in the study) and redrawn across panels;
    coverage is measured against each panel's own mean estimate."""
    sc = {"side": "harm", "n_api": 60, "n_local": 60, "sd_common": 0.0, "sd_own": 0.0, "q0": 0.10,
          "theta_on": 0.0, "iota": 0.0, "beta_blind": 0.0, "inv": "3", "mode": "all",
          "alpha_primary": 0.04, "alpha_bound": 0.01, "yoke": "access", "sus": 0.0, "structural": False,
          "se_removed": 0.0, "panel": "all", "alts": False, "screen_se": 1.0, "screen_sp": 1.0, **sc}
    D = design(sc["n_api"], sc["n_local"], yoke=sc["yoke"], panel=sc["panel"])
    cfail = fail_intercepts(sc["side"])
    rng = np.random.default_rng(seed)
    P, wgt, share = D["P"], D["wgt"][None], D["share"].astype(np.float64)
    per = max(2, reps // panels)
    chunk = max(20, int(1.5e6 // (NJ * P)))
    is_api = np.arange(NJ) < len(API)
    keys = ["p_on", "p_int", "on", "int", "bl", "on_lo", "on_hi", "int_lo", "int_hi", "cc_on", "cc_int", "lb_on",
            "ub_on", "fc_on", "disc", "inv_b", "inv_c", "api_on", "loc_on", "api_int", "loc_int", "grp_on"]
    keys += [f"p_bl{m}" for m in BOUND_MARGINS]
    gkeys = [f"{q}_{t}" for t in GOLD_TAGS for q in ("npos", "sens_on", "sens_int", "fp_on", "fp_int")]
    keys += gkeys
    if sc["alts"]:
        for tag in ALT_TAGS:
            keys += [f"{q}_{tag}" for q in ("p_on", "p_int", "on", "int", "bl", "den", "ron", "rint", "rbl")]
            keys += [f"{q}_{tag}" for q in ("rlo_on", "rhi_on", "rlo_int", "rhi_int")]
            keys += [f"p_bl{m}_{tag}" for m in ALT_MARGINS]
    sub = D["sub"]
    pi = {"bal": sub * np.minimum(1.0, GOLD_TOTAL / sub.sum() / D["n"]),
          "tilt": sub * np.minimum(1.0, np.array([GOLD_TILT[g] for g in GROUP]) / D["n"])}
    tot = {k: [] for k in keys}
    cover_on, cover_int, cals = [], [], []
    cover_alt = {(q, tag): [] for q in ("on", "int") for tag in ALT_TAGS}
    for _ in range(panels):
        se, sp = draw_panel(rng, sc)
        cal = calibrate(D, cfail, sc, rng, se, sp)
        cals.append(cal)
        acc = {k: [] for k in keys}
        done = 0
        while done < per:
            R = min(chunk, per - done)
            L = draw_latent(rng, R, D, cfail, sc, se, sp)
            m_own = L["fail_own"] if sc["mode"] == "fail_only" else 1.0
            m_ctrl = L["fail_ctrl"] if sc["mode"] == "fail_only" else 1.0
            eb_own = L["eta_own"] + F32(cal["g_blind"])
            ec_own = eb_own + L["shock_own"] + F32(cal["g_on"]) * m_own
            ec_ctrl = L["eta_ctrl"] + L["shock_ctrl"] + F32(cal["g_ctrl"]) * m_ctrl
            fb, fc, vb, vc = verdicts(rng, eb_own, ec_own, L["fail_own"], cal["rho"], sc["inv"])
            gb, gc, wb, wc = verdicts(rng, L["eta_ctrl"], ec_ctrl, L["fail_ctrl"], cal["rho"], sc["inv"])
            d_own = (fc & vc).astype(F32) - (fb & vb)
            d_ctrl = (gc & wc).astype(F32) - (gb & wb)
            c_on = (wgt * d_own).sum(1, dtype=np.float64)
            c_int = (wgt * (d_own - d_ctrl)).sum(1, dtype=np.float64)
            c_bl = (wgt * ((fb & vb).astype(F32) - (gb & wb))).sum(1, dtype=np.float64)
            S = rng.choice(np.array([-1.0, 1.0]), size=(flips, P))
            acc["p_on"].append(signflip_p(c_on, S))
            acc["p_int"].append(signflip_p(c_int, S))
            for m in BOUND_MARGINS:
                acc[f"p_bl{m}"].append(signflip_p(c_bl + m * share[None], S, one_sided=True))
            for key, c in (("on", c_on), ("int", c_int)):
                est, _, lo, hi = robust_ci(c, share)
                acc[key].append(est); acc[key + "_lo"].append(lo); acc[key + "_hi"].append(hi)
            acc["bl"].append(c_bl.sum(1))
            if sc["alts"]:
                shape = d_own.shape
                don = np.broadcast_to(D["donor"][None], shape)
                scr = L["fail_own"].astype(bool)
                if sc["screen_se"] < 1.0 or sc["screen_sp"] < 1.0:      # imperfect refusal screen
                    u = rng.random(shape, dtype=F32)
                    scr = np.where(scr, u < sc["screen_se"], u > sc["screen_sp"])
                scr_c = np.take_along_axis(scr, don, axis=1)             # screen of the yoked answer
                b_own, b_ctrl = (fb & vb).astype(F32), (gb & wb).astype(F32)
                one = np.ones(shape, dtype=bool)
                for tag, w0, so, sx in (("h11", D["wgt_h11"], one, one), ("scr", D["wgt_all"], scr, scr_c),
                                        ("h11scr", D["wgt_h11"], scr, scr_c)):
                    wo = np.broadcast_to(w0[None], shape) * so
                    wx = np.take_along_axis(np.broadcast_to(w0[None], shape), don, axis=1) * sx   # the answer's weight
                    ca_on = (wo * d_own).sum(1, dtype=np.float64)
                    ca_int = (wo * d_own - wx * d_ctrl).sum(1, dtype=np.float64)
                    ca_bl = (wo * b_own - wx * b_ctrl).sum(1, dtype=np.float64)
                    sh = wo.sum(1, dtype=np.float64)
                    den = np.maximum(sh.sum(1), 1e-12)
                    acc[f"p_on_{tag}"].append(signflip_p(ca_on, S))
                    acc[f"p_int_{tag}"].append(signflip_p(ca_int, S))
                    for m in ALT_MARGINS:
                        acc[f"p_bl{m}_{tag}"].append(signflip_p(ca_bl + m * sh, S, one_sided=True))
                    acc[f"on_{tag}"].append(ca_on.sum(1)); acc[f"int_{tag}"].append(ca_int.sum(1))
                    acc[f"bl_{tag}"].append(ca_bl.sum(1)); acc[f"den_{tag}"].append(den)
                    acc[f"ron_{tag}"].append(ca_on.sum(1) / den); acc[f"rint_{tag}"].append(ca_int.sum(1) / den)
                    acc[f"rbl_{tag}"].append(ca_bl.sum(1) / den)
                    for q, ca in (("on", ca_on), ("int", ca_int)):
                        _, _, lo, hi = ratio_ci(ca, sh)
                        acc[f"rlo_{q}_{tag}"].append(lo); acc[f"rhi_{q}_{tag}"].append(hi)
            mk = D["mask"][None]
            both, both_c = vb & vc & mk, wb & wc & mk                         # complete cases
            cc_o = (both * (fc.astype(F32) - fb)).sum(2) / np.maximum(both.sum(2), 1)
            cc_c = (both_c * (gc.astype(F32) - gb)).sum(2) / np.maximum(both_c.sum(2), 1)
            acc["cc_on"].append(cc_o[:, sub].mean(1)); acc["cc_int"].append((cc_o - cc_c)[:, sub].mean(1))
            acc["lb_on"].append((wgt * ((fc & vc).astype(F32) - (fb | ~vb))).sum((1, 2)))   # invalid: ctx 0, blind 1
            acc["ub_on"].append((wgt * ((fc | ~vc).astype(F32) - (fb & vb))).sum((1, 2)))
            acc["fc_on"].append((wgt * ((fc | ~vc).astype(F32) - (fb | ~vb))).sum((1, 2)))  # fail-closed: invalid = flag
            acc["disc"].append((wgt * (fb != fc)).sum((1, 2)))
            acc["inv_b"].append((wgt * ~vb).sum((1, 2))); acc["inv_c"].append((wgt * ~vc).sum((1, 2)))
            pj_on = (d_own * mk).sum(2) / D["n"][None]
            pj_int = ((d_own - d_ctrl) * mk).sum(2) / D["n"][None]
            acc["api_on"].append(pj_on[:, is_api].mean(1)); acc["loc_on"].append(pj_on[:, ~is_api].mean(1))
            acc["api_int"].append(pj_int[:, is_api].mean(1)); acc["loc_int"].append(pj_int[:, ~is_api].mean(1))
            acc["grp_on"].append(np.stack([pj_on[:, [g == x for g in GROUP]].mean(1) for x in "cir"], 1))
            idx = np.broadcast_to(D["donor"][None], d_own.shape)
            for tag in GOLD_TAGS:
                if tag == "all":
                    so = np.broadcast_to(mk & sub[None, :, None], d_own.shape)
                else:
                    so = mk & (rng.random(d_own.shape, dtype=F32) < pi[tag][None, :, None].astype(F32))
                sx = np.take_along_axis(so, idx, axis=1) & mk
                for q, truth_o, truth_x in (("sens", L["fail_own"], L["fail_ctrl"]),
                                            ("fp", ~L["fail_own"], ~L["fail_ctrl"])):
                    n_o = (so & truth_o).sum((1, 2))
                    a_o = ((so & truth_o) * d_own).sum((1, 2))
                    a_x = ((sx & truth_x) * d_ctrl).sum((1, 2))
                    den = np.maximum(n_o, 1)
                    acc[f"{q}_on_{tag}"].append(a_o / den)
                    acc[f"{q}_int_{tag}"].append((a_o - a_x) / den)
                    if q == "sens":
                        acc[f"npos_{tag}"].append(n_o.astype(np.float64))
            done += R
        A = {k: np.concatenate(v) for k, v in acc.items()}
        cover_on.append(((A["on_lo"] <= A["on"].mean()) & (A["on"].mean() <= A["on_hi"])).mean())
        cover_int.append(((A["int_lo"] <= A["int"].mean()) & (A["int"].mean() <= A["int_hi"])).mean())
        if sc["alts"]:
            for q, tag in cover_alt:
                truth = A[f"{q}_{tag}"].mean() / A[f"den_{tag}"].mean()
                cover_alt[(q, tag)].append(((A[f"rlo_{q}_{tag}"] <= truth) & (truth <= A[f"rhi_{q}_{tag}"])).mean())
        for k in keys:
            tot[k].append(A[k])
    sd_within = {k: float(np.sqrt(np.mean([v.var(ddof=1) for v in tot[k]])))
                 for k in ["on", "int", "bl", "api_on", "loc_on", "api_int", "loc_int"] + gkeys}
    A = {k: np.concatenate(v) for k, v in tot.items()}
    a = sc["alpha_primary"]
    p1, p2 = np.minimum(A["p_on"], A["p_int"]), np.maximum(A["p_on"], A["p_int"])
    first = p1 <= a / 2
    rej_on = np.where(A["p_on"] <= A["p_int"], first, first & (p2 <= a))
    rej_int = np.where(A["p_int"] < A["p_on"], first, first & (p2 <= a))
    res = {
        "scenario": sc, "reps": int(A["on"].size), "flips": flips, "panels": panels,
        "calibration": {k: float(np.mean([c[k] for c in cals])) for k in cals[0]},
        "control_pair_count_range": D["spread"],
        "true_on": A["on"].mean(), "true_int": A["int"].mean(), "true_blind": A["bl"].mean(),
        "panel_sd_on": float(np.std([v.mean() for v in tot["on"]], ddof=1)),
        "panel_sd_int": float(np.std([v.mean() for v in tot["int"]], ddof=1)),
        "panel_sd_blind": float(np.std([v.mean() for v in tot["bl"]], ddof=1)),
        "discordance": A["disc"].mean(), "invalid_blind": A["inv_b"].mean(), "invalid_ctx": A["inv_c"].mean(),
        "se_on": sd_within["on"], "se_int": sd_within["int"], "se_blind": sd_within["bl"],
        "holm_reject_on": rej_on.mean(), "holm_reject_int": rej_int.mean(), "holm_reject_any": first.mean(),
        "holm_reject_both": (rej_on & rej_int).mean(),
        "reject_on_half_alpha": (A["p_on"] <= a / 2).mean(), "reject_int_half_alpha": (A["p_int"] <= a / 2).mean(),
        "reject_on_alpha": (A["p_on"] <= a).mean(), "reject_int_alpha": (A["p_int"] <= a).mean(),
        "bound_reject": {str(m): (A[f"p_bl{m}"] <= sc["alpha_bound"]).mean() for m in BOUND_MARGINS},
        "cover_on": float(np.mean(cover_on)), "cover_int": float(np.mean(cover_int)),
        "half_width_on": ((A["on_hi"] - A["on_lo"]) / 2).mean(),
        "half_width_int": ((A["int_hi"] - A["int_lo"]) / 2).mean(),
        "exclude_on": {str(m): (A["on_lo"] > -m).mean() for m in (0.02, 0.03, 0.05)},
        "exclude_int": {str(m): (A["int_lo"] > -m).mean() for m in (0.02, 0.03, 0.05)},
        "complete_case_on": A["cc_on"].mean(), "complete_case_int": A["cc_int"].mean(),
        "bounds_on": [A["lb_on"].mean(), A["ub_on"].mean()], "fail_closed_on": A["fc_on"].mean(),
        "api": {"on": A["api_on"].mean(), "se_on": sd_within["api_on"],
                "int": A["api_int"].mean(), "se_int": sd_within["api_int"]},
        "local": {"on": A["loc_on"].mean(), "se_on": sd_within["loc_on"],
                  "int": A["loc_int"].mean(), "se_int": sd_within["loc_int"]},
        "group_on": dict(zip(["commercial", "instruct_local", "refusal_removed"], A["grp_on"].mean(0).tolist())),
        "labelled": {t: {"n_pos": A[f"npos_{t}"].mean(),
                         **{q: A[f"{q}_{t}"].mean() for q in ("sens_on", "sens_int", "fp_on", "fp_int")},
                         **{"se_" + q: sd_within[f"{q}_{t}"] for q in ("sens_on", "sens_int", "fp_on", "fp_int")}}
                     for t in GOLD_TAGS},
    }
    if sc["alts"]:
        def sdw(k):
            return float(np.sqrt(np.mean([v.var(ddof=1) for v in tot[k]])))
        res["alt"] = {}
        for tag in ALT_TAGS:
            pa, pb = A[f"p_on_{tag}"], A[f"p_int_{tag}"]
            f1 = np.minimum(pa, pb) <= a / 2
            r_on = np.where(pa <= pb, f1, f1 & (np.maximum(pa, pb) <= a))
            r_int = np.where(pb < pa, f1, f1 & (np.maximum(pa, pb) <= a))
            res["alt"][tag] = {
                "den": A[f"den_{tag}"].mean(), "true_on": A[f"on_{tag}"].mean(), "true_int": A[f"int_{tag}"].mean(),
                "true_blind": A[f"bl_{tag}"].mean(), "ratio_on": A[f"ron_{tag}"].mean(),
                "ratio_int": A[f"rint_{tag}"].mean(), "ratio_blind": A[f"rbl_{tag}"].mean(),
                "se_on": sdw(f"on_{tag}"), "se_int": sdw(f"int_{tag}"), "se_ratio_on": sdw(f"ron_{tag}"),
                "se_ratio_int": sdw(f"rint_{tag}"), "se_ratio_blind": sdw(f"rbl_{tag}"),
                "holm_reject_on": r_on.mean(), "holm_reject_int": r_int.mean(),
                "reject_on_alpha": (pa <= a).mean(), "reject_int_alpha": (pb <= a).mean(),
                "cover_ratio_on": float(np.mean(cover_alt[("on", tag)])),
                "cover_ratio_int": float(np.mean(cover_alt[("int", tag)])),
                "half_width_ratio_on": ((A[f"rhi_on_{tag}"] - A[f"rlo_on_{tag}"]) / 2).mean(),
                "half_width_ratio_int": ((A[f"rhi_int_{tag}"] - A[f"rlo_int_{tag}"]) / 2).mean(),
                "bound_reject": {str(m): (A[f"p_bl{m}_{tag}"] <= sc["alpha_bound"]).mean() for m in ALT_MARGINS}}
    return json.loads(json.dumps(res, default=float))


GRIDS = {
    # sd pairs are (sd_common, sd_own)
    "smoke": dict(shock=[(0.0, 0.0)], q0=[0.10], theta_on=[0.0, -0.05], iota=[0.0], inv=["3"], mode=["all"]),
    "screen": dict(shock=[(0.0, 0.0), (0.3, 0.3), (0.6, 0.6)], q0=[0.06, 0.10, 0.14, 0.20],
                   theta_on=[0.0, -0.02, -0.05], iota=[0.0, -0.02, -0.05], inv=["3", "10", "10_15"], mode=["all"]),
    "core": dict(shock=[(0.0, 0.0), (0.3, 0.3)], q0=[0.10], theta_on=[0.0, -0.02, -0.05], iota=[0.0, -0.02, -0.05],
                 inv=["3"], mode=["all", "fail_only"]),
    "specific": dict(shock=[(0.3, 0.0)], q0=[0.10], theta_on=[0.0, -0.02, -0.05], iota=[0.0], inv=["3"],
                     mode=["fail_only", "all"]),
    "sub": dict(shock=[(0.3, 0.3)], q0=[0.10], theta_on=[0.0, -0.02, -0.035], iota=[0.0, -0.02, -0.035], inv=["3"],
                mode=["fail_only"]),
    "sub2": dict(shock=[(0.3, 0.3)], q0=[0.10], theta_on=[0.0, -0.01, -0.0175], iota=[0.0, -0.01, -0.0175],
                 inv=["3"], mode=["fail_only"]),
    "null0": dict(shock=[(0.0, 0.0)], q0=[0.06, 0.10, 0.20], theta_on=[0.0], iota=[0.0], inv=["3", "10"],
                  mode=["fail_only"]),
    "modes": dict(shock=[(0.3, 0.3)], q0=[0.10], theta_on=[0.0, -0.02, -0.05], iota=[0.0, -0.02, -0.05],
                  inv=["3", "harm"], mode=["fail_only", "opposing"]),
}


def run_grid(name, reps, flips, extra, out, panels=20):
    g = GRIDS[name]
    rows = []
    t0 = time.time()
    combos = list(itertools.product(g["shock"], g["q0"], g["theta_on"], g["iota"], g["inv"], g["mode"]))
    for k, (sh, q0, th, io, inv, mode) in enumerate(combos):
        sc = dict(sd_common=sh[0], sd_own=sh[1], q0=q0, theta_on=th, iota=io, inv=inv, mode=mode, **extra)
        rows.append(simulate(sc, reps, flips, seed=SEED + k, panels=panels))
        if (k + 1) % 10 == 0 or k + 1 == len(combos):
            print(f"{k + 1}/{len(combos)} scenarios, {time.time() - t0:.0f} s", flush=True)
            out.write_text(json.dumps({"grid": name, "rows": rows}, indent=1))
    out.write_text(json.dumps({"grid": name, "rows": rows}, indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--grid", default="smoke")
    ap.add_argument("--reps", type=int, default=400)
    ap.add_argument("--flips", type=int, default=999)
    ap.add_argument("--side", default="harm")
    ap.add_argument("--n-api", type=int, default=60)
    ap.add_argument("--n-local", type=int, default=60)
    ap.add_argument("--beta-blind", type=float, default=0.0)
    ap.add_argument("--out", default="power_sim_v23_smoke.json")
    ap.add_argument("--panels", type=int, default=20)
    ap.add_argument("--yoke", default="access", choices=["access", "type"])
    ap.add_argument("--alts", action="store_true",
                    help="also test the open-model sub-panel and the screen-restricted estimands on the same data")
    ap.add_argument("--screen-se", type=float, default=1.0, help="P(screen marks a non-refusal | failure)")
    ap.add_argument("--screen-sp", type=float, default=1.0, help="P(screen marks a refusal | no failure)")
    ap.add_argument("--panel", default="all", choices=["all", "harm11", "mixed"],
                    help="harm11 = the ten local models and the refusal-removed API model, all on the local frame")
    ap.add_argument("--sus", type=float, default=0.0,
                    help="in-context logit shift of refusal-removed judges on harmful answers, own and control alike")
    ap.add_argument("--se-removed", type=float, default=0.0,
                    help="logit shift of the sensitivity of the refusal-removed judges")
    ap.add_argument("--structural", action="store_true",
                    help="no self-specific effect: the control arm receives the author arm's shift (iota is ignored)")
    a = ap.parse_args()
    OUT_DIR.mkdir(exist_ok=True)
    run_grid(a.grid, a.reps, a.flips, dict(side=a.side, n_api=a.n_api, n_local=a.n_local, beta_blind=a.beta_blind,
                                             yoke=a.yoke, sus=a.sus, structural=a.structural,
                                             se_removed=a.se_removed, panel=a.panel, alts=a.alts,
                                             screen_se=a.screen_se, screen_sp=a.screen_sp),
             OUT_DIR / a.out, panels=a.panels)
