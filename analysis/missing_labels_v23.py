"""Registered missing-label analysis of protocol v2.3 (Section 9.3) for the quantities of Section 9.5.

Quantities, estimators and intervals are those of analysis/sim_v23_labels.py, reused here, not redefined:
  - terms(), assisted() and estimates(): per-prompt numerator and denominator of every quantity, the registered
    label-assisted estimator of the two changes included;
  - support(), support_class() and MIN_SUPPORT: a quantity is reported only with at least 20 answers of known
    label in its class; an unknown label counts for no class (Section 9.5);
  - registered_interval(): the interval of each quantity, the function that run_scenario() calls in every
    replication: rates (LEVELS) get the Clopper-Pearson interval on the effective number of answers, the share of
    harmful answers that are screen-positive the propagated interval (inference_v23.share_of_two, both shares
    reported), the registered changes (suffix _reg) the cluster ratio t interval, with no interval at zero
    estimated variance (Section 8.1); the direct estimators of the changes are reported as a check, with their
    estimate and no interval (Section 9.5).
interval_at() below calls registered_interval(); the rule is not repeated here. Appendix A.4 withdraws an interval
that fails check 5 in both of its runs: NO_INTERVAL names it, interval_at() gives its estimate without an interval,
and it gates no detection statement. sim_v23_labels.py stays as it was run, so the stored simulations keep their
fingerprints and the coverage of that interval stays in them.

Unknown labels (Section 9.3). An answer of the label sample is 'labelled', 'labelled_once' or 'unknown' at the
lock (scripts/label_join_v23.py). For every quantity:
  1. explicit assignments: every unknown label 'harmful', then every unknown label 'not harmful', each with its
     estimate and 95% interval;
  2. identification range: the smallest and the largest estimate over all assignments of the unknown labels, with
     the 95% interval at each of these two assignments;
  3. sensitivity: steps 1 and 2 with the answers labelled once also unknown;
  4. counts: number and summed sampling weight of unknown answers and of answers labelled once, by group, screen
     result and side; skipped answers by labeller.
Each quantity is a ratio of two sums that are affine in the labels Y (the label-assisted estimator too: b_g is a
labelled share whose denominator does not depend on Y). The affine coefficients are read off the estimator itself,
by evaluating sim_v23_labels.estimates() with one unknown label switched on at a time, so they follow its code. The
extremes of a ratio of two affine functions of binary labels are found exactly by ratio_extremes().

Gate of the detection statement (Section 9.3; Section 2.4, addition 2). A detection change may be called negative
only when the largest upper limit of its 95% interval over every assignment of the unknown labels in its scope is
below zero, and positive only when the smallest lower limit is above zero; checked with the unknown labels and
again with the answers labelled once also unknown. Computed by enumeration of every assignment when at most 20
labels in the scope are unknown; with more, no statement. A limit equal to zero does not pass. If an assignment
gives no interval (zero estimated variance or no estimate), or the class has fewer than 20 answers of known label,
no statement. The enumeration evaluates the affine per-prompt sums of each assignment and the production
inference (inference_v23.cluster_ratio and interval); the two decisive assignments are computed again from the
estimator itself.

Input: the locked label file (labels_locked_v23.csv) and, for the harmful frame of the primary panel, the screen
result and the four delivered flags (A1, A2, C1, C2) of every answer, prepared by the analysis script. Arrays are
[author, prompt], authors instruction-tuned first, then refusal-removed (as analysis/sim_v23_dgp.design()).
"""
import csv
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "src"))
import inference_v23 as inf  # noqa: E402
import label_sample as LS  # noqa: E402
import sim_v23_labels as SL  # noqa: E402

MAX_ENUMERATED = 20          # Section 9.3: enumeration with at most 20 unknown labels in the scope of a quantity
CHUNK = 4096                 # assignments per vectorised step of the enumeration
# Section 9.5: the quantities whose interval is reported are those checked before the freeze
# (sim_v23_labels.CHECKED: "every interval of this section passes check 5 of Appendix A.4 ... or it is not
# reported"); beside each registered change, its direct estimator where sim_v23_labels defines one (estimate and
# counts only). The other names of sim_v23_labels.STATS (the per-group harmful shares b_g, the controls' changes,
# the _all and _acc variants) are not reported quantities; analyse(stats=...) takes any of them.
REPORTED = tuple(SL.CHECKED) + tuple(k.replace("_reg|", "|") for k in SL.CHECKED
                                     if "_reg|" in k and k.replace("_reg|", "|") in SL.STATS)
# Section 2.4, addition 2 and Section 9.3: the gate applies to the registered detection changes
GATED = tuple(k for k in SL.CHECKED if k.startswith("det_change_") and "_reg|" in k)
# Appendix A.4, a check that fails twice: the interval is not reported; the estimate and the counts are (Section
# 9.5). The registered detection change of the instruction-tuned group failed check 5 in low_failure_perfect|null
# at both runs of 11 November 2026: 94.32% against 94.34% (10,000 replications), then 94.40% against 94.67%
# (40,000 replications, seed 20261124). It stays in REPORTED and GATED; without an interval it gates no statement
# (Section 9.3).
NO_INTERVAL = {"det_change_own_reg|i": "interval not reported: it failed check 5 of Appendix A.4 in both runs; "
                                       "the estimate and the counts are (Section 9.5)"}
STATES = ("labelled", "labelled_once", "unknown")


# ---------------------------------------------------------------------------------------------------- input
def load_locked(path):
    """Rows of labels_locked_v23.csv with typed fields."""
    rows = []
    with open(path, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            r = dict(r)
            r["model"] = int(r["model"])
            r["weight"] = float(r["weight"])
            for k in ("second", "h60", "api_ref", "collapsed"):
                r[k] = r.get(k) == "true"
            if r["state"] not in STATES:
                raise ValueError(f"unknown state {r['state']!r} in {path}")
            if (r["state"] == "unknown") != (r["label"] == "") or r["label"] not in ("yes", "no", ""):
                raise ValueError(f"label and state disagree for an answer in {path}")
            rows.append(r)
    return rows


def build(rows, prompts, source_of, screen, flags, design=None):
    """Arrays of the harmful frame of the primary panel.

    rows: locked label rows (load_locked); prompts: identifiers of the harmful frame in frame order; source_of:
    prompt id -> source; screen: (model, prompt id) -> 'positive', 'negative' or 'none' for every answer of the
    primary panel on the harmful frame (an answer that was never generated is absent and counts as not
    screen-positive); flags: (model, prompt id) -> (A1, A2, C1, C2), 0 or 1, needed for every screen-positive answer
    (an answer without content has four zero flags, Section 10.1). design: src/label_sample.load_design()."""
    design = design or LS.load_design()
    inst, rem = design["groups"]["instruct_open"], design["groups"]["refusal_removed"]
    judges = inst + rem
    jx, px = {m: j for j, m in enumerate(judges)}, {p: i for i, p in enumerate(prompts)}
    J, P = len(judges), len(prompts)
    sources = sorted({source_of[p] for p in prompts})
    D = {"judges": judges, "group": np.array(["i"] * len(inst) + ["r"] * len(rem)), "P": P,
         "strata": np.array([sources.index(source_of[p]) for p in prompts])}
    S, W, Y = np.zeros((J, P)), np.zeros((J, P)), np.zeros((J, P))
    F = {k: np.zeros((J, P)) for k in ("A1", "A2", "C1", "C2")}
    once, unknown = np.zeros((J, P), bool), np.zeros((J, P), bool)
    absent = 0
    for m in judges:
        for p in prompts:
            s = screen.get((m, p))
            if s is None:
                absent += 1
                continue
            if s not in ("positive", "negative", "none"):
                raise ValueError(f"screen result {s!r} for ({m}, {p})")
            if s == "positive":
                S[jx[m], px[p]] = 1.0
                f = flags.get((m, p))
                if f is None or len(f) != 4 or any(v not in (0, 1) for v in f):
                    raise ValueError(f"the four flags of the screen-positive answer ({m}, {p}) are missing or invalid")
                for k, v in zip(("A1", "A2", "C1", "C2"), f):
                    F[k][jx[m], px[p]] = float(v)
    for r in rows:
        if r["side"] != "harmful" or r["model"] not in jx:
            continue
        if r["prompt_id"] not in px:
            raise ValueError(f"a labelled answer of model {r['model']} lies outside the harmful frame")
        j, i = jx[r["model"]], px[r["prompt_id"]]
        if (r["screen"] == "positive") != bool(S[j, i]):
            raise ValueError(f"the screen result of answer {r['answer_id']} differs from the label sample's")
        if r["weight"] <= 0:
            raise ValueError(f"answer {r['answer_id']} has no sampling weight")
        W[j, i] = r["weight"]
        Y[j, i] = 1.0 if r["label"] == "yes" else 0.0
        once[j, i] = r["state"] == "labelled_once"
        unknown[j, i] = r["state"] == "unknown"
    return dict(D=D, S=S, W=W, Y=Y, once=once, unknown=unknown, judges=judges, prompts=list(prompts),
                absent_answers=absent, **F)


# ------------------------------------------------------------------------------------------------ estimator
def _estimates(data, Y, W=None):
    """sim_v23_labels.estimates() on one complete assignment of the labels."""
    return SL.estimates(data["W"] if W is None else W, data["S"], Y, data["A1"], data["A2"], data["C1"],
                        data["C2"], data["D"])


def scope_mask(data, stat):
    """[author, prompt] mask of the answers whose label enters a quantity: screen-positive answers, or for the
    harmful share among screen-negative answers the screen-negative ones, or all for the share of harmful answers
    that pass the screen; authors of the quantity's group."""
    name, scope = stat.split("|")
    S = data["S"] > 0
    authors = SL.scopes(data["D"])[scope] > 0
    m = ~S if name == "harm_share_neg" else (np.ones_like(S) if name == "screen_pass_harm" or name.endswith("_all")
                                             else S)
    return m & authors[:, None]


def unknown_mask(data, once_unknown):
    return data["unknown"] | (data["once"] if once_unknown else np.zeros_like(data["once"]))


def affine(data, cells, Y0, stats=None):
    """Per-prompt numerators and denominators as affine functions of the labels at `cells` (list of (j, i)):
    {stat: (x0 [P], n0 [P], GX [k, P], GN [k, P])}, with Y0 the assignment where all of them are 0. Exact,
    because every quantity of sim_v23_labels is affine in Y."""
    base, _ = _estimates(data, Y0)
    stats = stats or tuple(base)
    P, k = data["D"]["P"], len(cells)
    out = {s: (np.asarray(base[s][0], float), np.asarray(base[s][1], float), np.zeros((k, P)), np.zeros((k, P)))
           for s in stats}
    for t, (j, i) in enumerate(cells):
        Y = Y0.copy()
        Y[j, i] = 1.0
        cur, _ = _estimates(data, Y)
        for s in stats:
            out[s][2][t] = np.asarray(cur[s][0], float) - out[s][0]
            out[s][3][t] = np.asarray(cur[s][1], float) - out[s][1]
    return out


def ratio_extremes(a, c, b, d):
    """Exact smallest and largest value of (a + c.y) / (b + d.y) over y in {0, 1}^k, for b + d.y > 0 at every y.

    Dinkelbach: at the optimal value lambda*, an optimal y sets y_i = 1 where c_i - lambda* d_i > 0 and y_i = 0
    where it is < 0 (either where it is 0). As lambda runs over the line, that rule takes at most k + 1 different
    values, one between each pair of consecutive breakpoints c_i / d_i; every one of them is evaluated.
    Returns ((low, y_low), (high, y_high)) with y as float arrays."""
    c, d = np.asarray(c, dtype=np.float64), np.asarray(d, dtype=np.float64)
    if b + np.minimum(d, 0.0).sum() <= 0:
        raise ValueError("an assignment of the unknown labels leaves the denominator at zero or below")

    def best(sign):
        cs, a_s = sign * c, sign * a
        nz = d != 0
        bps = np.unique(cs[nz] / d[nz])
        if bps.size:
            lams = np.concatenate([[bps[0] - 1.0 - abs(bps[0])], (bps[:-1] + bps[1:]) / 2,
                                   [bps[-1] + 1.0 + abs(bps[-1])]])
        else:
            lams = np.zeros(1)
        cand = ((cs[None, :] - lams[:, None] * d[None, :]) > 0).astype(np.float64)
        vals = (a_s + cand @ cs) / (b + cand @ d)
        i = int(np.argmax(vals))
        return sign * float(vals[i]), cand[i]

    return best(-1.0), best(1.0)


# ------------------------------------------------------------------------------------------------- intervals
def _class_counts(data, Y, known):
    return SL.support(data["W"] * known, data["S"], Y, data["D"])


def interval_at(data, stat, Y, shares_reported=True):
    """Estimate and registered 95% interval of one quantity at one complete assignment Y: the rule of
    sim_v23_labels.registered_interval(), which the simulation applies in every replication. shares_reported: both
    harmful shares are reported, which the propagated interval of 'screen_pass_harm' needs. None stands for "no
    estimate" and "no interval"; no_interval gives the reason. A quantity of NO_INTERVAL has its estimate and
    no interval (Appendix A.4)."""
    cells, events = _estimates(data, Y)
    reg = SL.registered_interval(cells, stat, data["D"]["strata"], shares_reported)
    if stat in NO_INTERVAL and reg["no_interval"] is None:          # Appendix A.4: the estimate only
        reg = dict(reg, lo=np.nan, hi=np.nan, kind=None, no_interval=NO_INTERVAL[stat])
    name, scope = stat.split("|")
    labelled = data["W"] > 0
    out = {"est": None, "lo": None, "hi": None, "se": None, "interval": reg["kind"],
           "no_interval": reg["no_interval"],
           "class_n": float(_class_counts(data, Y, labelled)[scope][SL.support_class(stat)]),
           # labelled answers that gain and that lose a flag (Section 9.5), as sim_v23_labels counts them
           "events": [float(v) for v in events["|".join(SL.truth_name(stat))]]}
    if bool(reg["ratio"]["estimable"]):
        out["est"], out["se"] = reg["est"], float(reg["ratio"]["se"])
    if reg["no_interval"] is None:
        out["lo"], out["hi"] = reg["lo"], reg["hi"]
    if name in SL.LEVELS and out["est"] is not None:
        out["n_eff"] = reg["n_eff"]
    return out


# ------------------------------------------------------------------------------------------- steps 1 to 3
def label_pass(data, once_unknown=False, stats=REPORTED):
    """Steps 1 and 2 (once_unknown=False) or step 3 (True) for every quantity in `stats`."""
    unk = unknown_mask(data, once_unknown)
    labelled = data["W"] > 0
    known = labelled & ~unk
    Y0 = np.where(unk, 0.0, data["Y"])
    Y1 = np.where(unk & labelled, 1.0, Y0)
    sup = _class_counts(data, Y0, known)
    shares = all(sup["all"][c] >= SL.MIN_SUPPORT for c in ("pos", "neg"))
    cells = [tuple(x) for x in np.argwhere(unk & labelled)]
    coef = affine(data, cells, Y0, stats) if cells else None
    out = {}
    for stat in stats:
        name, scope = stat.split("|")
        in_scope = scope_mask(data, stat)
        idx = [t for t, (j, i) in enumerate(cells) if in_scope[j, i]]
        e = {"support_known": float(sup[scope][SL.support_class(stat)]), "min_support": SL.MIN_SUPPORT,
             "unknown_in_scope": len(idx),
             "weight_unknown_in_scope": float(sum(data["W"][cells[t]] for t in idx))}
        e["reported"] = e["support_known"] >= SL.MIN_SUPPORT
        if not e["reported"]:
            out[stat] = e                       # below the minimum support: the count only (Section 9.5)
            continue
        e["all_harmful"] = interval_at(data, stat, Y1, shares)
        e["all_not_harmful"] = interval_at(data, stat, Y0, shares)
        if not idx:
            e["range"] = {"low": e["all_not_harmful"], "high": e["all_not_harmful"]}
            out[stat] = e
            continue
        x0, n0, GX, GN = coef[stat]
        try:
            (low, y_lo), (high, y_hi) = ratio_extremes(x0.sum(), GX[idx].sum(1), n0.sum(), GN[idx].sum(1))
        except ValueError as err:
            e["range"] = {"error": str(err)}
            out[stat] = e
            continue
        ends = {}
        for tag, y in (("low", y_lo), ("high", y_hi)):
            Y = Y0.copy()
            for t, v in zip(idx, y):
                Y[cells[t]] = v
            ends[tag] = interval_at(data, stat, Y, shares)
            ends[tag]["harmful_assigned"] = int(round(float(np.sum(y))))
        e["range"] = ends
        e["range_value"] = (low, high)
        out[stat] = e
    return out


def analyse(data, stats=REPORTED, gated=GATED, max_enumerated=MAX_ENUMERATED):
    """The registered missing-label analysis: steps 1 to 3 for every quantity, and the gate of every detection
    change. Step 4 (counts) comes from counts() on the locked rows."""
    complete = not data["unknown"][data["W"] > 0].any() and not data["once"][data["W"] > 0].any()
    return {"complete_labels": bool(complete), "steps_1_2": label_pass(data, False, stats),
            "step_3": label_pass(data, True, stats),
            "gates": {s: detection_gate(data, s, max_enumerated) for s in gated}}


# ------------------------------------------------------------------------------------------------------ gate
def _enumerate(x0, n0, GX, GN, strata, chunk=CHUNK):
    """Every assignment of k labels: largest upper and smallest lower limit of the cluster ratio t interval, the
    assignments that give them, and the number of assignments without an interval. This is the rule of
    sim_v23_labels.registered_interval() for a registered change, vectorised over the assignments; the two
    decisive assignments are computed again through it (_gate_check)."""
    k = GX.shape[0]
    bits = np.arange(k)
    best = {"max_hi": -np.inf, "arg_hi": None, "min_lo": np.inf, "arg_lo": None, "no_interval": 0}
    for start in range(0, 1 << k, chunk):
        ids = np.arange(start, min(1 << k, start + chunk))
        Y = ((ids[:, None] >> bits[None, :]) & 1).astype(np.float64)
        c = inf.cluster_ratio(x0 + Y @ GX, n0 + Y @ GN, strata)
        lo, hi = inf.interval(c)                 # NaN where the result is not available (Section 8.1)
        ok = inf.available(c) & np.isfinite(lo) & np.isfinite(hi)
        best["no_interval"] += int((~ok).sum())
        if not ok.any():
            continue
        lo, hi, sel = lo[ok], hi[ok], ids[ok]
        h, l_ = int(np.argmax(hi)), int(np.argmin(lo))
        if hi[h] > best["max_hi"]:
            best["max_hi"], best["arg_hi"] = float(hi[h]), int(sel[h])
        if lo[l_] < best["min_lo"]:
            best["min_lo"], best["arg_lo"] = float(lo[l_]), int(sel[l_])
    return best


def _gate_check(data, stat, once_unknown, max_enumerated):
    unk = unknown_mask(data, once_unknown)
    labelled = data["W"] > 0
    Y0 = np.where(unk, 0.0, data["Y"])
    name, scope = stat.split("|")
    support = float(_class_counts(data, Y0, labelled & ~unk)[scope][SL.support_class(stat)])
    cells = [tuple(x) for x in np.argwhere(unk & labelled & scope_mask(data, stat))]
    res = {"once_unknown": once_unknown, "unknown_in_scope": len(cells), "support_known": support,
           "negative": False, "positive": False, "reason": None}
    # Every assignment keeps at least the answers of known label in the class, and one assignment (all unknown
    # labels outside the class) keeps no more: "no assignment leaves the class below the minimum support" is
    # the same condition as "at least 20 answers of known label in the class".
    if support < SL.MIN_SUPPORT:
        res["reason"] = "fewer than 20 answers of known label in the class"
        return res
    if len(cells) > max_enumerated:
        res["reason"] = f"more than {max_enumerated} unknown labels in the scope: no enumeration, no statement"
        return res
    x0, n0, GX, GN = affine(data, cells, Y0, (stat,))[stat]
    best = _enumerate(x0, n0, GX, GN, data["D"]["strata"])
    res.update(assignments=1 << len(cells), without_interval=best["no_interval"])
    if best["no_interval"]:
        res["reason"] = "an assignment gives no interval (zero estimated variance or no estimate)"
        return res
    exact = {}
    for tag in ("arg_hi", "arg_lo"):            # the decisive assignments, computed again from the estimator
        Y = Y0.copy()
        for t, (j, i) in enumerate(cells):
            Y[j, i] = float((best[tag] >> t) & 1)
        exact[tag] = interval_at(data, stat, Y)
        if exact[tag]["lo"] is None:
            res["reason"] = "an assignment gives no interval (zero estimated variance or no estimate)"
            return res
    if abs(exact["arg_hi"]["hi"] - best["max_hi"]) > 1e-9 or abs(exact["arg_lo"]["lo"] - best["min_lo"]) > 1e-9:
        raise RuntimeError("the enumeration and the estimator disagree")
    res.update(max_upper=exact["arg_hi"]["hi"], min_lower=exact["arg_lo"]["lo"],
               negative=exact["arg_hi"]["hi"] < 0.0, positive=exact["arg_lo"]["lo"] > 0.0)
    if not (res["negative"] or res["positive"]):
        res["reason"] = "an assignment gives an interval that contains zero"
    return res


def detection_gate(data, stat, max_enumerated=MAX_ENUMERATED):
    """Gate of the detection statement for one registered detection change (Section 9.3). 'statement' is
    'negative', 'positive' or None; both checks (unknown labels; answers labelled once also unknown) must pass.
    A quantity of NO_INTERVAL has no reported interval (Appendix A.4): no check and no statement."""
    if not (stat.startswith("det_change_") and "_reg|" in stat):
        raise ValueError(f"{stat} is not a registered detection change")
    if stat in NO_INTERVAL:
        return {"stat": stat, "statement": None, "no_interval": NO_INTERVAL[stat], "checks": []}
    checks = [_gate_check(data, stat, False, max_enumerated), _gate_check(data, stat, True, max_enumerated)]
    statement = "negative" if all(c["negative"] for c in checks) else \
        "positive" if all(c["positive"] for c in checks) else None
    return {"stat": stat, "statement": statement, "checks": checks}


# ---------------------------------------------------------------------------------------------------- step 4
def counts(rows, design=None):
    """Step 4: number and summed sampling weight of unknown answers and of answers labelled once, by group,
    screen result and side, with the margins; skipped answers by labeller."""
    design = design or LS.load_design()
    out = {"by_group_side_screen": {}, "by_group": {}, "by_side": {}, "by_screen": {}, "total": {},
           "skipped_by_labeller": {"first": 0, "second": 0}, "unknown_reason": {}}
    for r in rows:
        for w in ("first", "second"):
            if r.get(f"{w}_status") == "skipped":
                out["skipped_by_labeller"][w] += 1
        if r["state"] == "labelled":
            continue
        if r["state"] == "unknown":
            out["unknown_reason"][r["unknown_reason"]] = out["unknown_reason"].get(r["unknown_reason"], 0) + 1
        g = design["group_of"][r["model"]]
        for table, key in (("by_group_side_screen", f"{g}|{r['side']}|{r['screen']}"), ("by_group", g),
                           ("by_side", r["side"]), ("by_screen", r["screen"]), ("total", "all")):
            cell = out[table].setdefault(key, {s: {"n": 0, "weight": 0.0} for s in ("unknown", "labelled_once")})
            cell[r["state"]]["n"] += 1
            cell[r["state"]]["weight"] += r["weight"]
    return out
