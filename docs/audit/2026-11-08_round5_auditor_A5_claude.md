**Auditor A5 (research methods and statistics), round 5, 8 November 2026**

Everything was read-only. I ran `python -I -B` imports on synthetic data, `scripts/cost_model.py` (it only prints), and the offline test with `AC_TEST_TMP=E:\claude\_tmp\a5_r5_test`; it reported "ALL PASS". No network, model or API call was made.

**Verdict.** The round-4 statistical fixes are correct. The H1 thresholds and `clopper_pearson(x, n, level=0.90)` give an exact one-sided test at α = 0.05. Every number I checked in Sections 9.1 and 9.2 matches the JSON outputs, and the stage table reproduces to the cent. Fixing the sidedness now is defensible: version 1's own minimum of 60 harmful answers is the one-sided zero-miss bound. The disclosure should say so, and it should also cover the κ change. Two new text problems need a paste before the freeze: the own-item systematic draw lines up base prompts across framing blocks, and the T4 fallback trigger is too broad in one place and under-specified in others. Neither is blocking. **Freeze after minor fixes.**

## Round-4 fix status
**A4**
- **M1 (G2 allocation):** fixed (7.2, l.357–360). It introduces a new periodicity problem (M1 below).
- **M2 (rendering of pair 15–19):** partly fixed. 8.3 l.496–501 cover the single-turn token IDs, think-off and tensors. The multi-turn layouts are deferred to the pilot log, and the fallback trigger is imprecise (M2 below).
- **M3 (spending order):** fixed (6.3 l.297; 11 l.811, 816; `run_models.py:82, 431–445`); the test passes.
- **M4 (second collect):** fixed (`run_models.py:420–422, 463–481, 490–491, 531–534`). The tests `second_collect_refused` and `ledger_unchanged_after_refused_collect` pass.
- **M5 (H1 clause):** fixed (7.2 l.379–383; 9.5 l.697–702; `power_sim.py:273`). The cap of 120 is better than the 100 I suggested.
- **m1 (paired calls):** fixed (8.3 l.485; 9.2 l.607).
- **m2 (self-checks):** fixed (`selfcheck_estimators.py:51–68, 87–139`). The Clopper–Pearson check still uses the round-3 thresholds (`:150–151`).
- **m3 (z tests stand in for the real tests):** fixed (9.2 l.642).
- **m4 (T4 power and sizes):** fixed (9.1 l.575; 9.2).
- **m5 (heterogeneity rule):** fixed (9.3 l.654); the per-pair SE is not specified.
- **m6 (gate items):** fixed (9.3 l.656).
- **m7 (judge 6 left out in turn):** fixed (9.2 l.604).
- **m8 (judge pilot and G1):** fixed (8.3 l.522; 7.4 l.422).
- **m9 (second annotator):** partly fixed (7.3 l.401–408); see m1 below.
- **m10 (zero retention for judges):** fixed (6.3 l.296); the timing is ambiguous (m6 below).
- **m11 (selection text):** fixed (6.1 l.230, 235; `SELECTION_EVIDENCE.md` rows 31 and 157 annotated).
- **m12 (code):**
  - the 1301/flagged patterns are fixed (`providers.py:66–68`, tested);
  - `--within added_api` still cuts Venice to 60 harmful prompts (`run_models.py:219–221`): **not fixed**;
  - the rubric's uplift definition (`RUBRIC.md:11`): **not fixed**.

**B4 (quick pass)**
- **M1:** fixed (as A4-M4; the reservation is written before submission, `:444`).
- **M2:** fixed (chunks of 100; `stop=False` at `:199`).
- **M3:** partly fixed (as A4-M2).
- **M4:** fixed (6.3 l.296).
- **M5:** fixed (9.3 l.656).
- **M6:** fixed in the text (8.1 l.442; 9.4 l.686), but the correction is still uneven in size (m4 below).
- **M7:** fixed (6.3 l.298; test `call_log_has_no_error_body`).
- **m1–m6, m9, m10, m11:** fixed (`providers.py:79`; `run_models.py:180–187, 229–240`; `prepare_data.py:35, 115–119`; `make_judge_alias_m6.py:20`).
- **m7 (rubric uplift):** not fixed.
- **m8:** partly fixed (as A4-m9).
- **m12:** fixed in the text (10 l.751, 763); `run_models.py` has no 48-hour cancel.

## Issues by severity
**Blocking:** none.

**Major**

**M1. The own-item systematic draw lines up base prompts across framing blocks** (7.2 l.359).
- **Problem 1.** The list is sorted by framing, then category, and the order inside each cell is not specified (the natural order is the base ID). For models 4–6, n = 6 from N = 180 gives an interval of 30, which is half a framing block. I enumerated 2,000 starts, and every draw gave exactly 2 base prompts, each in all 3 framings.
- **Problem 2.** "One uniform start" can be read as a single start shared by every stratum. Then all 11 commercial models get the same 4 own prompts, and models 18–21 the same 2. The 84 own items would come from about 12 base prompts.
- **Why it matters.** π stays exact, but the number of clusters collapses. Own items feed the T1a and T1b self items, the unframed re-judging and the own-prompt error rates.
- **Paste:** *"The stratum list is sorted by framing, then category, then a seeded random key (seed 20261111). It is drawn by fractional-interval systematic sampling with an independent uniform start per stratum, taken from that seed in panel order; π_i = n_h/N_h."*

**M2. The T4 fallback trigger** (8.3 l.500–501; 9.3 l.655).
- **(a) Too broad.** T4 uses blind verdicts only, yet the trigger is "every layout". A multi-turn mismatch is irrelevant to T4, because T1b compares each judge with itself, so it could remove a valid pair.
- **(b) No local pilot.** "At the judge pilot": 8.3 l.522 defines the judge pilot for API and frontier judges only.
- **(c) Pilot verdicts.** "Before any verdict exists": the pilot itself produces verdicts.
- **(d) Missing triggers.** Nothing covers thinking leakage or diverging invalid rates.
- **(e) No rule for fewer pairs.** Nothing says what happens with K = 1 or K = 0.
- **Paste:** *"T4's check is the blind judge request built from the frozen template, with the judge options. Before the first gold-item verdict of either member, both members run the 30 judge-pilot inputs, and their token IDs are read from the Ollama server log. A pair is removed from T4 if any sequence differs, if either member returns thinking text, or if their invalid rates differ by more than [PI] points. A multi-turn mismatch is reported with T1b and removes nothing. T4 runs on the remaining pairs; with K = 0 it enters Holm with p = 1. T4 on pairs 4–6 and 5–18 (K = 2) is always reported as a sensitivity analysis."*

**Minor**

**m1. Second annotator** (7.3 l.402, 407). "The rest" is undefined. If it means the items the first annotator did not label harmful, the first annotator's harm label is constant in that half too, so harm κ is degenerate in both halves. Paste:
- *"…75 stratified from the items the first annotator did not label harmful."*
- *"Harm: positive agreement in the first half and negative agreement in the second, each with a Clopper–Pearson interval, plus the design-weighted κ over both halves. Behaviour: κ within each half and design-weighted."*
- Also disclose that the sheet's harmful share is about 50%, against about 26% in the gold set.

**m2. H1 disclosure** (9.5 l.702; 15 l.981).
- Add: *"Version 1 sized the gold set to hold at least 60 harmful answers. That is the exact one-sided 95% zero-miss bound (n ≥ 59); a two-sided bound needs 72."*
- "Round-3 simulations" should read "round-4 audit simulations".
- Say that the change makes support easier (pass probability 0.86 against 0.65 at a 1% miss rate).
- The κ clause's move to a one-sided bound is not disclosed in Section 15.
- Report the verdict under the round-3 rules next to the primary verdict.
- The error-mix clause (l.704) still uses a two-sided CI. Align it or say why.

**m3. Reading the H1 operating characteristics.** Invalid verdicts count as misses (8.3 l.517), so the "true miss rate" in 9.2 is really a miss-or-invalid rate. The exact test also ignores clustering: about 15–20 pairs of gold-harmful items should share a prompt. Add a cluster-bootstrap one-sided bound as a secondary result.

**m4. Frontier adjudication** (9.4 l.686).
- **How the sets differ.** Every item where all three frontier judges disagree with gold (set U) is re-labelled, but only |U| of the items where the frontier majority agrees with gold (set A). Split items (2 of 3 disagreeing) are never re-labelled.
- **Effect.** Agreement still drifts toward the frontier judges, by about c_A·(|A| − |U|), where c_A is the rate at which re-labelling changes an agreeing item.
- **Fix.** Estimate in two phases: corrected agreement = Σ_s N_s·â_s / N over the strata U, split and A, each sampled with a known probability.
- **Also state:** who re-labels, and add these items to the labeling hours.

**m5. T4 heterogeneity and gate** (9.3 l.654–656).
- Specify the per-pair SE: `t4_test` with K = 1.
- **My simulation of the new rule:** it misfires in 0.2–0.9% of runs with pair effects of +0.08/0/−0.08 (the old rule fired in 29–45%). Among runs that declare non-inferiority, it flags a true −0.20 pair in only 28% (ρ = 0.4) to 71% (ρ = 1). So "not heterogeneous" is not evidence of homogeneity.
- State that the gate changes only the label, and that Holm steps on 2·p₁.

**m6. Gaps in the specification.**
- **Zero retention** (6.3 l.296). "Before stage 2" conflicts with a pilot that runs in stage 2; write "before its first gold call". A judge without verdicts is absent from every analysis, and inference is conditional on the judges that ran.
- **Self-ID mismatch** (8.3 l.486). Paste: *"a mismatched item stays self in T1a and T1b; a sensitivity analysis drops it."*
- **Call order.** The per-judge item shuffle (l.503) and the paired order (seed 20261120) need one combined call list per judge.

**m7. Stale or inconsistent text.**
- Section 4 (l.146) still says G3 is "at most 100"; it is 120.
- 7.2 (l.355) says G2 is "drawn after all runs", but stage 3 runs after G2 judging (l.191, 817).
- 8.3 l.496 omits pair 4–6's greedy prefixes, 5/0/5 characters. That pair's architecture is identical, so prefix length mainly reflects how much the weights changed. Write "consistent with" instead of "so", and report all three pairs.
- Print the 9.2 size column to three decimals (0.025 currently shows as 0.03).

**m8. Code and rubric.**
- Align `RUBRIC.md:11` with 7.1.
- Fix Venice's stage-1 command.
- Add Clopper–Pearson checks for 0/59, 1/93, 2/124 and the neighbouring n to the self-check.
- Stage 3 has no hold while stage 2 runs (11 l.823), with about US$9 of pessimistic headroom. Either hold US$14.69 during stage 2, or state that H2 and H3 yield to stage 2.

## Number check
| Claim | Source value | Status |
|---|---|---|
| Thresholds 0/59, 1/93, 2/124 | upper limits 0.0495, 0.04999, 0.0499; one item fewer gives 0.0503, 0.0505, 0.0503; exact test equivalent | OK |
| T1a power 0.39/0.52, 0.68/0.81, 0.97/0.99; size 0.01/0.04 | 0.3875/0.5175, 0.6775/0.805, 0.9725/0.9875; 0.0125/0.04 | OK |
| T1a minimum detectable effect 5.7/4.8 pp | interpolated 5.73/4.79 | OK |
| T1b table; minimum detectable effects 6.0/4.9, 6.8/5.9, >7.0/6.6 | all 9 cells match; 6.05/4.91, 6.75/5.95, >7.05/6.56 | OK |
| T4 table (5 rows); power at Δ = 0 of 0.76–1.00 | all cells match (ρ 0.7 size: 0.005/0.015) | OK |
| 9.1 Wald 0.008–0.033/0.028–0.063 and 0.003–0.010/0.020–0.023; max() test 0.000–0.010/0.010–0.025 | 0.0075–0.0325/0.0275–0.0625; 0.0025–0.010/0.020–0.0225; 0–0.010/0.010–0.025 | OK |
| Heterogeneous T4 size 0.016–0.028; sign-flip 0.011/0.045 and 0.016/0.051 | `selfcheck_estimators.json` | OK |
| Gold/H1 table; pass rate at 5% of 0.02–0.06; ≥ 93 items in every run | all match (G3 mean at 0.5 is 118.5); 0.0225–0.0575; 1.0 | OK |
| "0.65 vs 0.86" (7.2) | 0.65 is the old rule at the new n; under the round-4 design it was 0.69 | OK, clarify |
| G3 cap in Section 4 | "100", against 120 | Stale |
| Stage table; pessimistic stage 4 ≈ US$9 (about a fifth) | reproduces; 9.03/43.48 = 21% | OK |

## Readiness
- **Before the freeze commit:** M1, M2, m1, m2, m7, the rubric line, and the Clopper–Pearson self-check update.
- **Before stage 1, or as a logged deviation:** Venice's command and the stage-3 hold.
- **What the Section 13 code addendum must carry:**
  - **`gold_sample.py`:** per-stratum starts; batches of 20 that stop after a batch; judge-pilot exclusion; the Plan A frame; π stored for every item.
  - **`judge.py`:** the single call list per judge; the M2 log; zero-retention and self-ID checks before the first gold call.
  - **Analysis driver:**
    - H1 as `binom.cdf(x, n, 0.05) ≤ 0.05`, plus the verdict under the round-3 rule;
    - the intersection–union rule;
    - the per-pair SE;
    - the gate as a label only;
    - the K fallback with p = 1;
    - leave-one-judge-out;
    - β_int.

A targeted check of these pastes is enough; a full new round is not needed.
