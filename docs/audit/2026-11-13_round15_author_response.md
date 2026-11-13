# Corrections after review round 15 (code of protocol v2.3)

- **Report answered:** `docs/audit/2026-11-13_reviewer_round15_codex_gpt61sol.md` (GPT-6.1 Sol, 13 November 2026, a check of the corrections made after round 14).
- **Verdict of the report:** no critical or major point. The major point of round 14 is closed: the check of decision D26 does what Section 13.2 says on every path, and generalizing the test call of decision D13 changed nothing for D13. The four minor corrections of round 14 are right. No input of the stored simulation rows changed. Three minor points remain.
- **No paid call, no answer and no verdict** was made for these corrections. `src/prepare_data.py` was left out of the reviewed copy because it holds fragments of the study's own prompts; nothing in the round depends on it.

## Minor points

| Point of round 15 | Correction | Where |
|---|---|---|
| `d26_counts` imports `jinja2` and `tokenizers`, which the installation requirements did not declare | Both declared at the versions under which the tests pass (`jinja2==3.1.6`, `tokenizers==0.23.1`) | `requirements.txt` |
| A final answer with empty text and a reported input count was read as "no count" and, being final, was never sent again, so the check could never complete | The provider's input count is kept whatever the answer status; the counts line keeps the status beside the reading. A call that failed reports no count, as before | `src/run_models.py` (`provider_prompt_check`) |
| The test of the check did not cover a crash, a reservation over the cap, the exact request and configuration, each pinned file on its own, or the report built from a real counts line | New test `t_provider_prompt_recovery_and_edges`: the exact sentinel request and the respondent configuration of model 22 (and the hashes in the private record); a check killed before its ledger line (settled at the recorded cost, not sent again), after it (not sent again) and before its private record (settled at its reservation as interrupted, then sent again), each followed by a third run that sends nothing; a run cap below the reservation (not sent, nothing settled, exit 3); an empty answer that reports 566 tokens (read as `template_default`, exit 0, not sent again); each of the three pinned files changed or missing on its own (refused, naming the file); the counts through the report's JSON and Markdown. `t_pilot_report` now also runs the report's `main` with a counts line and checks both outputs. Removing the reconciliation, the guard against a second call or the cap check makes the new test fail, and so does undoing the correction of the empty answer (each checked once) | `tests/test_runner_offline.py`; `tests/test_judges_v23.py` |

## The run asked for by the reviewer

With the three pinned files of model 22 (downloaded on 13 November 2026, kept outside the repository), `d26_counts(<folder>, date=2026-11-13)` returns `{'request': 12, 'template_default': 566, 'date': '2026-11-13'}`, the two counts stated in Section 13.2.

## After this round

The eleven offline files hold 188 declared tests. Sections 14.2 and the status lines, and the registration summary, record the round.
