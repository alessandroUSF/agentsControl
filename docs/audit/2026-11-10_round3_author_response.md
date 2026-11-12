# Author's response to review round 3 (protocol v2.3)

- **Report answered:** `docs/audit/2026-11-10_reviewer_round3_codex_gpt61sol.md` (GPT-6.1 Sol, 10 November 2026).
- **Verdict of the report:** a defensible core, not ready for registration as written. One critical issue, seven major, three minor, eight undeclared differences from round 2.
- **What this response covers:** every finding, with what changed and where. The revised text is protocol v2.3 "revised after review round 3; draft for review round 4". Section numbers refer to it.
- **Conflicts of interest.** The reviewer is model 11 of the commercial panel. The drafting assistant comes from the developer of models 1 and 2. Both are disclosed in Section 17.3.
- **Nothing is committed or registered.** All changes are local and wait for the PI.

## 1. Findings of section 6

| Finding | What changed | Where |
|---|---|---|
| R3-C1: a choice of the panel after the freeze does not keep the confirmatory tests valid | The primary panel is chosen once, at the freeze, as decision D13 (eleven models, or the ten local models) and never changes. The ten-model branch is complete: control assignment, quotas, challenge set of 50, reference subset of 110, cost, simulations. If the eleven models are registered and calls of model 22 are missing at the analysis lock, the confirmatory conclusions are withheld and the rest is descriptive | 6.5, 10.4, 14.4, 18.2, 19.1; Appendix A.4 run (g) |
| R3-M1: registered reference intervals fail when events are rare (64.9% and 64.4%) | Rates: exact Clopper–Pearson interval on an effective number of answers. Share of harmful answers that are screen-positive: interval propagated from two 97.5% exact intervals (Bonferroni). Changes: cluster ratio interval with a minimum support of 20 and no interval at zero variance. Counts beside every quantity. Rerun with 10,000 replications and one million reference clusters: the exact intervals cover 96.7% to 100%; every registered interval passes its check | 7.4, 9.5; Appendix A.3, A.4 |
| R3-M2: the pilot calibration is not identified and sometimes impossible | The pilot scenario is replaced by pilot planning scenarios: they reproduce the observable screen and blind-flag marginals where feasible, over a registered grid of three screen assumptions. Harm prevalence, screen accuracy and sensitivity stay assumed. Unattainable targets are reported, never clipped silently. The mapping script, the grid and the screen worksheet are fixed with the pilot registration | 8.4, 13.3; Appendix A.4 run (f); 19.4 |
| R3-M3: scheduling defeats pairing and threatens protected work | Block 7 holds both presentations of each challenge answer, adjacent, in random order; the fallback is blind-only in the same place. Cuts remove remaining work and are recounted at the time of the cut. Holds protect higher-priority blocks. The reservation is a worst-case bound (UTF-8 bytes, the larger of input and cache-write price, output cap). Pessimistic cost US$115.68 against the cap of US$110: decision D14 before the pilot registration | 12.2 to 12.5, 19.1 |
| R3-M4: claim rules contain sign and identification errors | The sentence for P2 compares presentation contrasts without a direction of change, and is followed by one of four sentences on ι_W. What each contrast removes is stated; ι_W does not identify an effect of authorship. The refusal-removed group cannot separate author from kind of refusal removal | 2.3, 2.4, 6.3, 8.5 |
| R3-M5: missing labels can support unjustified detection claims | Your replacement text is adopted. Unknown labels stay unknown; two explicit assignments and an identification range; a detection statement only if its direction survives; missing counts and weight by group and screen; welfare skipping stays unconditional | 2.4, 9.3, 9.5; rubric Part B |
| R3-M6: the common harm instrument is not stable | Part A (substance, shared with the judges) and Part B (administration). Substantive clarifications become one dated amendment of Part A, before the first judging call of the pilot. D12 is decided before the pilot registration, point by point. Your sentence on what accuracy refers to is adopted | 9.1, 9.6, 11.1, 13.4, 14.3; `labels/RUBRIC.md`; D12 |
| R3-M7: validation can miss stale results and boundary failures | Zero denominator and zero variance are separate cases: the test is not carried out, nothing is rejected, P3 is not declared. Component-specific estimability of ι_W and ι_C. Fingerprints and the rejection of incompatible resume files. The code repairs of your section 5G are listed. Synthetic tests for empty cells, zero variance, missing control support, oversized contexts and reservation overruns. A rare-flag run | 8.1, 8.2, 8.5, 11, 14.2, 19.4; Appendix A.4 run (e) |
| R3-m1: hash and record descriptions overclaim | The canonical serialization of the control assignment is named, and both hashes are recorded. The second statement lists the scripts that touch pilot answers | 6.1, 19.3 |
| R3-m2: simulation summaries hide denominators | Replications with an interval, events, zero-variance counts, coverage over all rows next to the null rows, corrected captions for the `zero` rows (only `literal_null` is a size check), the discordance parameter explained. The check count is made by script: 344 checks under the revised rules | Appendix A |
| R3-m3: the safe-side target is ambiguous | Your endpoint text is adopted, with both targets. The commercial author-versus-control quantities use the matched subset of 30 prompts. A safe-side simulation checks the intervals | 8.7; Appendix A.4 run (d) |

## 2. Undeclared differences (section 3A)

All eight are declared in Section 17.2 with reason and consequence.
- Kept and declared: 30 commercial safe controls; model 22 on all 547 labelled answers; one fresh frame sample instead of G1 and G2; second labels 305 and 55.
- Restored: the comparison of all 22 models on the common set, as a description (Section 8.5).
- Explained: no G1 exclusion from the challenge set is needed, because no G1 label exists and no training item lies inside the frames.
- Stated: the safe-side targets (Section 8.7).
- Withdrawn explicitly: the crossed fixed-effects sensitivity of the blind verdicts and the summary over equal pairs.

## 3. Sections 4 and 5

- **Boundary details of section 4:** Section 8.1 to 8.5, as in R3-M7 above.
- **Check count (277 against 284):** the count is now made by a script from the stored result files. Under the revised table of Appendix A.4 there are 23, 14, 7, 216 and 84 checks of the five kinds: 344, none failed. The direct estimator, reported beside the registered one as a check, fell below its threshold once (94.27% against 94.35%); its second run is reported in Appendix A.4.
- **Code findings of 5G:** all listed in Section 19.4, with the file concerned. They are not yet repaired: the code is written after the PI approves the design.
- **Consistency notes of 5B:**
  - One branch for a missing second annotator: the statements that depend on labels are withdrawn (Sections 9.3, 13.4, 14.4, 18.5).
  - "Before the remaining confirmatory answers are generated" (Section 14.1).
  - An explicit pilot exception to the rule against looking at flags (Section 11.5).
  - "Never cut any primary-panel block" was already corrected: the repeatability calls of model 22 belong to cut 1 (Section 12.4).
  - The D1 switch covers the pilot rows and block 7 (Section 14.3).
  - The second statement lists the scripts that touch pilot answers (Section 19.3).
  - README: `scripts/cost_model.py` is in use; the offline statement excludes the two download commands.
  - The licence draft carries a dated note on its out-of-date parts.
- **Registration logic of 5C:** the screen revision now has a reading draw balanced by model and source, a worksheet fixed before the pilot, and mechanical rules for adding and removing phrases and for the window (Section 7.3). We did not find the phrase "outcome-independent" in the text. The firewall statement that the protocol makes is the narrow one: no change may follow an estimate of a presentation effect, and the pilot script computes none (Sections 13.1 and 14.3).
- **Human labels (5D):** nothing to change.

## 4. The PI's list (section 7)

- D6, D8, the transfer arrangements and the support contacts come before the training rounds (Section 19.1; action 14).
- D2 states its effect on answering and on judging, including the loss of the commercial contrast on harmful prompts.
- D3's assessment governs further local generation as well as paid calls.
- The PI approves in writing the missing-label rules, the access criteria and the ten-model branch with the decisions of the pilot registration (action 10), and approves Part A as closed after the training (action 14).
- The human methodological review is an action of its own before the freeze (action 15).
- The order of the actions is stated (Section 19.2). Adjudication, label lock and the release review are named actions (actions 18 and 21).
- The second annotator's commitment is stated as 24 hours of labelling, 4 hours of training items, and the discussions and adjudication on top. The reservation is no longer called a worst case until the code implements the bound (Section 12.5). D12 is no longer recommended "as written".

## 5. Literature (section 8)

Each work was checked by the author on its source page before it was added (Section 15.4 says how far):
- Chacón Menke and Tan (2025), arXiv:2503.17365.
- Weilnhammer et al. (2026), Nature Medicine 32, 3730–3740, including Extended Data Fig. 8b (four judges on 357 conversations).
- Alloula et al. (2026), arXiv:2606.07874.
- Arditi et al. (2024) already named Nina Panickssery. The refusal to claim priority is kept.

## 6. What was not changed, and why

- **The stratum-wise hypergeometric fallback** for the rates was not adopted. The exact intervals pass their checks with a wide margin, and the registered rule for a failing interval (not reported) covers any later failure.
- **R-S1 and R-S2 were not run again** to add fingerprints. Their registered-test code did not change after they were produced. The fingerprint and the fixed-DGP rerun are listed in Section 19.4 and are required for the runs before the freeze.
- **No code was repaired in this round.** The repairs are listed (Section 19.4) and wait for the PI's approval of the design.

## 7. Request for round 4

Your section 9 asked for a short targeted document check. Round 4 is asked to check that each finding above is resolved, that the eight differences are declared, and that the text is consistent. It is not asked for a redesign.
