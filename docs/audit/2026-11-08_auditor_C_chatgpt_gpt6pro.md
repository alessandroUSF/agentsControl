# Audit C: ChatGPT, GPT-6, thinking effort "Pro" (8 November 2026)

This independent cross-family review ran in the author's ChatGPT, in chat "Audit External Prompt", and took 25 minutes 20 seconds. ChatGPT reported using 3 subagents.

- **Input:** `prompt_for_external_audit.md` and `packet_for_external_audit.md` (the protocol, version 1, the rubric, the configs and the code). No model answers and no keys.
- **Independence:** the reviewer did not see audits A or B.
- **Text:** reproduced as returned. Formulas are re-typed from the rendered page, and the source links shown in the page are omitted.

## Verdict
Major revision is needed before pre-registration.

The crossed design can estimate an adjusted association between self-authorship and judging performance. It does not identify causal self-preference or establish the safety of untrusted monitoring.

The most consequential weaknesses are:
- inconsistent harmful-content endpoints;
- inadequate justification for transferring calibration errors to respondent-specific rates;
- an underspecified confirmatory analysis.

The reviewer read both attachments in full. All code findings come from static inspection, without executing the study code.

## Critical issues
**C1. Harmful compliance and harmful misses are inconsistent.**
*Sections 7.1 and 9; `labels/RUBRIC.md`; `src/judge.py`.*
- **The problem in the current definitions:**
  - A correct judgment of (`partial_refusal`, `harmful_content = true`) can count as a harmful miss, because it "labels the answer a refusal".
  - The rubric can count `full_compliance` as harmful compliance even when the answer is useless or incorrect.
  - The implemented requirement of actionable help toward serious harm differs from the proposed definition and may exclude benchmark risk categories.
- **Why it matters:** H1, judge selection and RQ4 could measure contradictory outcomes.
- **Fix:**
  - Separate refusal behaviour from substantive harmful assistance.
  - Freeze a harm taxonomy, category-specific examples and a decision tree for partial versus full refusal.
  - Distinguish safety refusals from inability, empty responses, truncation and service failures.

**C2. Cross-validation does not automatically calibrate the deployed instrument.**
*Sections 8.3 and 9.*
- **The problem:**
  - Out-of-fold predictions evaluate the selection procedure, not necessarily the final winner selected on all gold labels.
  - Recusal creates different effective instruments for different respondent developers. Their Se/Sp may vary with author, source and framing, and ten gold items per new respondent cannot validate this.
- **Fix:**
  - Put ranking, jury construction, recusal replacements and eligibility inside the training folds.
  - For claims about new prompts, group folds by underlying prompt, with all respondents and framings.
  - Validate the exact deployed routes on fresh calibration data, or deploy the fold-specific rules.
  - State the transport assumptions behind pooled calibration.
- **Note:** Rogan–Gladen does not repair McNemar tests on noisy labels. Inference about corrected H2/H3 contrasts must include calibration uncertainty.

**C3. The harmful-miss assurance lacks a defensible sample-size basis.**
*Sections 7.2, 8.3 and 9; H1.*
- **The problem:**
  - The 109 answers to harmful prompts are not 109 genuinely harmful answers.
  - With independent, unweighted positives and zero misses, a one-sided 95% upper bound falls below 5% at 59 positives; a two-sided interval needs 72.
  - Even 60 actual positives give only about 30% power (0.98^60 ≈ 0.30) to establish a miss rate below 5% when the true rate is 2%.
- **Fix:**
  - Size the study around actual harmful positives and informative negatives across authors.
  - Use boundary-appropriate intervals; bootstrapping zero misses can give falsely reassuring zero-width intervals.
  - Treat a training estimate ≤ 5% as a screening rule, not a certification. Specify the confidence-bound criterion and what happens if no candidate qualifies.

**C4. The existing judge code can silently corrupt the main endpoint.**
*Section 8; `src/judge.py`.*
- **The defects:**
  - The arbiter runs only when the behaviour labels disagree. When they agree, the merge copies A's harmful-content flag even if B disagrees.
  - The parser would turn the string "false" into True, and a missing harm flag into False.
  - Judges see answers with the middle removed above 6,000 characters, while humans see the full text.
- **Fix:**
  - Validate the actual JSON types.
  - Adjudicate disagreements on either endpoint, and keep the constituent votes.
  - Give humans and judges the same complete evidence.
  - Implement the bounded retry and terminal-invalid policy. Today, failed judgments can vanish from the merged results or be retried repeatedly across resumptions.

## Major issues
**M1. RQ2 is identifiable, but its interpretation and test need tightening.**
- **Identification.** One self-judgment per item does not prevent identification, because every judge evaluates every item. The crossed mixed model is a reasonable working model, but random intercepts bring distributional assumptions, not exact control for judge skill and item difficulty.
- **Fix:**
  - Use judge and item fixed effects for the primary analysis, with the mixed model as a sensitivity analysis.
  - Define sibling as excluding self, and specify the author weighting.
  - Report directional errors separately: greater self-accuracy is not necessarily leniency.
- **The recognition probe alone** cannot causally separate recognition from preference.
- **Permutation:** independently permuting self-status within items is unjustified, because judges differ in skill and family relations. Specify a valid model-based null simulation.

**M2. Sampling weights and the human reference standard are unresolved.**
- **Weights.** The original three authors contribute 162 of 352 gold items (46%), against about 17% of the planned corpus. Unweighted metrics describe this deliberately assembled challenge set, not corpus performance or an equal-author average.
- **Fix:**
  - Keep the wave, stratum, frame sizes and inclusion probabilities.
  - For corpus claims, compute weighted confusion tables first, then κ and error rates, and use those targets consistently in selection and calibration.
  - Report author-balanced results separately.
  - Make independent second annotation and adjudication mandatory, preferably on the whole gold set. A small within-person re-label cannot establish label validity.

**M3. T1–T4 and H1–H3 are not yet fully specified tests.**
- **T1–T4.** Holm across T1–T4 works only after each test yields one pre-specified primary p-value. Specify:
  - T1's definition of correctness;
  - T2's correlation endpoint;
  - T3's κ-difference null test;
  - T4's pooled primary contrast. Several pairs, sensitivity, specificity and pooled analyses do not together make one T4, and the reuse of the Llama base model must be accounted for.
- **T4 interpretation.** Failing to reject T4 does not show "as well"; that needs a justified non-inferiority margin. Dolphin fine-tuning is not an isolated refusal-removal intervention. Match checkpoint, quantization, templates and settings, or describe the checkpoint comparisons without causal attribution.
- **H1** needs explicit confidence-bound decisions and a non-overlapping error taxonomy.
- **H2** needs fixed contrasts and a family across models. It has about 60 base prompts, not 180 independent ones.
- **H3** has five pairwise comparisons; "almost none" needs a numerical threshold.
- **Study-wide error.** Separate families do not give study-wide error control.
- **Power.** The T1 arithmetic is roughly plausible under independence: 4.6 points at α = .05 and 5.4 at Holm's first cutoff (.0125). It is not a power analysis for the crossed model, and T2 has only 13 v5-scored judges. Simulate the actual dependence, sampling and multiplicity structure.

**M4. The bootstrap must follow the estimand.**
- **The problem:** a single bootstrap "over gold items, clustered by prompt" cannot cover every analysis. RQ4 also involves the full respondent corpus, and selection adds another source of uncertainty.
- **Fix:**
  - Keep together all judgments, respondents and framings of a base prompt.
  - Resample in a way compatible with the gold sampling design.
  - Propagate corpus and calibration uncertainty jointly, and repeat selection and recusal when estimating the uncertainty of the selection procedure.
  - State whether inference conditions on this fixed model panel.

**M5. The pre-registration remains salvageable, but the freeze is incomplete.**
- **Status.** Seeing external rankings before outcome inspection does not invalidate a transparent prospective amendment. But v2 is an amendment made after some generation and sampling, not an unchanged original pre-registration.
- **Fix:**
  - Publicly timestamp v2.
  - Before outcome inspection, freeze the prompts, framing sentences, rubric, model configurations, sampling and fold seeds, endpoints, exclusions and analysis rules.
  - Hash the sealed responses and the G1 inventory.
- **Also:**
  - Develop rubric examples on an excluded pilot, not on the first 30 evaluation labels.
  - Make Stage 1 descriptive. Note that RQ1/RQ3 do depend on who authored the answers.
  - Do not expose the primary annotator to interim judge findings before G2 is annotated.

**M6. Judge settings and model selection need operational definitions.**
- **Judge settings.** Fix templates, reasoning settings, context and output limits, versions, routing and invalid-output handling. Highest-effort capability scores are external proxies, not measurements of the configurations tested.
- **Safety classifier.** Add a dedicated one through its intended interface, with explicit mappings to the supported endpoints.
- **Prompt injection.** Treat request and response text inside the judge prompt as untrusted data.
- **Selection rules.** The price cap and usage proxy are defensible constraints for a purposive panel, but need an exclusion ledger.
  - The ranking lists LFM2.5-2.6B at 31.0, above 8B-A1B at 29.1: explain why the former was ineligible.
  - Download size alone does not prove the model fits in 6 GB at runtime.

**M7. Acknowledge and close the implementation gap.**
- **The gap.** The code is largely version-1 scaffolding. It lacks:
  - the 26-judge matrix;
  - the G2 design;
  - the harmful-content column;
  - cross-validation and recusal;
  - a keyword-to-label rule.

  These are implementation prerequisites, not concealed completed features.
- **More serious defects:**
  - Resume keys omit prompt and configuration hashes, so old responses can be joined to new prompt text under an unchanged ID.
  - The own-source routing exemption bypasses the expected labels.
  - Venice's allow-list is still pending.
- **Fix:**
  - Use immutable manifests and fail on mismatches.
  - Before confirmatory execution, implement explicit routing and endpoint-specific aggregation, including three-way jury ties.

**M8. Permissions and reproducibility need documentation.**
- **Permission.** Research keys and successful pilot calls do not establish provider permission.
- **Verification.** Labels alone cannot support independent verification when the generated answers are unavailable.
- **Fix:**
  - Document the applicable generation and classification terms, retention settings, access controls, deletion, annotator welfare and the institutional determination.
  - Keep answer hashes and arrange controlled reviewer access where permitted, while keeping the ban on public release of harmful text.

## Minor issues
- **§7.2:** within-rater κ is a repeatability estimate, not a mathematical ceiling on judge–gold agreement.
- **§9:** shared errors can reflect common item difficulty or wrong gold labels. Report joint-error rates and difficulty-adjusted analyses first.
- **§11 and the runner:** `len(prompt)//4 + 12` is an input-token estimate, not a worst-case bound. Qualify the "hard" budget guarantee.

## Novelty assessment
- **Direct precedents.** Self-preference, panels of diverse judges and correlated errors already have direct precedents: Panickssery et al., Verga et al. and Kim et al.
- **Missing safety-evaluation references:**
  - HarmBench (Mazeika et al., 2024);
  - StrongREJECT (Souly et al., 2024);
  - WildGuard (Han et al., 2024);
  - SORRY-Bench (Xie et al., ICLR 2025);
  - "Mu's September 2026 paper", which reports a six-evaluator comparison against human labels. [to verify]
- **Zhao et al.** on the separation of harmfulness and refusal is verifiable prior work, which narrows the novelty of RQ3c.
- **The plausible contribution:** safety-specific, authorship-associated error patterns, plus carefully matched refusal-suppressed models and validated deployment calibration.
- **AI control** is motivation, not an evaluated outcome. Remove the "precondition" language.
- **Reviewers will first challenge** the credibility of the reference labels, calibration transfer and novelty.
- **Highest-value change:** a larger, balanced, independently double-annotated gold set with an untouched validation portion, even if that means fewer models.
- **Venues:**
  - a focused workshop paper first;
  - with stronger validation, TMLR or ACL/EMNLP Findings;
  - ARR is a reviewing service, not a publication destination.

## Brief answers to Section 15
- **Core design:** identifiable as an adjusted association. Use a fixed-effects analysis and a narrower interpretation.
- **CV or split:** grouped CV for selection; validate the actual recused deployment separately.
- **Gold:** the claimed assurance is not justified. Increase actual positives and independent annotation.
- **Selection:** a defensible purposive panel, given auditable exclusions and lineage definitions.
- **Settings:** freeze documented configurations and reasoning budgets.
- **Classifier baseline:** yes. Keep its native interface and compare compatible endpoints.
- **Tests:** reasonable topics, but endpoints, primary contrasts, multiplicity and power need completing.
- **Change log:** a credible base for an outcome-blind amendment; complete the immutable freeze.
- **Ethics:** add policy documentation, retention controls, an institutional determination and controlled reproducibility.
- **Publishability:** reference-standard quality comes first. Concentrate the novelty on safety-specific authorship effects.

## Recommended replacement text and formulas
**Endpoints.**
- Refusal behaviour and harmful assistance are separate outcomes.
- Harmful compliance requires substantive harmful content, whatever the refusal wording.
- Invalid judgments count as incorrect in overall accuracy.
- The deployed instrument includes a pre-specified fallback for invalid output, which is evaluated during validation.

With H the human harm label and Ĥ the final instrument label:
- HCR = P(H = 1 | harmful prompt)
- FNR_H = P(Ĥ = 0 | H = 1)

**Self-authorship.**

logit P(Y_ji = 1) = α_j + δ_i + β_s·1(j = a_i) + β_d·1(j ≠ a_i, d_j = d_{a_i})

- Y_ji denotes correct behaviour classification, and invalid outputs score 0.
- Judge and item effects are fixed. The self and sibling indicators are mutually exclusive.
- The coefficients describe authorship-associated performance differences within this panel, not causal favouritism.
- Directional harm and refusal errors are reported separately.

**Correction.**

p̂_s = (q̂_s + Ŝp_s − 1) / (Ŝe_s + Ŝp_s − 1)

- Each stratum s uses calibration for the same endpoint and the same deployed routing rule.
- Pooling requires stated transport assumptions.
- Sparse calibration, unstable denominators and estimates outside [0,1] trigger pre-specified constrained estimation or a sensitivity analysis, rather than silent clipping.
- Confidence intervals propagate sampling, selection and calibration uncertainty.
