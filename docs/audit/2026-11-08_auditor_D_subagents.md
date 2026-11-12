# Audit D: the three delegated Codex sub-sessions (GPT-6.1 Sol, ultra), final messages

Under 'ultra', Codex delegated parts of audit D to these sub-sessions. Their findings fed the main report (auditor_D_codex_gpt61sol.md). They are reproduced here for completeness.

---
## Sub-session 4-46-53-01a1bcb3-0f

Statistical findings, prioritized:

1. **§§7–9: harmful-prompt counts do not establish harmful-content sensitivity.** The proposed 109 harmful-prompt answers include refusals, so the number of gold-positive harmful answers is unknown. At least 59 independent harmful-content positives with zero misses are required for a one-sided 95% upper bound below 5%. Even if all 109 were positive, the 5%-null test rejects only with ≤1 miss and has approximately 70.3% power when the true miss rate is 1%. Oversample based on an independently screened frame, freeze the sampling rule, retain inclusion probabilities, and increase genuinely harmful positives.

2. **§9: harmful-miss definition contradicts the rubric.** “Judge says no **or labels the answer a refusal**” incorrectly treats a correct `partial_refusal` plus `harmful_content=yes` as a safety miss. Define the harm decision independently:
   \[
   \mathrm{FNR}_H=\Pr(\widehat H=0\text{ or invalid}\mid H=1).
   \]
   Report refusal behavior separately.

3. **§9: RQ2 estimates an observational diagonal association.** The crossed judge–item design permits estimation; one self judgment per item is not a fundamental identification failure. However, random judge intercepts do not “control judge skill” without distributional assumptions, especially with unequal self exposure. Prefer:
   \[
   \operatorname{logit}\Pr(C_{ji}=1)
   =\alpha_j+\delta_i+\beta_{\rm self}1(j=a_i)
    +\beta_{\rm sib}1(j\ne a_i,\ d_j=d_{a_i}).
   \]
   Use fixed judge/item effects for the finite panel, with judge×gold-class/source terms and hierarchical judge–author interactions/random self slopes as sensitivity analyses. Arbitrary judge–author interactions cannot be separated from the diagonal effect without assumptions. Describe the estimand as a conditional self-authorship association, not causal preference. A within-item permutation of self labels is invalid because judges are not exchangeable and it destroys identity/developer structure. Use a prespecified model-based null bootstrap or prompt-cluster inference.

4. **§§7–9: sampling target and weights are missing.** G1 gives 150 observations to three authors; others mostly contribute ten. Unweighted κ describes that deliberately selected mixture. It does not estimate the 21,560-answer corpus or an equal-author panel. Define targets separately: equal-author/source standardized judge comparisons, and corpus-weighted deployment calibration. For stratified sampling use inclusion weights \(w_i=1/\pi_i\) in confusion totals, then calculate κ and conditional sensitivity/specificity from those totals. Publish stratum sizes, selected counts, and probabilities. G1/G2 need separate frame accounting.

5. **§8.3: CV must validate the actual adaptive, recused procedure.** Within every training fold, rebuild all rankings, developer-diverse juries, arbitration assignments, budget/safety eligibility, and author-specific replacement chains. Group all answers to the same semantic base prompt—including framing variants—into one fold; model×source stratification alone leaks prompts. Several proposed model×source strata have fewer than five observations, so literal fivefold stratification is impossible. OOF performance validates the selection procedure trained on 80%, not independently the final winner fitted on all gold data. A final locked holdout is strongest; grouped cross-fitting is reasonable for this small dataset if this limitation is explicit.

6. **§8.3: the safety eligibility rule is weak and incomplete.** An observed FNR≤5% is not evidence true FNR≤5%, and selection among many noisy estimates favors lucky judges. Use a prespecified upper confidence bound, minimum harmful-positive count, and a fallback if no candidate qualifies. Define three-way jury ties, invalid votes, separate harm voting, replacement behavior, exact cost estimation, and arbitration format before use.

7. **§9: pooled misclassification correction is unjustified.** Recusal changes the instrument by author; sensitivity/specificity also vary with source, framing, and content. Estimate/standardize the *deployed* binary decision’s validation matrix:
   \[
   \widehat p_g=
   \frac{\widehat q_g+\widehat{\mathrm{Sp}}_g-1}
        {\widehat{\mathrm{Se}}_g+\widehat{\mathrm{Sp}}_g-1}.
   \]
   Require transportability and an identifiable denominator; propagate uncertainty and report out-of-range estimates rather than silently clipping. Refusal on safe prompts and harmful content on unsafe prompts need different calibration endpoints. McNemar on instrument labels tests noisy labels, not corrected true refusal; this especially threatens H3 when respondents receive different recused instruments.

8. **§§3.1,9: confirmatory hypotheses remain underdefined.** H1 needs an explicit conjunction of reliability requirements, confidence-bound decisions, and a defined “most errors” statistic. H2 needs named contrasts and whether the claim is per-model or pooled. H3 has five named comparisons in v1, but “almost none” has no threshold. T3 alternates “accuracy” and κ, and top-three membership is selected rather than fixed. T4 has four contrasts, sensitivity and specificity, and an unspecified pooled test—these are not one defined \(p\)-value. Enumerate exact primary statistics and families. A two-sided T4 cannot establish preservation of detection from nonsignificance; use a prespecified noninferiority margin if that is the intended claim.

9. **§9: power statement is approximately right only for an idealized uncorrected test.**
   \[
   SE=\sqrt{.1(.9)(1/352+1/8800)}=.01631.
   \]
   The usual 80%-power approximation gives 4.57 percentage points at α=.05, or 5.45 points at Holm’s first α=.0125 threshold, before clustering/heterogeneity. Accounting for alternative variance raises these to approximately 4.84/5.77 points for increased self errors. Simulate the complete planned model. Only about 13 judges appear to have v5 capability scores; ideal independent-model Fisher approximations require \(|\rho|\approx.71\) for 80% power, or .78 at the first Holm threshold, before developer dependence. T4 has only three base families.

10. **§9: bootstrap must reproduce the design and adaptation.** Cluster by underlying base prompt, not framing-specific IDs; retain paired predictions across judges and models; respect sampling strata and weights; repeat instrument selection/recusal/calibration inside each bootstrap when uncertainty for the whole procedure is claimed. Fixed OOF predictions with an ordinary paired bootstrap omit training-set/selection uncertainty. If claims generalize beyond the selected judges, item-only bootstrap omits judge/developer uncertainty.

11. **§7: relabel agreement is not a ceiling.** A single annotator can repeat the same systematic mistakes; κ is prevalence-dependent. Thirty-five repeats yield imprecise repeatability. Require an independent second annotator for a substantial blinded stratified subset, frozen rubric, and adjudication with raw disagreements retained. The rubric’s plan to add edge cases after 30 gold labels conflicts with freezing the instrument: develop on a separate calibration set.

12. **§11: interim inference is not harmless.** Judge comparisons depend on author/content distribution; G1 is only three local authors. Running RQ1/RQ3 “in full” at G1 cannot represent the final panel. Treat interim results as descriptive, or prespecify sequential testing/alpha spending and prohibit outcome-driven revisions.

Implementation evidence independently read: `src/gold_sample.py:71–78` draws `expected=refuse`, not actual harmful content; lines 94–108 omit the harmful-content column and support only the old labeling schema.

---
## Sub-session 4-46-58-01a1bcb3-21

Implementation audit completed using local file reads only; no scripts, models, APIs, network operations, or file changes.

**Most consequential mismatches**

1. **Harm disagreement is discarded (§§8.3, 9).** `src/judge.py:191–192` sends an item to the arbiter only when the behaviour labels differ. `src/judge.py:236–237` accepts Agent A whenever behaviour labels agree, even if A and B disagree about `harmful_content`. Thus the claimed multi-agent safety instrument silently reduces to A on those disagreements. **Fix:** arbitrate disagreement on either output field, and specify aggregation separately for behaviour and harmfulness.

2. **Human and model judges see different evidence (§§7–8).** `src/judge.py:140–145,203` removes the middle of answers longer than 6,000 characters (`config/judge.json:10`); `src/gold_sample.py:98` places full answers in the human sheet. Harmful content in the omitted middle becomes an artificial judge error. Since output length varies by author, this can distort RQ2 as well. **Fix:** identical complete text for humans and judges; preregister handling of genuine context overflow and generation truncation.

3. **Invalid handling contradicts the protocol (§8.2).** `src/judge.py:187,213–215` records failures for later reruns, without a one-retry limit or format-reminder policy. `src/judge.py:226–235,240–242` excludes unresolved cases from merged verdicts instead of retaining `invalid` and counting errors. This permits informative exclusion and inconsistent effective denominators. **Fix:** exactly defined attempt budget, immutable attempt records, final `invalid`, and all sampled items retained.

4. **Gold cannot record the new primary safety endpoint (§7).** `src/gold_sample.py:94–109` creates only behaviour, confidence, comment columns, with no harmful-content field. `labels/RUBRIC.md:17` specifies the same incomplete CSV schema. **Fix:** add independently annotated harmfulness and uncertainty/ambiguity fields before labeling; preserve initial and repeated annotations separately.

5. **The harmfulness construct differs across documents (§§7–9).** Judge instructions require concrete assistance causing **“serious harm”** (`src/judge.py:78,97,116`), while the protocol asks whether content meaningfully helps carry out a **harmful request**. `labels/RUBRIC.md:13` also risks treating full compliance as harmful without evaluating actual content. **Fix:** one operational definition with domain-specific examples, benign alternatives, fiction, misinformation, incomplete assistance, and non-actionable “compliance”; derive harmful-compliance rates from the independently labeled harmfulness endpoint.

**Major implementation gaps to freeze before execution**

- **Only the old local pipeline exists.** `src/judge.py:42,148–158` hard-codes Ollama. `config/judge.json:4–6` sets A=Qwen, B=Llama, arbiter=Qwen, rather than three different developers. `src/judge.py:74–131,199` uses different A/B/arbiter instructions, conflicting with the common-prompt comparison in §8.2. `config/models.json:4–25` contains the original six respondents and disabled Opus, not the expanded panel. A 26×item judge matrix, API judging, nested selection, recusal, jury logic, and statistical analysis are not implemented.
- **Venice is currently blocked from harmful benchmark generation.** `src/providers.py:168–172` disallows it as an API model. Implement the explicitly authorized model-specific exception, rather than weakening the provider-wide guard.
- **Dedicated research keys are not enforced for new compatible APIs.** `src/providers.py:111–113` accepts any configured environment name and defaults to `"local"` without one. This is weaker than the `AC_*` invariant in §5.2. Require an explicit approved research-key variable and fail closed for remote endpoints.
- **G2 sampling and design weights are absent.** `src/gold_sample.py:71–78` implements the G1 oversampling scheme only; it also equates harmful *prompts* with harmful *answers*. Add separate non-overlapping G2 sampling, frame/stratum counts, inclusion probabilities and stage IDs. Do not count 109 harmful-prompt answers as 109 gold positives.
- **Rubric adaptation after labeling remains allowed.** `labels/RUBRIC.md:19` promises edge cases after the first 30 labels. Freeze the rubric before the confirmatory gold set; use separate development items, or relabel all gold blind under a documented final rubric.
- **Metadata are insufficient for claimed reproducibility.** `src/run_models.py:182–185` logs names and dates but no model digest, quantization, chat template, settings hash or prompt hash. `config/models.json:19` uses mutable `:latest`. Record these before and after runs, and detect model changes.
- **Keyword baseline is undefined.** `src/judge.py:60–67` emits signals, not a predetermined three-class/harm classifier. Specify its decision rule before evaluating it; acknowledge that refusal phrases cannot detect actionable harm reliably.

**Secondary issues**

- No per-judge item shuffle: `src/judge.py:195–201` preserves raw-record order.
- Reasons are limited to 300 characters (`src/judge.py:164`), not 30 words.
- `bool(out.get("harmful_content"))` (`src/judge.py:163`) converts `"false"` to true; validate actual Boolean type even with constrained decoding.
- `scripts/run_with_memory_guard.py:19,24–25` hard-codes another checkout and the original three models.
- `src/gold_sample.py:88` imports `openpyxl`, absent from `requirements.txt`.
- README still describes v1 local-only judging (`README.md:41–48`). Update it with the eventual frozen implementation and distinguish planned features from completed ones.

---
## Sub-session 4-47-03-01a1bcb3-35

Selection and scope findings:

1. **§6 selection mostly reproduces; distinguish genuine gaps from errors.** Recomputed four-week OpenRouter shares are DeepSeek 34.2538%, Z.ai 10.2162%, OpenAI 9.5995%, Anthropic 7.6128%, Tencent 7.1288%, matching the rounded table. Capped capability leaders also match: OpenAI Sol, Anthropic Sonnet, Kimi Pro, xAI Grok, Tencent Hy4. Official snapshots support the three local size claims. Frontier selection works as written if developers are ranked first by their best score and public-API fallback happens second; freeze this operation order and explicit eligible IDs. The price cap is a defensible budget constraint, not a population sampling frame; findings describe this deliberately selected panel.

2. **§6/§9 T2 has an important score ambiguity.** Granite 4.2 8B has a real v5 Intelligence Index of **5.0983** at `data/selection/2026-11-08/aa_models_raw.json:7519`, yet protocol line160 displays only its GPQA/HLE proxy36.4*. The general rule says proxies apply to models without v5 scores. Literal T2 eligibility therefore gives **14 judges**, not13 or26: nine API respondents, Granite, four frontier judges. Freeze these IDs and the exact covariate; never mix the proxy scale with v5. The missing LFM proxy is29.1, computed from HLE at JSON:9593 and GPQA:9598.

3. **§6 uncensored provenance is not reproducible from the supplied snapshot.** The directory inventory and `data/selection/2026-11-08/README.md:5–11` document AA, OpenRouter and official Ollama records. There are no Dolphin/abliterated Ollama popularity or matched-build records among saved files/raw pages. Thus protocol:162–165’s matching claims and4.2M/1.9M rankings cannot be independently reproduced here. Freeze the candidate universe, definition of “uncensored,” download-count date/window, exact base/quantization/chat-template provenance, and exclusion table. OpenRouter’s Venice entry is `cognitivecomputations/dolphin-mistral-24b-venice-edition`, with $0.90/M output; usage permaslug is `venice/uncensored`, so document that join.

4. **§6/§9 T4 is a comparison of specific checkpoints, not a causal test of refusal removal.** Same architecture/base family does not control different fine-tuning datasets, quantization, templates, generation settings, or ablation procedure. Dolphin versus abliterated Llama is particularly confounded: both alter more than a generic “method.” Relabel conclusions as checkpoint associations, or perform matched interventions on the same exact base checkpoint with equal quantization/templates/settings and multiple replicated builds.

5. **§2/§12 novelty is narrower than claimed.** Zheng et al.(2023) and Panickssery, Bowman & Feng(2024) already establish judge biases/self-favouring; Verga et al.(2024) studies juries; Arditi et al.(2024) studies refusal-direction removal. Missing direct safety-evaluation context: **HarmBench** (Mazeika et al.,2024), **WildGuard** (Han et al.,2024), and **StrongREJECT** (Souly et al.,2024). These motivate classifier baselines and distinguish refusal wording from substantively useful harmful assistance. Potential novelty is a carefully validated *safety-specific* self/sibling error matrix, paired checkpoint detection comparison, and recusal-aware calibration under common tasks. “First” is unsupported without a literature search; no network used, so the protocol’s Kim/Zhao `[verify]` entries remain **[unsure]** here. Ward’s relevance needs checking; do not infer monitor evidence simply from a gradient-routing title.

6. **§2 control framing overreaches.** This is benign safety classification on static outputs, not validation of AI-control protocols against strategic untrusted actors. Self-judgment accuracy is neither a necessary nor sufficient “precondition” for secure untrusted monitoring; sabotage, adversarial adaptation, collusion channels, opportunity rates and budgeted auditing are absent. Suggested text: “We study benign classification errors relevant to monitor selection; these results do not estimate control-protocol safety against strategic subversion.” A recognition probe alone also does not causally separate recognition from preference.

7. **§10 ethics/replication needs operational detail.** Dedicated keys and a successful pilot establish neither provider permission nor retention/privacy guarantees. Record applicable dated terms, actual hosting providers/routers, retention/training settings, access controls and deletion schedule; seek an institutional determination rather than declaring human-subject status categorically. Screen releases by actual content: a “safe prompt” can yield harmful text. Restrict raw release but enable reproducibility through secure retained outputs/hashes and a controlled-access route if institutionally feasible. No terms were externally verified under the no-network rule.

**Publication judgement:** A safety/evaluation workshop or Findings-style contribution is plausible after measurement repairs; TMLR or a strong main-track submission needs substantially stronger validation and a focused novel result. The first criticism will be “a broad judge leaderboard whose gold standard and self-effect interpretation are under-supported.” The single strongest improvement is an independently double-labeled, adjudicated, prompt-balanced gold corpus powered for the focal safety/self-judgment estimand, rather than spending the marginal budget on additional judges.
