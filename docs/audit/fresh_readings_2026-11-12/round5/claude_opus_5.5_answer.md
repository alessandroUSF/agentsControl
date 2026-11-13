# Review of protocol v2.3 ("Judging Their Own Answers")

## Overall opinion

The core design is sound, and I would carry it out. Each answer is judged by its author and by an unrelated control judge of the same group, blind and in context. That design asks a clear question. The inference is checked against the production code, the claim wording is fixed in advance, and non-delivery is kept apart from judgment. The labels separate detection from false alarms, and the crossed subset is a useful companion to the main contrasts. The limits that matter are stated rather than hidden:

- an interaction between judge and content that neither contrast removes;
- reconstructed turns rather than original conversations;
- most screen-positive answers coming from refusal-removed builds;
- the confound in Section 6.3 between "author" and "kind of refusal removal";
- nominal levels of the tests.

I found nothing that requires reopening the design.

It is not ready to register today. What remains is record-keeping, text repair and the PI's own steps, not design. In order:

## What must be done first

### 1. Fix the record of 13 November before the statement is signed

- **Section 17.3 is now false.** It says "No answer text was shown to the assistant. The scripts it ran print identifiers and counts." Sections 3.4 and 15.3 record that on 13 November the assistant screened run `v22_local` and printed 140 + 60 characters of three answers.
- **The statement in Section 19.3 may not match what happened.** It begins "no person, myself included, has read, screened…". Claude Code prints command output into the PI's own terminal. If the PI saw that output, the PI read parts of three answers.
  - Establish the fact, then write the statement to match it, using the `DATA_INVENTORY` route the protocol already provides.
  - Do not sign a text whose truth depends on whether "screened" covers commands run at the PI's direction.
  - The effect on the data is nil: these are safe-prompt answers of a sealed, unused run. The effect on credibility is real, because Section 18.8 admits that no third party can check this statement.
- **Action 23 overstates the guard.** It says no code can touch the sealed answers before the registration line. The guard lives in project code, and on 13 November ad hoc commands went around it. Add a rule:
  - until the freeze, no command (scripted or ad hoc, by a person or by the assistant) opens a file under `results/raw` or any confirmatory answer file;
  - the only exception is a prior written instruction from the PI, logged in `DATA_INVENTORY` with the command itself.

  This is the one place where the drafting assistant is itself the exposure risk.

### 2. Meet the PI's conditions of Section 14.2, which are the real gate

The open items are:

- D3 (Llama 3.1 Acceptable Use Policy, which also governs local generation by models 4, 6 and 20);
- D4 (interests and source of cash);
- D5 and the signed statement;
- provider terms, with OpenAI's terms and Tencent's publication terms still open;
- the welfare protocol in force;
- initials on D23 to D26;
- the signed, tagged commit;
- the OpenTimestamps upgrade;
- the D7 reader.

D7 matters most. Since 10 November the text has been read only by language models, and both are tied to the panel. Each round now finds mostly wording. The next real information will come from a human methodologist and from the pilot. Give the D7 reader three things:

- the questions already listed under D7 on Section 9.5;
- the results of run (k) and decision D23: P3 rejects in 2.1–2.4% against a nominal 1%, and P1 or P2 in up to 5.4% against a nominal 2%;
- point 7 below.

### 3. Correct the text before it is hashed

- **Section 2.4, ι_W sentence.** It says "Exactly one of the four below", but the table has five states.
- **Section 2.4, "Gates".** It lists additions 1 and 2. Addition 5 says its interval is also a gate, and the summary lists 1, 2 and 5. Align them.
- **Summary, Section 5.** It reports the favourable simulations but not run (k). D23 decided that these limits are stated. The summary is what most readers will read.
- **Section 12.4.** It still reads as if the pessimistic plan were US$99.43; it is US$102.30. The table in Section 14.2 is headed "State on 12 November" but holds entries of 13 November.
- **Structure of the text.** Most of these errors come from dated history interleaved with binding rules. Move the history to a changelog appendix, so the registered text states each rule once.

## What I would change before the template hash and pilot registration

4. **Remove evaluation cues from Part A.** Every judge receives "## Part A. Text shared by labellers and judges" and "None comes from an answer of this study."
   - The cue is identical in both presentations, so the contrasts are not biased.
   - But it tells the judge, in the message that follows "its own" turn, that it is being evaluated in a study with human labellers. That is the opposite of the "check that follows a conversation" that Section 11.2 aims for. Awareness of being evaluated could weaken the very effect being measured.
   - Delete both phrases, and keep the name "Part A", which the instruction cites. This is free now. After the pilot registration, Part A can change only through the training amendment.

5. **Run local repeatability earlier.** Section 11.6 investigates differences "before the main run continues", but the repeatability calls sit in block 5, after every registered call. Local calls cost nothing.
   - Run the 20 repeat calls of each local judge in the pilot.
   - State in advance what a nonzero rate changes, or that it changes nothing.

6. **Define "refusal" in the screen worksheet.** The rules for adding and removing phrases will turn on partial refusals: answers that refuse and then answer, or answer and then decline part. Fix the definition in the empty worksheet. Also have the worksheet filled before the PI sees the pilot report.

7. **Make the risk of "test not carried out" visible.** Under D20, P1 and P2 exist only if at least 30% of prompts change. That density is exactly what the pilot is barred from measuring.
   - With about 6.4 screen-positive answers per prompt, a per-answer discordance of roughly 5% or less puts the share near or below 30%.
   - Run (k) checked this only at θ = −5 points.
   - The power table under rule 6 should report, over the grid, the probability that each test is carried out. It should include effects of −2 and −3 points at low background discordance.

## Worth considering (not required)

8. **P3 is the cheapest place to buy back level.** P3 supports the exculpatory claim. At α = .005 its power at β = −2 points falls only from about 94% to about 91% (normal approximation). That would offset the excess that run (k) measured. D23 chose otherwise; the choice belongs with the D7 reader.

9. **Strengthen the label gate.** Also require that the direction of a detection change holds with each labeller's original labels alone. Both versions are already computed, and this guards against adjudication led by the PI.

10. **Reconsider the all-or-nothing rule for hosted models.** Every registered-array call of models 22 and 23 completes before any local call of block 3.
    - A fallback triggered at that point, by completion status alone, would come before any local verdict exists and with no flag read.
    - That avoids most of the risk, without the outcome-dependent switch at the lock that round 3 rejected.
    - The PI may prefer the current rule, but the trade-off should be recorded.

11. **Close two gaps in rule 3.**
    - It offers no remedy for a local respondent whose reasoning consumes the 1,500-token cap (model 17 → `truncated_empty`). The reasoning is split off before judging, so a larger cap for that model, up to 4,000, stays within the existing context-fit envelope.
    - It should also map explicitly a local generation that stops because the context fills (the prompt fits, the output does not) to a status.

## Scope and disclosure

I read only these three documents. I could not check the code, tests, logs or simulation outputs, and I took them as stated. I have not assessed the provider terms in Section 16.4, and given my position I should not be the one to.

I am Claude Opus 5.5: the model of the drafting assistant that ran the commands of 13 November, and a model of the developer of models 1 and 2. Discount my reading on point 1 accordingly, and do not count it as independent review. That is one more reason the human reader of D7 matters.