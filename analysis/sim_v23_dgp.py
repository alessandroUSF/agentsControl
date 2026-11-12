"""Data-generating process for the registered-inference simulations of protocol v2.3 (primary panel).

Panel: the primary panel of config/panel_v23.json, read by design(): twelve open models, five instruction-tuned
("i") and seven refusal-removed ("r"), the hosted models 22 and 23 included. design(drop=...) leaves hosted
models out and then uses the control assignment of that smaller panel (Section 6.5; run (g) of Appendix A.4).
Prompts: two source strata of equal size. The control judge of every answer comes from the production assignment
(src/yoking.py), with the block labels of scripts/control_assignment_v23.py. All arrays are indexed by the
ANSWER: [replication, author, prompt]; a control verdict is stored with the answer it refers to, never with the
control judge's own answers.

Latent model (the one of analysis/power_sim_v23.py):
  harmful answer ("failure") ~ Bernoulli(expit(c_author + a_p)), a_p ~ N(0, 0.8)
  blind logit of judge k on an answer = logit(Se_k if failure else 1 - Sp_k) + u_p + v_answer + w
      u_p ~ N(0, 0.6) (prompt), v ~ N(0, 0.6) (answer, shared by every verdict on it), w ~ N(0, 0.4) (call)
  in-context logit = blind logit + g * m + s_p (+ t_p in the author arm) + h_judge * m_h
  m = 1 on failures only (mode "fail_only") or everywhere; flags of the two presentations share a uniform
  with probability rho; a verdict is invalid with the probabilities of invalid_probs().
  screen S ~ Bernoulli(screen_se if failure else 1 - screen_sp), drawn before any verdict; with
  screen_mode="informative" (run (b)) P(S = 1) = expit(a_Y + v), a_1 and a_0 set so that the shares are the same
  screen_se and 1 - screen_sp on average over v.
Group "c" (commercial models, used by the safe-side run (d)) takes the rate fail_c.
"""
import functools
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import brentq
from scipy.special import expit, logit

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import frames_v23  # noqa: E402  (production frames: identifiers and sources only)
import yoking  # noqa: E402  (production assignment of control judges)

F32 = np.float32
PANEL_SEED = 20261121
SD_FAIL, SD_PROMPT, SD_ANSWER, SD_CALL = 0.8, 0.6, 0.6, 0.4     # standard deviations of the latent effects
SHIFT_RANGE = 12.0           # calibrated shifts are searched in [-12, 12] logits
BASE = dict(theta=0.0, iota=0.0, beta=0.0, sd_common=0.3, sd_own=0.3, q0=0.10, inv="3", mode="fail_only",
            screen_se=0.9, screen_sp=0.8, fail_i=0.15, fail_r=0.70, se_removed=None, source_shift=0.0,
            h_pattern="none", h_amp=0.5, h_content="all", shifts="calibrated")
SAFE_FRAMES = ("safe", "safe_commercial_controls")
# Unequal rates of harmful answers by author (R-S2, Appendix A.2): spread evenly over these ranges, in panel order.
HET_RANGE = {"i": (0.05, 0.25), "r": (0.45, 0.95)}


def block_label(group, dropped, hosted):
    """Label of a control-assignment block, as in scripts/control_assignment_v23.py: the refusal-removed group
    without some of its hosted models is 'refusal_removed_without_<n>', without all of them
    'refusal_removed_local'. The safe frames add '|safe' (frame_label)."""
    if group != "refusal_removed" or not dropped:
        return group
    if sorted(dropped) == sorted(hosted):
        return "refusal_removed_local"
    return "refusal_removed_without_" + "_".join(str(x) for x in sorted(dropped))


def frame_label(block, frame):
    return f"{block}|safe" if frame in SAFE_FRAMES else block


def assign(ids, names, members, panel, label):
    """Production assignment of one block: ctrl[author] for every prompt, checked."""
    allowed = yoking.allowed_controls(members, panel)
    asg = yoking.assign_controls(ids, names, members, allowed, panel["seed"], label)
    yoking.check(asg, members, allowed)
    return asg


def design(drop=(), frame="harmful"):
    """Primary panel on a frame of the sealed sample (identifiers and sources only), with the production
    assignment of control judges. drop: hosted models (config 'hosted_primary') left out of the panel; their
    group then uses the assignment block of Section 6.5. frame: 'harmful' (default) or 'safe'."""
    panel = yoking.load_panel()
    drop = sorted({int(x) for x in drop})
    hosted = panel["hosted_primary"]
    if not set(drop) <= set(hosted):
        raise ValueError(f"only hosted models of the primary panel can be left out: {hosted}")
    inst = panel["groups"]["instruct_open"]
    rem = [m for m in panel["groups"]["refusal_removed"] if m not in drop]
    judges = inst + rem
    idx = {m: i for i, m in enumerate(judges)}
    ids, names = frames_v23.frames()[frame]
    P = len(ids)
    sources = sorted(set(names.values()))
    ctrl = np.zeros((len(judges), P), dtype=np.int64)      # ctrl[a, p]: control judge of author a's answer
    blocks = {}
    for g, members in (("instruct_open", inst), ("refusal_removed", rem)):
        blocks[g] = frame_label(block_label(g, drop, hosted), frame)
        asg = assign(ids, names, members, panel, blocks[g])
        for p, pid in enumerate(ids):
            for a, k in asg[pid].items():
                ctrl[idx[a], p] = idx[k]
    auth = np.zeros_like(ctrl)                              # auth[k, p]: author whose answer judge k controls
    for p in range(P):
        auth[ctrl[:, p], p] = np.arange(len(judges))
    return dict(judges=judges, group=np.array(["i"] * len(inst) + ["r"] * len(rem)), P=P,
                strata=np.array([sources.index(names[p]) for p in ids]), ctrl=ctrl, auth=auth,
                frame=frame, dropped=drop, blocks=blocks)


def het_rates(D):
    """Rates of harmful answers by author for the scenarios with unequal rates (R-S2 and runs (b), (g)):
    evenly spaced over 5% to 25% in the instruction-tuned group and 45% to 95% in the refusal-removed group, in
    panel order. With five and six models these are the rates of Appendix A.2. A.2 names six refusal-removed
    rates (eleven models); with seven (twelve models) the same range and mean give 45, 53.3, 61.7, 70, 78.3,
    86.7 and 95%, and with five (the ten local models) 45, 57.5, 70, 82.5 and 95%."""
    out = {}
    for g, key in (("i", "fail_i"), ("r", "fail_r")):
        n = int((D["group"] == g).sum())
        out[key] = [round(float(x), 10) for x in np.linspace(*HET_RANGE[g], n)]
    return out


@functools.lru_cache(maxsize=None)
def fail_intercept(target, sd=SD_FAIL):
    """Constant c with mean expit(c + a) = target, a ~ N(0, sd). Raises when the target cannot be reached in
    [-15, 15] (it is never clipped silently). Cached: the value depends on the arguments only."""
    a = np.random.default_rng(1).normal(0, sd, 200000)
    lo, hi = -15.0, 15.0
    if not expit(lo + a).mean() <= target <= expit(hi + a).mean():
        raise ValueError(f"rate {target} cannot be reached by an intercept in [-15, 15]")
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if expit(mid + a).mean() < target else (lo, mid)
    return (lo + hi) / 2


@functools.lru_cache(maxsize=None)
def screen_intercepts(share_harmful, share_other, sd=SD_ANSWER):
    """(a_0, a_1) of the informative screen of run (b): E expit(a_1 + v) = share_harmful and
    E expit(a_0 + v) = share_other, v ~ N(0, sd), by Gauss-Hermite quadrature."""
    x, w = np.polynomial.hermite_e.hermegauss(80)
    w = w / w.sum()

    def solve(share):
        if not 0.0 < share < 1.0:
            raise ValueError(f"an informative screen needs shares strictly between 0 and 1, got {share}")
        return float(brentq(lambda c: float((w * expit(c + sd * x)).sum()) - share, -40.0, 40.0, xtol=1e-12))

    return solve(share_other), solve(share_harmful)


def judge_accuracy(D, seed=PANEL_SEED):
    """Baseline sensitivities and specificities of the judges, drawn once: Se ~ U(0.70, 0.95), Sp ~ U(0.85, 0.98)."""
    rng = np.random.default_rng(seed)
    J = len(D["judges"])
    return rng.uniform(0.70, 0.95, J), rng.uniform(0.85, 0.98, J)


def panel_quality(D, sc, seed=PANEL_SEED):
    """Fixed judge panel: sensitivities, specificities, failure intercepts and presentation shifts.
    sc["se_judge"] (one value per judge, run (f)) replaces the drawn sensitivities; sc["se_removed"] sets those of
    the refusal-removed judges."""
    J = len(D["judges"])
    se, sp = judge_accuracy(D, seed)
    rem = D["group"] == "r"
    if sc.get("se_judge") is not None:
        se = np.asarray(sc["se_judge"], dtype=float)
        if se.shape != (J,):
            raise ValueError("se_judge needs one sensitivity per judge")
    if sc["se_removed"] is not None:
        se = np.where(rem, sc["se_removed"], se)
    rates = np.zeros(J)
    for g, key in (("i", "fail_i"), ("r", "fail_r"), ("c", "fail_c")):
        m = D["group"] == g
        if m.any():
            rates[m] = np.broadcast_to(np.asarray(sc[key], dtype=float), (int(m.sum()),))
    h = np.zeros(J)
    if sc["h_pattern"] == "alternating":
        h = np.where(np.arange(J) % 2 == 0, sc["h_amp"], -sc["h_amp"])
    elif sc["h_pattern"] == "aligned":                      # inside each group: higher failure rate, lower shift
        for g in ("i", "r", "c"):
            m = np.where(D["group"] == g)[0]
            if m.size:
                med = np.median(rates[m])
                h[m] = -sc["h_amp"] * np.sign(rates[m] - med)
    out = dict(se=se, sp=sp, rates=rates, h=h, cfail=np.array([fail_intercept(float(r)) for r in rates]))
    if sc.get("screen_mode", "independent") == "informative":
        out["screen_a"] = screen_intercepts(float(sc["screen_se"]), float(1 - sc["screen_sp"]))
    return out


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


def draw_latent(rng, R, D, sc, q):
    J, P = len(D["judges"]), D["P"]
    shape = (R, J, P)
    src = sc["source_shift"] * np.where(D["strata"] == 0, 1.0, -1.0)[None, None, :]
    fail = rng.random(shape) < expit(q["cfail"][None, :, None] + src + rng.normal(0, SD_FAIL, (R, 1, P)))
    u, v = rng.normal(0, SD_PROMPT, (R, 1, P)), rng.normal(0, SD_ANSWER, shape)
    se_c, sp_c = q["se"][D["ctrl"]][None], q["sp"][D["ctrl"]][None]
    eta_a = logit(np.where(fail, q["se"][None, :, None], 1 - q["sp"][None, :, None])) + u + v
    eta_c = logit(np.where(fail, se_c, 1 - sp_c)) + u + v
    eta_a = (eta_a + rng.normal(0, SD_CALL, shape)).astype(F32)
    eta_c = (eta_c + rng.normal(0, SD_CALL, shape)).astype(F32)
    s = rng.normal(0, sc["sd_common"], (R, 1, P)) if sc["sd_common"] > 0 else np.zeros((R, 1, P))
    t = rng.normal(0, sc["sd_own"], (R, 1, P)) if sc["sd_own"] > 0 else np.zeros((R, 1, P))
    mh = fail if sc["h_content"] == "fail" else 1.0
    h_a, h_c = q["h"][None, :, None] * mh, q["h"][D["ctrl"]][None] * mh
    if "screen_a" in q:                                     # informative screen: it depends on the answer effect v
        a0, a1 = q["screen_a"]
        p_screen = expit(np.where(fail, a1, a0) + v)
    else:
        p_screen = np.where(fail, sc["screen_se"], 1 - sc["screen_sp"])
    screen = rng.random(shape) < p_screen
    return dict(fail=fail, eta_a=eta_a, eta_c=eta_c, shock_a=(s + t + h_a).astype(F32),
                shock_c=(s + h_c + np.zeros(shape)).astype(F32), screen=screen)


def arm_logits(L, sc, g):
    m = L["fail"].astype(F32) if sc["mode"] == "fail_only" else F32(1.0)
    a1 = L["eta_a"] + F32(g["blind"])
    return a1, a1 + L["shock_a"] + F32(g["on"]) * m, L["eta_c"], L["eta_c"] + L["shock_c"] + F32(g["ctrl"]) * m


def expected(L, sc, g):
    """Expected delivered-valid flags of the four arms given the latent draw: A1, A2, C1, C2."""
    ib, ic = invalid_probs(sc["inv"], L["fail"])
    a1, a2, c1, c2 = arm_logits(L, sc, g)
    return (1 - ib) * expit(a1), (1 - ic) * expit(a2), (1 - ib) * expit(c1), (1 - ic) * expit(c2)


def _root(f, target=None):
    """Root of the increasing function f on [-12, 12] logits. Returns (shift, record): record is None when the
    root exists in the range. Otherwise the target cannot be reached: the end of the range that comes nearest is
    returned, with the record {"target", "nearest", "shift"} (the target's value, the value that the nearest end
    reaches and that end), so that the caller reports it instead of clipping silently (Appendix A.4, run (f))."""
    lo, hi = f(-SHIFT_RANGE), f(SHIFT_RANGE)
    if lo > 0 or hi < 0:
        end, gap = (-SHIFT_RANGE, lo) if lo > 0 else (SHIFT_RANGE, hi)
        value = None if target is None else float(target)
        return end, {"target": value, "nearest": None if value is None else value + float(gap), "shift": end}
    if lo == 0:
        return -SHIFT_RANGE, None
    if hi == 0:
        return SHIFT_RANGE, None
    return float(brentq(f, -SHIFT_RANGE, SHIFT_RANGE, xtol=1e-6, maxiter=100)), None


def calibrate(rng, D, sc, q, reps=500):
    """Shifts g so that the SCREENED delivered-flag ratios of a large sample equal the targets
    (beta, theta, theta - iota), and the coupling rho that gives the null discordance q0.
    Targets that cannot be reached are listed in diag["unreached"] (name, target, nearest value, shift used);
    the scenario then runs with the nearest value, and the caller reports it."""
    L = draw_latent(rng, reps, D, sc, q)
    S = L["screen"]
    den = float(S.sum())
    g = dict(blind=0.0, on=0.0, ctrl=0.0)
    unreached = []
    if den == 0:
        raise ValueError("the calibration sample has no screen-positive answer; raise --cal-reps")
    if sc["shifts"] != "zero":
        # The expected delivered flags of expected() and arm_logits(), written out so that the arms that a shift
        # does not move are computed once (the same expressions, in the same order, so the same numbers).
        ib, ic = invalid_probs(sc["inv"], L["fail"])
        m = L["fail"].astype(F32) if sc["mode"] == "fail_only" else F32(1.0)
        c1 = (1 - ib) * expit(L["eta_c"])
        c2_base = L["eta_c"] + L["shock_c"]

        def solve(key, name, f, target):
            g[key], miss = _root(f, target)
            if miss:
                unreached.append(dict(miss, name=name))

        def f_blind(x):
            a1 = (1 - ib) * expit(L["eta_a"] + F32(x))
            return float((S * (a1 - c1)).sum()) / den - sc["beta"]

        solve("blind", "beta", f_blind, sc["beta"])
        a1_logit = L["eta_a"] + F32(g["blind"])
        a1 = (1 - ib) * expit(a1_logit)
        a2_base = a1_logit + L["shock_a"]

        def f_on(x):
            a2 = (1 - ic) * expit(a2_base + F32(x) * m)
            return float((S * (a2 - a1)).sum()) / den - sc["theta"]

        def f_ctrl(x):
            c2 = (1 - ic) * expit(c2_base + F32(x) * m)
            return float((S * (c2 - c1)).sum()) / den - (sc["theta"] - sc["iota"])

        solve("on", "theta", f_on, sc["theta"])
        solve("ctrl", "theta - iota", f_ctrl, sc["theta"] - sc["iota"])
    pb = expit(L["eta_a"] + F32(g["blind"]))
    pc = expit(L["eta_a"] + F32(g["blind"]) + L["shock_a"])
    a, b = float((pb * (1 - pc) + pc * (1 - pb)).mean()), float(np.abs(pc - pb).mean())
    raw = (a - sc["q0"]) / max(a - b, 1e-9)
    rho = float(np.clip(raw, 0.0, 1.0))
    if raw != rho:              # the discordance q0 lies outside [floor, independent]: report, do not hide
        unreached.append({"name": "q0", "target": float(sc["q0"]), "nearest": a if raw < 0 else b,
                          "shift": rho})
    return g, rho, dict(q0_independent=a, q0_floor=b, screen_rate=den / S.size,
                        removed_share=float(S[:, D["group"] == "r", :].sum()) / den, unreached=unreached)


def canon(v):
    """A JSON-ready copy with a fixed order, for fingerprints."""
    if isinstance(v, dict):
        return {str(k): canon(x) for k, x in sorted(v.items(), key=lambda t: str(t[0]))}
    if isinstance(v, (set, frozenset)):
        return sorted(str(x) for x in v)
    if isinstance(v, (list, tuple)):
        return [canon(x) for x in v]
    if isinstance(v, np.ndarray):
        return canon(v.tolist())
    if isinstance(v, np.generic):
        return v.item()
    return v if isinstance(v, (str, int, float, bool, type(None))) else type(v).__name__
