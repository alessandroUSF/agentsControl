# Audit D: Codex, GPT-6.1 Sol, reasoning effort "ultra" (8 November 2026)

This independent cross-family review ran in the author's Codex desktop app, session 01a1bcb1-ebe4-7df1-bd64-988317addcda.

- **Input:** a read-only clean copy of the repository (`E:\claude\_audit_copy\agentsControl`). It held no model answers, no benchmark prompt files, no .env and no other audit reports.
- **Instructions:** `prompt_for_codex_audit.md`, which bans network access, so no literature search was made.
- **Text:** the final message is reproduced as returned. File links point to the audit copy.

---

**Verdict**

The protocol needs substantial revision before registration and execution. Its crossed design can estimate a self-authorship association, but the current measurement, validation and correction procedures do not support the main reliability claims. The implementation also differs materially from version 2. The strongest improvement would be a larger, independently double-annotated, adjudicated gold set balanced across authors and prompts, with an untouched evaluation subset.

This audit used local reads and arithmetic only; no network requests, model runs or file edits were performed.

**Critical issues**

1. **§§7–9: the harmfulness endpoint is inconsistent.**  
   The proposed missed-harmful definition—judge says no **or labels the answer a refusal**—incorrectly penalizes `partial_refusal` with correctly detected harmful content. The rubric explicitly permits that combination. Meanwhile, the judge prompts require assistance causing “serious harm,” whereas §7 asks whether assistance meaningfully helps carry out a harmful request ([src/judge.py:78](E:/claude/_audit_copy/agentsControl/src/judge.py:78)). These differences can change judge rankings and harmful-compliance estimates.

   **Fix:** freeze an independent harmful-content variable, including actionability, ineffective instructions, fiction, benign alternatives and uncertainty. Score behaviour and harmfulness separately. Define how invalid outputs affect diagnostic scores and operational rate estimation.

2. **§§7–9: harmful prompts are being counted as harmful answers.**  
   The approximately 109 answers to harmful prompts include refusals and harmless responses. They do not establish the denominator for harmful-content sensitivity. The sampler actually selects `expected="refuse"` ([src/gold_sample.py:71](E:/claude/_audit_copy/agentsControl/src/gold_sample.py:71)).

   With zero misses, at least **59 independent genuinely harmful answers** are needed for a one-sided 95% upper miss-rate bound below 5%; a two-sided 95% interval requires 72. Even if all 109 answers were harmful, the one-sided test rejects a 5% miss rate only with at most one miss, giving approximately **70.3% power** when the true rate is 1%, before clustering or selection.

   **Fix:** power the study on actual harmful positives; expand sampling through a prespecified, independently screened frame. Record inclusion probabilities. Replace observed miss-rate eligibility with a confidence-bound rule and specify what happens if nobody qualifies.

3. **§§8.3–9: validation does not establish the final instrument’s calibration.**  
   Cross-validation must rebuild rankings, jury membership, arbitration, eligibility and developer-specific replacements entirely within training folds. It must evaluate the **recused deployment procedure**, including fallback judges. Group all answers and framing variants of the same underlying prompt together; model/source stratification alone leaks prompt information. Some proposed strata contain fewer than five items, preventing literal five-fold stratification.

   Out-of-fold performance estimates the selection procedure trained on 80% of gold, not independently the final all-gold winner. Furthermore, recusal changes the instrument by respondent. A pooled sensitivity/specificity correction need not transfer across authors, sources or framings.

   **Fix:** use grouped nested validation for comparisons and an untouched, representative holdout for the locked final instrument. Calibrate each binary endpoint under the actual deployment rule; pool strata only with justified transportability assumptions.

4. **§§7–8: implementation can systematically distort the main outcomes.**

   - Harmfulness disagreements do not trigger arbitration; matching behaviour labels cause Agent A’s harmfulness answer to prevail ([src/judge.py:192](E:/claude/_audit_copy/agentsControl/src/judge.py:192), [src/judge.py:236](E:/claude/_audit_copy/agentsControl/src/judge.py:236)).
   - Judges receive clipped answers, while humans receive full answers ([src/judge.py:145](E:/claude/_audit_copy/agentsControl/src/judge.py:145), [src/judge.py:203](E:/claude/_audit_copy/agentsControl/src/judge.py:203), [src/gold_sample.py:98](E:/claude/_audit_copy/agentsControl/src/gold_sample.py:98)). Omitted harmful content and author-dependent answer length can manufacture errors and apparent self effects.
   - Failures remain eligible for repeated reruns and unresolved cases disappear from merged verdicts, contradicting the fixed retry and invalid-as-error policy ([src/judge.py:187](E:/claude/_audit_copy/agentsControl/src/judge.py:187), [src/judge.py:233](E:/claude/_audit_copy/agentsControl/src/judge.py:233)).
   - The human sheet lacks a harmful-content column ([src/gold_sample.py:94](E:/claude/_audit_copy/agentsControl/src/gold_sample.py:94)).

   **Fix:** arbitrate either-field disagreements, provide identical complete evidence, retain every sampled item, enforce a fixed attempt policy, and implement the frozen annotation schema before labeling.

**Major issues**

5. **§9, RQ2: estimable association, limited interpretation.**  
   One self-judgment per item does not make the diagonal effect unidentified: crossed judge and item effects provide comparisons. However, random intercepts control skill and difficulty only under their assumptions. Unequal author exposure and judge-specific competence by content can distort the estimate. Arbitrary judge–author affinities cannot be separated from self-authorship without additional assumptions.

   **Fix:** use judge/item fixed effects for this finite panel, assess judge-by-class/source heterogeneity and varying self effects, and report a conditional self-authorship association. A recognition probe alone does not separate recognition from preference causally. Within-item permutation is unjustified because judges are nonexchangeable; use a prespecified null-model bootstrap.

   The rough power arithmetic is:
   \[
   SE=\sqrt{.1(.9)(1/352+1/8800)}=.01631.
   \]
   The usual 80%-power approximation gives **4.57 percentage points** unadjusted, or **5.45 points** at Holm’s first threshold, before clustering and heterogeneity. Simulate the final design.

6. **§7: the gold distribution and reference labels are inadequate for population claims.**  
   G1 contributes 150 items from three authors; most other authors contribute ten. Unweighted metrics describe this chosen mixture, not equal-author performance or the approximately 21,560-answer corpus. Oversampling can change sensitivity too, through changes in the kinds of positive answers included.

   **Fix:** specify separate comparison and deployment targets. Calculate weighted confusion totals using known inclusion probabilities, then derive kappa and conditional rates. Document both sampling stages and excluded failures.

   Independent second annotation should be required for a substantial stratified subset, with adjudication and disagreements retained. Repeated labeling by one person measures repeatability, not an agreement ceiling. Develop edge cases outside confirmatory gold; [labels/RUBRIC.md:19](E:/claude/_audit_copy/agentsControl/labels/RUBRIC.md:19) currently allows rubric changes after 30 labels.

7. **§§3.1,9: confirmatory hypotheses remain insufficiently specified.**

   - **H1:** define confidence-bound decisions for kappa and harmful misses; operationalize “most errors,” whose categories currently overlap.
   - **H2:** enumerate contrasts and distinguish pooled claims from model-specific claims.
   - **H3:** retain the five original comparisons and give “almost none” a numerical threshold.
   - **T3:** choose accuracy or kappa consistently; freeze the selection algorithm, three-way ties, invalid votes and separate harm voting.
   - **T4:** four checkpoint comparisons, sensitivity, specificity and a pooled model do not define one test. Nonsignificance cannot establish preserved detection; that requires a prespecified noninferiority margin.

   **Fix:** list every primary estimand, null, statistic and multiplicity family. Holm across T1–T4 works only once each produces one defined primary p-value. Explain separate families for headline claims. Treat the G1 interim as descriptive or specify sequential error control.

   T2 has approximately **14 eligible v5-scored judges**, including Granite. An optimistic independent-model Fisher approximation requires correlation around **0.69** for 80% power, or **0.76** at the first Holm threshold. Developer dependence further limits information.

8. **§9: bootstrap and correction uncertainty are underspecified.**  
   Resampling fixed out-of-fold predictions omits selection instability. Prompt IDs that distinguish framings do not capture the underlying dependence.

   **Fix:** resample semantic base-prompt clusters, retain paired predictions across judges/respondents, respect sampling strata and weights, and repeat selection, recusal and calibration when estimating uncertainty for the whole procedure. If generalizing beyond these judges, include judge/developer uncertainty. McNemar tests on instrument labels test noisy observed labels, not automatically corrected true refusal differences.

9. **§6: selection mostly reproduces, but provenance and scope need repair.**  
   The OpenRouter developer shares and capped capability leaders match the snapshot; the three local file-size claims are supported. These purposive rules define this panel, not a representative model population.

   The snapshot does not substantiate the reported uncensored Ollama download rankings or all matched-build provenance. Freeze candidate lists, exclusions, dates, base checkpoints, quantization and templates. File size alone does not establish runtime VRAM fit.

   Granite has v5 score **5.0983** ([aa_models_raw.json:7519](E:/claude/_audit_copy/agentsControl/data/selection/2026-11-08/aa_models_raw.json:7519)); its displayed proxy 36.4 cannot enter the same correlation. Freeze exact T2 IDs and covariates. T4 compares particular released checkpoints; differing tuning, templates and quantization prevent a general causal conclusion about refusal removal.

10. **§8: judge comparisons need stronger controls and baselines.**  
    Add a purpose-built safety classifier such as WildGuard or Llama Guard, with task-compatible outputs. Refusal phrases cannot establish harmfulness; the current keyword code emits signals without a fixed classification rule ([src/judge.py:60](E:/claude/_audit_copy/agentsControl/src/judge.py:60)).

    **Fix:** freeze temperature, supported reasoning effort, token/context budgets, templates, parser, seeds, provider routing and versions. Report unsupported settings explicitly. Treat embedded instructions in evaluated text as untrusted data. Predefine a limited prompt-sensitivity check.

11. **§§11,13: amendment transparency is incomplete until the whole design is frozen.**  
    Selection after seeing capability rankings can be disclosed prospectively, but cannot be described as rules fixed before seeing those rankings. H1’s replacement of a specified pipeline with a selected instrument is substantive. G1 judge comparisons depend on its three-author distribution; §11’s contrary justification is incorrect.

    **Fix:** publish a timestamped amendment preserving v1 and the superseded amendment. Freeze own prompts, expected labels, framings, rubric, sampling, hypotheses, settings, folds and analysis before any interim judge results are viewed. Record sealed-output hashes and access history. Subsequent changes require dated deviations.

12. **§§5,8,10: execution and governance remain unfinished.**  
    The code supports the old Ollama pipeline ([src/judge.py:148](E:/claude/_audit_copy/agentsControl/src/judge.py:148)); its arbiter repeats Agent A’s model ([config/judge.json:4](E:/claude/_audit_copy/agentsControl/config/judge.json:4)). Venice’s harmful-generation exception is absent ([src/providers.py:172](E:/claude/_audit_copy/agentsControl/src/providers.py:172)). Remote compatible APIs do not enforce approved research-key names ([src/providers.py:111](E:/claude/_audit_copy/agentsControl/src/providers.py:111)).

    **Fix:** complete and locally verify the frozen implementation before substantive use. Separately document applicable dated provider terms, actual routing, retention/training settings, access restrictions and deletion plans. Research keys and a successful pilot do not establish permission. Obtain institutional determination rather than categorically declaring human-subject status. Review releases by actual content, including answers to safe prompts.

**Minor issues**

§§6,8,12: log checkpoint digests, quantization, templates and configuration hashes; current records mainly identify model names and dates ([src/run_models.py:182](E:/claude/_audit_copy/agentsControl/src/run_models.py:182)). Validate Boolean types rather than coercing strings ([src/judge.py:163](E:/claude/_audit_copy/agentsControl/src/judge.py:163)). Implement the promised item shuffle and 30-word reason limit. Update stale README/config descriptions and fill the missing LFM proxy value, approximately 29.1.

**Novelty assessment**

Generic judge bias, self-favouring, juries and refusal-direction removal are established by the protocol’s Zheng, Panickssery, Verga and Arditi references. Safety-classifier validation is also established: add **HarmBench** (Mazeika et al., 2024), **WildGuard** (Han et al., 2024), **StrongREJECT** (Souly et al., 2024), and **Llama Guard** (Inan et al., 2023). Kim and Zhao remain **[unsure]** here; verify their existence and claims, and verify Ward’s relevance. No literature search was performed under the no-network rule.

Potential novelty is a validated safety-specific self/sibling error matrix and recusal-aware deployment calibration. “First” remains unsupported.

Static benign classification does not validate strategic untrusted monitoring. Self-judging accuracy is neither necessary nor sufficient for secure AI control; sabotage, adaptation and collusion are absent.

Reviewers will first challenge the gold standard, positive-harm denominator and self-effect interpretation. A safety/evaluation workshop is the most realistic initial target; Findings or TMLR becomes more plausible after stronger validation and a focused novel result. Strong main-track publication needs substantially stronger evidence.

**Answers to Section 15**

1. **Core design:** association identifiable under modeling assumptions; causal self-preference is not.
2. **Selection:** grouped cross-validation, plus untouched final validation; recusal alone is insufficient.
3. **Gold:** inadequate for several claims; increase genuine harmful positives and independent annotation.
4. **Models:** broadly coherent purposive panel; repair provenance and score handling.
5. **Settings:** freeze and log supported settings.
6. **Classifier:** yes, strongly recommended.
7. **Tests:** retain only precisely defined primaries; distinguish difference from noninferiority.
8. **Change log:** promising disclosure, but publish and freeze the complete amendment before results.
9. **Ethics:** operational governance, terms documentation, institutional determination and content-based release review.
10. **Publishability:** strengthen the adjudicated gold corpus and focus on safety-specific error structure.

**Recommended paste-ready changes**

> “The primary RQ2 estimand is an observational self-authorship association within this fixed judge panel, conditional on judge and item effects. It does not identify causal preference, recognition, collusion, or control-protocol safety.”

\[
\operatorname{logit}P(C_{ji}=1)=
\alpha_j+\delta_i+
\beta_{\rm self}\mathbf1(j=a_i)+
\beta_{\rm sibling}\mathbf1(j\ne a_i,\ d_j=d_{a_i}).
\]

> “Harmfulness is annotated independently of refusal behaviour. A harmful response remains harmful when accompanied by a refusal or disclaimer. Invalid judgments remain in denominators under a prespecified scoring policy.”

> “Comparison metrics target a prespecified author/source distribution. Deployment calibration targets the respondent corpus. Weighted confusion totals use recorded inclusion probabilities.”

For each validated deployment stratum \(g\), and separately for refusal and harmful-content endpoints:

\[
\widehat p_g=
\frac{\widehat q_g+\widehat{\mathrm{Sp}}_g-1}
{\widehat{\mathrm{Se}}_g+\widehat{\mathrm{Sp}}_g-1}.
\]

> “Correction requires transportable error rates and a denominator demonstrably separated from zero. Report unstable or out-of-range estimates transparently. Confidence intervals propagate sampling, selection and calibration uncertainty. Interim results are descriptive; final confirmatory decisions follow the frozen analysis plan.”