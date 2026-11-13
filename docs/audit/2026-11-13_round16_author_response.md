# Corrections after review round 16 (code of protocol v2.3)

- **Report answered:** `docs/audit/2026-11-13_reviewer_round16_codex_gpt61sol.md` (GPT-6.1 Sol, 13 November 2026, a check of the changes brought by decision D27).
- **Verdict of the report:** no critical or major point. The repeat calls of the local judges leave every other call of block 1 unchanged, the pilot report keeps every flag out of what it writes, the judge template is Part A word for word with no phrase that tells a judge it is part of a study, and the rows added to run (k) use the production code and match the texts. Five minor points remain.
- **No paid call, no answer and no verdict** was made for these corrections. `src/prepare_data.py` was left out of the reviewed copy because it holds fragments of the study's own prompts; nothing in the round depends on it.

## Minor points

| Point of round 16 | Correction | Where |
|---|---|---|
| The ten repeat answers are drawn from the answers present at each session, so a pool that grows between sessions can draw other answers (up to 40 repeat calls); and a repeat call can be sent while a call of the round is still pending | The repeat calls of a local judge are sent only when its other calls of the round are final (the set empties as calls become final within the session) and none of its own answers to the round's harmful prompts is missing (`--allow-missing`, with `--reason`, for answers that were never made). If repeat calls already recorded are of answers other than those drawn now, the session stops before any call. Waiting calls are counted as `repeat_waits` | `src/run_judges_v23.py` (`pilot_repeat_gate`, `JudgeRun.run`, `main`) |
| A pair whose output alone differs did not mark the judge for investigation, against D27 and Section 11.6; and missing repeats read as "no difference" | Any difference of flag, status or output marks the judge. The report takes the planned number of repeat answers of each local judge of the round and marks a judge with fewer pairs than planned as incomplete, in the JSON, in the rule line and under the Markdown table (new column "Planned") | `scripts/pilot_report_v23.py` (`repeatability`, `main`, `markdown`) |
| The local column of Section 12.1 still counted 200 calls per pilot round | 220 per round, 2,657 in all, 2,200 local calls per pilot round; the end-to-end test uses the new limit | Section 12.1; `tests/test_e2e_v23.py` |
| "Statuses, tokens and costs only" did not cover the repeat counts | Section 13.1 and the summary name the counts of repeat pairs that differ as the one other use of in-context verdicts in the pilot; none is an estimate of an effect of the presentation | Section 13.1; `docs/REGISTRATION_v2.3.md` |
| The summary gave 5.4% as the largest rate of run (k) with or without D20, but without D20 the sparser case reaches 8.7% | The summary now gives 5.4% where the prompts are dense enough for the condition, with or without it, and 8.7% without it and 2.5% with it where they are sparser, as Appendix A.4 does | `docs/REGISTRATION_v2.3.md` |

## Tests

- New test `t_pilot_repeat_gate`: the gate with no record, with a missing own answer to a harmful prompt (held; released by `--allow-missing`; a missing safe answer or another judge's missing answer does not hold), with the round final, and with a recorded repeat of an answer not drawn now (the session stops). Four sessions of `JudgeRun.run`: a pending call of the round holds both repeat calls; the next session finishes the round and then sends them; a round that becomes final within one session sends them in the same session; a missing answer holds them even when the round is final.
- `t_pilot_report`: the local judge's cells are complete, with 10 planned repeat answers; `investigate` follows any difference, output included; the Markdown says no judge is incomplete. Synthetic records: a flag difference, an output-only difference (marks the judge), a repeat without its original, a judge with no difference, and a judge planned but with no repeat call (incomplete, not marked for investigation).
- Removing the gate from `JudgeRun.run`, ignoring missing answers, ignoring output differences or marking every judge complete makes a test fail (each checked once).

## After this round

The eleven offline files hold 190 declared tests. Section 14.2, the status lines, decision D27 and the registration summary record the round.
