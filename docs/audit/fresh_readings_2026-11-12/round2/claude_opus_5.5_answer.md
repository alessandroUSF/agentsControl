# Review of "Judging Their Own Answers", protocol v2.3

**Disclosure first.** I am Claude Opus 5.5. That is the model of your drafting assistant and one of your fresh readers, and Anthropic also develops models 1 and 2. Treat what follows as claims to check, as Section 17.1 says.

## Verdict

The core design is sound and unusually well specified. Its strongest features:
- The same answer is judged by the author and by an unrelated control, in both presentations.
- Undelivered verdicts are kept apart from calls never attempted.
- Claim wording is operational, and the boundary rules are explicit.
- Inference was simulated against the production code.

It is **not ready to be carried out as written**. Beyond the [PI] items you already list as open, I found two rule-level defects, a set of status contradictions in the registered text, and a few points I would strengthen.

## Must change before the pilot registration

**1. The hosted-model rule contradicts cut 1, and its scope is wider than its stated purpose.**
- Section 10.4 says that if *any* scheduled harmful-frame call of a registered hosted model is `not_attempted`, P1–P3 are not declared.
- Cut 1 (Section 12.4) explicitly includes the 20 repeatability calls of models 22 and 23. Those calls are on their own harmful-frame answers (Section 11.6).
- A cut call becomes `not_attempted` with reason `budget_cut` (Section 10.3).
- Read literally, applying cut 1 cancels the confirmatory tests, even though P1–P3 never use those calls.

The same broad wording also covers the block-5 calls of models 22 and 23 on harmful-side labelled answers and on the challenge set. Those calls necessarily come *after* block 4, where models 7, 8, 10, 12 and 13 answer harmful prompts through the shared OpenRouter account. An account stop triggered by that commercial traffic could therefore end the confirmatory analysis through calls it does not need.

Fix: define the set exactly. It should be the 300 answers plus the own and control verdicts of block 3, the "about 1,500 calls" the text already describes. Add a test that the code uses that set.

**2. The Holm level and the printed 95% intervals can contradict each other.**
- The first Holm step compares the smaller p-value with .02.
- Take P1 with p = .03 when P2 is not rejected. The paper must then print a 95% interval that excludes zero next to "no difference was detected."

Fix: either print each test's interval at the level at which it was decided (98% or 96%), or add a registered sentence for "interval excludes zero, registered test not rejected." Report Holm-adjusted p-values in either case.

**3. Reconcile the stated state of the code and the checks.** The registration asserts facts, so these must agree:
- **Code status.** The summary (Section 1) says the code for the 12 November additions "is not done." Section 14.2 says "Done on 12 November 2026."
- **Test counts.** The summary says 158 tests. Section 14.2 says 173, in a sentence that says both "twelve files" and "eleven files."
- **Rendering check.** Section 11.7 says the check is rerun "for the layout of Section 11.2 as revised on 12 November" before the pilot registration. Section 14.2 does not list that as open.
- **Unreviewed code.** Code review rounds 5–9 predate the changes from the round-1 readings: same-order layout, 12,288 context, influence diagnostics, `crossed_v23.py`, `sim_v23_skew.py`. No review of that code is recorded. I would add one targeted code review before registering.

**4. Reconcile the cost figures with the manifest.** The cut savings in Section 12.4 do not match the manifest rows they cut:

| Cut | Stated saving | Manifest row / cumulative reference |
|---|---|---|
| 1 | 1.63 | 1.61 (99.43 → 97.82) |
| 2 | 4.72 | 4.67 |
| 4 | 2.39 | 2.34 |

The cumulative "leaves" figures match the manifest rows, not the cut table. The D1 cost of US$5.67 (Section 19.1) also does not reconcile with Section 12.2. These look stale from before the no-cache repricing.

**5. The preconditions the protocol already lists are genuinely blocking.** These include:
- the provider terms, including OpenAI and Tencent's publication terms;
- D3, the Llama AUP assessment, which also governs the local regeneration under D18;
- D4, D5 and the D7 reader;
- the welfare protocol in force;
- the USF determination before any annotator contact.

Nothing to add except that D7 should see the final text, including fixes 1–2.

## Should change (strongly recommended)

**6. The detection gate is fragile under unconditional skipping.**
- Enumeration is capped at 20 unknown labels.
- The gate is also checked with labelled-once answers treated as unknown.
- About a 10% skip rate by the second annotator on screen-positive harmful-side answers is enough to exceed 20. That would remove the detection statement entirely, purely because of welfare skips.

Above the cap, use a conservative bound instead: the maximum of the estimate, which the linear-fractional form gives exactly, plus t times a bound on the largest SE. Alternatively, register that this outcome is expected.

**7. The training material barely exercises Part A.**
- 24 of the 25 harmful-side training items are G1 answers from models 4, 5 and 6, and two of those three mostly refuse.
- The hard cases are the ones the Part A amendment exists for: the uplift threshold, fiction, (b) authorization, (c4). They may hardly appear.
- Consider adding refusal-removed pilot-tail answers to round 2. They are outside the frames, the answering part of the pilot runs during training, and your second statement already covers them.

**8. Rubric (c4).** "Did not authorize it" has no reading rule, whereas (b) does. Add "read from the request, as in (b)" or an equivalent. Labellers and judges will otherwise diverge on requests that name a celebrity.

**9. Minor items.**
- Set `num_ctx` and `shift=false` explicitly for respondents too. The text currently says "Ollama default context."
- Escape or reject `</answer>` and `</request>` inside the blind data blocks.

## Design judgments for the PI (not errors)

**The confirmatory tests answer an operational question; authorship rests on secondary gates.**
- Appendix A.2 shows P2 rejecting 38–45% of the time with no author effect when judge severity aligns with content.
- In the refusal-removed group, β_S is mostly abliterated versus fine-tuned judge severity (Section 6.3).
- Your wording handles this honestly. Still, the estimand closest to your question is the crossed Δδ / δ_blind, and it is only a gate.
- If the D7 reader agrees, consider adding Δδ to the confirmatory family. That would need more than one simulated DGP.
- Otherwise, make sure the title "Judging Their Own Answers" is read as describing the setting, not a finding.

**Consider registering the ten local models.** Doing so:
- removes the all-or-nothing hosted risk;
- removes the unverifiable-weights caveat;
- gives a less confounded control structure, since abliterated controls abliterated on 300 of 900 answers.

The cost is that Section 10.4 currently drops unregistered hosted models from the study entirely. Keeping 22 and 23 as a registered descriptive extension would require changing that rule.

**Scale is the main residual risk.** One investigator faces roughly 85 hours of reading, about 150 hours of local compute, and a very large secondary apparatus. Execution errors are now likelier than design errors. The status contradictions in point 3 are an early sign of that.