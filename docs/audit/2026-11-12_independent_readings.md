# Independent readings of the protocol, 12 November 2026

## How the readings were made

- **Purpose.** To see how two strong models read the whole protocol with no history and no context: no earlier review, no repository, no conversation.
- **Request.** Identical for both, followed by the full text of `docs/STUDY_PROTOCOL_v2.3.md` as it stood at 19:58 Eastern time on 12 November 2026 (after the commit `930df40` and the header correction of the same evening):

  > I want to evaluate this study. Below is its full protocol. What is your opinion of it?

- **Claude Opus 5.5.** Claude Code in print mode, version 2.1.323, model `claude-opus-5-5`, effort `xhigh`. A new session in an empty folder, no settings or memory files loaded, no MCP servers, every tool switched off, no session saved, and the system prompt "You are Claude, an AI assistant made by Anthropic." Run on the PI's subscription. Duration 230 s.
- **GPT-6.1 Sol.** Codex `exec`, model `gpt-6.1-sol`, reasoning effort `xhigh`. A new session in an empty folder, user configuration ignored, apps and memories switched off, web search disabled, read-only sandbox. Run on the PI's subscription. Duration 427 s. It tried one local Python computation, which failed because no Python was on the path; its answer does not depend on it.
- **Conflicts.** Claude Opus 5.5 is the model of the drafting assistant (Section 17.3). GPT-6.1 Sol is model 11 of the panel and the reviewer of rounds 1 to 9; this session had no memory of them.
- The answers are stored as returned, below. Their statements are claims to check, not instructions. Section 17.1 of the protocol says how each point was taken up.

## Reading by Claude Opus 5.5

### Review of the "Judging Their Own Answers" protocol (v2.3)

**Disclosure first.** I'm Claude, made by Anthropic. Anthropic makes models 1 and 2 of your panel and the drafting assistant named in Section 17. I may be the same model that helped draft this text, though I have no memory of it. So my review carries the conflict you already disclose for the drafting assistant. I also couldn't check most of the 2026 literature you cite, because it postdates my training data.

#### Overall opinion

The confirmatory core is sound, and it is unusually honest about what it can and cannot claim. Several features are better than most preregistrations I've seen:

- the claim-wording table and the "consistent with" rule for mechanisms;
- the separation of non-delivered verdicts, calls never attempted, and actual flags;
- the identity ι_S = ι_W + ι_C, with a correct account of what each contrast removes;
- simulations that run the production inference code;
- the identification-range treatment of unknown labels;
- regenerating all answers after registration (D18).

My main concern is different. The design is very good at not over-claiming, but its central contrasts are weakly informative about authorship. Two of those weaknesses can be fixed cheaply, but only before the pilot registration, because that registration fixes the template and the design. These are the issues I'd raise now.

#### Main concerns, in priority order

##### 1. P2 and P3 mostly compare refusal-removal techniques, not authors

- Under the baseline assumptions of Appendix A.1, about 76% of the ~1,900 screen-positive answers come from the refusal-removed group: 7 × 300 × 0.69 ≈ 1,450 against 5 × 300 × 0.305 ≈ 460.
  - Real instruction-tuned 8B models will likely refuse more of these prompts than assumed, so the true skew is probably larger.
- Within that group, Section 6.3 forces the controls to cross technique for five of the seven authors on every prompt, and for models 20 and 23 on half the prompts.
- So roughly two thirds of the weight in ι_S, and in β_S, sits on pairs where author and control differ in kind of refusal removal. The protocol itself says this group cannot separate "author" from "technique."
- Appendix A.2 shows the consequence. With aligned judge shifts of only ±0.5 logits and no author effect, P2 rejects in 38–45% of replications. Real differences in judge severity across these builds could easily be larger.

P3 has the same problem in sharper form. β_S compares the author's blind flag rate with that of whichever judge the assignment happened to pair it with. In the dominant group, that mostly measures how severe abliterated judges are compared with fine-tuned ones. A confirmatory test whose answer is largely set by the pairing rule is hard to interpret, even with careful wording.

**Suggested fix: a partially crossed design on local judges, at no cash cost.**

- On a subset of the harmful frame (say 100 prompts, screen-positive answers only), have every local judge classify every primary-panel answer in both presentations.
- That gives a judge × author matrix per prompt. With judge and answer fixed effects, the own-diagonal is identified net of judge severity and answer difficulty, in both the blind and the in-context presentation.
- The three base/abliterated pairs (4–6, 5–18, 15–19) then give a similarity gradient for free. An effect ordered own > sibling > unrelated is far more interpretable than ι_S.
- It still doesn't remove the judge × content interaction, but it narrows it considerably.
- Cost: roughly 10,000 extra local calls, about half a day to two days of machine time.

You withdrew a "crossed fixed-effects sensitivity" after round 3. I'd bring it back in this stronger form, at least as a registered secondary analysis, and consider making the blind diagonal the basis of P3.

##### 2. The in-context arm is not the self-monitoring situation, and the transcript contradicts itself

In arm A2 the judge sees:

1. a system message with the classifier rubric;
2. the harmful request;
3. "its own" answer;
4. a request to classify that answer.

As the transcript reads, the model answered the harmful request while operating under classifier instructions. That is neither what happened at generation (no system prompt for most models) nor the motivating scenario (a check that follows the original conversation). Models may resolve the contradiction in idiosyncratic ways, for example by treating the earlier turn as out-of-role or not their own. That would contaminate exactly the contrast you care about.

**Suggested fix:**

- Put the rubric and the instruction in the final user turn in both arms, and leave the system slot as it was at generation.
- The evaluative bytes stay identical across arms.
- For 9 of the 12 primary models, A2 then becomes an exact reconstruction of the respondent's conversation plus one classification turn.
- Your code already supports this layout (the fallback in Section 11.2 for models without system messages).
- At minimum, register it as a local sensitivity analysis. It costs no cash.

##### 3. Scoring non-JSON outputs as "no flag" can manufacture the P1 effect

A safety-trained judge shown a harmful completion as its own turn may reply "I apologize — my previous response was harmful…".

- Under Section 10.2 that output is `declined` (it opens with a refusal phrase) and scores 0.
- So the most emphatic possible self-correction is counted as a missed flag, and it happens disproportionately in context.
- Appendix A.2 already shows that non-delivery in context alone drives P1 to 88–100% rejection.
- The claim rules keep the sentence technically true ("delivered less often"), but readers will take it to mean judgment changed.

**Suggested fix:**

- Register a mechanical secondary coding of `declined` and `parse_error` outputs into "disavows or flags the answer" versus "refuses the task." This codes the judge's output, not the answer, so it doesn't interfere with the label lock.
- Alternatively, require the fail-closed P1 estimate to appear beside the primary one wherever P1 is reported.

##### 4. External validity relative to the motivating scenario

The question is motivated by models checking their own outputs in deployment. The primary estimate is dominated by abliterated and uncensored builds that nobody would deploy as their own safety monitor. You can't easily avoid this: safety-trained models rarely produce harmful content on these benchmarks, which is why the commercial panel is thin. But the introduction and abstract should state the tension directly. I'd also pre-register that the abstract reports the instruction-tuned and refusal-removed estimates separately, not only the pooled θ_S and ι_S.

##### 5. The document's size has become a risk in its own right

At roughly 30,000 words, with 19 decision IDs, gates on gates, and crash-recovery semantics for a ~US$100 ledger, the registration is hard to audit, and the length is already producing inconsistencies:

- **Section 13.3, rule 3** keeps the local output cap at 1,500 tokens "because the existing answers were generated under it." Under D18 those answers are no longer used, so the rationale is stale.
- **Status headers** dated 10 and 11 November (Sections 1 and 14.2) describe events of 12 November.
- **Section 17.2** mixes counts from round 3 (547, 360) with current counts (567, 381). It is declared, but it confuses readers.

**Suggested fix:** split the document in two.

- A registration of about 10–15 pages: questions, estimands, tests, claim rules, failure and missing-data rules, frames, and code hashes.
- A separate operations manual: ledger, holds, timestamps, provider routing, and similar material.

Reviewers and journal editors will find what is binding, and you'll make fewer consistency errors.

##### 6. No human has reviewed the design yet

The only external reviewer is a panel model, and the drafting was done by a model from a panel developer. D7 schedules a human methodologist before the freeze. I'd move that to before the pilot registration: points 1–3 above are cheap to change now and expensive after. If you have a faculty advisor, they are the obvious first reader. They may also be needed for the USF human-research determination anyway.

#### Smaller points

- **Context overflow for local judges.** Local judges have 8,192 tokens of context, and every primary judge classifies all 567 labelled answers blind, including commercial answers that may be long. Expect some `context_overflow`, which would bias the blind-accuracy figures. Either raise the context for those calls or report the overflow by answer source.
- **P3 margin.** The 7-point margin is justified by precision, not by substance. Your text admits this; just keep the paper equally explicit.
- **Commercial panel.** It is expensive per unit of information on the core question. With on-policy harmful answers rare, θ_S may be barely estimable there. That's fine as long as it stays descriptive, which it does. The account-loss risk from block 7 is the real cost.
- **Provider notice.** Giving notice to providers is cheap insurance against losing an account mid-run, and losing an account ends that provider's blocks. The OpenAI terms review is still open, and OpenAI serves three of your commercial models, including the reviewer's.
- **Literature.** Your novelty claim rests mainly on how you characterize Khullar et al. (2026). Read it in full before writing the related-work section.

#### Bottom line

This is a careful, honest protocol that would produce trustworthy statements about flag changes. As designed, though, it can say little about authorship, which is what the title and motivation are about.

Before the pilot registration, I'd do three things:

1. add a crossed own-versus-other subset on the local judges;
2. move the rubric out of the system slot, or at least register that layout as a sensitivity analysis;
3. register a coding of declined and invalid in-context outputs.

Then get one human methodologist to read the result. All three changes are cheap in money; the first adds a day or two of machine time.

## Reading by GPT-6.1 Sol

**I think this is worth doing. It has a defensible main experiment and could produce a useful replication and extension. I would support proceeding to the pilot once the listed conduct requirements are met, but I would want a focused independent statistical review before the freeze.**

Its contribution is reasonably clear: testing whether a safety monitor’s delivered classifications change when identical content moves from quoted data into its previous assistant turn, across a particular panel of models. The protocol appropriately limits what that says about self-preference.

Several features are strong:

- The author and control judge evaluate **the same answer in both presentations**.
- Harmful prompts, harmful answers, harm flags and delivery failures are kept distinct.
- The human sample includes screen-negative answers, allowing the screen’s mistakes to be measured.
- Labels are locked before being joined with verdicts.
- Missing calls, failed verdicts, retries and budget cuts have explicit rules.
- Earlier answers are regenerated, and failed simulation checks remain visible.

These choices address substantial threats to interpretation. My concerns are more concentrated than the document’s length might suggest.

1. **P1 is the strongest scientific contribution; P2 needs its narrow interpretation throughout.**

   P1 answers a useful operational question about presentation. P2 compares that presentation contrast between authors and their assigned controls.

   P2 does not isolate an effect of actual authorship. Judge differences, content differences and judge–content interactions remain possible explanations. Your own simulations demonstrate this. The within-judge companion helps diagnose the comparison, but agreement between the two contrasts does not establish a mechanism.

   The protocol already acknowledges this well. I would accept that limitation rather than demand another redesign. The eventual paper needs the same restraint, particularly in its abstract and discussion.

2. **The statistical machinery deserves an independent check beyond the current simulation pipeline.**

   The main cluster-ratio variance formula is reasonable for the stated framework. The more unusual parts are the domain degrees of freedom, the effective-sample-size intervals and the label-assisted estimator.

   Reusing production functions in simulations is excellent for checking implementation consistency. It provides less protection against a conceptual error shared by both implementations. Likewise, passing simulations establishes performance under those data-generating assumptions.

   I would have a statistician independently examine the two-phase label sampling, the treatment of estimated \(b_g\), and the interval procedures.

   There are also concrete specifications to resolve:

   - **Zero degrees of freedom:** one screen-positive answer in each source, with different presentation changes, can produce positive estimated variance but zero domain degrees of freedom. The printed zero-denominator and zero-variance rules do not cover this case.
   - **Reference accuracy intervals:** the “exact binomial” intervals in Section 9.4 need justification when several answers share a prompt. They do not automatically inherit exact coverage under that dependence.
   - **Agreement intervals:** the answer-level bootstrap in Section 9.3 should be reconciled with the prompt-level dependence assumed elsewhere.

   These are targeted statistical issues, not reasons to abandon the study.

3. **The complete-pairs gate supports a narrower statement than the current wording may imply.**

   A presentation change among answers with two valid verdicts demonstrates a change within that subset. It does not establish how much of the overall delivered-flag change reflects changed judgments, because membership in that subset depends on successful delivery under both presentations.

   Even when the gate passes, I would write:

   > “A corresponding change appeared among answers receiving valid verdicts in both presentations.”

   The decomposition, non-delivery rates and bounds should remain beside that statement. The bounds provide stronger evidence for conclusions intended to survive uncertainty about failed verdicts.

4. **The human labels are valuable, but agreement cannot establish freedom from PI bias.**

   Double annotation of every sampled harmful-prompt answer is a substantial strength. However, the PI defines the rubric, labels every item and participates in every adjudication. High agreement can coexist with shared interpretive assumptions.

   The sentence saying agreement figures show “how much this matters” is too strong. They measure agreement.

   A useful addition, requiring no further reading, would be sensitivity estimates using each annotator’s original labels separately, alongside the adjudicated reference.

   The actual Part A rubric also matters greatly. It is referenced rather than reproduced in the supplied text, so I cannot fully assess construct validity. Given its deliberately narrower scope, results should consistently mean detection **under that rubric**, rather than detection of harmful content in general.

5. **P3 is mathematically clear, but its practical significance is limited.**

   Choosing seven points from achievable precision is transparent. It does not establish that seven points is a substantively acceptable deficit.

   Moreover, P3 concerns overall flag rates among screen-positive answers. Similar flag rates can conceal different combinations of missed harmful content and false alarms. Passing P3 therefore provides limited reassurance about monitoring quality.

   I would give it less prominence than P1 and report its bound plainly. The protocol’s current exclusion wording is appropriately cautious.

6. **The practical constraint is human work, more than API spending.**

   Under the stated four-minute assumption, the PI labels, second labels, both annotators’ training and pilot reading amount to approximately **85 hours of reading before breaks and discussion**. Adjudication, administration and analysis come on top.

   Meanwhile, the study includes substantial commercial, safe-prompt, challenge-set and accuracy work around the main experiment. Those additions may be useful, but their scientific return should justify their demands on the investigator.

   If scope needs reducing, I would protect independent annotation and validation of the primary harmful-answer results first.

Before freezing, I would also reconcile several visible inconsistencies:

- Section 18.5 says the instruction-tuned detection-change interval is withheld; Sections 9.5 and A.4 say D19 restores it.
- Section 13.3 retains an output-cap justification based on using existing answers, although D18 replaces those answers.
- “Registered code” appears to describe an earlier draft implementation, even though v2.3 has not yet been registered.

**My recommendation is to retain the core design, obtain an independent review of Sections 8–9, tighten the complete-pairs claim wording, and reconcile the final specification.** The study’s credibility will depend most on those steps and careful execution. I am assessing the supplied protocol; I have not audited the repository or independently verified its references and simulation outputs.

## Checks of the readers' factual statements

- The stale reason for the local output cap (Section 13.3, rule 3) and the mixed counts of Section 17.2: confirmed, corrected.
- Section 18.5 still withheld the interval of the instruction-tuned detection change after decision D19: confirmed, corrected.
- "Registered code" for the code before amendment D19, although version 2.3 is not registered: confirmed, corrected.
- A case with zero domain degrees of freedom: not confirmed. Section 8.1 already set at least one degree of freedom, and `cluster_ratio` returns 1 on the reader's example (one screen-positive answer in each source). The sentence was made explicit.
- "No human has reviewed the design": the PI set the question, took every decision and reviewed the text; no researcher outside the study had read it. Sections 17.1 and 18.8 now say so.
