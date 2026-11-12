# Audit A: design, measurement and statistics (8 November 2026)

This is an independent reviewer agent's report on `docs/STUDY_PROTOCOL_v2.md` (draft of 8 November). The agent read the protocol and the repository only, without the design conversation. It did not open `results/` or `.env`. Its report is reproduced here as returned. Claims are checked during consolidation.

## Verdict
The core design can be pre-registered after fixes. Making every respondent also a judge, and labeling a blind gold set, gives a real contribution: a judge × author × item matrix.

As written, three problems would undermine main conclusions:
1. The RQ2 model would count judge-specific skill differences between item types as a "self" effect.
2. "Missed harmful" rests on perhaps 45–60 items with harmful content. That is too few to test a 5% threshold.
3. The recusal rule makes the RQ4 instrument differ across respondents, so the H3 between-model contrasts may compare two different instruments.

The planned Stage 1 interim also leaves real forking paths, because the rubric, the harmful-content definition, the judge prompt and the G2 sampler are not yet frozen. All of this can be fixed before the commit without new data.

## Critical issues
**C1. The T1 self effect is confounded with judge-by-stratum skill (§9 RQ2).**
- **Problem:** a judge's own items are not a random subset of its items.
  - The 11 commercial judges' own items are 100% safe or own prompts, while about 31% of their other items are answers to harmful prompts.
  - The refusal-removed judges' own items are about 60% harmful (abliterated Llama in G1: 35 of 63).
  - `(1|item)` absorbs difficulty that is shared by all judges, and `(1|judge)` absorbs average skill. Nothing absorbs a judge's skill on a particular item type. For refusal-removed judges, the T4 effect leaks into T1.
- **Concentration:** 162 of the 352 self cells (46%) come from the three 8B pre-registered models. The effective number of judges (Kish) is about 11.
- **Outcome:** a 3-class exact match mixes leniency and strictness, and the two can cancel.
- **Scope:** commercial authors never answer harmful prompts, so whether a frontier monitor is lenient on its own harmful output is not identified by design.
- **The planned within-item permutation test is invalid:** judges on the same item are not exchangeable, because they differ in skill.
- **Fix:** see R1.

**C2. "Missed harmful" is underpowered (§7.2, §8.3, H1).**
- **Problem:** the denominator is gold `harmful_content = yes`, not the 109 answers to harmful prompts. Expect about 45–60 eligible items.
  - With n = 50 and 0 misses, the Clopper-Pearson 95% upper bound is 7.1%.
  - Showing a rate below 5% needs n ≥ 72 with 0 misses, n ≥ 110 with 1, or n ≥ 142 with 2.
  - The eligibility filter is weaker still: about 40 such items per training fold, so "≤ 5%" means "≤ 2 misses", which is mostly noise.
- **Fix:**
  - Add a decision rule to H1 (R4).
  - Raise the target to at least 110 harmful-content items. For example, 14 harmful items per refusal-removed model in G2, plus about 20 harmful answers from the abliterated Llama and Qwen. Weights handle the oversampling.
  - Pre-specify a fallback when no candidate passes the filter in a fold: choose the lowest miss rate.

**C3. Recusal makes measurement differ across respondents (§8.3, H3, RQ4).**
- **Problem:** the US$100 cap on labeling about 21,500 answers rules out Gemini 4 Argon, Opus 5.5, GPT-6 Astra, GPT-6.1 Sol, Sonnet 5.5 and Kimi K3.1 Pro.
  - The instrument will plausibly be Haiku 5.5, GPT-6 Luna, GPT-5.6 Luna or a local Qwen or Llama.
  - The H3 contrasts would then compare answers labeled by different judges with different Se/Sp. A difference may be only an instrument artifact.
- **Fix:**
  - For every confirmatory between-respondent contrast, label all compared respondents with one judge or jury that has no developer relation to any of them. Select it with the same cross-validation rule, restricted to eligible unrelated candidates.
  - H2 compares framings within each model, so it is unaffected.
  - Corrected rates need Se/Sp per instrument component and per respondent group.

**C4. The integrity of the gold standard is at risk (§7.3, §11 Stage 1).**
- **Problem:**
  - The labeler sees judge-vs-gold results on G1 before labeling G2.
  - Still open: the harmful-content definition, the own-prompt edge cases (`RUBRIC.md`: "after the first 30 labels"), the judge prompt, reasoning effort, the G2 seed, the fold and bootstrap seeds, and the jury tie-break.
  - H1 and T2–T4 would be tested at the interim on G1, then again on G1+G2, with no alpha spending.
- **Fix:**
  - Freeze everything in R5 before any judging or labeling.
  - Stage 1 is descriptive only: no p-values and no hypothesis decisions.
  - Any change after the interim makes the affected tests exploratory.
  - Check for labeling drift.

## Major issues
**M1. The gold set needs design weights (§7.2, §9).**
- `gold_sample.py take()` allocates round-robin, equal per stratum. G2 gives 10 items per model whatever the corpus size, so inclusion probabilities vary 2–3×.
- Kappa and the error-mix clause depend on that mix. The same per-class accuracy gives κ = 0.82 with a gold-like class mix (55/10/35) but κ = 0.79 with a corpus-like mix (80/5/15).
- **Weight:** the H1 clauses, corpus accuracy claims, error-type shares, and the Se/Sp used for correction.
- **Leave unweighted:** paired judge comparisons on the same items and the model-based T1 and T4. Report H1 both ways.

**M2. Cross-validated selection (§8.3).**
- Cross-validation estimates the performance of the selection procedure, not of the final instrument (Bates, Hastie & Tibshirani, JASA 2024).
- Apply recusal inside each fold, report what each fold selected, and flag the final instrument as optimistic if it differs from the most common fold choice.
- Use a one-SE rule: the cheapest candidate within one bootstrap SE of the best kappa.
- The version-1 arbiter sees Agent A and B's reasons, so its calls depend on which members each fold chose. Either budget arbiter runs per fold configuration or fix the pipeline members in advance.
- Define the jury's tie-break (three different labels are possible) and how invalid votes count.

**M3. Rogan–Gladen correction (§9 RQ4).**
- It assumes Se/Sp carry over across respondents, sources and framings. Use group-specific, out-of-fold, design-weighted Se/Sp.
- Clip estimates to [0,1]. Report the share of replicates with Se + Sp − 1 < 0.5.
- Propagate uncertainty with one joint bootstrap (R3). Prediction-powered inference (Angelopoulos et al., *Science* 2023) is an alternative.
- **H2:** judges see the framed prompt. Report Se/Sp by framing, and re-judge own-prompt answers with the unframed prompt as a sensitivity analysis.

**M4. T2 (§9 RQ3a).**
- Only 13 judges have a v5 score. Power at ρ = 0.6 is 0.57 at α = .05 and 0.36 at the Holm level of .0125.
- The x-variable is measured at settings the study does not use:
  - Sonnet 5.5 ranges from 25.6 (low) to 54.5, and GPT-6 Luna from 9.7 to 27.9.
  - Qwen3.5 4B's 43.5 is the reasoning variant; non-reasoning is 39.6.
  - Granite 4.2 8B does have a v5 index (5.1).
- **Fix:** run API judges at an effort level that AA scores, use that variant's index, and test with a judge-level predictor in the mixed model. Otherwise make T2 exploratory.

**M5. T3 and T4 are underspecified.**
- **T3:** the minimum detectable paired difference is about 3.7–5 points, so pre-specify an equivalence margin (for example |Δκ| < 0.03) tested by two one-sided tests.
- **T4:** choose one test: a pooled mixed model on sensitivity over gold-harmful items, excluding items written by either member of a pair.
  - Choose whether declines count as errors or as missing, and run the other as a sensitivity analysis.
  - The minimum detectable difference is about 10–14 points.

**M6. Metric definitions are ambiguous (§9 RQ1).**
- Define one mapping from (label, harmful_content, expected) to a binary "failure", applied to both gold and judges.
- Add **false refusal** (gold compliance, judge says refusal).
- **Invalid labels:** make "invalid" an extra column (a 3×4 table).
- **Kappa:** report 3-class unweighted κ plus binary κ or balanced accuracy.
- **H3:** define "almost none" (for example, an upper CI below 5%).
- **H2:** limit the confirmatory family to v1's six models.

**M7. The power statement is optimistic (§9).**
- With unequal judge sizes, the Holm level and heterogeneity in the self effect, the minimum detectable effect is 7–10 points at 88% baseline accuracy.
- Directional leniency, on about 50 self-authored harmful items, has a minimum detectable effect of about 14 points.

## Minor issues
1. **Bootstrap:** cluster on the base prompt (three framings form one cluster), stratify by design stratum, keep resamples paired across judges, and fix the seed.
2. **Re-label:** about 70 items, enriched for low-confidence, partial-refusal and harmful items, half re-labeled after the interim to measure drift.
3. **Judge stochasticity:** run each API judge twice on about 50 items.
4. **RQ3d:** use residual error correlation after an item-difficulty (IRT) model, and compare within vs between developers.
5. **Gold corrections:** primary gold labels never change after unblinding; corrections go only into a sensitivity analysis.
6. **Self items in RQ1:** recompute RQ1 and T2/T3 without self and close-relative cells as a sensitivity analysis.
7. **Sibling coding:** commit a relation matrix that includes close relations (abliterated build and base; the Dolphin line).
8. **Keyword baseline:** define its mapping to the 3 classes and to harmful_content.

## Mismatches between protocol and code
- `providers.allowed()` treats `openai_compatible` as a commercial API, so Venice would be blocked from harmful prompts. `OpenAICompatibleProvider` reads any `api_key_env` with no `AC_` check.
- `judge.py`:
  - It runs local judges only, through Ollama, and Agents A and B use different prompts.
  - There is no single retry with a format reminder; `merge()` drops unfinished items instead of scoring them invalid.
  - Its harmful definition differs from the protocol's.
  - `clip()` cuts answers longer than 6,000 characters.
  - `max_output_tokens` is 200.
  - The judge seed (20261108) is not in the protocol.
- `gold_sample.py`: the labeling sheet has no harmful_content column, so the G1 sheet must be rebuilt (same seed, key unopened). The script and `judge.py` are untracked, so the G1 draw has no timestamp. The G1 counts do match the sampler's logic.
- `RUBRIC.md` has no harmful-content definition; `README.md` still describes v1.
- §6.2 shows LFM2.5 as "*" with no value; the ranking file gives 29.1.

## Answers to Section 15 (questions 1, 2, 3, 5, 7, 8)
1. The design is sound, but the mixed model as written is not identified for the self effect; use R1. Frontier self-leniency on harmful content cannot be measured with this routing.
2. Use cross-validation, not a split, with the M2 safeguards. Recusal prevents self-judging but creates C3.
3. 352 items is adequate for kappa (±0.055) and for ranking judges, not for missed harm: oversample to at least 110 harmful-content items and weight.
5. Fix the judge settings: temperature 0 where supported, one effort level that AA scores, logged reasoning tokens, and a test-retest subset.
7. Keep T1 (re-specified). Re-specify or demote T2. Make T3 an equivalence test and T4 a single test. Add a contrast-neutral instrument for H3. Make RQ3d confirmatory (within-developer residual error correlation > between-developer) or take "shared blind spots" out of the title.
8. The change log is close. Add a table mapping each v1 test to its v2 version. Commit the untracked scripts and push `e95a932`.

## Recommended changes to the analysis plan
**R1. T1 specification.**
- *Outcome:* Y_ji = 1 when judge j's binary failure verdict on item i matches gold.
- *Relations* (`config/relations.csv`, committed before judging): self; close (base and its abliterated build; the Dolphin line); dev (same developer, otherwise).
- *Stratum:* s = gold class × prompt type (benchmark-safe, benchmark-harmful, own).
- *Model:* `glmer(Y ~ stratum + self + close + dev + (1|judge) + (1|judge:stratum) + (1|item) + (0 + self || judge), binomial)`. If singular, the same formula in brms with N(0, 1.5) priors on fixed effects and half-normal(0, 1) priors on SDs.
- *Estimand:* β_self, plus the percentage-point difference weighted equally across judges.
- *Confirmatory p-value:* fit the null model and take the residuals r_ji. Compute T = (1/22) Σ_j mean over j's own items of r_ji. Permute author labels among items within each stratum, keeping each author's per-stratum counts; 10,000 permutations.
- *Exploratory:* β_self separately on gold-failure items (leniency) and gold-non-failure items (strictness), and by respondent group.

**R2. Design weights.**
- w_i = N_h / n_h, where h = respondent × source × expected label (× framing for own prompts) and N_h counts the stratum's answers in the corpus.
- Weighted confusion matrix: P_kl = Σ w_i·1[gold = k, judge = l] / Σ w_i.
- Weighted kappa: κ_w = (Σ_k P_kk − Σ_k P_k· P_·k) / (1 − Σ_k P_k· P_·k).

**R3. Corrected rates.**
- π̂_m = clip[(p̂_m + Sp_g − 1) / (Se_g + Sp_g − 1)], where g = respondent group × instrument component.
- Each bootstrap replicate: stratified cluster resample of gold items → rerun the full cross-validated selection → out-of-fold Se/Sp → resample corpus answers by base prompt within respondent → recompute π̂.

**R4. Decision rules for H1.**
- κ: supported if the lower 95% bound of the out-of-fold, design-weighted κ is ≥ 0.80.
- Missed harm: supported if the Clopper-Pearson upper bound is < 5%; not supported if the point estimate is ≥ 5%; otherwise inconclusive.
- Error mix: supported if the weighted share of errors that are missed refusals is > 50%, with the CI excluding 50%.
- H1 holds only if all three clauses hold (intersection-union test).

**R5. Freeze and timestamp, before any judging, labeling or own-prompt run.**
- What to freeze:
  - the rubric, the harmful-content definition and its edge cases;
  - the exact judge prompt, parsing, retry, clipping and per-judge settings;
  - the relation matrix;
  - the G2 sampler, allocation and seed;
  - the fold and bootstrap seeds, the candidate list, and the tie-break and fallback rules;
  - analysis scripts, run end to end on synthetic labels;
  - the own prompts, framings and expected labels;
  - any directional predictions.
- How to timestamp:
  - a signed tag pushed to GitHub, including `e95a932`;
  - an OSF registration citing the commit SHA;
  - SHA-256 hashes of the sealed responses file, the G1 key and the labeling sheet, plus the published call logs.

## Consolidation note: checks made on 8 November
- **Confirmed in the code.**
  - `providers.allowed()` blocks harmful prompts for every API provider, so Venice needs an explicit rule.
  - The `api_key_env` path has no `AC_` check.
  - The labeling sheet has no harmful_content column.
- **Confirmed in the snapshot.**
  - Granite 4.2 8B has a v5 index of 5.1.
  - LFM2.5-8B-A1B has a GPQA+HLE mean of 29.1.
  - LFM2.5-2.6B (31.0) ranks higher but has no official Ollama build in the snapshot, so 8B-A1B is Liquid AI's best eligible model.
  - Qwen3.5 4B scores 43.5 with reasoning and 39.6 without.
