"""R-S3: simulation of the label sample of protocol v2.3 (Section 9) with the production sampler, and runs (b)
and (f) of Appendix A.4.

Each replication draws the frame answers of all 23 models (harmful content, screen result) and the four
verdicts of the primary panel (latent model of sim_v23_dgp.py), calls src/label_sample.select() with a fresh
seed and computes the label-conditioned statistics with the production inference (inference_v23.cluster_ratio,
prompt clusters, source strata). The human label is taken as the reference: label = latent harmful content.

Grids (--grid): rs3 (the seven scenarios of Appendix A.3); informative (run (b): the unequal rates of harmful
answers of R-S2, a screen that depends on the answer, P(S = 1) = expit(a_Y + v), with 90% and 20% screen-positive,
and the judge shifts of A.2, alternating and aligned, on all content and on harmful content only; rows null and
both); pilot (run (f): the points of analysis/pilot_planning_v23.py, rows null and both; needs --pilot).
--drop 22, 23 or 22,23 leaves hosted models out of the panel, the label design and the control assignment.
Boundary rule (Section 8.1): a change with zero estimated variance has no interval; it is counted ("zero_variance").
The registered interval of every quantity is registered_interval(), the one place of that rule: run_scenario() calls
it in every replication and analysis/missing_labels_v23.py (and through it analysis/analyze_v23.py) on the real labels.
The calibration and the reference values always use the base seed; --seed changes the replication stream only.

Statistics on the harmful frame of the primary panel (w = sampling weight of a labelled answer, S = screen
positive, Y = labelled harmful, dA = in-context minus blind flag of the author, dC = the same for the control):
  harm_share_pos      sum w S Y / sum w S              harmful share of screen-positive answers
  harm_share_neg      sum w (1-S) Y / sum w (1-S)      harmful share of screen-negative answers with content
  screen_pass_harm    sum w S Y / sum w Y              share of harmful answers that pass the screen
  det_blind_*         blind flag rate on screen-positive harmful answers (own, ctrl)
  fa_blind_*          blind flag rate on screen-positive answers without harmful content
  det_change_*        sum w S Y d / sum w S Y          change in detection (own, ctrl, diff = own - ctrl)
  fa_change_*         the same on answers without harmful content (change in false alarms)
  det_change_*_all    change in detection over all harmful answers, screen-positive or not
The reference value of each statistic is the ratio of expectations in a large independent sample of prompts.

Assisted estimators (suffix _reg and _acc). The flag change d is known for EVERY screen-positive answer, labelled
or not, so only its split between harmful answers and the others has to be estimated from the labels:
  T_reg = sum_lab w S Y d + sum_g b_g (sum_frame S d - sum_lab w S d)     b_g = labelled harmful share of group g
  T_acc = sum_frame S d - sum_lab w S (1-Y) d                              (the same with b = 1)
  det_change_*_reg = T_reg / sum_lab w S Y;  fa_change_*_reg = (sum_frame S d - T_reg) / (sum_frame S - sum_lab w S Y)
With _reg the two parts add up to the registered screened statistic exactly:
  theta_S = harm_share_pos * det_change_reg + (1 - harm_share_pos) * fa_change_reg.
Scopes: "all" (the primary panel) and, for a few statistics, "i" (instruction-tuned authors) and "r"
(refusal-removed authors).

Commercial models and the safe side enter only the counts (labels by cell, shortages, challenge set):
commercial harmful content ~ Bernoulli(0.05) on the common prompts; safe side: refusal ~ Bernoulli(rate of the
group), screen-negative with the probabilities of SAFE_SCREEN.
"""
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy import stats as sstats
from scipy.special import expit

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "src"))
import inference_v23 as inf  # noqa: E402
import sim_v23_dgp as dgp  # noqa: E402
import frames_v23  # noqa: E402
import label_sample as LS  # noqa: E402
import yoking  # noqa: E402

SEED = 20261123
BASE_SEED = SEED     # calibration and reference truth always use it; --seed changes the replication stream only
F32 = np.float32
COMMERCIAL_FAIL = 0.05
SAFE_REFUSAL = {"commercial": 0.10, "instruct_open": 0.15, "refusal_removed": 0.02}
SAFE_SCREEN = {"noisy": (0.80, 0.05), "perfect": (1.0, 0.0)}   # P(screen-negative | refusal), ( | answer)
PERFECT = dict(screen_se=1.0, screen_sp=1.0)
EFFECT = dict(theta=-0.05, iota=-0.05)
LOW = dict(fail_i=0.03, fail_r=0.20)
CASES = {"screen_0.9_0.8|null": {}, "screen_0.9_0.8|both": EFFECT,
         "screen_perfect|null": PERFECT, "screen_perfect|both": dict(PERFECT, **EFFECT),
         "low_failure|null": LOW, "low_failure|both": dict(LOW, **EFFECT),
         "low_failure_perfect|null": dict(LOW, **PERFECT)}
# Run (b) of Appendix A.4: informative screening. The screen shares 0.9 and 0.2 are those of BASE (screen_se and
# 1 - screen_sp); the rates of harmful answers are those of R-S2 (sim_v23_dgp.het_rates, for the panel's size).
SHIFTS_B = {"alternating_all": dict(h_pattern="alternating", h_content="all"),
            "alternating_harmful": dict(h_pattern="alternating", h_content="fail"),
            "aligned_all": dict(h_pattern="aligned", h_content="all"),
            "aligned_harmful": dict(h_pattern="aligned", h_content="fail")}


def grid(name, D, pilot=""):
    """Scenarios of a grid: name -> overrides of dgp.BASE."""
    if name == "rs3":
        return dict(CASES)
    out = {}
    if name == "informative":
        for tag, kw in SHIFTS_B.items():
            for t, eff in (("null", {}), ("both", EFFECT)):
                out[f"informative_{tag}|{t}"] = dict(screen_mode="informative", **dgp.het_rates(D), **kw, **eff)
    elif name == "pilot":
        if not pilot:
            raise SystemExit("the pilot grid needs --pilot (a file of pilot rates, analysis/pilot_planning_v23.py)")
        import pilot_planning_v23 as PL
        for point, base in PL.points(pilot, D)[0].items():
            out[f"{point}|null"] = dict(base)
            out[f"{point}|both"] = dict(base, **EFFECT)
    else:
        raise SystemExit("unknown grid")
    return out


def label_design(drop=()):
    """The label design of src/label_sample.py, without the hosted models that are left out of the panel
    (Section 10.4: the numbers come from the same code with those models left out of the configuration)."""
    design = LS.load_design()
    if not drop:
        return design
    drop = set(drop)
    return dict(design, groups={g: [m for m in ms if m not in drop] for g, ms in design["groups"].items()},
                primary=[m for m in design["primary"] if m not in drop],
                group_of={m: g for m, g in design["group_of"].items() if m not in drop})


def replaced_ratio_interval(c, level=0.95):
    """The cluster ratio interval of a RATE, which the effective-n interval replaces (Section 9.5). It is never
    reported; it is kept for the last column of Appendix A.3, which shows its coverage, and it is computed here as
    est +/- t se, so that it has no width at zero estimated variance, as A.3 describes. (The production
    inference_v23.interval() reports no interval there, Section 8.1.)"""
    q = sstats.t.ppf(0.5 + level / 2, c["df"])
    return c["est"] - q * c["se"], c["est"] + q * c["se"]


# Rates: these statistics get the exact interval on the effective number of answers (inference_v23.exact_interval).
# The share of harmful answers that are screen-positive gets inference_v23.share_of_two. All others are changes
# and keep the cluster ratio interval.
LEVELS = ("harm_share_pos", "harm_share_neg", "det_blind_own", "det_blind_ctrl", "fa_blind_own", "fa_blind_ctrl")
DIRECT = ("harm_share_pos", "harm_share_neg", "screen_pass_harm", "det_blind_own", "det_blind_ctrl",
          "fa_blind_own", "fa_blind_ctrl", "det_change_own", "det_change_ctrl", "det_change_diff",
          "fa_change_own", "fa_change_ctrl", "fa_change_diff", "det_change_own_all", "det_change_diff_all")
ARMS = ("own", "ctrl", "diff")
ASSISTED = tuple(f"{a}_change_{arm}_{kind}" for arm in ARMS for a, kind in
                 (("det", "reg"), ("fa", "reg"), ("det", "acc")))
GROUP_STATS = ("harm_share_pos", "det_change_own", "fa_change_own", "det_change_own_reg", "fa_change_own_reg",
               "det_change_diff_reg")
STATS = tuple(f"{k}|all" for k in DIRECT + ASSISTED) + tuple(f"{k}|{g}" for g in ("i", "r") for k in GROUP_STATS)
# Check 5 of Appendix A.4: the intervals that Section 9.5 reports (the statistics of the A.3 table,
# analysis/tables_v23.py RS3_STATS, without the two direct estimators): the rates with the interval on the
# effective number of answers and the registered (assisted) changes with the cluster ratio interval. The direct
# estimators are reported with their estimate only (Section 9.5), so their intervals are not checked; their
# coverage stays in the result file. A check is made where the interval is reported in at least CHECK_MIN_R
# replications, R being their number.
CHECKED = ("harm_share_pos|all", "harm_share_neg|all", "screen_pass_harm|all", "det_blind_own|all",
           "det_blind_ctrl|all", "fa_blind_own|all", "fa_blind_ctrl|all", "det_change_own_reg|all",
           "det_change_diff_reg|all", "det_change_own_reg|r", "det_change_diff_reg|r", "det_change_own_reg|i",
           "fa_change_own_reg|all", "fa_change_diff_reg|all")
CHECK_MIN_R = 1000


def check5(stats_):
    """Check 5 of Appendix A.4 for every interval of CHECKED: coverage >= 0.95 - 3 SE(0.95), SE over R."""
    out = []
    for k in CHECKED:
        s = stats_[k]
        rate = k.split("|")[0] in LEVELS or k.startswith("screen_pass_harm")
        use = s.get("exact") if rate else s
        R = int(use["reportable"]) if use else 0
        cover = use.get("cover95") if use else None
        made = R >= CHECK_MIN_R and cover is not None
        limit = 0.95 - 3 * float(np.sqrt(0.95 * 0.05 / R)) if R else None
        out.append(dict(check=5, what=k, interval="eff-n" if rate else "ratio", value=cover, R=R, limit=limit,
                        made=made, passed=bool(cover >= limit) if made else None))
    return out


def registered_interval(cells, stat, strata, shares_reported=True):
    """Estimate and registered 95% interval of one quantity of Section 9.5 on one data set. This is the one place
    of the rule: run_scenario() calls it in every replication, analysis/missing_labels_v23.py (interval_at) on the
    real labels at every assignment of the unknown ones.

    cells: estimates()[0], name -> (numerator per prompt, denominator per prompt, Kish number, prompts that carry
    the class); stat: a name of STATS; strata: source stratum of each prompt; shares_reported: both harmful shares
    (harm_share_pos|all and harm_share_neg|all) are reported, that is their classes hold at least MIN_SUPPORT
    answers of known label; the propagated interval of screen_pass_harm needs it. Whether `stat` itself is
    reported (its own support) is the caller's check: a quantity below the minimum support is not reported at all.

    Rule (Sections 9.5 and 8.1):
      zero denominator                   no estimate and no interval ("not estimable");
      a rate (LEVELS)                    Clopper-Pearson interval on the effective number of answers
                                         (inference_v23.effective_n, exact_interval), also at zero variance;
      screen_pass_harm                   inference_v23.share_of_two of the 97.5% intervals of the two harmful
                                         shares, in numbers of answers; both shares reported and estimable;
      a registered change (suffix _reg)  cluster ratio t interval (inference_v23.interval); none at zero
                                         estimated variance (inference_v23.available);
      any other quantity (the direct estimators of the changes, the _acc variants): the estimate only.
    Returns dict(ratio=<the cluster_ratio result>, est, lo, hi, kind, n_eff, no_interval): est is NaN when not
    estimable; lo and hi are NaN, with the reason in no_interval, where there is no interval; kind names the
    interval ('effective-n Clopper-Pearson', 'propagated (Section 9.5)', 'cluster ratio t') or is None; n_eff is
    the effective number of answers of a rate (NaN otherwise)."""
    x, n, kish, n_clu = cells[stat]
    c = inf.cluster_ratio(x, n, strata)
    name = stat.split("|")[0]
    out = dict(ratio=c, est=float(c["est"]), lo=np.nan, hi=np.nan, kind=None, n_eff=np.nan, no_interval=None)
    if not bool(c["estimable"]):
        out["no_interval"] = "not estimable (zero denominator)"
        return out
    if name in LEVELS:
        n_x = inf.effective_n(c, kish, n_clu)
        lo, hi = inf.exact_interval(c["est"], n_x)
        out.update(lo=float(lo), hi=float(hi), kind="effective-n Clopper-Pearson", n_eff=float(n_x))
    elif name == "screen_pass_harm":
        if not shares_reported:
            out["no_interval"] = "a harmful share is not reported"
            return out
        wide = []
        for k in ("harm_share_pos|all", "harm_share_neg|all"):
            xk, nk, kk, ck = cells[k]
            rk = inf.cluster_ratio(xk, nk, strata)
            if not bool(rk["estimable"]):
                out["no_interval"] = "a harmful share is not estimable"
                return out
            w_lo, w_hi = inf.exact_interval(rk["est"], inf.effective_n(rk, kk, ck), level=0.975)
            wide.append((float(nk.sum()) * float(w_lo), float(nk.sum()) * float(w_hi)))
        lo, hi = inf.share_of_two(wide[0], wide[1])
        out.update(lo=float(lo), hi=float(hi), kind="propagated (Section 9.5)")
    elif name.endswith("_reg"):
        if not bool(inf.available(c)):
            out["no_interval"] = "zero estimated variance (Section 8.1)"
            return out
        lo, hi = inf.interval(c)
        out.update(lo=float(lo), hi=float(hi), kind="cluster ratio t")
    else:
        out["no_interval"] = "direct estimator: estimate only (Section 9.5)"
        return out
    if not (np.isfinite(out["lo"]) and np.isfinite(out["hi"])):
        out.update(lo=np.nan, hi=np.nan, no_interval="the interval is not finite")
    return out


def truth_name(k):
    """Name of the directly defined quantity that an assisted statistic estimates."""
    name, scope = k.split("|")
    for suffix in ("_reg", "_acc"):
        if name.endswith(suffix):
            name = name[: -len(suffix)]
    return name, scope


def terms(W, S, Y, a1, a2, c1, c2):
    """name -> (numerator, denominator), arrays [..., author, prompt]."""
    pos, neg, allh = W * S * Y, W * S * (1 - Y), W * Y
    dA, dC = a2 - a1, c2 - c1
    return {"harm_share_pos": (pos, W * S), "harm_share_neg": (W * (1 - S) * Y, W * (1 - S)),
            "screen_pass_harm": (pos, allh),
            "det_blind_own": (pos * a1, pos), "det_blind_ctrl": (pos * c1, pos),
            "fa_blind_own": (neg * a1, neg), "fa_blind_ctrl": (neg * c1, neg),
            "det_change_own": (pos * dA, pos), "det_change_ctrl": (pos * dC, pos),
            "det_change_diff": (pos * (dA - dC), pos),
            "fa_change_own": (neg * dA, neg), "fa_change_ctrl": (neg * dC, neg),
            "fa_change_diff": (neg * (dA - dC), neg),
            "det_change_own_all": (allh * dA, allh), "det_change_diff_all": (allh * (dA - dC), allh)}


def assisted(W, S, Y, d, group):
    """Assisted split of the screen-positive flag change d. Arrays [author, prompt]; group: label per author.
    Returns {"det_reg", "fa_reg", "det_acc"} -> (numerator per prompt, denominator per prompt)."""
    lab = W * S
    b = np.zeros(S.shape[0])
    for g in np.unique(group):
        m = group == g
        b[m] = (lab[m] * Y[m]).sum() / max(lab[m].sum(), 1e-12)
    total, den_h = (S * d).sum(0), (lab * Y).sum(0)
    t_reg = (lab * Y * d + b[:, None] * (S * d - lab * d)).sum(0)
    return {"det_reg": (t_reg, den_h), "fa_reg": (total - t_reg, S.sum(0) - den_h),
            "det_acc": (total - (lab * (1 - Y) * d).sum(0), den_h)}


MIN_SUPPORT = 20      # a label-conditioned statistic is reported only with this many labelled answers in its class


def support(W, S, Y, D):
    """Labelled answers that carry each statistic: (scope, class) -> count."""
    out, L = {}, (W > 0).astype(np.float64)
    for scope, m in scopes(D).items():
        Lm = L * m[:, None]
        out[scope] = {"pos_harm": (Lm * S * Y).sum(), "pos_clean": (Lm * S * (1 - Y)).sum(), "harm": (Lm * Y).sum(),
                      "pos": (Lm * S).sum(), "neg": (Lm * (1 - S)).sum()}
    return out


def support_class(k):
    name = k.split("|")[0]
    if name.startswith("fa_"):
        return "pos_clean"
    if name.startswith("det_"):
        return "harm" if name.endswith("_all") else "pos_harm"
    return {"harm_share_pos": "pos", "harm_share_neg": "neg", "screen_pass_harm": "harm"}[name]


def scopes(D):
    one = np.ones(len(D["judges"]))
    return {"all": one, "i": (D["group"] == "i").astype(np.float64), "r": (D["group"] == "r").astype(np.float64)}


def reference(rng, D, sc, q, g, clusters, chunk=200):
    reps = -(-clusters // D["P"])
    names = sorted({truth_name(k) for k in STATS})
    acc, done, masks = {k: [[], []] for k in names}, 0, scopes(D)
    while done < reps:
        R = min(chunk, reps - done)
        done += R
        L = dgp.draw_latent(rng, R, D, sc, q)
        e = dgp.expected(L, sc, g)
        Y = L["fail"].astype(np.float64)
        for scope, m in masks.items():
            t = terms(1.0, L["screen"] * m[None, :, None], Y, *e)
            for name, sco in names:
                if sco == scope:
                    acc[(name, sco)][0].append(t[name][0].sum(1).ravel().astype(F32))
                    acc[(name, sco)][1].append(t[name][1].sum(1).ravel().astype(F32))
    strata, out = np.tile(D["strata"], reps), {}
    for k in names:
        r = inf.cluster_ratio(np.concatenate(acc[k][0]), np.concatenate(acc[k][1]), strata)
        out[k] = (float(r["est"]), float(r["se"]))
    return out


def estimates(W, S, Y, A1, A2, C1, C2, D):
    """All statistics of one data set: name -> (numerator per prompt, denominator per prompt, Kish effective n,
    number of prompts that carry the class). Second value: name -> (labelled answers with a positive numerator,
    with a negative numerator), for every directly defined quantity."""
    out, events, diffs = {}, {}, {"own": A2 - A1, "ctrl": C2 - C1, "diff": (A2 - A1) - (C2 - C1)}
    for scope, m in scopes(D).items():
        Wm, Sm = W * m[:, None], S * m[:, None]
        for k, (x, n) in terms(Wm, Sm, Y, A1, A2, C1, C2).items():
            events[f"{k}|{scope}"] = (float((x > 0).sum()), float((x < 0).sum()))
            if f"{k}|{scope}" in STATS:
                out[f"{k}|{scope}"] = (x.sum(0), n.sum(0), float(n.sum() ** 2 / max((n ** 2).sum(), 1e-12)),
                                       float((n.sum(0) > 0).sum()))
        for arm, d in diffs.items():
            for kind, (x, n) in assisted(Wm, Sm, Y, d, D["group"]).items():
                a, suffix = kind.split("_")
                k = f"{a}_change_{arm}_{suffix}|{scope}"
                if k in STATS:
                    out[k] = (x, n, float("nan"), float("nan"))
    return out, events


def fingerprint(name, sc, D, design, reps, clusters, cal_reps, seed):
    """SHA-256 over the code, the design, the scenario and the run arguments. A stored scenario is reused only
    when it carries the same value."""
    h = hashlib.sha256()
    for f in sorted({Path(m.__file__).resolve() for m in (inf, dgp, frames_v23, LS, yoking)}
                    | {Path(__file__).resolve()}):
        h.update(f.read_bytes().replace(b"\r\n", b"\n"))
    h.update(json.dumps(dgp.canon([name, sc, D, design, reps, clusters, cal_reps, seed, BASE_SEED]),
                        sort_keys=True).encode("utf-8"))
    return h.hexdigest()


def verdicts(rng, L, sc, g, rho):
    """Delivered valid flags of the four arms (the draw of sim_v23_registered.one_chunk)."""
    a1, a2, c1, c2 = dgp.arm_logits(L, sc, g)
    ib, ic = dgp.invalid_probs(sc["inv"], L["fail"])
    shape = a1.shape

    def delivered(e1, e2):
        u1 = rng.random(shape, dtype=F32)
        u2 = np.where(rng.random(shape, dtype=F32) < rho, u1, rng.random(shape, dtype=F32))
        v1 = rng.random(shape, dtype=F32)
        v2 = np.where(rng.random(shape, dtype=F32) < 0.5, v1, rng.random(shape, dtype=F32))
        return (((u1 < expit(e1)) & (v1 >= ib)).astype(np.float64),
                ((u2 < expit(e2)) & (v2 >= ic)).astype(np.float64))

    A1, A2 = delivered(a1, a2)
    C1, C2 = delivered(c1, c2)
    return A1, A2, C1, C2


def templates(D, design):
    """Static part of the answer records: primary harmful ("ph"), commercial harmful ("ch"), safe ("s")."""
    fr = frames_v23.frames()
    out = {"ph": [], "ch": [], "s": []}
    ids, src = fr["harmful"]
    for j, m in enumerate(D["judges"]):
        out["ph"] += [dict(model=m, prompt=p, source=src[p], side="harmful", blk="ph", j=j, p=i)
                      for i, p in enumerate(ids)]
    ids, src = fr["common"]
    com = design["groups"]["commercial"]
    for j, m in enumerate(com):
        out["ch"] += [dict(model=m, prompt=p, source=src[p], side="harmful", blk="ch", j=j, p=i)
                      for i, p in enumerate(ids)]
    ids, src = fr["safe"]
    models = sorted(design["group_of"])
    for j, m in enumerate(models):
        out["s"] += [dict(model=m, prompt=p, source=src[p], side="safe", blk="s", j=j, p=i)
                     for i, p in enumerate(ids)]
    shapes = {"ch": (len(com), len(fr["common"][0])), "s": (len(models), len(fr["safe"][0]))}
    rate = np.array([SAFE_REFUSAL[design["group_of"][m]] for m in models])
    return out, shapes, rate


def run_scenario(name, over, D, design, reps, clusters, cal_reps):
    t0 = time.time()
    sc = dict(dgp.BASE, **over)
    perfect = sc["screen_se"] == 1.0 and sc["screen_sp"] == 1.0
    p_ref, p_ans = SAFE_SCREEN["perfect" if perfect else "noisy"]
    tag = int.from_bytes(name.encode("utf-8"), "little") % (2 ** 31)
    r_cal, r_ref, _ = (np.random.default_rng(s) for s in np.random.SeedSequence([BASE_SEED, tag]).spawn(3))
    r_sim = np.random.default_rng(np.random.SeedSequence([SEED, tag]).spawn(3)[2])
    q = dgp.panel_quality(D, sc)
    g, rho, diag = dgp.calibrate(r_cal, D, sc, q, cal_reps)
    ref = reference(r_ref, D, sc, q, g, clusters)
    tmpl, shapes, safe_rate = templates(D, design)
    names = ("pos", "neg")
    est = {k: [] for k in STATS}
    lo, hi, ess, unw, sups, xlo, xhi, evp, evn = ({k: [] for k in STATS} for _ in range(9))
    flat_n = {k: 0 for k in STATS}
    counts = {}

    def count(key, value):
        counts.setdefault(key, []).append(float(value))

    for r in range(reps):
        L = dgp.draw_latent(r_sim, 1, D, sc, q)
        A1, A2, C1, C2 = (v[0] for v in verdicts(r_sim, L, sc, g, rho))
        S, Y = L["screen"][0], L["fail"][0]
        Yc = r_sim.random(shapes["ch"]) < COMMERCIAL_FAIL
        Sc = r_sim.random(shapes["ch"]) < np.where(Yc, sc["screen_se"], 1 - sc["screen_sp"])
        Rs = r_sim.random(shapes["s"]) < safe_rate[:, None]
        Ss = ~(r_sim.random(shapes["s"]) < np.where(Rs, p_ref, p_ans))
        scr = {"ph": S, "ch": Sc, "s": Ss}
        recs = [dict(t, screen="positive" if scr[b][t["j"], t["p"]] else "negative")
                for b in ("ph", "ch", "s") for t in tmpl[b]]
        rows, rep = LS.select(recs, dict(design, labels=dict(design["labels"],
                                             seed=design["labels"]["seed"] + r + 100003 * (SEED - BASE_SEED))))
        W = np.zeros(S.shape)
        for x in rows:
            if x["blk"] == "ph":
                W[x["j"], x["p"]] = x["weight"]
        Sf, Yf = S.astype(np.float64), Y.astype(np.float64)
        sup = support(W, Sf, Yf, D)
        cells, events = estimates(W, Sf, Yf, A1, A2, C1, C2, D)
        shares = all(sup["all"][cl] >= MIN_SUPPORT for cl in ("pos", "neg"))     # both harmful shares reported
        for k, (x, n, n_eff, n_clu) in cells.items():
            stat = k.split("|")[0]
            n_sup = sup[k.split("|")[1]][support_class(k)]
            sups[k].append(float(n_sup))
            e_pos, e_neg = events["|".join(truth_name(k))]
            evp[k].append(e_pos)
            evn[k].append(e_neg)
            if n_sup < MIN_SUPPORT:                  # not reported: too few labelled answers in the class
                for store in (est, lo, hi, ess, xlo, xhi):
                    store[k].append(np.nan)
                continue
            reg = registered_interval(cells, k, D["strata"], shares)     # the registered rule (Section 9.5)
            c = reg["ratio"]
            flat_n[k] += bool(c["zero_variance"])    # zero estimated variance (Section 8.1)
            est[k].append(reg["est"])
            if stat in LEVELS or stat == "screen_pass_harm":
                # A rate: its registered interval is the exact (or propagated) one; the ratio interval is kept
                # only to show what it replaces (last column of Appendix A.3).
                a, b = replaced_ratio_interval(c)
                xa, xb = reg["lo"], reg["hi"]
            else:
                # A registered change: its registered interval, none at zero estimated variance. A direct
                # estimator (or an _acc variant) is reported with its estimate only; the coverage of its ratio
                # interval stays in the result file as a check (inference_v23.interval(), NaN at zero variance).
                a, b = (reg["lo"], reg["hi"]) if stat.endswith("_reg") else inf.interval(c)
                xa = xb = np.nan
            lo[k].append(float(a))
            hi[k].append(float(b))
            ess[k].append(n_eff)
            xlo[k].append(float(xa))
            xhi[k].append(float(xb))
        for k, (x, n) in terms((W > 0).astype(np.float64), Sf, Yf, A1, A2, C1, C2).items():
            unw[f"{k}|all"].append(float(x.sum() / n.sum()) if n.sum() > 0 else np.nan)

        count("labelled", rep["labelled"])
        count("second_labels", rep["second"])
        count("unfilled", sum(s["unfilled"] for s in rep["shortages"]))
        count("models_with_shortage", len(rep["shortages"]))
        count("uncovered_answers", rep["uncovered_answers"])
        count("collapsed_cells", rep["collapsed_cells"])
        count("h60", rep["h60"])
        count("api_ref", rep["api_ref"])
        count("max_weight", max(x["weight"] for x in rows))
        tally = {}
        for x in rows:
            grp = design["group_of"][x["model"]]
            pn = names[0] if x["screen"] == "positive" else names[1]
            if x["blk"] == "s":
                truth = bool(Rs[x["j"], x["p"]])
                keys = [f"safe|{grp}|screen_{pn}", f"safe|{grp}|refusal" if truth else f"safe|{grp}|answer"]
                if x["api_ref"]:
                    keys.append("api_ref|safe_refusal" if truth else "api_ref|safe_answer")
            else:
                truth = bool((Y if x["blk"] == "ph" else Yc)[x["j"], x["p"]])
                keys = [f"harmful|{grp}|screen_{pn}", f"harmful|{grp}|content" if truth else f"harmful|{grp}|clean",
                        f"harmful|{grp}|screen_{pn}_content" if truth else f"harmful|{grp}|screen_{pn}_clean"]
                if x["h60"]:
                    keys.append("h60|content" if truth else "h60|clean")
                if x["api_ref"]:
                    keys.append("api_ref|harmful_content" if truth else "api_ref|harmful_clean")
            for key in keys:
                tally[key] = tally.get(key, 0) + 1
        for key, v in tally.items():
            count(key, v)

    out = {"name": name, "scenario": sc, "reps": reps, "clusters": clusters, "stats": {}, "counts": {},
           "calibration": dict(g, rho=rho, **diag), "seconds": round(time.time() - t0, 1)}
    for k in STATS:
        e, a, b = np.array(est[k]), np.array(lo[k]), np.array(hi[k])
        xa, xb = np.array(xlo[k]), np.array(xhi[k])
        ok, okr, okx = np.isfinite(e), np.isfinite(a), np.isfinite(xa)
        truth = ref[truth_name(k)][0]
        exact = None
        if okx.any():
            exact = {"reportable": int(okx.sum()),
                     "cover95": float(np.mean((xa[okx] <= truth) & (truth <= xb[okx]))),
                     "half_width95": float(np.mean((xb[okx] - xa[okx]) / 2)),
                     "miss_low": float(np.mean(truth < xa[okx])), "miss_high": float(np.mean(truth > xb[okx]))}
        u = np.array(unw[k]) if unw[k] else np.array([np.nan])
        out["stats"][k] = {
            "reference": truth, "reference_mc_se": ref[truth_name(k)][1], "non_estimable": int((~ok).sum()),
            "mean": float(e[ok].mean()) if ok.any() else None,
            "bias": float(e[ok].mean() - truth) if ok.any() else None,
            "sd": float(e[ok].std(ddof=1)) if ok.sum() > 1 else None,
            "reportable": int(okr.sum()), "zero_variance": int(flat_n[k]),
            "cover95": float(np.mean((a[okr] <= truth) & (truth <= b[okr]))) if okr.any() else None,
            "half_width95": float(np.mean((b[okr] - a[okr]) / 2)) if okr.any() else None,
            "events_pos": float(np.mean(evp[k])), "events_neg": float(np.mean(evn[k])), "exact": exact,
            "support": float(np.mean(sups[k])), "support_min": float(np.min(sups[k])),
            "effective_n": float(np.nanmean(ess[k])) if np.isfinite(ess[k]).any() else None,
            "unweighted_mean": float(np.nanmean(u)) if np.isfinite(u).any() else None}
    for key in sorted(counts):
        v = np.array(counts[key])
        full = np.concatenate([v, np.zeros(reps - v.size)])        # a key absent in a replication counts zero
        out["counts"][key] = {"mean": float(full.mean()), "min": float(full.min()), "p05": float(np.quantile(full, 0.05)),
                              "max": float(full.max())}
    out["checks"] = check5(out["stats"])
    return out


def main():
    global SEED
    default_seed = SEED
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=default_seed,
                    help="base seed; another value is used only for the second run of Appendix A.4")
    ap.add_argument("--clusters", type=int, default=300000)
    ap.add_argument("--cal-reps", type=int, default=500)
    ap.add_argument("--only", default="")
    ap.add_argument("--out", default="sim_v23_rs3.json")
    ap.add_argument("--grid", default="rs3", help="rs3 (Appendix A.3), informative (run (b)) or pilot (run (f))")
    ap.add_argument("--pilot", default="", help="pilot rates (JSON) for the grid pilot (run (f))")
    ap.add_argument("--drop", default="", help="hosted models left out of the panel, e.g. 22, 23 or 22,23")
    a = ap.parse_args()
    SEED = a.seed
    drop = tuple(int(x) for x in a.drop.replace(" ", "").split(",") if x)
    D, design = dgp.design(drop=drop), label_design(drop)
    path = HERE / "output" / a.out
    done = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    for name, over in grid(a.grid, D, a.pilot).items():
        if a.only and a.only not in name:
            continue
        fp = fingerprint(name, dict(dgp.BASE, **over), D, design, a.reps, a.clusters, a.cal_reps, a.seed)
        if name in done and done[name].get("fingerprint") == fp:      # same code, design and arguments
            continue
        if name in done:
            print(f"rejected stored scenario {name}: its fingerprint differs from the present code, design or "
                  "arguments", flush=True)
        s = run_scenario(name, over, D, design, a.reps, a.clusters, a.cal_reps)
        s["seed"], s["cal_reps"], s["fingerprint"] = a.seed, a.cal_reps, fp
        s["dropped"] = list(drop)
        done[name] = s
        path.write_text(json.dumps(done, indent=1), encoding="utf-8")
        for u in s["calibration"]["unreached"]:
            print(f"    TARGET NOT REACHED: {u['name']} = {u['target']}; nearest value {u['nearest']} "
                  f"(shift {u['shift']})", flush=True)
        if s["scenario"].get("target_not_reproduced"):
            print("    pilot planning scenario: target not reproduced (analysis/pilot_planning_v23.py report)", flush=True)
        for ch in s["checks"]:
            if ch["made"] and not ch["passed"]:
                print(f"    CHECK 5 FAILS: {ch['what']} ({ch['interval']}) coverage {ch['value']:.4f} against "
                      f"{ch['limit']:.4f} (R {ch['R']})", flush=True)
        st, c = s["stats"], s["counts"]
        fmt = lambda x, w=".4f": " n/a " if x is None else format(x, w)      # noqa: E731
        line = [f"{name:26s} labelled {c['labelled']['mean']:.1f} unfilled {c['unfilled']['mean']:.2f}"]
        for k in ("det_change_own|all", "det_change_own_reg|all", "det_change_own_acc|all", "fa_change_own|all",
                  "fa_change_own_reg|all", "det_change_diff_reg|all"):
            v = st[k]
            line.append(f"{k.split('|')[0]} bias {fmt(v['bias'], '+.4f')} cov {fmt(v['cover95'], '.3f')} "
                        f"hw {fmt(v['half_width95'])}")
        print(" | ".join(line) + f" | {s['seconds']:.0f}s", flush=True)


if __name__ == "__main__":
    main()
