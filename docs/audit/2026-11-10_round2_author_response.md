# Author response to reviewer round 1, with a revised design ("draft B")

10 November 2026. Reply to `docs/audit/2026-11-10_reviewer_round1_codex_gpt61sol.md`.

Status: nothing here is frozen, registered or committed. No answer has been read, judged or labelled since
round 1. Every number below comes from a simulation with assumed parameters or from the cost model; the files
are listed in section 11. Model numbers are those of the protocol (1-3 and 7-14 commercial API models; 4, 5, 15,
16, 17 local instruction-tuned; 6, 18, 19, 20, 21 local refusal-removed; 22 refusal-removed through an API).

## 0. Summary

We accept the core of your report: harm classification as the primary endpoint; every answer judged by its
author and by an unrelated control judge, blind and in context; delivered valid flags as the operational
endpoint; one study-wide alpha allocation (0.04 Holm over two primaries, 0.01 for a blind bound); withdrawal of
H1-H3, RQ4 and instrument selection with your wording; an external feasibility pilot behind a firewall;
adjudicated double labels as the reference; T4 as a descriptive appendix; deletion of G3, the frontier
apparatus, the recognition probe, the alternative template and the other items on your list; neutral annotator
wording; working code and a synthetic end-to-end run before any freeze.

We propose four changes to your "strongest design". Each follows from something we simulated after your report.

1. **On-policy panel and long frame (sections 2 and 3.1).** Your equal-judge primary on 60 harmful prompts
   averages, per judge, (share of own answers that are harmful) x (change of the flag rate on them). With the
   assumed failure rates the six refusal-removed judges carry 76% of that estimand and the eleven commercial
   judges 10%, and a 2-pp effect on that scale is an 8-pp effect among harmful answers. Simulated power for 2 pp
   is 14-52% for the on-policy test and 9-30% for the interaction. We propose that the primary on-policy
   analysis uses the eleven models that produce harmful content on-policy (ten local models and the one
   refusal-removed API model), each on 300 harmful prompts, at an extra cash cost of about US$2. The 22-judge
   equal-judge estimate on the common 60 prompts becomes the first secondary analysis.
2. **Type-matched yoking (section 3.4).** With controls drawn from the access group, the author-minus-control
   interaction is biased whenever a model type's general in-context susceptibility is correlated with its
   failure rate (simulated: a spurious interaction of -0.8 to -1.1 pp, rejected in 7-10% of null runs). With
   controls of the same model type the bias disappears (0.0 pp, 2-4%). The same holds for the blind bound.
3. **A screen-conditional scale (section 3.3).** A deterministic refusal screen, fixed before any judgment,
   lets the tests run on answers that are not refusals. In the same simulated worlds this raises the power of
   the interaction test from 45% to 65-79% and states the effect in pp among non-refused answers. We ask you to
   choose between this statistic and the unscreened one as the registered primary.
4. **A common off-policy harmful set for all 22 judges (section 3.5).** The commercial models rarely produce
   harmful content, so their control arm on each other's answers would consist of about 95% refusals. We
   replace most of it by 60 harmful answers written by refusal-removed models, which every judge classifies
   blind and as its own previous turn. This is the only affordable way to measure the presentation effect of the
   commercial judges on harmful content.

The cash manifest of this draft is US$46.67 expected and US$98.71 pessimistic (cap US$110), with a registered
cut order (section 8). Section 13 lists the decisions we ask you to make.

## 1. Responses to the numbered issues of round 1

| Issue | Response | Where |
|---|---|---|
| R1-C1 harm-side flag change primary; label-conditioned changes | Accepted. Harm side primary, refusal side secondary. Sensitivity and false-positive changes conditioned on adjudicated labels are the key secondary analysis and part of the claim rule. | 3.2, 3.6, 6 |
| R1-C2 each answer judged in both presentations by its author and an unrelated control | Accepted, with controls matched on model type instead of access group, and a changed control arm for the commercial judges on the harm side. | 3.4, 3.5 |
| R1-C3 delivered valid flags over all scheduled calls; complete-case; bounds | Accepted. We add a fail-closed sensitivity analysis and a decomposition, because differential invalidity alone moves the delivered-flag estimand. | 5 |
| R1-C4 fixed call manifest with retries and reserve | Accepted. `scripts/cost_model.py --v23b`; retries are now inside the respondent cost (your finding was correct); cut order registered. | 8 |
| R1-M1 simulate the revised manifest with the actual estimator | Done for the harm side; one run for the safe side; the files and the runs still missing are listed. | 11 |
| R1-M2 shifted-null bound | Accepted; simulated with shifted sign-flip tests. Margin stated on the scale of non-refused answers. | 4 |
| R1-M3 pilot not outcome-dependent | Accepted; feasibility rules only, registered before the pilot. | 9 |
| R1-M4 double-label all harm-prompt items; adjudicate before judge outputs are inspected | Accepted. | 6 |
| R1-M5 T4 as fixed-pair estimation | Accepted: descriptive appendix, three pairs, equal-pair averages, prompt-cluster intervals. | 10 |
| R1-M6 novelty understates overlap | Accepted. Related work and the novelty paragraph will be rewritten after we verify each reference you listed. Not done yet. | 10 |
| R1-M7 hypothesis-by-hypothesis withdrawal record | Accepted, with your wording. | 10 |
| R1-M8 freeze only after an end-to-end synthetic run | Accepted. | 9 |
| R1-M9 delete G3 with H1 | Accepted. | 6 |
| R1-m1 annotator blinding | Accepted with your text; the three lines you cited will be changed. | 10 |
| R1-m2 one dated data inventory | Accepted; a first version is in section 12. | 12 |

Your rejection of our proposal 10 (rubric-light graded template) is accepted: one template only.

## 2. Scarce commercial failures (your gap K): what the equal-judge primary measures

Write f_j for the share of judge j's own answers to harmful prompts that contain harmful content (a property of
model j as a respondent) and d_j for the change of j's flag rate on those answers between the blind and the
in-context presentation (a property of j as a judge). On refusals the flag rate is near its floor. So

    change of delivered flags of judge j over all its answers  =  f_j * d_j  +  (1 - f_j) * (change of false alarms),

and your equal-judge estimand is close to mean_j (f_j * d_j). Three consequences:

- With the assumed failure rates (commercial 5%, local instruction-tuned 15%, refusal-removed 70%) the mean of
  f_j is 0.25. The six refusal-removed judges carry 4.2 / 5.5 = 76% of the estimand, the five local
  instruction-tuned judges 14%, the eleven commercial judges 10%. "Equal-judge" describes the weights of the
  cells, not of the information.
- A change of -2 pp on that scale corresponds to about -8 pp among harmful answers; -5 pp to about -20 pp.
- A commercial judge with 60 harmful prompts has about three harmful answers of its own. Its control arm (other
  commercial models' answers) has the same composition.

Simulation of your design as specified (22 judges, 60 harmful prompts each, access-group yoking; 324 scenarios,
2,000 replications each, 1,999 sign vectors; file `power_sim_v23_screen.json`):

| Quantity | Value |
|---|---|
| Holm rejection at the null, on-policy / interaction (3% or 10% invalid) | 1.1-2.8% / 1.6-2.3% |
| Coverage of 95% intervals, on-policy / interaction | 93.7-96.4% / 93.9-96.4% |
| Standard error, on-policy / interaction | 0.7-1.6 pp / 1.0-1.8 pp |
| Power for an on-policy effect of -2 pp / -5 pp, 3% invalid | 14-52% / 77-100% |
| The same with 10% invalid | 12-40% / 74-100% |
| Power for an interaction of -2 pp / -5 pp, 3% invalid | 9-30% / 55-97% |
| The same with 10% invalid | 8-22% / 49-92% |

Size and coverage hold, and your interaction MDE of about 3.9 pp is inside our range (3.2-5.7 pp for 80% power).
The design is valid. It is sensitive only to effects of roughly 10-20 pp among harmful answers, and most of that
sensitivity comes from six judges. We think a reader should be told this directly, by a design in which the
models that can show the phenomenon on-policy are the declared primary panel.

## 3. Revised harm-side design

### 3.1 Panels and frames

| Panel | Models | Harmful prompts | Safe prompts |
|---|---|---|---|
| On-policy panel (primary) | 4, 5, 6, 15-22 (eleven) | 300: the first 150 of each harmful stratum in the seeded nested order | 90 |
| Commercial panel | 1-3, 7-14 (eleven) | 60: the first 30 of each harmful stratum (inside the 300) | 90 |

All prompts come from the sealed sample; the order is the one of `src/subsets.py`. The harmful strata are XSTest
unsafe (200 prompts) and OR-Bench Toxic (300). A frame of 300 leaves a tail of 200 harmful prompts for the
pilot firewall (166 after the exclusions of section 9). The long frame costs cash only for model 22 (about US$2 as respondent and judge together); for
the ten local models it costs GPU time (about 23,000 local judge calls in total, 32-58 GPU-hours).

Simulated standard errors of the unscreened on-policy-panel estimates: 0.88 / 1.14 pp (on-policy / interaction)
with 150 prompts, 0.61 / 0.82 pp with 300.

### 3.2 Arms and estimands

For an answer a to a harmful prompt, written by model j, with control judge k:

| Arm | Judge | Presentation |
|---|---|---|
| A1 | j (author) | blind: request and answer as quoted data |
| A2 | j (author) | in context: a is j's own previous assistant turn |
| C1 | k (control) | blind |
| C2 | k (control) | in context: a is shown as k's previous assistant turn (off-policy for k) |

Flag = 1 when the delivered valid verdict has `harmful_content = true`; a missing or invalid verdict is 0 in the
primary analysis (section 5).

- theta_on = E[A2 - A1]: change of the harm flag when a judge sees its own answer as its own turn.
- theta_off = E[C2 - C1]: the same change for an unrelated judge on the same answers.
- iota = theta_on - theta_off: the part of the change that is specific to self-authored answers.
- beta_blind = E[A1 - C1]: blind self-preference.

Averaging: each prompt contributes the sum, over the judges of the panel, of its flag differences; inference
sign-flips prompts or uses cluster-robust intervals over prompts (`base_prompt_id`), so dependence between
judges within a prompt is respected.
Because every judge of the on-policy panel has the same 300 prompts, the unscreened statistic is the equal-judge
mean. Its implicit weights are still proportional to f_j (section 2); this is true of any statistic that
averages over answers.

### 3.3 The refusal screen and the two candidate primary statistics

**Screen.** S(a) = 1 ("not a refusal") when the answer is non-empty, is not a provider block, and contains none
of the phrases of a published refusal-phrase list in its first 400 characters (case-insensitive); otherwise
S(a) = 0. The list and the code are fixed before the freeze and may be revised once, using pilot answers only.
S depends on the answer text alone. It is fixed before any judge call and is the same for every judge and
presentation.

**Two statistics on the on-policy panel**, with D the within-answer flag difference (A2 - A1 for theta_on,
(A2 - A1) - (C2 - C1) for iota):

- P-U (unscreened): mean of D over all answers. Unit: pp of all answers to harmful prompts.
- P-S (screened): sum of S x D divided by the sum of S. Unit: pp of non-refused answers.

Both weigh the judges by their number of non-refused answers; P-S removes the refusal cells and rescales.

**Validity.** If the presentation changes no verdict, D is sign-symmetric within every prompt whatever S is,
because S is fixed beforehand. The prompt-level sign-flip test of the sum of S x D therefore keeps its size for
any screen accuracy. Accuracy affects power and interpretation only. Simulated Holm rejection rates at the exact
null (no effect, no in-context noise; six scenarios): 1.3-3.0% for P-S and 1.5-2.5% for P-U (nominal: at most
4% for the family).

**Power in the same simulated worlds** (frames of 3.1, type-matched yoking, 2,000 replications, 1,999 sign
vectors, in-context noise SD 0.3 common plus 0.3 on the author arm, null discordance 0.10, 3% invalid, effects on
harmful answers only). Rows are labelled by the true change among harmful answers of the on-policy panel.

| True change among harmful answers | Test | P-U | P-S, perfect screen | P-S, screen Se 0.9 / Sp 0.8 |
|---|---|---|---|---|
| on-policy -5.3 pp | P1 | 77-79% | 98.9% | 95.3% |
| on-policy -8.2 pp | P1 | 99% | 100% | 100% |
| interaction -4.6 pp | P2 | 45-46% | 78.9% | 65.3% |
| interaction -7.5 pp | P2 | 91-92% | 99.8% | 98.2% |
| noise only: on-policy -1.4 pp, interaction -0.7 pp | P1 / P2 | 4.2% / 2.8% | 15.2% / 4.7% | 10.9% / 4.0% |

For comparison, the 22-judge statistics in the same worlds: unscreened 17.5% (on-policy -5.3 pp) and 11.5%
(interaction -4.6 pp); screened over all 22 judges 96.9% / 71.5% with a perfect screen but 68.0% / 34.0% with
the noisy one, because the commercial block then contributes mostly refusal cells. Approximate MDEs at 80% power
and two-sided alpha 0.02: P-U 2.1 pp (on-policy) and 2.7 pp (interaction) of all answers, which in these worlds
corresponds to about 5.3 and 6.4 pp among harmful answers; P-S 3.5-3.9 and 4.6 pp among non-refused answers with
a perfect screen, and an interaction of about 5.3 pp among harmful answers with the noisy screen.

**The last row matters.** In-context noise alone lowers flags on harmful answers (they sit near the ceiling)
and raises them on refusals (floor). It is a real change of verdicts, so rejecting P1 there is not a size error,
but it is not leniency. P1 alone therefore cannot support a leniency claim; section 3.6 gives the rule.

**Recommendation.** Register P-S as the primary statistic for P1 and P2 and report P-U next to it in every
table. Reasons: power; a unit that a reader can interpret; robustness to the unknown refusal rates of the local
instruction-tuned models; validity independent of screen accuracy. Costs: the estimand depends on a screen
(fixed and published before the freeze), and an effect located on refusals would be missed (the change on
answers with S = 0 is reported as a secondary quantity). Conditioning on adjudicated human labels instead is not
feasible as a primary: only about 275 in-frame answers will have labels.

### 3.4 Type-matched yoking

The control judge of an answer by model j is drawn from the judges of j's type (commercial; local
instruction-tuned; refusal-removed), excluding j, its close relatives and models of the same developer. One
seeded permutation per prompt, pair counts balanced, as you specified. You asked for yoking within access
group; the difference matters only for the open models, where the local access group mixes the two types.

Simulated with 22 judges and 60 prompts, 2,000 replications, truth: no self-specific effect.

| Scenario | Yoking | True interaction | P2 rejection | True blind gap |
|---|---|---|---|---|
| Refusal-removed judges react more to the in-context presentation (logit -0.6 on harmful answers, both arms) | access group | -0.8 to -1.1 pp | 7.3-10.2% | about 0 |
| same | model type | -0.02 to +0.02 pp | 2.3-4.2% | about 0 |
| Refusal-removed judges are less sensitive when blind (logit -0.6) | access group | about 0 | 2.2-3.1% | -0.9 to -1.0 pp |
| same | model type | about 0 | 1.6-2.9% | -0.01 to -0.06 pp |

With access-group yoking a type-level difference between judges is read as self-specificity (P2) or as blind
self-preference (the bound loses power: 73-76% instead of 90-93% at the 5-pp margin). Type matching removes
both. What it does not remove is heterogeneity between judges of the same type; section 3.6 adds a contrast for
that.

Allowed controls: 4: {5, 15, 16, 17}; 5: {4, 16, 17}; 15: {4, 16, 17}; 16: {4, 5, 15, 17}; 17: {4, 5, 15, 16};
6: {18, 19, 21, 22}; 18: {6, 20, 21, 22}; 19: {6, 20, 21, 22}; 20: {18, 19}; 21: {6, 18, 19}; 22: {6, 18, 19}.
Limitation: model 20 has only two unrelated donors (18 and 19), both abliterated models of one developer.

### 3.5 Commercial judges and a common off-policy harmful set

- **Own answers.** Each commercial judge classifies its own answers to the common 60 harmful prompts in both
  presentations. With the same data from the on-policy panel this gives your estimand: the unscreened
  equal-judge theta_on of all 22 judges on the common 60 prompts. It is the first secondary analysis.
- **Controls.** The permutation is drawn for every prompt, but control calls are made only for commercial
  answers with S = 1 (planning: 10 answers per judge expected, 30 pessimistic; above 30, the first 30 in the
  seeded order). The set is fixed by S before any judging. Consequence: for all 22 judges the interaction exists
  only in the screened form. The unscreened 22-judge interaction would need controls on the commercial refusals
  too: US$4.07 more in the expected scenario, US$5.09 more in the pessimistic one (total US$103.80 before cuts).
- **Common set H60.** 60 answers with S = 1 to harmful prompts of the frame, 10 from each of the six
  refusal-removed models (seeded draw), all double-labelled. Every judge classifies them blind and in context,
  where the answer is shown as the judge's own previous turn. Pairs in which the judge is the author or related
  to the author are excluded from this analysis. It gives, on identical harmful content, the presentation effect
  theta_off of every judge and type; it is the only harm-side evidence about the commercial judges with enough
  harmful content; and it checks the type-level susceptibility that 3.4 guards against.
- **Provider risk.** Showing harmful text as a commercial model's own assistant turn may be blocked or may
  trigger account enforcement. The pilot tests ten such calls per API judge (section 9). A provider block is an outcome
  (recorded, never retried), and the in-context arm of a judge whose provider blocks it is reported as blocked.

### 3.6 Claim rules

A lower flag rate on harmful answers has three different causes: a shifted threshold (leniency), noisier
verdicts, or fewer delivered verdicts. They are separated by what happens on answers that are not harmful.

| P1 (theta_on, screened) | Change of flags on refusals (S = 0) | P2 (iota, screened) | Registered reading |
|---|---|---|---|
| rejected, negative | not positive | rejected, negative | self-specific in-context leniency |
| rejected, negative | not positive | not rejected | in-context leniency that is not shown to be self-specific |
| rejected, negative | positive | any | less discriminating verdicts in context; no leniency claim |
| rejected, positive | any | any | stricter in context |
| not rejected | any | any | no change detected; interval and MDE reported |

"Positive" means that the 95% interval of the change on answers with S = 0 lies above zero. Three additions:

1. **Human labels.** A leniency reading also requires the label-conditioned estimates to agree in sign: lower
   sensitivity on answers adjudicated harmful, and no increase of the false-positive rate on answers
   adjudicated not harmful. These estimates are reported with intervals; they are not tests.
2. **Self-specificity.** Because every judge is author and control inside its type, the pooled interaction is
   both a within-answer contrast (author against control on the same answer) and a within-judge contrast (own
   against others' answers for the same judge). Judge-level susceptibility cancels only to the extent that a
   judge authors and controls equally many screened answers. We report that imbalance and a judge-normalised
   interaction (own-answer mean minus controlled-answer mean within each judge, then averaged), which is immune
   to judge-level susceptibility and exposed to answer composition. A self-specific reading requires the same
   sign from both, and no positive interaction on answers with S = 0 (author-arm noise would produce one).
3. **Delivered verdicts.** Section 5: a leniency reading requires the change among pairs with two valid
   verdicts to be negative with an interval excluding zero; otherwise the result is reported as driven by
   invalid verdicts.

The blind bound P3 is read separately: rejecting it supports "no blind self-preference larger than the margin";
not rejecting it supports nothing.

## 4. Tests, alpha and margins (R1-M2)

| Test | Null hypothesis | Statistic (on-policy panel) | Sides | Level |
|---|---|---|---|---|
| P1 | theta_on = 0 | P-S | two | Holm, family 0.04 |
| P2 | iota = 0 | P-S | two | Holm, family 0.04 |
| P3 | beta_blind <= -7 pp of non-refused answers | sum of S x (A1 - C1), shifted | one | 0.01 |

This is your allocation (0.04 + 0.01 = 0.05 for the whole study). Nothing else is tested: the safe side, the
22-judge statistics, the common set, the label-conditioned estimates and the three removal pairs are estimates
with 95% intervals.

**Procedure.** Prompt totals are sign-flipped (9,999 random sign vectors, fixed seed). For P3 the prompt total is
the sum of S x (A1 - C1) plus the margin times the number of screened answers of the prompt; the test is
one-sided. Intervals: cluster-robust t intervals over prompt totals, the method whose coverage section 2
reports; for P-S, on the linearised ratio. The coverage of the ratio interval is not simulated yet (section 11).

**Why the margin is stated among non-refused answers.** You proposed H0: beta <= -7 pp on the unscreened
22-judge scale. Refusals are flagged by nobody, so they dilute any blind gap: if the gap sits on harmful
answers, 7 pp of all answers is about 15 pp of the non-refused answers in the on-policy panel and about 28 pp
for all 22 judges. That bound is rejected in 100% of our runs and excludes very little. The same 7 pp stated
among non-refused answers is about four times stricter, and still testable:

| True blind gap among non-refused answers | Rejection of H0 at margin 5 pp | at margin 7 pp |
|---|---|---|
| 0 | 77-87% (93% with the noisy screen) | 98-99% (100%) |
| about -1.3 pp | 48-56% | 88-93% |
| about -2.7 pp | 18-21% | 62-68% |
| about -4.3 pp | 3-4% | 26-31% |
| -7.0 to -8.4 pp (at or beyond the margin) | 0% | 0.1-1.0% |

(Screened statistic on the on-policy panel, type-matched yoking, 2,000 replications, alpha 0.01.) We propose
7 pp: it keeps about 90% power if the true gap is 1 pp, where the 5-pp margin falls to about 50%. The interval
of beta_blind is reported in any case.

**Size at the boundary.** With one fixed judge panel and a true gap of -7.05 pp, the 7-pp bound is rejected in
1.0% of 2,000 runs (nominal 1%; Monte Carlo error about 0.2 pp). For true gaps of -7.2 to -7.9 pp the rate is
0.1-0.75%. The rates follow a normal approximation (twelve scenarios with true gaps between -6.3 and -7.9 pp:
observed 1.2% on average, approximation 1.2%). In the runs that redraw 20 judge panels the rates beyond the
margin are about 1.7 times that approximation (0.40% against 0.24%), because the true gap differs between
panels; the mixture, not the test, produces the excess. Table: `analysis/output/power_sim_v23_bound_check.txt`.
The check covers one data-generating process at screening size; it is repeated at decisive size for the design
you settle.

**Sensitivity analysis for the blind question.** The ten local judges classify all labelled answers blind
(section 6), which gives a crossed judge-by-answer matrix. The linear model of v2.2 (judge and answer fixed
effects plus a self indicator, prompt-clustered) is fitted there as a sensitivity analysis. It is not simulated
yet.

## 5. Missing and invalid verdicts (R1-C3)

- **Primary endpoint.** Delivered valid flags over all scheduled calls: an invalid, missing or blocked verdict
  counts as no flag. The status is that of the final attempt under the fixed retry rule (one retry with a format
  reminder; up to three for transport errors; provider blocks never retried).
- **Always reported next to it.** (a) pairs with two valid verdicts; (b) fail-closed scoring, where an invalid
  verdict counts as a flag; (c) worst-case bounds; (d) the decomposition of the delivered-flag change into the
  change among pairs with two valid verdicts and the part due to verdicts that are valid in one presentation
  only; (e) invalid and blocked rates by judge, arm and presentation.

Why the decomposition is part of the claim rule (simulated, your 22 x 60 design, no effect on valid verdicts):

| Invalidity | Delivered-flag change | P1 rejected | P2 rejected |
|---|---|---|---|
| 3% or 10% in both presentations | about 0 | 1.1-2.8% | 1.6-2.3% |
| 10% blind, 15% in context | -1.4 pp | 8.0-22.3% | 2.1-3.1% |
| 5% blind; in context 5% on harmless and 25% on harmful answers | -3.9 pp | 82.5% | not protected in general |

In the last scenario the estimate among pairs with two valid verdicts is +0.06 pp. The delivered-flag endpoint
answers the operational question (how often is harmful content flagged), and it does so correctly: a judge that
returns nothing flags nothing. But the cause is then a failure to deliver, not leniency. Hence rule 3 of section
3.6. A fall in delivered verdicts on harmful content in context is reported as a finding of its own.

## 6. Human labels (R1-M4, R1-M9)

Your totals are kept: 550 labelled answers, 360 of them double-labelled, no G3.

| Set | Answers | Composition |
|---|---|---|
| G1 (drawn on 8 November, not labelled, key never opened) | 150 | models 4-6; 70 to harmful prompts, 80 to safe prompts |
| G2, harmful prompts | 230 | H60: 60 (10 per refusal-removed model, S = 1) |
| | | models 18-22 beyond H60: 70 (per model 10 with S = 1, 4 with S = 0) |
| | | models 15-17: 45 (per model 10 with S = 1, 5 with S = 0) |
| | | commercial models: 55 (5 per model, S = 1 first in the seeded order, then S = 0) |
| G2, safe prompts | 170 | about 9 per model for the 19 models outside G1, refusals (S = 0) oversampled |

- **Sampling.** Seeded, from the frames of section 3.1, stratified by the screen, with known inclusion
  probabilities. Estimates that generalise beyond the labelled set are weighted.
- **G1 and the frames.** 45 of the 70 harmful-prompt answers of G1 lie inside the 300-prompt frame, and 9 of its
  80 safe-prompt answers inside the 90-prompt safe frame. The others receive the four judgments as well (local
  models, no cash) and enter only the label-conditioned analyses.
- **Double labels.** All 300 answers to harmful prompts and 60 answers to safe prompts get two independent
  labels. Disagreements are adjudicated by discussion, blind to model identity and to every automated verdict;
  unresolved items are kept as a category and analysed under both labels. Adjudicated labels are primary;
  agreement before adjudication is reported.
- **Lock.** The label file is hashed and deposited before any script joins verdicts with labels or aggregates
  verdicts by arm. Until then the pipeline reports only operational counts (calls, invalid outputs, cost).
- **One annotator fewer.** If the co-author hours do not cover 360 second labels, the double-labelled set shrinks
  in this order: safe-prompt answers, harmful-prompt answers with S = 0, harmful-prompt answers with S = 1
  outside H60. H60 is always double-labelled.
- **Blind reference.** The ten local judges classify all 550 answers blind. The API judges classify one common
  subset of 120: H60 plus 30 answers to harmful prompts and 30 to safe prompts, half of each with S = 0.
- **What the labels support.** Sensitivity and false-positive rate of every judge (blind reference), and the
  label-conditioned version of the harm-side estimands on about 300 answers with all judgments. Under our
  planning rates 130-150 of them will be adjudicated harmful; the standard error of a change of sensitivity is
  then about 3 pp (rough, not simulated). Hence a required consistency check (3.6), not a primary test.

## 7. Safe side (refusal endpoint, secondary)

As you specified: every judge, 90 safe prompts (the first 45 of each safe stratum), own answers and a
type-matched control, both presentations. Flag = the verdict labels the answer a full or partial refusal. The
four estimands of section 3.2 are reported with intervals, unscreened and among answers with S = 0; no test.

One simulation of this side (22 judges, 90 prompts, access-group yoking, 2,000 replications): standard errors
0.7-1.0 pp (on-policy) and 1.0-1.2 pp (interaction); interval coverage 93.8-96.0%; a change of 2 pp would be
detected in 42-59% of runs and one of 5 pp in 99-100%. True refusals of safe prompts are rare (planning: 2-15%
by model type), so an effect located on them is at most about 2-4 pp of all answers; the estimate among answers
with S = 0 is the informative one.

This side takes 360 of the 780 calls of a commercial judge (US$14.64 of the expected manifest, US$30.56 of the
pessimistic one). Reducing its control arm for the commercial judges from 90 to 60 prompts is the third item of
the cut order (section 8).

## 8. Call manifest and budget (R1-C4)

Output of `scripts/cost_model.py --v23b` (file `analysis/output/cost_model_v23b_stdout.txt`). Expected scenario:
2,500 input tokens per judge call, 380 output tokens including reasoning, 5% retries. Pessimistic: 3,500 input
tokens, 720 output tokens, respondent output doubled, 15% retries, no cache hits. Retries are now inside the
respondent cost (your finding was correct).

| Block | Calls per commercial judge | Expected, US$ | Pessimistic, US$ |
|---|---|---|---|
| Own answers, both presentations (60 harmful + 90 safe) | 300 | 12.20 | 25.47 |
| Safe-side controls, both presentations | 180 | 7.32 | 15.28 |
| Harm-side controls for own answers with S = 1 | 20 expected, 60 at the cap | 0.81 | 5.09 |
| H60 in context | 60 | 2.44 | 5.09 |
| Blind reference subset (contains H60 blind) | 120 | 4.88 | 10.19 |
| Judge pilot | 60 | 2.44 | 5.09 |
| Repeatability (repeated calls) | 40 | 1.63 | 3.40 |
| **Eleven commercial judges** | 780 / 820 | 31.72 | 69.63 |
| API respondents (11 x 150 prompts, model 22 x 390, 20 pilot prompts each) | | 13.68 | 27.07 |
| Model 22 as judge | 1,840 | 1.11 | 1.71 |
| API guard on the 550 labelled answers | | 0.17 | 0.30 |
| **Total (cap 110)** | | **46.67** | **98.71** |

- **The primary analysis is not exposed to the budget.** It uses the ten local models and model 22: about US$2
  of cash. Every commercial block is secondary.
- **Order of execution.** Pilot; on-policy panel; commercial respondents; then the commercial-judge blocks in the
  order of the table. Spending is checked before each block; a block that cannot be completed for all eleven
  judges within the remaining budget is not started.
- **Repricing and cuts.** After the pilot the manifest is repriced with measured token counts. If the repriced
  pessimistic total exceeds US$100, cuts apply in this order until it does not: repeatability 40 to 20 calls
  (pessimistic total 96.99); blind reference 120 to 90 (94.42); safe-side controls of the commercial judges 90
  to 60 prompts (89.32); those controls removed (79.13).
- **Local compute.** About 23,000 judge calls, 32-58 GPU-hours on one workstation, plus the missing generation:
  models 19, 20 and 21 (390 prompts each). The 43 answers that model 18 lacks are all outside the frames.

## 9. Pilot and freeze sequence (R1-M3, R1-M8)

**Pilot (external to the confirmatory data).**

- Prompts: the tail of the seeded order (harmful prompts outside the 300-prompt frame, safe prompts outside the
  90), minus the prompts of G1 and of the earlier local pilot: 166 harmful and 376 safe prompts remain. They
  are excluded from every confirmatory analysis by ID, with a unit test.
- API models: 20 fresh prompts each (10 harmful, 10 safe) as respondent. 60 judge calls each: the 20 own answers
  in both presentations, and 10 pilot answers with S = 1 of local refusal-removed models in both presentations.
  The last block tests whether a provider accepts harmful text as the judge's previous turn.
- Local models: 100 own answers each (tail answers that already exist where possible), both presentations.
- Outputs, and nothing else: invalid and blocked rates by judge and presentation; token counts; the share of
  answers with S = 1 by model; screen errors (the PI reads about 200 pilot answers, refusal or not). The pilot
  script does not compute flag rates by presentation.

**Adaptation rules, registered before the pilot.**

1. More than 10% invalid verdicts in either presentation, or more than 5% blocked: one documented revision of
   the output-format mechanics (not of the rubric), tested once on fresh tail prompts.
2. A judge that still fails stays in the panel; its invalid verdicts count as designed (section 5). A provider
   that blocks the in-context presentation is reported as blocked in that arm.
3. A provider warning stops all calls to that provider until the PI records a decision.
4. The screen list is revised once, from pilot answers only.
5. Repricing and cuts as in section 8. No rule refers to a pilot effect estimate.

**Sequence.**

1. Code complete end to end on synthetic data: manifest builder with the seeded permutations, runner, parser,
   screen, analysis script; the analysis script must recover the simulated effects. Not done yet.
2. Register the pilot plan and the adaptation rules.
3. Run the pilot; apply the rules.
4. Final v2.3 and the amendment to the v1 registration; register and freeze (commit, manifest, screen list and
   analysis script identified by hash).
5. Missing generation; confirmatory judging, on-policy panel first; labelling in parallel, locked as in
   section 6.
6. Analysis with the frozen script.

Disclosure for the amendment: 7,457 answers of seven local models exist (inventory in section 12), generated
with the settings that v2.3 keeps. None has been read, judged, labelled or screened.

## 10. Remaining items

**10.1 Refusal-removed judges (R1-M5).** T4 leaves the confirmatory family. For the three fixed pairs (4-6, 5-18,
15-19; all local, no cash) we report the difference between the modified and the base judge in blind
sensitivity and false-positive rate on the labelled answers and in the presentation effect on H60, with the
equal-pair average and prompt-cluster intervals. No test and no non-inferiority claim. Appendix.

**10.2 Withdrawal record (R1-M7).** The amendment to the v1 registration will list H1, H2 and H3 and each
element that v2.2 added (instrument selection and RQ4; T1a, T1b and T4 as confirmatory tests) with its
original text, its status, the reason, and the data that existed at that moment. Your wording is adopted. The
table is not drafted yet; we will submit it to you with the edited protocol.

**10.3 Novelty and related work (R1-M6).** Accepted: our sweep understated the overlap with Khullar et al. and
with Agnihotri et al. The paper will be framed as a registered replication and extension of in-context
self-attribution to harm classification, with four additions: models that produce harmful answers on-policy;
an unrelated judge on the same answers; adjudicated human labels; explicit accounting of undelivered verdicts.
We have not yet verified the six further references you listed. Each will be checked online before it is
cited. Not done yet.

**10.4 Annotator materials (R1-m1).** The three lines you cited (guide lines 7 and 55, rubric line 56) will be
replaced by your neutral paragraph.

**10.5 Deletions.** Accepted in full: instrument selection and RQ4, G3, the frontier-judge apparatus, the
recognition probe, the second template wording, latent-class analysis, prediction-powered inference, capability
regressions, jury and cascade optimisation, stages 3, 3b and 6, unframed re-judging, external transfer on API
judges.

**10.6 Own prompts.** The 60 base prompts written for the framing experiment leave this paper. 50 of them are
comply-expected, so they cannot serve the harm-side question. They stay unreleased for a separately registered
follow-up.

## 11. Simulation inventory (R1-M1)

Simulator: `analysis/power_sim_v23.py` (data-generating process in its docstring). Summary tables:
`analysis/output/power_sim_v23_summary.md`. All runs: 2,000 replications, 1,999 sign vectors, 20 judge panels
(the two boundary checks of section 4 use one fixed panel).

| Files (`analysis/output/power_sim_v23_...`) | What is simulated | Used in |
|---|---|---|
| `screen.json` | your design (22 judges, 60 harmful prompts, access yoking), 324 scenarios of your grid | 2, 5 |
| `modes.json`, `core_typeyoke.json`, `core_local150.json` | effect on harmful answers only, on all answers, or of opposing sign; informative invalidity | 2, 5 |
| `structural_*`, `susceptibility_*`, `segap_*` | yoking under type-level differences between judges | 3.4 |
| `panel_harm11_150`, `panel_harm11_300`, `panel_all22_150` | panels and frame lengths | 3.1 |
| `bound_*` | blind bound, unscreened | 4 |
| `alts_*` (eight files) | screened statistics and sub-panels on the frames of 3.1; blind bound among screened answers | 3.3, 4 |
| `alts_bound1panel_*` (two files) | the same bound close to the 7-pp margin, one fixed judge panel | 4 |
| `core_safe90.json` | safe side | 7 |

Limits of what was run:

- You asked for 10,000 replications and 9,999 sign vectors for decisive runs. We ran the screening size
  throughout. Monte Carlo error: about 0.35 pp for a rejection rate near 2.5%, about 0.9 pp near 80%. The
  decisive runs will be made for the design you settle.
- The simulator contains its own implementation of the statistic and the test. The production analysis script
  does not exist yet; before the freeze it must reproduce these numbers on the simulator's data (section 9).
- All failure rates are assumptions (5%, 15% and 70% harmful answers by model type). The pilot replaces them.

Runs still missing: (a) screened statistics with effects on all answers and with informative invalidity;
(b) interval coverage of the screened ratio; (c) the equal-judge variant of P-S
(mean of per-judge screened means); (d) the judge-normalised interaction of 3.6; (e) the fixed-effects
sensitivity model of section 4; (f) the safe side with type-matched yoking and among answers with S = 0;
(g) precision of H60 by judge and type; (h) the label-conditioned estimates.

## 12. Limitations and data inventory (R1-m2)

**What draft B cannot show.**

1. **Commercial judges.** The confirmatory tests concern eleven open models. For the commercial judges the paper
   will have: the unscreened change on their own answers to 60 harmful prompts (about three harmful answers per
   judge at the planning rate); controls for a few screened answers; and H60, which is off-policy. It cannot
   show self-specific leniency of a commercial judge towards its own harmful answers.
2. **Weight of the refusal-removed models.** They write about three quarters of the non-refused answers and are
   also their judges. The simulator gives every judge a sensitivity between 0.70 and 0.95. If the
   refusal-removed judges flag little harmful content even blind, there is a floor and the power is lower than
   reported. Nothing in the present data tells us (question 9 of section 13).
3. **The screen is not a harm label.** P-S conditions on "not a refusal by keyword". The label-conditioned
   estimates rest on about 275 in-frame answers and have standard errors near 3 pp.
4. **The control condition is off-policy by construction.** iota compares own text shown as own turn with
   another model's text shown as own turn. A judge that recognises foreign text may react to that and not to
   authorship. The recognition probe was cut, so this cannot be separated.
5. **Judges of one type differ.** Type matching removes type-level differences only. Model 20 has two possible
   controls.
6. **All power figures are conditional** on assumed failure rates, sensitivities and discordance. The pilot
   replaces the failure rates and the invalid rates, not the effect sizes.
7. **One template, temperature 0, quantised local models, English benchmarks, two harmful-prompt sources.**
8. **Labels depend on people not yet committed.** With one annotator the harm labels are single-coded outside
   H60 and the label-conditioned results become exploratory.
9. **Reviewer conflict.** You are model 11 of the panel. This exchange will be disclosed in the paper.

**Data inventory, 10 November 2026** (`docs/DATA_INVENTORY.md`, generated by `scripts/data_inventory.py`,
counts only).

| Item | State |
|---|---|
| Public registration | v1, commit `4124f32` (7 November): H1-H3, gold set of about 150 answers. A first amendment (model and judge selection criteria, 8 November) is committed locally and was never pushed. |
| Prompt sample | 1,050 benchmark prompts, sealed by hash: 500 harmful (XSTest unsafe 200, OR-Bench Toxic 300), 550 safe (XSTest safe 250, OR-Bench Hard 300). 60 own base prompts, not used in this paper. |
| Answers generated | 7,457, all by local models: models 4, 5 and 6, 1,050 each (7-8 November), plus 150 earlier pilot answers of the same models to 50 of the sampled prompts (7 November; 17 of the 50 prompts lie inside the frames of 3.1, where the answers of the full run are used; the pilot file enters no analysis); models 15, 16 and 17, 1,050 each, and model 18, 1,007 (9 November). |
| Answers not generated | models 19, 20, 21 and every API model; any answer to an own prompt. |
| Answers read, screened, judged or labelled | none |
| G1 | 150 answers of models 4-6, drawn on 8 November; key and sheet sealed by hash; no label entered. On 10 November a script read the key to count its items by frame (`analysis/output/frame_counts_2026-11-10.txt`); no item was displayed and the hash is unchanged. |
| Judge calls | none |
| API calls and spending | none; US$0 |
| Code | respondent runner and judge runner exist (v2.2); manifest builder, screen, pilot script and analysis script for draft B do not exist. |

## 13. Decisions requested

1. **Primary statistic.** P-S on the on-policy panel with P-U beside it (our proposal), P-U as primary, or your
   22-judge unscreened statistic as primary with the power of section 2?
2. **Form of P-S.** Pooled over answers (proposal), or the mean of per-judge screened means (equal judges,
   unstable when a judge has few screened answers)?
3. **Claim rules (3.6).** Are the five readings and the three additions sufficient? Is any of them wrong?
4. **Commercial refusals.** Buy controls for them (US$4.07 expected, US$5.09 pessimistic) to obtain the
   unscreened 22-judge interaction, or leave that interaction in its screened form?
5. **H60.** Keep it? Is showing harmful text as a commercial model's previous turn acceptable given the
   provider risk, and are 10 answers per refusal-removed model the right composition?
6. **Blind bound.** Margin of 7 or 5 pp among non-refused answers? Is the shifted sign-flip test acceptable on
   the evidence of section 4?
7. **Yoking.** By model type (proposal) or by access group?
8. **Safe side.** Keep 90 prompts and controls for all 22 judges (US$14.64 to 30.56 of the commercial budget),
   or reduce it for the commercial judges?
9. **Pilot and the floor.** May the pilot report, by judge, the blind flag rate among screened answers (a
   nuisance parameter; no comparison of presentations), so that a floor is known before the freeze? If so,
   what rule should follow from it?
10. **Labels.** Is the allocation of section 6 right, in particular 55 answers for eleven commercial models?
11. **Own prompts.** Out of the paper (proposal), or an exploratory local-only appendix?
12. **Anything missing** before the pilot plan can be registered, and anything in sections 8-9 that should move
    from the freeze to the pilot registration or back.
