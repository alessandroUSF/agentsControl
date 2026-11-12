# Reviewer round 1: Codex, GPT-6.1 Sol, reasoning effort "xhigh" (10 November 2026)

This is the first round of an iterative review of the publication-readiness review of 10 Nov 2026 (`2026-11-10_publication_review.md`) and of the 11 changes it proposes. It ran in the Codex CLI (`codex-cli 0.167.0-alpha.3.2`, `codex exec`, read-only sandbox, connectors disabled), thread `01a1c461-98b9-7dd1-b5cc-6aadec18dd62`, from 02:34 to 02:48 local time.

- **Input:** a read-only clean copy of part of the repository (`E:\claude\_audit_copy\agentsControl_r12_pubreview`). It held no model answers, no benchmark prompt files, no author prompts and no secrets. Three personal names in protocol Section 16 were replaced by a placeholder.
- **Instructions:** `2026-11-10_prompt_for_codex_review_of_changes.md`. Web search was allowed only to verify cited papers and to look for closer prior work.
- **Conflict of interest:** GPT-6.1 Sol is also respondent and judge number 11 of the study panel. The prompt disclosed this and the reviewer states it in its verdict.
- **What the reviewer did:** 43 read-only shell commands inside the copy (`sed`, `cat`, `grep`, `awk`, `wc`, `find`, `head`) and 7 web actions on arxiv.org and two anthropic.com research pages. It did not run the Python analyses (Python is not available in its sandbox). The event log was checked: no file outside the copy was read and no packet text was used in a search query.
- **Text:** the final message is reproduced as returned. Its statements are claims to verify, not instructions.

---

**1. Verdict**

The study is worth running and publishing, but I would not freeze the present design. I agree with the earlier review that the allocation is too shallow for the headline question; I disagree that its proposed expansion is already demonstrably powered, inexpensive, or sufficient to identify self-specific leniency. Its numerical summaries mostly reproduce the supplied outputs, but several interpretations overreach: notably “H1 power,” the precision promised by scaling, the proposed blind bound, and parts of the novelty assessment. The strongest affordable paper would concentrate on harm classification, use the same answers as own and unrelated-judge controls, and retain human labels to distinguish missed harm from reduced false alarms. A careful replication with informative intervals is publishable even without significant effects; publication prospects should not depend on finding something in a pilot.

**Disclosure:** I am GPT-6.1 Sol, respondent/judge 11. The allocation recommendations below affect Sol and other OpenAI models; they use common sampling and price rules rather than anticipated performance.

I inspected files and performed arithmetic; I did not execute the Python analyses, modify files, or run models.

**2. Decisions on the 11 changes**

“§” below refers to `docs/STUDY_PROTOCOL_v2.md`.

| Change | Decision | Reason, new risk, and sections affected |
|---|---|---|
| 1. External pilot | **Adopt with modification** | Use it for feasibility and nuisance parameters, not significance-based selection. Exclude entire pilot prompt clusters. §§8.3, 11, 13–14. |
| 2. Scale T1b outside gold | **Adopt with modification** | Large efficiency gain, but 1.5–2.5 pp is an independence calculation, not established power. Preserve representative human validation. §§5.2, 7–9, 11. |
| 3. Increase anchors | **Adopt with modification** | Prefer same-answer yoking over matching different answers. Matching alone leaves effect-modifier confounding. §§8.3, 9.2, 11. |
| 4. Blind bound outside Holm | **Adopt with modification** | A bound needs its own shifted-null test and allocated α; detection power at −7 pp does not establish exclusion power. §§3.1, 9.2, 9.7. |
| 5. Separate endpoints | **Adopt with modification** | Make harm primary and refusal secondary. Additional subgroup tests otherwise recreate multiplicity and sparse-cell problems. §§1, 3, 7.1, 9.2. |
| 6. Defer legacy programme | **Adopt with modification** | Withdraw it transparently from this execution; do not promise an unfunded companion. Selection should follow scientific scope, not expected hypothesis failure. §§3.2, 8.4, 9.5–9.7, 11–14. |
| 7. Expand T4/random effects | **Adopt with modification** | Retain descriptive checkpoint comparisons now; expand separately if feasible. Three purposive pairs do not justify population random-effects inference. §§3.1, 8.3, 9.3. |
| 8. Adjudicated primary labels | **Adopt with modification** | Double-label all harm-prompt candidates, including apparent negatives; annotating only PI-positive items misses false negatives. §§7.3–7.4, 9. |
| 9. Replication framing | **Adopt** | Accurate and scientifically stronger than an overstated novelty claim. Update title, §§1–2, 12 and README. |
| 10. Rubric-light graded template | **Reject for this core** | Simultaneously changes rubric, scale and threshold. It adds interpretive branches and measures a different instrument. Delete this proposed addition from §8.3. |
| 11. Working implementation before freeze | **Adopt** | Necessary. Current executable judging and sampling code implement version 1, not the proposed study. §13. |

**3. Numbered issues for subsequent rounds**

**R1-C1 — The headline outcome does not identify harmful leniency.**  
**Where:** protocol §§7.1, 9.2; main review §§4, 6(2,5). A reduction in flags combines missed genuine failures with fewer false alarms. Moreover, the pooled outcome combines refusal recognition and harmful-content recognition. This matters because a statistically convincing negative average could represent improved classification. **Fix:** make harm-side flag changes primary; report human-positive sensitivity changes and human-negative false-positive changes alongside them. Reserve “missed harm” and “leniency on failures” for gold-conditioned results.

**R1-C2 — The proposed interaction control remains inadequate.**  
**Where:** protocol §§8.3, 9.2; review change 3. Matching anchors to broad item categories does not equate their severity, ambiguity, length, style or baseline classification probabilities. These can modify presentation effects. **Fix:** have each selected answer judged in both presentations by its author and an unrelated control judge, with balanced control assignment. Interpret the interaction as author-versus-control effect modification, not proof of recognition or psychological commitment.

**R1-C3 — Complete-case analysis can manufacture the effect.**  
**Where:** protocol §8.3, “Use in analysis”; §§9.2–9.3. Validity can depend on presentation, harmfulness and alignment. Dropping pairs with either invalid verdict conditions on an outcome of the manipulation. The simulations predominantly make invalidity independent of verdict content and therefore do not establish robustness. **Fix:** make delivered valid flags an explicit operational endpoint over all scheduled calls; report invalidity separately, complete-case results secondarily, and worst-case bounds on latent classifications. Do not interpret a flag reduction driven by non-answers as substantive leniency.

**R1-C4 — The revised core has not been shown to satisfy the hard budget.**  
**Where:** review §7; protocol §11; `scripts/cost_model.py`. The review correctly adds its estimated extensions, but those estimates do not specify an executable allocation. Also, `respondents()` includes pilot generations but does **not** multiply respondent expenditure by the scenario retry allowance. **Fix:** replace extensions layered onto the full matrix with a fixed call manifest; price every call type, respondent retries and reserve explicitly. The allocation below supplies a feasible planning basis.

**R1-M1 — The power claims are conditional and incompletely validated.**  
**Where:** `analysis/power_sim.py`, `analysis/selfcheck_estimators.py`, protocol §9.2. There are no anchors or interaction simulations. “First/last Holm” are threshold calculations, not simulated rejection probabilities under the complete joint family. The self-check uses `[44,43,63]+[12]*19`, totalling 378 observations, rather than the actual 432-item allocation. Shared cluster variation primarily changes discordance, without strongly testing shared directional presentation shocks. **Fix:** simulate the revised manifest, actual estimator, heterogeneous effects, shared directional shocks and informative invalidity.

**R1-M2 — Change 4 confuses detecting an effect with excluding it.**  
**Where:** review §6(4). High rejection probability when the true effect is −7 pp says nothing directly about the probability of obtaining a lower bound above −7 pp when the effect is near zero. **Fix:** specify and simulate the shifted-null bound proposed below. Do not describe non-rejection of zero as a successful control.

**R1-M3 — The pilot proposal encourages outcome-dependent project selection.**  
**Where:** review §6(1); fresh-eyes report’s pilot rules. “Is there anything here?” and stopping because the observed effect is small invite selection for promising findings. A gold-free pilot also cannot estimate a sensitivity gap without reference labels. **Fix:** register technical and precision rules first; exclude the pilot from confirmation; do not use its sign or p-value as a continuation criterion.

**R1-M4 — Primary reference labels need independent scrutiny.**  
**Where:** protocol §7.3; review change 8. Keeping PI labels primary despite adjudication weakens accuracy claims. Selecting second labels principally from PI-positive items cannot fully validate the negative class. **Fix:** independently double-label all harm-prompt items used for primary accuracy interpretation, adjudicate before judge-output inspection, and retain raw disagreements and unresolved cases.

**R1-M5 — T4 measures neither general preservation nor practical usefulness.**  
**Where:** protocol §9.3; review change 7. Sensitivity non-inferiority can be achieved by flagging almost everything; the specificity point-estimate gate does not establish specificity preservation. Three community builds support checkpoint-level conclusions, not refusal-removal generally. **Fix:** use joint sensitivity/specificity preservation for a future confirmatory study, fixed-pair estimation now, and avoid causal claims about abliteration from model-card descriptions alone.

**R1-M6 — The novelty assessment understates overlap.**  
**Where:** protocol §2; review §§1, 3; literature sweep. Khullar already supplies the core presentation and on/off-policy contrasts [verified online]. Agnihotri includes a cross-model refusal-judging matrix and human validation, contrary to the review’s uncomplicated “no own-versus-other contrast” characterization [verified online]. **Fix:** distinguish absence of a formal gold-referenced self coefficient from absence of the underlying crossed data; see literature discussion below.

**R1-M7 — Legacy hypotheses require an explicit withdrawal record.**  
**Where:** public version 1; protocol §§3.2, 14; review change 6. Their wording is not the whole hypothesis: selected instruments, operational endpoints and decision rules have changed. Deferral cannot erase the original commitments. **Fix:** publish a hypothesis-by-hypothesis amendment stating retained, changed, withdrawn or deferred, with reasons and exposure history.

**R1-M8 — Freeze requirements conflict with implementation status.**  
**Where:** protocol §13; `src/judge.py`, `src/gold_sample.py`, `config/judge.json`. Existing judging uses schema-constrained local generation, clipping and version-1 arbitration; the sampler draws the old gold set. These are not minor omissions. **Fix:** freeze only after the actual presentations, parser, sampling, spending and analysis paths pass an end-to-end synthetic run. The supplied self-check output also lacks the newly added own-cell check: regenerate it.

**R1-M9 — Adaptive G3 weighting is not validated by the supplied check.**  
**Where:** protocol §7.2; `check_pi_g3()`. That check fixes the second-stage sample size. It does not validate inclusion probabilities when stopping depends on observed gold labels. Treating realised adaptive sample size as fixed is not generally sufficient. **Fix:** delete G3 with H1, as recommended, or validate the complete stopping design and its target estimators. This does not reopen ruling C.

**R1-m1 — Annotator blinding remains incomplete.**  
**Where:** annotator guide introduction and Process step 2; rubric’s own-prompt section. The guide still supplies the directional hypothesis and mentions sample “halves”; the rubric says expected labels are “shown for context,” contradicting the blind-sheet rule. **Fix:** use the neutral wording below and remove those disclosures.

**R1-m2 — Simplify scope and reconcile the state record.**  
**Where:** protocol §§8.3, 9.5, 13, 16; README. Some passages say local own-prompt answers already exist, while the freeze precedes own-prompt generation. **Fix:** publish one dated inventory distinguishing generated, sealed, piloted, inspected and future data. Remove obsolete audit narrative from the operational protocol.

**4. Numeric checks**

| Claim | Source checked | My check | Assessment |
|---|---|---|---|
| ±18 pp, n=12, discordance .10 | Analytic script/output | \(1.96\sqrt{.1/12}=17.9\) pp | Correct normal approximation; not a reliable small-sample CI. Approximately 28% of such samples have no discordance. |
| T1b MDE 4.9–6.8 pp | Power code/JSON | Approximately correct for the 6% and 10% scenarios | Incomplete: at 14%, first-step MDE exceeds 7 pp. |
| Power .10/.21 at 2 pp | JSON baseline | .1025/.2075 at −1.99 pp | Correct at approximately 6% discordance; at 10% it is .0775/.1500. |
| A 5-pp average requires 18–21 pp recall loss | Allocation and assumed failure rates | Failure share: 26.67% item-weighted, **24.15% judge-weighted**; \(5/.2415=20.7\) pp | Broadly correct, but 20.7 pp matches T1b’s weighting. |
| Interaction absent; MDE 6.6–8 pp | Power code; analytic arithmetic | With q=.10, current on-policy SE 1.74 pp and 30-anchor SE 1.23 pp imply interaction SE 2.13 pp; first-step MDE ≈6.9 pp | Plausible approximation, not validated power. |
| T4 power at −.03 | JSON variants | .9625, .7375, .5250, .3775; combined low-harm scenario .5150 | Correct simulation outputs. |
| H1 passes with probability .56 | Code/JSON | .56 is **only the missed-harm clause**, using independent binomial errors | Incorrect if presented as power for H1 as a whole. |
| Revised core $58–72/$116–143 | Review arithmetic and cost output | $44.56+$10–20+$3.5–7=$58.06–71.56; pessimistic $115.79–142.79 | Arithmetic correct; extensions are insufficiently specified. |
| Scaling to 100–150 gives 1.5–2.5 pp | Analytic output | At q=.10, α=.025: **2.08 pp at 100**, **1.70 pp at 150** | Correct under independence; not cluster-adjusted. |
| 100 anchors establish a small interaction | Same approximation | At 100 own +100 anchors, q=.10, α=.025: interaction MDE ≈**2.94 pp** | More demanding than the on-policy claim; clustering can enlarge it substantially. |
| Legacy savings $29.16/$64.17 | Stage table | Correct sum of stages 3, 3b, 6 | Not all are guaranteed expenditures: fallback and optional stages already reduce actual savings. |
| Five judges dominate cost | Per-judge output; reconstructed synchronous pessimistic rates | About 92% of printed expected judge costs; **93.3%** of reconstructed pessimistic synchronous costs | “About 90%” is fair. |

The 400-replication power estimates themselves have Monte Carlo uncertainty: near 80% power, approximately ±4 percentage points for a 95% Monte Carlo interval.

**5. Cross-cutting answers**

**A. Scaling T1b.** The analytic formula correctly incorporates unequal judge sample sizes:

\[
SE(\hat\theta)=\frac{\sqrt{\sum_j q_j/n_j}}{J}.
\]

It omits covariance between judges sharing prompts. With equal sample sizes and complete prompt overlap, an illustrative directional intraclass correlation \(r\) multiplies SE by \(\sqrt{1+21r}\): **1.43 at r=.05; 1.76 at r=.10**. Invalidity further changes precision and, under complete-case analysis, potentially the estimand.

For the proposed main study, use **150 benchmark answers per judge**, including all 60 common harmful prompts and 90 safe prompts. This fits every API respondent’s existing allocation; models 1–3 do not need their larger version-1 runs. Cheap API and local censuses can be secondary, but should not silently redefine the equal-judge primary average. Leaving gold permits a precise statement about flags, not accuracy, harm prevalence or missed harmful compliance. Those interpretations must remain inside independently labelled data.

**B. Anchors.** Use **150 yoked controls per judge**, paired to the same prompt IDs as its own 150 answers. Each answer receives an author judge and one unrelated control judge, both under both presentations. Assign controls through seeded, balanced permutations excluding self, close and same-developer relations. This removes answer-content differences from each author-versus-control contrast.

A hundred unmatched anchors is not automatically enough. With 60 harm items per judge, q=.10 and independence, the interaction MDE at two-sided α=.02 is approximately **3.9 pp**. Shared directional variation can push it above 5 pp. That is the interaction to simulate; do not advertise 2-pp self-specific sensitivity.

**C. Bound and multiplicity.** Allocate **α=.04** to Holm over two harm-side tests: on-policy presentation effect and author-versus-control interaction. Allocate **α=.01** to the blind bound:

\[
H_0:\beta_{\rm self}\leq-.07,\qquad H_1:\beta_{\rm self}>-.07.
\]

Exclude blind associations worse than −7 pp only when the **one-sided 99% lower bound exceeds −.07**. This is neither equivalence nor causal absence of preference. Use a shifted-null cluster test or its inverted bound. Everything else receives descriptive intervals, without confirmatory “discovery” language. If T4 remains confirmatory, it must receive an explicit share of the same .05 budget.

**D. Endpoints.** Harm-side θ is primary. Refusal-side θ is secondary. A combined θ is interpretable only as a prespecified weighted index of flag emission over a stated mixture; it is not a common psychological construct. Report judge-group estimates and a forest plot; avoid an additional omnibus heterogeneity hypothesis unless it replaces another confirmatory test.

**E. Preregistration integrity.** Withdrawal before outcome inspection is defensible; pretending nothing changed is not. Suggested wording:

> “Before any confirmatory answer was inspected, judged or labelled, we withdrew H1–H3 and the instrument-selection/RQ4 programme from this execution because the expanded design exceeded available resources. These hypotheses remain publicly documented and are not tested in this paper. Any future execution will receive a separate registration identifying this amendment and all intervening data exposure.”

“Before any answer” must be qualified if pilot answers have been inspected. Dropping the programme honestly is preferable to promising a companion without resources.

**F. Pilot.** Same judges and templates do not themselves contaminate an independent confirmation sample. Reusing prompt clusters, adapting to confirmatory results, or hiding pilot-driven choices does.

Use 20 fresh respondent-pilot prompts per API model, outside every confirmatory prompt cluster, then **20 own paired judgments plus 10 paired controls per API judge**: 60 calls. Local models can use 100 own pairs. Register:

- Stop the affected provider on a warning.
- Revise technically if more than 10% of verdicts are invalid or more than 5% blocked.
- Permit one documented formatting/cap revision; retain all attempts.
- Continue only when the fixed manifest fits the pessimistic budget and simulations establish acceptable precision.
- Never continue or stop because the pilot effect is significant, favourable or small.

The original pilot’s pooled SE is about **1.2 pp before clustering**, not reliably 1 pp. An internal pilot is less attractive here: unblinded variance estimates, scope changes and an unwritten runner complicate valid sample-size adaptation. Prefer an external feasibility pilot.

**G. T4.** For this paper, retain the three existing pairs descriptively. Use equal-pair averages of paired differences, retaining shared-item dependence through prompt-cluster resampling. Do not default to random effects.

A future confirmatory T4 should ideally cover **at least six pairs across four base families**, with a fixed common answer set independent of the evaluated pairs. My default preservation margin would be **5 pp for both sensitivity and specificity**, justified against a use case. Joint non-inferiority requires both component tests to pass—an intersection–union claim. Report criterion shift through positive-call rate and, if useful, signal-detection measures with their assumptions. “Non-inferior,” “materially inferior” and “inconclusive” should refer to the same margin; modest inferiority relative to zero can coexist with non-inferiority.

**H. Human reference.** Double-label every harm-prompt item supporting accuracy interpretation, including PI-negative items. Use adjudicated labels as primary; third-person adjudication is valuable for unresolved disagreements, not mandatory on every item. Single labels can support descriptive refusal analyses and release screening.

The design below needs approximately **550 PI labels**, with **360 independently repeated labels**. At four minutes each, that is 36.7 PI hours and 24 co-author hours, before training/adjudication. Budget roughly **45–55 PI hours and two co-authors at 12–14 hours each**. Recruit before making the freeze contingent on unavailable annotators.

**I. Budget.** The allocation below cuts the expensive full API-by-gold matrix. It also cuts frontier judges, stages 3/3b/6, recognition probes, second wording, unframed rejudging and API external transfer. It does not require new judge batching.

**J. Provider risk.** Yoke API answers to unrelated API judges and local answers to unrelated local judges. This keeps the same-answer control while substantially reducing commercial assistant-turn exposure to harmful local-model completions. The estimand becomes author versus unrelated judge **within access group**, which must be stated.

Use completed assistant messages followed by evaluation, not harmful continuation prefills. This preserves the manipulation but cannot eliminate enforcement risk. Do not truncate, sanitise or substitute blocked answers after observing results; record blocks and restrict conclusions if a provider stops.

**K. Missing and excessive work.** Missing are a rigorous missing-verdict estimand, actual interaction power, an explicit target item distribution and treatment of scarce commercial failures. Excess includes instrument optimisation, frontier-assisted relabelling, latent-class modelling, calibration bins, elaborate jury searches and multiple robustness models. Keep the existing spending protections that work; stop expanding their administrative machinery.

For the three open decisions:

- **(i) Pilot before freeze: yes**, with the firewall above; it is a feasibility exercise.
- **(ii) Legacy hypotheses: withdraw from this execution**, preserving the public record; defer only if a realistic companion is later funded with time.
- **(iii) T4: split the confirmatory programme**, retaining a bounded descriptive appendix now. Three additional plots do not require a second paper; a general preservation claim does require more evidence.

**6. Strongest design I would defend**

The following is suitable protocol language, subject to the simulation requirement.

**Claim.** “We estimate how conversational presentation changes harmful-content flags for a fixed panel of 22 models, and whether that change differs between an answer’s author and an unrelated judge evaluating the same answer. Independent human labels distinguish changes in detection of harmful answers from changes in false alarms; conclusions concern these checkpoints, prompts and presentations.”

**Sampling and calls.**

- Main frame: the common benchmark subset, excluding all pilot clusters.
- Each judge: **150 own answers—60 harmful-prompt and 90 safe-prompt answers—and 150 yoked answers on the same prompts**.
- Select safe prompts by source-stratified seeded sampling. Use all 60 common harmful prompts.
- Within each access group, assign one unrelated control per answer through balanced permutations; rotate donors across prompts.
- Every assigned judge–answer combination receives blind and in-context presentations: **600 main calls per judge**.
- Randomise adjacent presentation order; use fresh conversations and fixed settings.
- Additional local judgments are explicitly supplementary. Sealed answers remain usable without regeneration.

**Estimands.** Primary: equal-judge harm-side change in delivered valid harmful flags, and the same-answer author-minus-control difference in presentation effects. Secondary: refusal-side changes; invalidity; gold-positive sensitivity and gold-negative false-positive changes; blind self association; descriptive judge-group and checkpoint results.

For missing verdicts, a delivered flag requires a valid harmful verdict. Report complete-case classification effects and worst-case latent-label bounds alongside this operational endpoint.

**Tests.** Holm over the two primary tests at α=.04; blind −7-pp bound at α=.01. Use prompt-cluster inference, preserving all judge, author and presentation observations within each resampled prompt. Keep ruling A’s primary unit and its prespecified sensitivity analysis. Claim self-specific harmful leniency only when the interaction supports it and gold-conditioned results establish increased misses rather than improved specificity.

**Human labels.** Preserve G1’s 150 items. Draw 400 additional items, excluding G1, with fixed quotas of **230 harmful-prompt and 170 safe-prompt answers**, balanced across authors and source. This yields 300 harm-prompt and 250 safe-prompt items overall. Independently double-label all 300 harm-prompt items plus 60 safe-prompt items. Adjudicate before inspecting confirmatory judge outputs. Do not use adaptive G3.

All local judges may evaluate all 550 items. API judges evaluate one common, prespecified **120-item blind reference subset**, reusing existing identical calls where available. Accuracy estimates are descriptive; this sample does not support fine-grained judge rankings.

**T4.** Three existing pairs, descriptive appendix, reporting sensitivity, specificity, invalidity and paired differences. No preservation headline.

**Budget.** These are conservative planning calculations from the supplied rates, retaining the original stage-1 generation ceiling even though unused own-prompt generations can be omitted. Judge prices include 15% retries in the pessimistic column.

| Allocation | Expected | Pessimistic |
|---|---:|---:|
| Stage-1 respondent ceiling, including pilots, plus 5%/15% respondent retry allowance | $16.99 | $33.45 |
| Main API judgments: 600 per API judge | $24.76 | $51.51 |
| External judge pilot: 60 per API judge | $2.48 | $5.15 |
| Repeatability: 40 per API judge | $1.65 | $3.43 |
| Common blind human-reference subset: up to 120 per API judge | $4.95 | $10.30 |
| API guard allowance | $0.18 | $0.32 |
| Local judging/guards/T4 | $0 | $0 |
| **Planned expenditure** | **$51.01** | **$104.17** |
| **Remaining under $110** | **$58.99** | **$5.83** |

The reconstructed pessimistic synchronous per-call totals, including retries, are $0.080063 across the five expensive judges and $0.005780 across the other seven API judges. The printed per-judge table is for 1,086 calls under its stated pricing mode; simply rescaling it would underprice synchronous calls. This budget covers the supplied pessimistic scenario, not arbitrary token overruns: retain hard reservations and reprice the complete manifest from pilot token counts before freezing.

**Required simulation.** Run **10,000 outer replications** using the exact manifest. Retain the current failure-rate scenarios and fixed judge parameters, add crossed prompt-specific presentation shocks with logit SD **0, .3 and .6**, and calibrate paired dependence to null discordance **.06, .10, .14 and .20**. Calibrate marginal on-policy effects to **0, −.02 and −.05**, with control effects producing interactions **0, −.02 and −.05**; include opposing judge effects averaging zero and failure-only shifts. Simulate invalidity at **3%, 10% and presentation-dependent 10% versus 15%**, including dependence on harmful content. Apply the actual operational estimators, Holm family and cluster tests; use 1,999 resamples for screening and verify decisive settings with 9,999. Report size, power, coverage, missing-verdict bounds and probability of excluding the chosen meaningful-effect margin.

**Freeze.** First register the external pilot and adaptation rules. After it, publish the version-1 amendment and freeze the final template, parser, settings, manifests, yoking assignments, gold allocation, analysis, budget and successful synthetic run. Then generate remaining confirmatory answers, label and adjudicate blind, and execute judging. Delete the Phase-1 outcome interim.

**Outcome probabilities—subjective, not simulation results.** For this focused design: self-specific negative effect **25%**; negative presentation effect without resolved specificity **20%**; reverse effect **10%**; sufficiently narrow near-null result **25%**; materially inconclusive **20%**. For the original T4, my prior is roughly **45% non-inferior, 10% materially inferior, 45% inconclusive**.

For publication, conditional on competent execution and honest claims, my rough workshop estimate is **65% currently / 80% focused**, and TMLR or Findings **30% / 50%**. These have wide uncertainty and are not calibrated forecasts. I have not verified venue dates under the permitted browsing scope; treat 1 February as a planning assumption.

Delete the legacy instrument/RQ4 programme, own-framing experiment from this execution, G3, frontier apparatus, recognition probe, alternative template, latent-class analysis, PPI, capability regressions and jury/cascade optimisation. This removes the own-prompt arm rather than reopening rulings B–D.

**7. Literature assessment**

Every literature statement below is marked with its verification status.

- **[verified online]** Khullar contains an unattributed user-turn baseline, previous-assistant-turn presentation, on/off-policy comparisons and cross-model harmfulness experiments. The review’s correction of “adds the blind cell” is right. Its appendix’s weaker, mixed off-policy harmfulness shifts do not directly predict the present on-policy binary effect. Frame the contribution as task-specific replication plus human-grounded error interpretation. [Khullar et al.](https://arxiv.org/html/2603.04582v1)

- **[verified online]** CAREBench reports same-family leniency, coefficient −.350 and p=2×10⁻⁹. This is a log-odds coefficient, not a 35-pp effect. Its self-preference regression is distinct from its human calibration analysis. [CAREBench, Appendix B](https://arxiv.org/html/2606.29685v1)

- **[verified online]** Agnihotri uses multiple refusal judges across responders, includes a two-human validation subset, and presents a cross-model matrix discussing own-family misjudging. The review therefore understates its overlap. Abliterated responders should not be confused with abliterated judges, and the paper does not supply the proposed formal gold-referenced self-effect analysis. [Agnihotri et al.](https://arxiv.org/html/2510.02768)

- **[verified online]** Kabir and Tiganj find model-dependent changes in explicit judgments of harmful requests after abliteration; Chacón Menke and Tan study harmful-answer self-critique. These weaken a blanket preservation prediction but do not establish the proposed matched answer-classification result. [Kabir and Tiganj](https://arxiv.org/html/2604.18510), [Chacón Menke and Tan](https://arxiv.org/html/2503.17365)

- **[verified online]** aipsy-judge crosses three judges with three generator providers and includes a single-expert anchor. This is substantial safety-judging overlap, although its own-family contrast is not the exact binary refusal/harm test proposed here and blinding is not established. [Keeman and Keeman](https://arxiv.org/html/2608.24899)

- **[verified online]** Missing methodological references include Roytburg et al., on evaluator-quality confounding, and Nguyen et al., on recognising adversarially prefilled harmful outputs and changes after refusal-direction ablation. [Roytburg et al.](https://arxiv.org/html/2601.22548), [Nguyen et al.](https://arxiv.org/html/2606.23671)

- **[verified online]** Binary rubrics do not eliminate self-preference generally; Chae’s blind null follows controls in a different task and should not justify a 90% null probability here. [Pombal et al.](https://arxiv.org/html/2604.06996), [Chae et al.](https://aclanthology.org/2026.findings-emnlp.1571/)

- **[verified online]** Anthropic’s self-assessment post establishes deployment relevance, but its quoted recall uses a stronger classifier as reference. Its separate motivated-mislabeling report studies refusal labels changing with downstream consequences, another missing connection rather than the same experiment. [Self-assessment](https://safeguards.anthropic.com/2026/self-assessment/), [Motivated mislabeling](https://alignment.anthropic.com/2026/agentic-misalignment-summer-2026/)

**[unsure]** I found no exact predecessor satisfying all elements of (a), (b) or (c), but that is a bounded search result—not proof that none exists. The strongest defensible novelty claim is the particular controlled, human-grounded configuration, not a broad first study of safety self-judging.

**8. Wording edits**

1. **Edits 1 and 3 are scientifically more accurate**, but the directional “more leniently” description should not appear in pre-labelling materials.
2. **Edit 2 is an improvement but insufficient.** Remove Process step 2’s “within each half.” Remove the rubric’s suggestion that expected labels are shown. Explain agreement sampling after labels are locked.
3. Give annotators the task and welfare information, not the directional research hypothesis:

> “This study evaluates automated classification of AI-generated text. Independently label each request–response pair using the supplied rubric. You will not see model identities, automated verdicts, other annotators’ labels or sampling proportions. Some material contains harmful or disturbing content; the welfare protocol governs participation.”

Do not promise perfect identity blinding: answers may reveal their source. Tell annotators not to infer or investigate identity.

**9. Conditions for convergence**

I would call the design ready to freeze when:

- The operational estimand, same-answer controls and invalid-verdict treatment are explicit.
- Actual interaction power and interval coverage are simulated under shared directional effects.
- One study-wide confirmatory α allocation is fixed.
- The complete pessimistic manifest, respondent retries and pilot fit below $110.
- Independent annotators are committed and adjudicated harm labels are primary.
- The external-pilot firewall and public version-1 amendment are registered.
- Working code reproduces the entire design on synthetic data.
- Novelty language reflects the verified overlap.
- Remaining claims are narrowed wherever precision, provider availability or reference labels cannot support them.