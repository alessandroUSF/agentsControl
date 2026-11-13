"""Decision D20 (PI, 12 November 2026): P1 and P2 are carried out only when the change is not sparse (Section 8.1).

The registered t tests of P1 and P2 exceed their nominal level when a change is carried by very few prompts and the
other prompts do not change at all (run (j) of Appendix A.4). A test that keeps its level for every distribution of
the bounded per-prompt totals could not detect the planned effect at this sample size (Section 8.1). D20 therefore
keeps the t tests and adds a registered condition on the data: a test is carried out only when at least THRESHOLD of
the prompts with a screen-positive answer (N_p > 0) have a per-prompt total X_p that is not zero. Below it the test is
not carried out (Section 8.1: a test not carried out is never a rejection), the other test is compared with .02
(Holm), and the estimate and its interval are reported as description.

The condition reads only the per-prompt totals of the statistic being tested: those of theta_S for P1 and of iota_S
for P2. P3 is not affected. inference_v23 is not changed (its fingerprint stays); the condition is applied to its
p-values here, by the analysis (analysis/analyze_v23.py) and by run (j) (analysis/sim_v23_sparse.py).
"""
import numpy as np

import inference_v23 as inf

THRESHOLD = 0.30
SPARSE_REASON = (f"fewer than {THRESHOLD:.0%} of the prompts with a screen-positive answer changed "
                 "(decision D20, Section 8.1)")


def share_nonzero(X, N):
    """Share of the prompts with N_p > 0 whose total X_p is not zero; arrays [..., P]. 0 when no prompt has N_p > 0."""
    X, N = np.asarray(X), np.asarray(N)
    pos = N > 0
    k = pos.sum(-1)
    return np.where(k > 0, ((X != 0) & pos).sum(-1) / np.maximum(k, 1), 0.0)


def dense(X, N, threshold=THRESHOLD):
    return share_nonzero(X, N) >= threshold


def decide(theta, iota, beta, X_th, X_io, N, threshold=THRESHOLD, N_io=None):
    """inference_v23.registered_tests with the condition of D20. theta, iota, beta: cluster_ratio results; X_th, X_io,
    N: per-prompt totals [..., P]. Returns the keys of registered_tests (P1 and P2 decided again with Holm over the
    tests that are carried out) and p1_dense, p2_dense, p1_share, p2_share. N_io: the N of X_io when it differs from
    that of X_th (the fragility count adds hypothetical prompts to one statistic only); by default N."""
    t = dict(inf.registered_tests(theta, iota, beta))
    s1, s2 = share_nonzero(X_th, N), share_nonzero(X_io, N if N_io is None else N_io)
    d1, d2 = s1 >= threshold, s2 >= threshold
    c1 = np.asarray(t["p1_carried_out"]) & d1
    c2 = np.asarray(t["p2_carried_out"]) & d2
    q1 = np.where(c1, t["p1_p"], np.nan)
    q2 = np.where(c2, t["p2_p"], np.nan)
    r1, r2 = inf.holm_two(q1, q2)
    t.update(p1=r1 & c1, p2=r2 & c2, p1_carried_out=c1, p2_carried_out=c2, p1_dense=d1, p2_dense=d2,
             p1_share=s1, p2_share=s2)
    return t
