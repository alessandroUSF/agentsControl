"""Fragility count of the registered tests (protocol v2.3, Section 8.1; decision D20 of 12 November 2026).
Description only: it never changes a decision of a registered test. A test that is not carried out under the
condition of D20 (analysis/density_v23.py) has no count; the analysis prints "not carried out" for it.

The registered t tests take the per-prompt totals as a sample whose mean is estimated. Their level is nominal: a
rare, large change can be missing from the sample, and the test then rejects too often (run (j) of Appendix A.4).
The totals are bounded, so the question "how many unseen prompts would undo this decision?" has an answer. For a
rejected test, the fragility count is the smallest k such that the registered decision no longer rejects after k
hypothetical prompts are added, all in the same stratum (whichever undoes it first), each with the largest number
of screen-positive answers of any prompt in the sample, N_max, and a total at its bound against the decision:

  P1 (theta_S): +N_max when the estimate is negative, -N_max when it is positive (the bound of sum S (A2 - A1));
  P2 (iota_S):  +2 N_max or -2 N_max in the same way (the bound of sum S ((A2 - A1) - (C2 - C1)));
  P3 (beta_S):  -N_max, the largest deficit (the bound of sum S (A1 - C1) on the side of the null).

The other statistics are left as they are. The decision is the registered one, with the condition of D20
(density_v23.decide, rule "d20", the default since code review round 11 of 13 November 2026): P1 and P2 go through
Holm over the tests that are carried out, and the shares of D20 are those of the data with the hypothetical prompts
(they are not zero, so they never make a test sparse). rule "registered" gives the counts under
inference_v23.registered_tests without the condition, as run (j) of Appendix A.4 stores them for its comparison
(analysis/sim_v23_sparse.py). A test that is not rejected, or not carried out, has count 0. A rejection that survives
KMAX added prompts has count KMAX + 1, reported as "more than KMAX"."""
import numpy as np

import density_v23 as DN
import inference_v23 as inf

BOUND = {"th": 1.0, "io": 2.0, "be": 1.0}
TESTS = (("p1", "th"), ("p2", "io"), ("p3", "be"))
KMAX = 10
RULES = ("d20", "registered")


def _decide(r, Xth, Xio, Nth, Nio, rule):
    """The decisions of the three tests under the rule."""
    if rule == "registered":
        return inf.registered_tests(r["th"], r["io"], r["be"])
    return DN.decide(r["th"], r["io"], r["be"], Xth, Xio, Nth, N_io=Nio)


def _against(k, est):
    """Sign of an added prompt's total: against the estimate for theta and iota, a deficit for beta."""
    est = np.asarray(est, np.float64)
    if k == "be":
        return -np.ones_like(est)
    s = -np.sign(est)
    return np.where(s == 0, 1.0, s)


def counts(X, N, strata, kmax=KMAX, tests=TESTS, rule="d20"):
    """Fragility counts. X: {"th", "io", "be"} -> totals [..., P]; N: [..., P]; strata: [P] labels; rule: "d20" (the
    registered decision with the condition of D20) or "registered" (without it, run (j)).
    Returns {"p1", "p2", "p3"} -> integer arrays [...] (0: not rejected; kmax + 1: more than kmax)."""
    if rule not in RULES:
        raise ValueError(f"rule must be one of {RULES}")
    N = np.asarray(N, np.float64)
    X = {k: np.asarray(v, np.float64) for k, v in X.items()}
    strata = np.asarray(strata)
    r0 = {k: inf.cluster_ratio(X[k], N, strata) for k in ("th", "io", "be")}
    dec0 = _decide(r0, X["th"], X["io"], N, N, rule)
    n_add = N.max(-1)
    out = {}
    for test, k in tests:
        rejected = np.asarray(dec0[test], bool)
        count = np.where(rejected, kmax + 1, 0)
        pending = rejected.copy()
        x_add = _against(k, r0[k]["est"]) * BOUND[k] * n_add
        for kk in range(1, kmax + 1):
            if not pending.any():
                break
            undone = np.zeros_like(pending)
            for h in np.unique(strata):
                xa = np.concatenate([X[k], np.repeat(x_add[..., None], kk, -1)], -1)
                na = np.concatenate([N, np.repeat(n_add[..., None], kk, -1)], -1)
                sa = np.concatenate([strata, np.repeat(np.asarray([h]), kk)])
                r = dict(r0)
                r[k] = inf.cluster_ratio(xa, na, sa)
                Xth, Nth = (xa, na) if k == "th" else (X["th"], N)
                Xio, Nio = (xa, na) if k == "io" else (X["io"], N)
                undone |= ~np.asarray(_decide(r, Xth, Xio, Nth, Nio, rule)[test], bool)
            count = np.where(pending & undone, kk, count)
            pending &= ~undone
        out[test] = count
    return out


def label(c, kmax=KMAX):
    """The reported form of one count."""
    c = int(c)
    return "not rejected" if c == 0 else (f"more than {kmax}" if c > kmax else str(c))
