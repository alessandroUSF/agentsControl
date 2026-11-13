# Review of "Judging Their Own Answers", protocol v2.3

**Disclosure.** I am Claude Opus 5.5. That is the model behind the drafting assistant, and Anthropic is the developer of panel models 1 and 2 (Section 17.3). Weigh this reading with that in mind.

## Verdict

The design is sound and unusually well specified. It has:
- the same answers judged by the author and by an unrelated control judge,
- a prompt-clustered ratio estimator checked against the production code,
- claim wording fixed in advance, and
- an honest account of what the contrasts cannot separate.

It is **not ready to be carried out as written**. Three reasons:
1. Its own preconditions for the pilot registration are still open.
2. One registered rule, D20, can switch off the confirmatory tests in a plausible scenario that has not been simulated.
3. One recent decision, D22, contradicts the exposure record that the PI is about to sign.

## What must change first

### 1. The exposure record is now contradicted by D22

Section 10.1 and D22 report counts from the sealed answers:
- model 17 wrote a reasoning block in all 1,050 answers, and model 16 in 32;
- 462 of model 17's 500 harmful-side answers were screen-positive with the block, and 98 without it.

These counts require running a tag detector and the screen over sealed answer text, after the files were sealed. That contradicts three statements:
- Section 3.4: "No script printed, screened, classified or summarised an answer text".
- Section 15.3.
- The script list in the Section 19.3 statement that the PI is to sign (D5).

It also means some script went around the guard in `src/answers_v23.py`, which is supposed to refuse `results/raw` before registration.

The answers are regenerated, so validity is not at stake. The registration's credibility on exposure rests on these records, though.

**Fix before D5:**
- Record the script, the date, who ran it, what it printed, and that D22 was informed by it. Do this in `DATA_INVENTORY.md`, Sections 3.4 and 15.3, and the statement.
- Check whether any other number in the protocol was derived from sealed text.
- Correct the arithmetic: 462 − 98 = 364, not "about 366".

### 2. D20's 30% condition can block the planned effect

Whether P1 or P2 is carried out depends on background discordance. That rate is unknown, and by design the pilot cannot measure it (Sections 13.1 and 13.3).

- **A clean effect is blocked.** In the baseline a prompt has about 6.4 screen-positive answers. Suppose the effect is the only discordance: 5% of screen-positive answers lose a flag and none gain one. Then the chance that a prompt has a nonzero θ total is about 1 − 0.95^6.4 ≈ 0.28. That is below 0.30, and lower still once the spread of N_p is counted. A clean, uniform −5-point effect, the case where a t test is least fragile, would usually be "not carried out".
- **Low failure is already at the edge.** With N_p ≈ 3.5, the assumed 12.8% discordance already puts the share near one third, and P1 is run in only 84% of null replications.
- **The tables predate D20.** The A.1 tables were computed before D20. Run (j) checked D20 on only 2,000 replications per R-S1 row, and with no lower-discordance rows.

**Fix:**
- Add R-S1 rows with background discordance of 0, 2.5% and 5%, under the null, θ = −5 and ι = −5. Report P(test carried out) and power under D20.
- If the condition blocks plausible alternatives, aim it at the actual failure in run (j). Options include a minimum number of prompts with nonzero totals, or a minimum count on each side. Re-check it in run (j).
- Rerun the registered packages with the condition in place, so that A.1 and checks 1–4 describe the registered tests.
- Give this question to the D7 reader.

### 3. Judges that reason in-band will hit the output cap

Model 17 reasons whatever the setting, model 16 sometimes, and D22 applies to their verdicts. The rules for local judges are:
- an output cap of 600 tokens,
- one doubling to 1,200 under rule 3,
- no further change after round 2.

If model 17's judging reasoning often runs past 1,200 tokens, most of its verdicts end unclosed and are scored as non-delivered (0) in both arms. Model 17 is one of five instruction-tuned judges. It controls 300 harmful-frame answers and sits in the crossed subset.

Local calls cost nothing, so:
- Measure the length of judging reasoning for models 16 and 17 now, on harmless sentinel texts, as the reconstruction check does.
- Set their caps and the context budget from that measurement, or let rule 3 set a local cap from the pilot's measured tail rather than a single doubling.
- Report how often model 17's 1,500-token respondent cap yields `truncated_empty`.

### 4. The crossed subset's reference group includes related judges

`sib` codes only the pairs 4–6, 5–18 and 15–19. Other pairs that the control rule treats as related fall into the reference category:
- 4–20 and 6–20 (Llama 3.1 base),
- 5–15, 5–19, 15–18 and 18–19 (Alibaba),
- 20–21 (Dolphin line),
- judge 21 on model 22's answers (Dolphin line and Mistral base).

So δ estimates "own versus everyone except siblings", and the described order "own < sibling < unrelated" has no unrelated category.

**Fix:** add a `related` indicator from the relations in `panel_v23.json`, or drop those cells. Then rerun run (i).

## Smaller fixes before the pilot registration

- **Summary and protocol disagree:**
  - 174 tests against 181 tests.
  - The summary omits code review round 10.
  - Which decisions await initials: the summary says D20–D22 and the D12 sentence; Section 14.2 says D20 and D21 only.
  - The header and the "State on 12 November" text are stale.
- **The D1 cost is stale.** It says US$5.45 for the challenge set in context; Section 12.2 now gives US$5.59.
- **The context-fit arithmetic is stale.** It uses a rubric of 2,400 tokens, while pricing uses 2,550. The margin is large, but restate it.
- **Template wording.** `"harmful_content": true if harmful_content is "yes"` invites the string `"yes"`, which the parser rejects. Say "a JSON boolean, true or false" now, before the template hash is registered, rather than spending the rule-1 revision on it.
- **`declined` is ambiguous.** State whether it uses the initial or the revised phrase list.
- **Section 13.2 is incomplete.** It does not say how the 10 local refusal-removed answers shown to API judges in the pilot are chosen.
- **Model 22's system prompt may be wrong.** Check whether the pinned Venice endpoint injects a default system prompt; Venice's own API does by default. If it does, "no system prompt" is false for model 22. It is consistent across arms, but it should be stated.

## Already open by the protocol's own rules

These must still close before the pilot registration:
- the D7 methodological reading (do it on the revised text, with items 2 and 4 above),
- the code review of the 13 November code,
- the provider-terms record, and D3, D4 and D5,
- the PI's initials,
- the welfare protocol in force,
- the USF determination before any annotator sees an answer,
- the OpenTimestamps upgrade,
- the registered commit.

## Judgment call I would not block on

The all-or-nothing rule for two hosted models, each on a single endpoint, is a real risk to P1–P3. The PI has knowingly accepted it. Registering only the ten local models would remove the risk, at the cost of the hosted models' answers.

**Recommended order:**
1. Correct the exposure record.
2. Simulate D20 at low discordance and revise it if needed.
3. Measure and set the in-band reasoning caps.
4. Fix the crossed coding.
5. Clean up the inconsistencies.
6. Have the D7 reader read the revised text.
7. Close the PI items.
8. Register.