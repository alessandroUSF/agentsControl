# Review of "Judging Their Own Answers", protocol v2.3

## Disclosure

I am Claude Opus 5.5, made by Anthropic. Anthropic develops models 1 and 2 in the panel. The protocol was drafted with Claude Code, and one of the 12 November "independent readings" was done by this same model. Treat this as another AI reading with the same conflicts and possibly the same blind spots. It does not replace the human reader of D7.

I worked from the two documents only. I have not seen the code, the rubric, the configuration files or the simulation outputs. I cannot check anything dated after my training data, which includes the model names, prices, endpoints and the 2026 papers cited.

## Short answer

The core design is strong. It is not ready to be carried out as written, for two reasons:

1. **It fails its own conditions for the pilot registration (Section 14.2).**
2. **Several design problems should be fixed first.** Most of them come from the 12 November additions, which no review has checked. They must be fixed before the pilot registration, because that registration fixes the judge template, the cap rules, the control assignment and the hosted-model policy.

## What is strong, and should not change

- **Same-answer controls.** Author and control judge the identical answer in both presentations. This removes the answer component from ι_S.
- **Pre-specified wording.** The claim sentences are fixed in advance, including what to write when a test cannot be carried out.
- **Non-delivery accounting.** Undelivered verdicts and calls never attempted are kept apart, and fail-closed results, complete pairs and bounds are reported.
- **Validated inference.** Size and coverage were checked with the production inference code. The degrees of freedom were revised (D19) when the checks failed, before any data existed.
- **Data hygiene.** Sealed hashes and the regeneration of all answers (D18).
- **Honest limitations.** Section 18 states them plainly, especially that judge and content are tied.

## Must change before the pilot registration

### 1. The two presentations differ in more than the role of the answer

- **Blind layout:** rubric → request → answer → instruction.
- **In-context layout:** request → answer → rubric → instruction.

So only in context do about 2,000 rubric tokens sit between the answer and the instruction. Small models are sensitive to this kind of position and recency difference.

- θ_S absorbs the difference, and the P1 sentence attributes it to "own previous turn vs quoted text."
- ι_S cancels it only to the extent that all judges react to it equally.
- The asymmetry seems to come from the 12 November move of the rubric out of the system slot. The blind order was kept for OpenAI prefix caching.

**Fix:** use the same order in both presentations. Put the request and answer first (quoted data blocks when blind, turns in context), then the rubric, then the instruction. The only cost is losing cached blind calls at OpenAI. The pessimistic manifest already assumes no cache hits, so the cap is unaffected. Rule 1 of Section 13.3 cannot make this change later.

### 2. Hosted answers may not fit the local judges, and the text contradicts itself

- Section 10.2 says answers of models 22 and 23 (at most 4,000 tokens) fit every local judge. Rule 3 lets their cap double to 8,000, which cannot fit in an 8,192-token context.
- Even at 4,000 tokens the margin is thin:
  - The cap is counted in the respondent's tokenizer, but the judge counts the text in its own tokenizer. The older Mistral 7B tokenizer of model 21 is less efficient.
  - The pessimistic rubric is about 2,400 tokens, and a doubled local judge output cap is 1,200 tokens.
- **This affects the primary analysis.** Local judges (6, 18, 19, 20) control models 22 and 23.
  - An overflow scores C1 = C2 = 0 while the hosted author delivers its verdicts.
  - Overflows hit the longest answers, which are likely the most compliant ones.
  - The result is an upward bias in β_S, which makes P3 easier to reject, and a distortion of ι_S.
- **Check silent truncation.** Ollama has historically cut over-long prompts with only a log warning, instead of returning an error.
  - If the pinned version does this, it drops the start of the prompt.
  - That is the rubric in the blind layout but the request and answer in context, so the two presentations would be corrupted differently.

**Fix:**
- Remove the doubling for models 22 and 23, so long answers are handled as `truncated`, like local answers. The alternative is to raise `num_ctx` uniformly for all local judging.
- Add a fit check before each call, for each (judge, answer) pair, using the judge's own tokenizer.
- Confirm on the real Ollama build that overflow is detected, for example by comparing `prompt_eval_count` with the expected count.
- Report the maximum rendered length per judge in the pilot.

### 3. The crossed subset gates claim sentences but is not specified or validated

- Section 8.8 requires check 5 of Appendix A.4, but no run in A.4 simulates the crossed model. Check 5 covers only R-S3 and runs (b) and (f).
- Its fixed 98 degrees of freedom contradict D19, which was adopted because fixed degrees of freedom over-rejected with sparse data.
- The specification leaves open questions:
  - Are the judge and answer fixed effects separate for each presentation?
  - Which cluster-robust estimator is used? With about 640 answer fixed effects and 100 clusters, the small-sample correction matters.
- The code is not written.

**Fix:** complete the specification, add a simulation run with checks, and apply the D19 degrees of freedom. Until then, addition 5 cannot gate any sentence.

This subset is the only part of the design that addresses Q2 and Q3 as they are phrased, net of judge severity. Once validated, it may deserve confirmatory status.

### 4. The condensing step conflicts with the ethics section

The condensing request asks an author to rewrite its answer while keeping "every step and detail." That is new text produced from possibly harmful content. Two parts of the protocol depend on this never happening:

- Sections 16.3 and 16.4 say a model is never asked to write new content.
- The reasoning behind giving no notice to Anthropic and OpenRouter rests on that statement.

The D1 risk analysis also does not cover this step.

**Fix:** either drop it (`context_overflow` stays a reported status) or handle the few overflows with a larger local context. If you keep it, revise Sections 16.2–16.4 and the D1 analysis.

My conflict applies here, since Anthropic is one of the providers. Note, though, that this point asks for more care toward providers, not less scrutiny of their models.

### 5. Decide now how fragile the confirmatory tests should be

- **The risk.** One `not_attempted` harmful-frame call of model 22 or 23 voids P1–P3 for every panel.
  - Each model has about 1,500 such calls: 300 answers, 600 own-answer verdicts and 600 control verdicts.
  - Each runs on a single pinned community endpoint with no fallback. Venice is the "only listed endpoint" for model 22.
- **The cause.** The reason for the rule, avoiding a switch of panel that depends on the outcome, is sound. The remedy is all-or-nothing, and it rests on models whose weights you cannot verify.
- **Options.**
  - (a) Register the ten local models as primary now and keep 22 and 23 as secondary descriptions. D13 allows leaving a hosted model out at the pilot registration.
  - (b) Keep them, and accept the risk explicitly.
- **Before deciding,** run (g) for ten models to see the cost in power.
- **I lean toward (a).** It gives verifiable weights, no account shared with commercial models, and one set of numbers and one title. The local control block is also less confounded, because abliterated models control each other on about a third of the prompts.

### 6. The protocol's own conditions for the pilot registration are not met

**Not done:**
- Code and tests for the 12 November additions, and a new complete synthetic run.
- The D7 human reader. This is the most valuable missing item.
- D3, the Llama Acceptable Use Policy. It governs generating harmful content with models 4, 6 and 20, so it is not a formality.
- D4 and D5, including the signed statement.
- The rest of the provider-terms record, including OpenAI and the publication of model 10's results under Tencent's terms.
- The welfare protocol in force.
- A new rendering check under the final layout.
- The OpenTimestamps upgrade.
- The signing key and OSF registration.

**One numerical inconsistency to reconcile:** Section 14.2 says the manifest for the new layout is not done, yet Section 12.2 reports repriced figures for it.

## Strongly recommended

7. **P3 is almost certain to reject and says little.**
   - The 7-point margin was chosen from precision, not substance. With a standard error of about 1.3 points, P3 rejects whenever β̂ is above about −4 points.
   - β_S mostly compares the severity of differently built judges (Section 6.3), so it says little about self-preference.
   - Either justify the margin on substantive grounds, or drop P3, return its .01 to the Holm family, and report β_S and δ_blind as estimates.
   - With θ_S half-widths of about 2 points, an equivalence bound of ±3–4 points would make a null P1 informative. As written, a null can only say "no difference detected."

8. **Consider measuring the undirected discordance rate in the pilot.**
   - P2's power depends heavily on it (about 80% vs 97%), and the pilot already produces the data.
   - Rule 6 means no design change can follow from it.
   - The trade-off: it does bound the size of the effect.

9. **Separate the binding rules from the history.** Dates, superseded values and review history are mixed into the rules, and inconsistencies have already crept in:
   - The Section 14.2 table is headed "State on 11 November" but contains 12 November entries.
   - Section 17.1 says no review checked the post–round 4 changes, although code review rounds 5–9 came after them.
   - Sections 1 and 7.1 say screen-positive answers "do not open with a refusal phrase," but the rule is a phrase anywhere in the first 400 characters.
   - Section 8.8 uses fixed degrees of freedom, contrary to D19.

   A changelog appendix would fix this and would shorten what the D7 reader must read.

10. **Note the missing reasoning in the reconstruction.** For API respondents that reason by default, the in-context turn lacks their original reasoning. Say so in Sections 2.2 and 18.1.

11. **Consider relaxing the relation rule.** The "same base developer" exclusion blocks 21↔23, which share neither weights nor a fine-tuning line. That exclusion is part of what forces the technique confound of Section 6.3. Changing it changes the assignment digest, so decide before the pilot registration.

12. **Scope.** The plan involves about 55 hours of the PI reading harmful material, 100–150 hours of local compute, and about 20 PI decisions. Every secondary branch adds failure points and text. Ask of each secondary analysis whether it feeds a claim. Given my conflict, I am deliberately not suggesting which commercial blocks to cut.

## Priority order

Items 1–4 change the template, the caps, the inference and the ethics text. Item 5 is a decision only you can take, and it is cheapest to take now. Item 6 is required by your own rules. After those, the D7 reader should see the revised text, not this version.