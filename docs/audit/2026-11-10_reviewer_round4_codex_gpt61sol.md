# Review round 4 of protocol v2.3 (revised after round 3), by GPT-6.1 Sol

- **Date:** 10 November 2026, 14:52 to 15:01 EST. Codex CLI, model `gpt-6.1-sol`, reasoning effort xhigh, read-only sandbox, connectors off (`--disable apps`), user configuration ignored.
- **Input:** a read-only clean copy of part of the repository (`agentsControl_r15_round4`, 87 files) with no answer text, no benchmark prompt file, no label key and no secret.
- **Prompt:** `docs/audit/2026-11-10_prompt_for_codex_round4.md`.
- **Session log audit:** 30 shell commands, all inside the copy; no web action; no read outside the copy.
- **Status:** stored as returned. Its statements are claims to verify, not instructions.

---

## 1. Round-3 findings

I reviewed the revised protocol, author response, diff, changed supporting documents and samples of stored results. All access stayed inside the working directory; no files were changed, and no model or API calls were made.

**Conflict of interest:** I am model 11 of the commercial panel, from OpenAI. Findings concerning commercial scheduling, cuts, reference comparisons and safe-side reporting bear on OpenAI’s models 3, 9 and 11. The same recommendations apply across providers.

“Resolved on a condition” distinguishes an adequate specification awaiting implementation from a remaining document correction.

| Finding | Status | Assessment and deciding section |
|---|---|---|
| **R3-C1** | **Resolved** | Section 10.4 fixes the panel at the freeze and withholds confirmation if required model-22 calls remain unattempted. Sections 6.5 and 10.4 specify the ten-model branch adequately. |
| **R3-M1** | **Resolved on a condition** | The stored R-S3 results repair the previously demonstrated undercoverage for the reported quantities. However, the effective-sample-size intervals are approximate, and §§9.5/A.3 must lose their unconditional exactness/conservatism claims; the promised informative-screening validation remains required. |
| **R3-M2** | **Resolved on a condition** | A.4(f) now distinguishes observable marginals from assumed nuisance parameters and records unattainable targets explicitly. Implement and freeze that mapping before the pilot registration, as §§14.2/19.4 require. |
| **R3-M3** | **Resolved on a condition** | Sections 12.3–12.5 adequately specify adjacent challenge pairs, remaining-work cuts and protected spending. Repair the new screen/sample scheduling contradiction described below, then implement and test the safeguards before registration. |
| **R3-M4** | **Resolved** | Sections 2.3–2.4 and 6.3 correctly distinguish contrast signs, additive judge effects and unresolved judge–content confounding. Non-estimability and the secondary status of interval gates are explicit. |
| **R3-M5** | **Not resolved** | Section 9.3 correctly preserves unknown labels and seeks identification extrema, but intervals at the extrema of the **estimate** do not establish interval robustness over all assignments. Section 18.5 also retains the superseded harmful-by-default rule. |
| **R3-M6** | **Resolved on a condition** | The revised rubric supplies scope, exceptions and shared substantive guidance; §§9.6/11.1 close Part A before pilot judging. D12 and the prescribed publication/rendering checks must actually occur, with the late-recruitment branch keeping the rubric unchanged. |
| **R3-M7** | **Resolved on a condition** | Sections 8.1–8.5 and 19.4 specify the requested boundary policies, fingerprints, rendering checks and synthetic cases. These remain implementation requirements, not completed validation. |
| **R3-m1** | **Resolved on a condition** | Section 6.1 distinguishes canonical and file hashes correctly; I reproduced the file hash. Section 19.3 expands the exposure statement, but the signable D5 copy in `PI_DECISIONS.md` still needs synchronization. |
| **R3-m2** | **Resolved** | Appendix A now exposes reportability, sparse denominators, exclusions, corrected `zero` captions and the failed rerun. The revised stored-run count is 344. |
| **R3-m3** | **Resolved on a condition** | Section 8.7 clearly defines the refusal-classification endpoint, both screening targets and the matched commercial subset. Run A.4(d) and apply its interval-withholding rule before the freeze. |

## 2. Undeclared differences

**Yes: all eight differences are now declared in §17.2, and their substantive handling is adequate.**

| Difference | Revised handling |
|---|---|
| Commercial safe controls, 60→30 | Declared with reduced precision and commercial coverage acknowledged. |
| Model 22 judging all labels | Declared; frame-weighted accuracy distinguished from commercial reference-subset accuracy. |
| Fresh frame sample replacing G1/G2 | Declared, including retirement of G1 and its training role. |
| Second labels, 300/60→305/55 | Redistribution and unchanged total declared. |
| All-model common-60 comparison | Restored explicitly in §8.5 as descriptive. |
| Removal of G1 exclusion from challenge set | Explained: training material is outside the frames and no G1 labels exist. |
| Safe-side unscreened and screen-negative targets | Both stated in §8.7. |
| Crossed fixed-effects sensitivity and equal-pair summary | Explicitly withdrawn. |

The monetary illustrations in this declaration need updating or identification as historical figures; see §4 below.

## 3. Consistency

**The principal label, call and branch arithmetic reconciles.**

| Quantity | Checked value |
|---|---:|
| Eleven-model PI labels | 150 + 100 + 55 + 242 = **547** |
| Eleven-model second labels | 305 + 33 + 22 = **360** |
| Ten-model PI labels | 125 + 100 + 55 + 231 = **511** |
| Ten-model second labels | 280 + 30 + 22 = **332** |
| Judge calls: local / model 22 / commercial | **2,587 / 2,307 / 800** |
| Commercial calls with ten primary models | **780** |
| Stored R-S1 / R-S2 rows | **35 / 19** |
| Stored checks | 23 + 14 + 7 + 216 + 84 = **344** |

The ten-model challenge/reference sizes, 50/110, and unchanged 300 clusters/298 degrees of freedom are consistent. The stated seeds agree with configuration and code: frame ordering 20261110, assignment/R-S1/R-S2 20261121, labels 20261122, R-S3 20261123 and rerun 20261124.

Samples checked against JSON and generated tables include:

| Result | Stored value and protocol display |
|---|---|
| R-S1 baseline null family-wise rejection | 3.48% → **3.5%** |
| Baseline θ interval coverage | 95.01% → **95.0%** |
| R-S3 baseline harmful share | 78.635% → **78.64%** |
| Low-failure screen-negative harmful-share coverage, revised interval | 99.06% → **99.1%** |
| Low-failure harmful screen-pass coverage, revised interval | 99.85% → **99.9%** |
| Low-failure instruction-group detection interval | **9/10,000** reportable replications |
| Direct detection interval, first run / rerun | **94.27% / 94.46%**, both below their respective thresholds |

The rerun retains the sampled reference truths and changes the replication stream as stated.

The manifest’s block values sum to **$54.3421 expected and $115.6836 pessimistic**, supporting the displayed $54.34/$115.68. Subsequent cut totals have a small rounding error, detailed below.

The two-registration sequence is coherent at its controlling provisions: code and synthetic validation → pilot registration → training/Part A closure → pilot judging → allowed revisions and validation → freeze. The ten-model and flags-only branches are now recognized, though supporting copies need synchronization.

The cross-reference aid reports 465 references with no dangling section numbers. That does not catch the semantic contradictions below. Sections 14.2/19.4 generally describe missing code candidly; existing offline-test logs do not establish that the v2.3 pipeline or its revised safeguards work.

## 4. New problems

**No new critical problem found.** Three major specification issues and three minor consistency repairs remain.

### Major — The new execution order contradicts screen/sample timing

**Place:** §§7.1, 9.2, 12.3 and 13.4.

Section 12.3 performs primary harmful-frame judging in block 3, then screening and label sampling in block 4. Sections 7.1/9.2 require these operations before verdicts exist, while §13.4 puts screening and sampling before judging. The revision therefore cannot be implemented literally.

**Concrete fix:** preserve the stated spending priorities, but explicitly screen primary answers before block 3. Specify that the later label draw may occur after primary verdict generation, using only the frozen sampler’s permitted metadata and screen fields, with verdicts inaccessible to selection and human readers; align §§9.2/13.4 with that sequence.

### Major — Effective-count intervals are presented as mathematically exact

**Place:** §9.5; A.3 “Rates”; A.4 conservatism statements.

The new procedure substitutes a data-dependent, potentially fractional effective sample size into beta quantiles. This does not make the weighted, clustered statistic a binomial count. Consequently, neither “exact” nor “conservative by construction” follows, and Bonferroni alone cannot supply the asserted unconditional 95% guarantee.

The stored results show useful empirical improvement. They do not establish the stronger mathematical claim.

**Concrete fix:** describe these as approximate effective-sample-size intervals, empirically conservative in the examined scenarios. Make the propagated interval’s guarantee conditional on valid component coverage, retain the registered validation/withholding rules, and complete the already-specified informative-screening run before the freeze. This does not require adopting the previously suggested hypergeometric method.

### Major — The missing-label gate checks the wrong extrema

**Place:** §§2.4 and 9.3; implementation requirements in §19.4.

An assignment maximizing the point estimate need not maximize its upper confidence limit: assignments also change the denominator, cluster residuals and standard error. Thus checking intervals at the smallest/largest estimates, plus the two uniform assignments, does not establish that a detection statement survives every unknown-label assignment.

**Concrete fix:** retain the point-estimate identification range, but gate a decrease on the **largest upper confidence limit across admissible assignments** being below zero, including the labelled-once sensitivity analysis. Specify handling of ties, insufficient support and undefined intervals; an unsupported case must withhold the sentence. Extend the planned enumeration checks to verify this gate, not merely the point-estimate range.

### Minor — Supporting and limitation text retains superseded rules

**Place:** §18.5; `PI_DECISIONS.md` D5/D6/D8; README registration summary; rubric/packet training instructions; §18.8.

Relevant inconsistencies include:

- Section 18.5 still assigns unresolved answers harmful in the main analysis and describes PI-only adjudication, contradicting §9.3’s unknown status and joint adjudication.
- The signable D5 statement omits the expanded pilot-operation list. Pilot and training operations should also be listed separately.
- D6/D8 deadlines remain freeze-oriented in the decision file, while §19.1 requires them before training.
- README still says freeze precedes *any* confirmatory answer generation, despite retained existing answers.
- Training instructions need the §9.6 late-recruitment exception, which permits no rubric amendment.
- Section 18.8’s absolute prohibition on primary-panel cuts omits model-22 repeatability.

**Concrete fix:** synchronize these copies with the controlling revised provisions before PI signatures and packet delivery.

### Minor — The first-round reading draw is 190, not 198

**Place:** §§7.3, 13.3 and 19.2.

Ten local models contribute 180 answers. Model 22 receives only five harmful prompts per source in round 1, so its contribution under the shortage rule is ten: **190 total**. The corresponding ten-model draw is 180.

**Concrete fix:** state 190 for a complete first round with eleven models, report actual shortages, and distinguish any later draw after round 2. Update workload descriptions accordingly.

### Minor — Cut totals use prematurely rounded amounts

**Place:** §§1, 12.2, 12.4 and D12/D14 summaries.

Summing stored block values and rounding only the final totals gives:

| After cut | Correct total |
|---|---:|
| 1 | $113.69 |
| 2 | **$107.80** |
| 3 | **$101.90** |
| 4 | **$98.95** |

**Concrete fix:** generate cumulative totals from unrounded values. Also update §17.2’s old $5.09/$0.40 illustrations or label them as preceding the rubric expansion. Three cuts still satisfy the $105 ceiling.

## 5. Verdict

**The core is ready for the PI’s decisions, and another design round is unnecessary.** The revised fixed-panel rule resolves the critical objection.

Correct the three major specifications above before treating the document as the final implementation contract. Synchronize the supporting copies and generated numbers alongside those corrections.

Registration remains conditional on the already-listed code repairs, complete synthetic pipeline, adverse-path tests and pre-freeze simulations. The next substantive review should inspect that implementation and its outputs.

**Could not check:**

- Unwritten runners, template, analysis pipeline and simulation options.
- Execution or independent reproduction of simulations and offline tests; Python was unavailable.
- Prices against the underlying provider snapshot, actual service availability, retention settings or institutional decisions.
- Literature was not rechecked; this review makes no new literature claims.