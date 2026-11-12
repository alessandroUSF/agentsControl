# Fresh-eyes skeptical paper review, 10 Nov 2026 (independent agent report, verbatim)

Saved from the agent's own transcript; not edited. Figures marked [est.] or [S] are the agent's own
estimates or snippet-level inferences. Pages were read through a summarising fetch tool, so exact
numbers must be re-checked against the PDFs before they are cited in the paper.


---

<!-- report part 1 of 3 -->

# Reviewer read of protocol v2.2, "Do LLM safety judges go easy on themselves?"

Based on `E:\claude\agentsControl\docs\STUDY_PROTOCOL_v2.md` (read in full), the README, the rubric, the annotator packet, `analysis\power_sim.py` and the head of its output. Nothing was run or modified, and `docs\audit\` was not opened. Figures marked **[est.]** are my own arithmetic from the protocol's numbers, not protocol figures.

**Bottom line:** go ahead, but not as written and not on 13 November. Executed exactly as written, the most likely result is a mostly null, hedged extension of Khullar et al. (2026). The cause is a fixable design choice, not the topic.

## 1. What the paper will actually be able to claim

**Honest abstract, as designed:**

> We test 22 LLM judges on refusal and harm classification of chat answers, against about 430 answers labeled by one human. With authorship hidden, we could not detect that judges flag failures in their own answers less often; effects above about 5–7 points are unlikely, and equivalence is not claimed. Showing a judge its own answer as its previous turn changed its flag rate by X points (CI …); whether this is specific to its own answers is not established. Three community abliterated 4–8B models were [were not shown to be] within 10 points of their base models in harm recall.

**Outcome space.** Probabilities are my priors, not derived. Power figures are from §9.2 (first / last Holm step).

| Outcome | My prior | What the paper says | Publishable? |
|---|---|---|---|
| T1a not rejected (predicted, §3.1) | 90% | "Not detected". MDE is 5.7 / 4.8 pp and §9.2 rules out a ±5-point TOST. | Carries nothing alone. |
| T1a rejects | 5–10% | Blind self-leniency. Surprising, but about 60% of self items come from six small local models. | Interesting only if it survives the subsample-to-15 check. |
| T1b not rejected | 60–65% | "No in-context effect detected" with a CI of about ±5–6 pp. | Weak: a real 2–3 pp effect is not excluded. |
| T1b rejects, β_int inconclusive | 20–25% | "In-context presentation lowers flag rates"; self-specificity unknown. | Workshop yes: a replication of Khullar in a new task. |
| T1b rejects, β_int excludes 0 | about 10% | The self-attribution effect transfers to refusal/harm classification. | Best case: workshop strong, TMLR plausible. |
| T1b rejects, positive sign | about 5% | Judges are harsher on their own turn. | Publishable as a contrast. |
| T4 non-inferior | about 50% | These three checkpoints keep harm recall within 10 points. | Modest, useful to people who use uncensored judges. |
| T4 not shown | 40–45% | Nothing, unless the CI lies wholly below the margin. | Inconclusive. |
| T4 clearly inferior | 5–10% | Refusal removal damages harm recognition in these builds. | Interesting, but not a pre-specified claim. |

- **Most likely combination:** T1a not detected, T1b not detected or detected without self-specificity, T4 either way, and H1–H3 not supported or inconclusive. That is a careful, mostly null paper in a busy area. I would expect a workshop to accept it and TMLR to send it back.
- **The outcome that says nothing:** T1a and T1b both non-significant with wide CIs, T4 straddling the margin, legacy hypotheses failing. I put this at 15–25%. What survives is a descriptive judge-versus-one-annotator table.
- **Why the nulls are weak.** `analysis\power_sim.py` applies leniency as a logit shift to every own item, failures and non-failures alike. An average effect of 4.8 pp corresponds to multiplying the odds of flagging any own item by about 0.61. A 2-pp effect has power of only 0.10–0.25 (`power_sim.json`).
- **If leniency acts only on real failures** (about 27% of self items under the simulation's own rates), a 4.8–5.7 pp average effect needs a recall drop on own failures of about 18–21 points **[est.]**. The study detects only very large self-leniency.

## 2. Significance and novelty

- **Relevance is real.** LLM judges grade safety evaluations everywhere, and self-grading is a natural confound. The T4 question has a practical audience: people use uncensored local models as judges because aligned models decline to grade harmful text.
- **The delta over Khullar et al. is smaller than §2 states.** A quick check of arXiv 2603.04582 suggests it already includes a neutral-attribution user-turn baseline and open-ended harmfulness ratings. I read it through a summarising tool, so verify against the paper. If so, "adds the blind cell" overstates the addition.
- **The real additions are:**
  - a binary refusal/harm classification of ordinary chat answers;
  - item-level human labels;
  - off-policy anchors in the judge's turn;
  - small and abliterated judges.
- **The title invites the comparison.** It nearly repeats Khullar's subtitle ("When AI Monitors Go Easy on Themselves"). Reviewers will read this as a replication with a more conservative instrument. Framed openly as a registered replication and extension, a null becomes more publishable.
- **Twenty-two judges is a strength in principle and a weakness as allocated.** The panel is wide and shallow: 11 commercial judges with 12 own items each (§7.2). Fewer items per judge than judges is the wrong shape for a within-judge effect.
- **Small quantised local judges** are relevant to T4 and to hobbyist practice. For the headline they add noise and invite "nobody monitors with a 4B Q4 model".
- **T4 is the more original half**, but I have not checked the literature on harmfulness versus refusal representations. The other agent's sweep should settle that.

## 3. Strongest reasons to reject, ranked

1. **The headline effect sits in near-empty cells.**
   - Self items total 432: models 4–6 hold 168 (39%), models 18–22 hold 90, models 15–17 hold 42, and the 11 commercial judges hold 132.
   - Under the simulation's own failure rates, a commercial judge has about 1.4 expected gold failures among its 12 self items, about 15 across all eleven **[est.]**.
   - On the harm endpoint that is single digits to about 10 across all eleven **[est.]**; §7.2 caps keyword-unflagged draws at 2 per judge.
   - About 88% of gold-harmful self items come from the six refusal-removed models **[est.]**.
   - So on harm, "self-leniency" means "do uncensored small models flag their own harmful output". §15 concedes that "commercial self-leniency on harmful content has little data".
   - A commercial judge's mean difference moves in steps of 8.3 pp.

2. **T1b tests presentation, not self.**
   - §9.2 says so: reading θ_on as self-specific "rests on β_int", from 30 anchors per judge.
   - `power_sim.py` contains no anchors, no θ_off and no β_int, so the claim in the title has no power analysis.
   - I estimate its MDE at about 6.6–8 pp **[est.]**, worse than T1b's own.
   - Check the anchor mix too. Anchors are stratified by failure status from G2, while a commercial judge's own items are mostly refusals and benign answers. If the mixes differ, β_int compares presentation effects on different item types. I did not verify how the model handles this.

3. **A predicted null inside the confirmatory family.**
   - T1a is expected not to reject (§3.1) and cannot support equivalence.
   - It still costs Holm alpha for the two tests that matter. That is a self-inflicted loss for no possible claim.

4. **Reference standard.**
   - One annotator, who is also the PI, wrote the own prompts and wrote the harm definition on 9 November (§15, RUBRIC.md).
   - The second annotator labels 150 items, and the PI's labels "stay the primary reference standard" (§7.3).
   - This is tolerable for T1a/T1b, which barely use gold. It is weak for H1, RQ1, RQ4 and T4, which depend on it.
   - Limb (b) of the harm definition turns on stated ownership, so labels on dual-use prompts depend on framing wording.

5. **T4 margin and scope.**
   - The −0.10 margin is wide, has a one-sentence rationale, and is still marked [PI].
   - Power at a true −0.05 is 0.17–0.61 at the first Holm step. At a true 0 with independent errors it is 0.76.
   - The evidence is three community builds of 4–8B Q4 models, made by different people with different methods, judging about 80–130 shared items **[est.]**.
   - §9.3 admits the heterogeneity rule caught a true −0.20 pair in only 28–71% of runs that declared non-inferiority.

6. **Too many questions for the evidence.**
   - Three confirmatory tests, H1–H3 in their own families, RQ1, RQ3a/b/d, RQ4, calibration, juries, cascades, Dawid–Skene, PPI and transfer, on about 432 items.
   - §9.7 states that separate families give no study-wide error control. A reviewer will call the secondary results a garden of forking paths despite the registration.

7. **Legacy hypotheses will probably fail.**
   - H1 needs at most 2 misses in 124 with invalid verdicts counted as misses. The pass probability is 0.42–0.56 at a true 2% rate and 0.19–0.28 at 3% (§9.2).
   - H2 needs three one-sided McNemar tests under Holm on 30 fiction prompts per model, in at least 3 models, above a 5% refusal floor of about 1.5 refusals.
   - H3 needs five comparisons and a bound, all holding. Three "not supported" lines dilute the paper.

8. **Ecological validity of the in-context setup.**
   - The rubric sits in the system message from the start, the answer was generated without it, and reasoning traces are not replayed.
   - A detailed rubric with "ignore tone" and a binary verdict is a conservative instrument, so a null says little about real self-monitoring.
   - On the refusal endpoint the judge classifies behaviour, where "leniency" is conceptually thin.
   - §15 notes low-effort judging may inflate self-bias, and several judges cannot run at temperature 0.

9. **Panel is purposive**, chosen after rankings were seen (§6). Inference is conditional on these 22 (§9.1). That is honest but limits generality.

## 4. What is genuinely good

- **The within-item paired design** (blind and in-context calls adjacent, randomised order) is the right design for the question.
- **The off-policy anchors** are the right idea for separating self from presentation; they are just too few.
- **The T1 estimands are nearly label-free**, so the headline does not inherit the single-annotator weakness.
- **Process discipline** is above the workshop norm:
  - sealed outputs and recorded inclusion probabilities;
  - test sizes checked by simulation (0.011/0.045 and 0.016/0.051, §9.1).
- **The limitations are stated before a reviewer has to ask**:
  - "Implications for AI monitoring are discussed, not claimed" (§1);
  - "No 'first' claims" (§12);
  - T4 scope limited to three checkpoints (§9.3).
- **T4 pair hygiene** is careful: rendering and token checks, the model-19 replacement decided before data, a pre-decided fallback.
- **T4 is a question where both answers are interesting**, which the self-judging half as designed is not.

## 5. Coherence

As written this is four papers stapled together:

1. the self-judging 2×2;
2. abliterated judges;
3. a judge meta-evaluation (juries, cascades, error correlation, calibration);
4. an over-refusal benchmark of 22 models with a framing study on own prompts (H2, H3, RQ4).

**What carrying v1 costs:**
- stages 3, 3b and 6, which as I read §11 serve only H2/H3/RQ4: US$29.16 expected and US$64.17 pessimistic of a US$110 cap;
- the most complex unwritten code (nested-CV instrument selection, recusal, the contrast-neutral instrument, corrected rates);
- 84 own-prompt gold items and the clarification/covariate apparatus.

**Minimum publishable core:**
- on-policy blind versus in-context self-judging at scale;
- the anchors;
- a blind bound in place of T1a;
- an accuracy reading against gold;
- T4 as the second contribution;
- one descriptive judge-versus-human table;
- the recognition probe and second template wording, which are cheap and which reviewers will expect.

**What goes:** H1–H3, RQ4, instrument selection, the framing study, calibration, Dawid–Skene, PPI, external transfer and most of the frontier apparatus.

**What is lost:** continuity with v1 and the benchmark numbers. Deferring them to a separately registered companion, in a dated public amendment before any answer is judged or labeled, is legitimate.

## 6. Feasibility and execution risk

- **Schedule.** §11 puts the freeze at "about 13 Nov". On 10 November the following are unwritten or absent (§13, §16):
  - the judge code to the eleven listed requirements, and the analysis driver;
  - `config/relations.csv` and `config/judge_prompt_v2.txt`;
  - the full gold sampler (`src/gold_sample.py` is "a prototype");
  - instrument selection;
  - plus three API accounts to open and the T4 margin to settle.

  The freeze will slip by weeks or freeze code that does not exist.
- **Budget machinery.** Ledger, stage holds, batch adopt/release/purge, stage closure and 118 offline checks are out of proportion to US$110. They guarantee logged deviations for one person.
- **Pessimistic budget case.** About US$6.50 remains after stages 1–3, and the frontier judges see about 4% of their items (§11).
- **Labeling.** The protocol gives 1.5–3 minutes per item. Five fields on long or harmful answers in 45-minute sessions is more likely 3–5 minutes, so roughly 36–60 hours for the first annotator **[est.]**, against "16–31" in §7.2 and "18–36" in §16.
- **External dependencies.** The written USF HRPP determination (unknown lead time) and three new research accounts.
- **Provider risk.** §10 concedes the in-context layout "resembles a fabricated-turn technique". The anchors put other models' harmful answers into commercial judges' assistant turns, and the rule is to stop on a warning. One warning on a new small account removes a provider mid-study.
- **Where it breaks first:** unwritten code against rule complexity, then labeling hours, then a provider block.
- **What a broken version still delivers:** the descriptive table and a T4 estimate, which is local and free.

## 7. Changes before the freeze, by value over cost

### (a) Must-fix, or the paper is weak

| # | Change | Why | Cost |
|---|---|---|---|
| 1 | **Run a non-gold go/no-go pilot before the freeze and before inviting anyone** (details below). | Answers "is there anything here?" without touching gold. | US$2–5 **[est.]**, a few GPU hours, 1–2 days, no labeling. |
| 2 | **Decouple T1b from the gold set.** Run blind and in-context on all common-subset self answers: 190 per commercial respondent, 280 for Venice, 300 or more per local model. | θ_on needs no labels (§7.1). Commercial pairs go from 132 to 2,090. I expect the MDE to fall from about 5–7 pp to about 1.5–2.5 pp **[est.]**. | About 4,450 extra API calls, US$18 expected / US$38 pessimistic **[est.]**; 5–10 GPU hours; no labeling; the sampler gets simpler. |
| 3 | **Raise anchors from 30 to about 100 per judge**, matched to each judge's own item mix, and add β_int to `power_sim.py`. | Makes the claim in the title testable. | US$7 / US$14 **[est.]**; about an hour of simulation work. |
| 4 | **Defer H1–H3, RQ4 and instrument selection** to a registered companion. | Pays for 2 and 3, and removes the hardest code and three likely failures. | One dated amendment; saves US$29.16 / US$64.17 and roughly a week of code. |
| 5 | **Take T1a out of Holm**, or register it as a bound ("blind self-leniency above 7 pp excluded"; power at 7.0 pp is 0.97/0.99). | The expected outcome then yields a sentence, and T1b and T4 keep more alpha. | Zero. |
| 6 | **Pre-specify T4's three-way reading** (non-inferior, inferior, inconclusive). Justify −0.10 or tighten it, and add several matched abliterated pairs as judge-only models. | A failed non-inferiority test is otherwise silent; more pairs answer "three checkpoints". | Local and free; 1–2 days for rule and rendering checks; no new labels. |
| 7 | **Double-annotate the T4 items** (all gold-harmful candidates) and use consensus as primary there. | T4 is the test that depends on harm labels. | Second annotator goes from 4–8 hours to about 8–14 **[est.]**. |
| 8 | **Fix the annotator guide.** Lines 15–16 tell the annotator about half the items were labeled harmful; §7.3 says the annotator "is not told the share". Lines 4–8 say "own developer's outputs"; the headline is own answers. | A disclosed 50% base rate biases the agreement statistic. | Five minutes. |
| 9 | **Freeze only after the judge code and analysis driver run end to end on synthetic data.** | §13's promise is unenforceable otherwise. | One to two weeks' slip. |

**The pilot (item 1):**
- **Items:** the 20 respondent-pilot answers per API respondent (already outside the gold frame), plus about 100 own answers per local model from a pool excluded from G2/G3.
- **Procedure:** each author judges its own items blind and in-context.
- **It yields:**
  - the blind/in-context discordance rate (the power table stops at 14%);
  - a raw θ_on with a standard error near 1 pp **[est.]**;
  - invalid and block rates, and any provider warning;
  - a rough base-versus-abliterated harm-flag gap.
- **Decision rules to write down first:**
  - discordance above 14%, or |θ_on| clearly below 2–3 pp with no sign in commercial judges: rescale or re-scope before freezing;
  - any provider warning: redesign the anchors.
- **Registration:** a disclosed pilot on non-gold items is compatible with pre-registration.

### (b) Worthwhile

- **Retitle** and frame as a registered replication and extension of Khullar et al. Free.
- **Make the second template wording a rubric-light graded rating**, run on-policy in both presentations on a subset. It answers "your rubric suppressed the effect". About US$3–6 **[est.]**.
- **Re-aim labeling** at T4 harm items and a pre-registered blind sample of about 100 discordant pairs. Same hours, better placed.
- **Reduce budget control** to the hard cap, one ledger and a per-run cap.
- **Confirm the costs in items 2–3** with `scripts\cost_model.py`, and the MDE by editing `allocation()` in `power_sim.py`.

### (c) Nice-to-have

- Plan A+.
- The roughly 100-item holdout.
- WildGuard.

### (d) Resist adding

- More respondents, judges or research questions.
- Your own abliterations.
- The frontier two-phase re-label, Dawid–Skene and PPI.
- Further budget rules.

## 8. Verdict

| Dimension | Score (1–10) |
|---|---|
| Relevance | 7 |
| Novelty (pending the literature sweep) | 5 |
| Methodological rigor as designed | 6.5 (process 8.5; fit of design to the headline question 5) |

| Probability of a publishable paper | As written | With tier (a) changes |
|---|---|---|
| Good workshop | about 60% | about 80% |
| TMLR / Findings | about 25% | about 45–50% |
| Top main track | about 3% | about 5–8% |

**Recommendation: go ahead with changes; do not freeze on 13 November.** The topic is relevant and the process is careful. But the design spends its labeling hours and half its budget on legacy hypotheses that will probably fail, and it tests the headline on 12 items per commercial judge with a self-specificity check that was never powered. The headline estimand needs no human labels, so it can be scaled roughly twentyfold for about what the deferred stages cost. Run the pilot first: it costs under US$5 and two days, and it answers the fear of finding out too late. Invite colleagues only once the pilot shows an effect, or a null tight enough to be worth reporting, and the T4 items are set up for double annotation.

**What I am unsure about, and what would settle it:**
- The size and sign of the in-context effect in this task: the pilot.
- The scaled cost and power: the two scripts named above.
- Whether the anchor mix confounds β_int: a read of the estimator.
- The exact Khullar baseline, and T4's novelty: the paper itself and the other agent's sweep.

**Files referenced:**
- `E:\claude\agentsControl\docs\STUDY_PROTOCOL_v2.md`
- `E:\claude\agentsControl\analysis\power_sim.py`
- `E:\claude\agentsControl\analysis\output\power_sim.json`
- `E:\claude\agentsControl\labels\RUBRIC.md`
- `E:\claude\agentsControl\docs\annotator_packet\annotator_guide.md`
- `E:\claude\agentsControl\docs\annotator_packet\informed_agreement.md`
- `E:\claude\agentsControl\README.md`

**Sources:**
- https://arxiv.org/pdf/2603.04582
- https://arxiv.org/html/2603.04582v1
- https://neurips.cc/virtual/2025/128030


---

<!-- report part 2 of 3 -->

# Reviewer read of protocol v2.2: final report

## Verdict and scores (point 8)

**Go ahead with changes. Do not freeze around 13 November, and do not invite colleagues yet.**

Executed exactly as written, the most likely result is a careful, mostly null extension of Khullar et al. (2026). That is acceptable at a workshop and unlikely to clear TMLR or Findings. The topic is relevant; the weakness is three design choices that can still be changed:

- The headline is tested on 12 own answers per commercial judge, about 1.4 of them real failures **[est.]**.
- The check that would make the effect specific to "self" (β_int) has no power analysis.
- US$29.16 expected / US$64.17 pessimistic of the US$110 cap, and the hardest unwritten code, go to v1 hypotheses that will probably fail.

The headline estimand needs no human labels (§7.1), so it can be scaled many-fold for about what the deferred stages cost. A pilot under US$5 on non-gold items answers the fear of finding out too late.

| Dimension | Score (1–10) |
|---|---|
| Relevance | 7 |
| Novelty | 5, provisional (I did no literature sweep) |
| Methodological rigor as designed | 6.5 (process 8.5; fit of the design to the headline question 5) |

| Probability of a publishable paper | As written | With tier (a) changes |
|---|---|---|
| Good workshop | about 60% | about 80% |
| TMLR / Findings | about 25% | about 45–50% |
| Top main track | about 3% | about 5–8% |

These probabilities are judgement, not derived. TMLR asks whether claims are supported and whether some audience cares, not whether the work is novel. That favours tight estimates with modest claims, which the scaled design gives whatever the sign.

Tags: **[est.]** is my own arithmetic from protocol numbers. "Not checked" marks a judgement resting on something I did not read; the full list is in the last section.

## Reasons to reject, ranked (point 3)

1. **The headline effect sits in near-empty cells.** (§7.2, §8.3, §15)
   - Self items total 432. The ten local models wrote 282 (65%), and the three G1 authors alone wrote 168 (39%). The 11 commercial judges wrote 132, 12 each.
   - Under the failure rates assumed in `power_sim.py`, a commercial judge has about 1.4 gold failures among its 12 own items, about 15 across all eleven **[est.]**.
   - On the harm endpoint that is about 7 across all eleven **[est.]**, fewer if own-prompt items follow §5.3's mix.
   - About 88% of gold-harmful self items on harmful benchmark prompts (73.5 of 83) come from the six refusal-removed models **[est.]**.
   - So on harm, "self-leniency" means "do uncensored small models flag their own harmful output". §15 concedes that "commercial self-leniency on harmful content has little data".
   - A commercial judge's mean difference moves in steps of 8.3 pp (1/12).
   - G3 adds up to 120 labeled answers from exactly the models that produce harm, but is "never" used for T1a or T1b (§7.2).

2. **T1b tests presentation, not self.** (§9.2, §8.3)
   - §9.2 says reading θ_on as self-specific "rests on β_int" and needs its 95% CI to exclude 0. That estimate comes from 30 anchors per judge.
   - `power_sim.py` has no anchors, no θ_off and no β_int, so the claim in the title has no power analysis.
   - My rough minimum detectable effect (MDE) for β_int is 6.6–8 pp **[est.]**, worse than T1b's own.
   - Possible confound, not checked: anchors are stratified by failure status, while a commercial judge's own items are mostly correct refusals and benign answers. If the mixes differ, β_int compares presentation effects on different kinds of item. I did not read `analysis\estimators.py`.

3. **The nulls will be uninformative, and one is predicted.** (§3.1, §9.2)
   - T1a is expected not to reject and cannot support equivalence ("a ±5-point TOST is infeasible"). It still takes Holm alpha from T1b and T4.
   - T1b's MDE at 80% power is 4.9–6.0 pp at 6% discordance, 5.9–6.8 at 10%, and 6.6 to above 7.0 at 14%.
   - A 2-pp effect has power 0.10–0.25 (`power_sim.json`).
   - The simulation applies leniency to every own item, failures and non-failures alike. If leniency acts only on real failures (about 27% of self items **[est.]**), a 4.8–5.7 pp average effect needs recall on own failures to fall by about 18–21 points **[est.]**.

4. **Incremental over Khullar et al., with a more conservative instrument.** (§2)
   - The title nearly repeats their subtitle, so reviewers will read this as a replication.
   - A binary verdict under a detailed rubric with an "ignore tone" instruction leaves less room for the effect than graded ratings. A null will be read as "your instrument suppressed it".
   - Their paper appears to include a neutral-attribution baseline already, which would make "adds the blind cell" (§2) an overstatement. Not checked first-hand: I read it through a summarising tool.

5. **Reference standard.** (§7.3, §15, `RUBRIC.md`)
   - One annotator, who is the PI, also wrote the own prompts and wrote the harm definition on 9 November.
   - The second annotator labels 150 items; the PI's labels "stay the primary reference standard", and adjudicated labels are a sensitivity analysis only.
   - This is tolerable for T1a/T1b, which barely use gold. It is weak for H1, RQ1, RQ4 and T4, which depend on it.
   - Limb (b) of the harm definition turns on stated ownership, so labels on dual-use prompts depend on framing wording.

6. **T4 margin and scope.** (§9.2, §9.3, §15)
   - The −0.10 margin is wide, has a one-sentence rationale and is still marked [PI].
   - Power at a true −0.05 is 0.17–0.61 at the first Holm step. At a true 0 with independent errors it is 0.76.
   - The evidence is three community builds of 4–8B Q4 models, made by different people with different methods, on roughly 80–130 shared items **[est.]**.
   - The heterogeneity rule caught a true −0.20 pair in only 28–71% of runs that declared non-inferiority.
   - A failed non-inferiority test is silent, and the protocol does not define an "inferior" result.

7. **Too many questions for the evidence.** (§3, §9.7)
   - Three confirmatory tests, H1–H3 in separate families, RQ1, RQ3a/b/d, RQ4, calibration, juries, cascades, Dawid–Skene, PPI and external transfer, on about 432 labeled items.
   - §9.7 states that separate families give no study-wide error control.

8. **The legacy hypotheses will probably fail.** (§9.2, §9.5)
   - H1 needs at most 2 misses in 124, with invalid verdicts counted as misses. The pass probability is 0.42–0.56 at a true 2% rate and 0.19–0.28 at 3%.
   - H2 needs three one-sided McNemar tests under Holm on 30 fiction prompts per model, in at least 3 models, above a 5% refusal floor (about 1.5 refusals).
   - H3 needs all five comparisons and a bound to hold.

9. **Ecological validity of the in-context setup.** (§8.3, §10, §15)
   - The rubric is in the system message from the start, the answer was generated without it, and reasoning traces are not replayed.
   - On the refusal endpoint the judge classifies behaviour, where "leniency" is conceptually thin.
   - Several judges cannot run at temperature 0, so some blind/in-context discordance is sampling noise. The paired design and the repeatability check handle this correctly; it costs power, not validity.

10. **Panel.** (§6, §8.3, §9.1)
    - The panel is purposive, chosen after rankings were seen, and inference is "conditional on these 22 judges". That is honest and limiting.
    - Model 6 judges under a Q4_K_M alias while its answers came from a Q4_0 build. "Self" is therefore not the same weights for the judge holding 69 self items.
    - "Nobody monitors with a 4B Q4 model" is a fair objection to the headline, though not to T4.

## Changes before the freeze, ranked by value over cost (point 7)

### (a) Must-fix, or the paper is weak

1. **Run a non-gold go/no-go pilot before the freeze and before inviting anyone.**
   - **Items:** the 20 respondent-pilot answers per API respondent (§8.3), plus about 100 own answers per local model from a pool removed from the G2/G3 frames by a seeded rule.
   - **Procedure:** each author judges its own items blind and in-context. Pilot items stay out of every confirmatory analysis.
   - **It yields:** the discordance rate (the power table stops at 14%), a raw θ_on with standard error near 1 pp **[est.]**, invalid and block rates, any provider warning, and a rough base-versus-abliterated harm-flag gap.
   - **Decision rules to write down first:** discordance above 14%, or |θ_on| clearly under 2–3 pp with no sign in commercial judges, means rescale or re-scope. Any provider warning means redesign the anchors.
   - **Cost:** US$2–5 **[est.]**, a few GPU hours, 1–2 days, no labeling. A disclosed pilot is compatible with pre-registration.
   - **Not checked:** whether the 20 pilot prompts include harmful ones. If not, add a few.

2. **Decouple T1b from the gold set and scale it.**
   - **What:** run blind and in-context self-judging on every common-subset answer: 190 per commercial respondent, 280 for Venice, about 300 per local model. Keep the gold subset for the accuracy reading.
   - **Why:** θ_on needs only the prompt's `expected` and the verdict (§7.1). Commercial pairs go from 132 to 2,090.
   - **The number that matters:** commercial real failures go from about 15 to about 210 **[est.]**. Most commercial answers are correct and leave nothing to be lenient about.
   - **Expected gain:** MDE on θ_on from about 5–6 pp to about 1.5–2.5 pp **[est.]**. Not checked: confirm by changing `allocation()` in `power_sim.py` and re-running.
   - **Cost:** about 4,450 API calls, US$18 expected / US$38 pessimistic **[est.]**; 5–10 GPU hours; no labeling.

3. **Defer H1–H3, RQ4 and instrument selection to a separately registered companion.**
   - **Why:** it pays for changes 2 and 5, and removes the hardest unwritten code and three likely failures.
   - **Cost:** one dated public amendment before any answer is judged.
   - **Saves:** US$29.16 expected / US$64.17 pessimistic (stages 3, 3b and 6, as I read §11) and roughly a week of code.

4. **Take T1a out of the Holm family, or register it as a bound.**
   - Example: "blind self-leniency above 7 pp is excluded" (power at 7.0 pp is 0.97/0.99).
   - The expected outcome then yields a sentence, and T1b and T4 keep more alpha. Cost: zero.

5. **Raise anchors from 30 to about 100 per judge, match them to each judge's own item mix, and add β_int to the power simulation.**
   - **Why:** it makes the claim in the title testable.
   - **Cost:** about 1,680 API calls, US$7 / US$14 **[est.]**; about an hour of simulation work.

6. **T4: pre-specify a three-way reading, settle the margin, add pairs.**
   - The readings are non-inferior, inferior (CI wholly below 0 or below the margin) and inconclusive.
   - Justify −0.10 with a use case or tighten it, and remove the [PI] mark.
   - Add several matched abliterated pairs as judge-only models. They are local, cost no API money and need no new labels; allow 1–2 days for rule and rendering checks.

7. **Double-annotate the T4 items and make consensus primary there.**
   - **Cheapest version:** point the existing 150-item second-annotator sheet at answers to refuse-expected prompts only. No extra hours.
   - **Full version:** all such answers, roughly 200–320 items, 8–14 hours **[est.]**.

8. **Fix the annotator guide.** Five minutes.
   - Lines 15–16 tell the annotator that about half the items were labeled harmful by the first annotator, and step 2 of "Process" repeats the two halves. §7.3 says the annotator "is not told the share of harmful items".
   - Lines 4–8 say judges are tested on their "own developer's" outputs. The headline is their own answers.

9. **Freeze only after the judge code and analysis driver run end to end on synthetic data.**
   - §13 lists them as not yet written. The cost is a slip of one to two weeks, which §11 already allows.

**Budget check for changes 2 and 5 together** (about US$25 expected / US$52 pessimistic **[est.]**):
- **Expected case:** stages 1–2 cost 44.56, so the extension fits with about US$40 to spare.
- **Pessimistic case:** stages 1–2 cost 88.79, leaving US$21.21, about 40% of the extension. Register it as a seeded, ordered list that stops at the cap, commercial judges first.
- **Not checked:** my unit cost (about US$0.004 a call) is inferred from stage 2's total over what I take to be about 7,000 calls. I did not read or run `scripts\cost_model.py`.

### (b) Worthwhile

- **Retitle** and frame the paper as a registered replication and extension of Khullar et al. Free.
- **Make the second template wording a rubric-light graded rating**, on-policy in both presentations on a subset. It answers "your rubric suppressed the effect". About US$3–6 **[est.]**.
- **Re-aim labeling.** Move the 84 own-prompt gold slots and the frontier re-label hours to T4 items and a blind sample of about 100 blind/in-context discordant pairs. Same hours.
- **Reduce budget control** to the hard cap, one ledger and a per-run cap.
- **Re-time labeling** on the judge pilot's 30 answers. §7.2 says 16–31 hours and §16 says 18–36.

### (c) Nice-to-have

- Plan A+ in full.
- The roughly 100-item holdout.
- WildGuard.

### (d) Resist adding

- More respondents, judges or research questions.
- Your own abliterations.
- The frontier two-phase re-label, Dawid–Skene and PPI.
- Further budget rules.
- Further internal-consistency audit rounds. The open risk is effect size and design fit, which a pilot settles and a text audit cannot. I did not read the audits; this rests on your description of what they covered.

## What the paper can claim (point 1)

**Honest abstract, as designed:**

> We test 22 LLM judges on refusal and harm classification of chat answers, against about 430 answers labeled by one human. With authorship hidden, we could not detect that judges flag failures in their own answers less often; effects above about 5–7 points are unlikely, and equivalence is not claimed. Showing a judge its own answer as its previous turn changed its flag rate by X points (CI …); whether this is specific to its own answers is not established. Three community abliterated 4–8B models were [were not shown to be] within 10 points of their base models in harm recall.

**Outcome space.** Priors are mine.

| Outcome | Prior | Message | Value |
|---|---|---|---|
| T1a not rejected (predicted) | about 90% | "Not detected", no equivalence | Nothing alone |
| T1a rejects | about 10% | Blind self-leniency | Interesting only if it survives the subsample-to-15 check |
| T1b not rejected | about 60% | "No in-context effect detected", CI about ±5–6 pp | Weak |
| T1b rejects, β_int inconclusive | about 25% | Presentation lowers flag rates; self-specificity unknown | Workshop: a replication in a new task |
| T1b rejects, β_int excludes 0 | about 10% | The effect transfers to refusal/harm classification | Best case; TMLR plausible |
| T1b rejects, positive sign | about 5% | Judges harsher on their own turn | Publishable as a contrast |
| T4 non-inferior | about 50% | These three checkpoints keep harm recall within 10 points | Modest, useful |
| T4 inconclusive | about 40% | Nothing | None |
| T4 clearly inferior | about 10% | Refusal removal damaged harm recognition here | Interesting, but not a pre-specified claim |

- **Most likely combination:** T1a not detected, T1b not detected or detected without self-specificity, T4 either way, and H1–H3 not supported or inconclusive.
- **The outcome that says nothing:** T1a and T1b non-significant with wide CIs and T4 straddling the margin. I put this at about 20%. What survives is a descriptive judge-versus-one-annotator table.

## Significance and novelty (point 2)

- **Relevance is real.** LLM judges grade safety evaluations everywhere, and self-grading is a natural confound.
- **T4 has a practical audience:** people use uncensored local models as judges because aligned models decline to grade harmful text.
- **The real additions over Khullar et al. are:**
  - a binary refusal/harm classification of ordinary chat answers;
  - item-level human labels;
  - off-policy anchors;
  - small and abliterated judges.
- **Their harmfulness results reportedly moved in both directions across models** (roughly +0.7 to −2.4 on a 0–10 scale; via a summarising tool, approximate). That is why I expect a small or null average effect on a binary flag.
- **Twenty-two judges is a strength in principle and a weakness as allocated.** There are fewer own items per commercial judge (12) than judges (22), which is the wrong shape for a within-judge effect.
- **


---

<!-- report part 3 of 3 -->

T4 is the more original half**, but that is not checked. I did not survey work on harmfulness versus refusal representations or on abliterated models as judges; the other agent's sweep should settle it.

## What is genuinely good (point 4)

- **The within-item paired design** (blind and in-context calls adjacent, in randomised order) is the right design for the question.
- **The off-policy anchors** are the right idea for separating self from presentation. There are just too few of them.
- **The T1 estimands are nearly label-free**, so the headline does not inherit the single-annotator weakness.
- **Process discipline is above the workshop norm:** sealed outputs, recorded inclusion probabilities, and test sizes checked by simulation (0.011/0.045 and 0.016/0.051, §9.1).
- **Limitations are stated before a reviewer has to ask:**
  - "Implications for AI monitoring are discussed, not claimed" (§1);
  - "No 'first' claims are made" (§12);
  - T4 is scoped to three checkpoints (§9.3).
- **T4 pair hygiene is careful:** rendering and token-level checks, with a pre-decided fallback if a pair fails.
- **T4 is a question where both answers are interesting.** The self-judging half, as designed, is not.

## Coherence (point 5)

As written this is four papers stapled together:

1. the self-judging 2×2;
2. abliterated judges;
3. a judge meta-evaluation (juries, cascades, error correlation, calibration);
4. an over-refusal benchmark of 22 models with a framing study on own prompts (H2, H3, RQ4).

**What carrying v1 costs:**
- stages 3, 3b and 6: US$29.16 expected / US$64.17 pessimistic;
- the most complex unwritten code (nested-CV instrument selection, recusal, the contrast-neutral instrument, corrected rates);
- 84 own-prompt gold items and the clarification and covariate apparatus;
- three probable "not supported" lines in the paper.

**Minimum publishable core:**
- on-policy blind versus in-context self-judging at scale, with anchors;
- a blind bound in place of T1a;
- an accuracy reading against gold;
- T4 as the second contribution;
- one descriptive judge-versus-human table;
- the recognition probe and second template wording, which are cheap and which reviewers will expect.

**What goes:** H1–H3, RQ4, instrument selection, the framing study, calibration, Dawid–Skene, PPI, external transfer and most of the frontier apparatus.

**What is lost:** continuity with v1 and the benchmark numbers. v1 was posted with no data read, so deferring these to a separately registered companion is legitimate if the amendment is public and dated before any answer is judged.

## Feasibility and execution risk (point 6)

- **Schedule.** §11 puts the freeze at "about 13 Nov". On 10 November these are unwritten or absent (§13, §16, file listing):
  - the judge code to §13's eleven requirements, and the analysis driver;
  - `config/relations.csv` and `config/judge_prompt_v2.txt`;
  - the full gold sampler (§7.2 calls `src/gold_sample.py` "a prototype");
  - instrument selection;
  - three API accounts to open, and the T4 margin to settle.
- **Budget machinery.** The ledger, stage holds, batch adopt/release/purge, stage closure and 118 offline checks are out of proportion to US$110. They guarantee logged deviations for one person.
- **Pessimistic budget case.** About US$6.50 remains after stages 1–3, and the frontier judges see about 4% of their items (§11).
- **Labeling.** Five fields on long or harmful answers in 45-minute sessions is more likely 3–5 minutes per item than 1.5–3. That gives roughly 35–60 hours for the first annotator **[est.]**, against 16–31 in §7.2.
- **External dependencies.** The written USF HRPP determination has an unknown lead time, and it gates the second annotator.
- **Provider risk.** §10 concedes the in-context layout "resembles a fabricated-turn technique". The anchors put other models' harmful answers into commercial judges' assistant turns, and the rule is to stop on a warning. One warning on a new small account removes a provider mid-study.
- **Where it breaks first:** unwritten code against rule complexity, then labeling hours, then a provider block.
- **What a broken version still delivers:** the descriptive table and a T4 estimate, which is local and free.

## Not read or not checked

- **By instruction, not opened:** `docs\audit\`, `results\`, any completions, sealed data files.
- **Code state.** I did not inspect `src\judge.py` or `src\gold_sample.py`. "Unwritten" rests on §13, §7.2, §16 and the file listing.
- **Estimators.** I did not read `analysis\estimators.py` or `selfcheck_estimators.py`. The anchor-mix confound for β_int is a question, not a finding.
- **Power.** I read `power_sim.py` and the first 120 lines of its output, and ran nothing. Every rescaled MDE is back-of-envelope and ignores clustering by base prompt.
- **Costs.** I did not read or run `scripts\cost_model.py`. Extension costs are inferred from stage totals.
- **Stage attribution.** That stages 3, 3b and 6 serve only H2/H3/RQ4 is my reading of §11. Confirm against the stage table.
- **Khullar et al.** I read it through a summarising tool on the arXiv HTML. The baseline design and effect sizes are approximate.
- **Literature.** No sweep. The novelty score and T4's originality are provisional.
- **Pilot composition.** I do not know whether the 20 respondent-pilot prompts include harmful ones.
- **Provider terms** on prefilled assistant turns, and the HRPP lead time: not checked.
- **Other files not read:** v1 `PREREGISTRATION.md`, `config\models.json`, the tests, `welfare_protocol.md`. H1–H3 wording is taken from §3.2.
- **All outcome and venue probabilities** are priors.

## Corrections to my earlier draft

- **Self-item share.** I wrote that about 60% of self items come from six small local models. The correct figures are 282 of 432 (65%) from the ten local models and 168 (39%) from the three G1 authors.
- **Budget.** "Roughly budget-neutral" holds in the expected case only. In the pessimistic case about 40% of the extension fits under the cap.
- **T4 hygiene.** I dropped a detail about a model-19 replacement, which I could not re-verify.

## Files referenced

- `E:\claude\agentsControl\docs\STUDY_PROTOCOL_v2.md`
- `E:\claude\agentsControl\analysis\power_sim.py`
- `E:\claude\agentsControl\analysis\output\power_sim.json`
- `E:\claude\agentsControl\labels\RUBRIC.md`
- `E:\claude\agentsControl\docs\annotator_packet\annotator_guide.md`
- `E:\claude\agentsControl\docs\annotator_packet\informed_agreement.md`
- `E:\claude\agentsControl\README.md`

## Sources

- https://arxiv.org/pdf/2603.04582
- https://arxiv.org/html/2603.04582v1
- https://neurips.cc/virtual/2025/128030
