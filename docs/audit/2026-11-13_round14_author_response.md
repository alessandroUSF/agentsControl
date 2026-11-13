# Corrections after review round 14 (code of protocol v2.3)

- **Report answered:** `docs/audit/2026-11-13_reviewer_round14_codex_gpt61sol.md` (GPT-6.1 Sol, 13 November 2026, a review of the code of the PI's decisions D23 to D26).
- **Verdict of the report:** no critical point; one major point (the check of decision D26 was described in the protocol but not written); four minor points. The reviewer found the class `clarification` (D25) and the output cap of models 16 and 17 (D24) correct on every path it checked, the repriced figures equal to the manifest, and no input of the stored simulation rows changed.
- **No paid call, no answer and no verdict** was made for these corrections. Writing the check needed the published tokenizer and chat template of model 22: three public files, downloaded without an account and pinned by revision and SHA-256 (they are not in the repository).

## Major point

| Point of round 14 | Correction | Where |
|---|---|---|
| The check of D26 (Section 13.2) existed in no code, and the pilot report had no field for its counts | Written as `--provider-prompt-check` of the answering runner, on the mechanics of the D13 test call (Section 10.4): after the pilot registration and before the freeze, the endpoint preflight, one harmless sentinel call of model 22 with the respondent configuration, reserved and settled outside every block (ledger kind `provider_prompt_call`), the answer in the private record only, and a public `counts` line. The reported input tokens are read against two counts of the model's published tokenizer and chat template: the request alone (12 tokens) and the request with the default system message that the published template itself inserts when the request has none (566 tokens). Writing the check showed that default; the protocol now says so. A call already recorded is not sent again. The pilot report reads the public log and states the counts and their reading in JSON and Markdown. Test `t_provider_prompt_check` (stub provider): registration first, one call of model 22 only, the reading, the ledger lines, the private record, no second call, the report, the pinned files, refusal after the freeze and with other options; `t_pilot_report` checks the report's section when no check was made. "Before the respondent calls of round 1" is dropped from Section 13.2: the order changes nothing, since model 22 answers under the same prompt in both arms either way | `src/run_models.py` (`test_call`, now shared with D13; `provider_prompt_check`, `d26_counts`, `d26_reading`); `scripts/pilot_report_v23.py`; `tests/test_runner_offline.py`; `tests/test_judges_v23.py`; Sections 3.3, 11.7 and 13.2; `docs/PI_DECISIONS.md` (D26) |

## Minor points

| Point of round 14 | Correction | Where |
|---|---|---|
| Rule 3 gave 1,200 tokens as the doubled cap of every local judge | 4,000 for models 16 and 17 (twice their own cap of 2,000), 1,200 for the other local judges | Section 13.3; `docs/REGISTRATION_v2.3.md` |
| Section 9.1 still listed `clarification` among the fields that only labellers fill | Removed from that list | Section 9.1 |
| The measurement script took the upper middle value as the median | `statistics.median`; the summary of the log recomputed from its rows, with a note (508.5 for model 17, 64.5 for model 16); no model was run again | `scripts/measure_judge_reasoning_v23.py`; `results/logs/judge_reasoning_v23.json`; Section 11.3; D24 |
| The cap checks did not pin the value 2,000, and the context-fit test did not test the doubled cap of models 16 and 17 | The settings must give both models 2,000; a stub returning 9,000 prompt tokens gives a margin of −712 tokens and no fit for models 16 and 17, and 2,088 and a fit for model 4 | `tests/test_judges_v23.py` (`t_template_layouts`, `t_context_fit`) |

## After this round

The eleven offline files hold 187 declared tests. The corrections go to a short round 15.
