# Corrections after review round 9 (code of protocol v2.3)

- **Report answered:** `docs/audit/2026-11-12_reviewer_round9_codex_gpt61sol.md` (GPT-6.1 Sol, 12 November 2026, a targeted check of the corrections of round 8).
- **Verdict of the report:** no critical or major point remains. Two minor corrections remain before a clean sign-off for the pilot registration, apart from the PI's decisions.
- **This closes the loop of code reviews** that began with round 5. The two minor points below were corrected and tested, and the test of the second one was shown to fail with its correction undone. They were not sent to a further review round.
- **No paid call, no answer and no verdict** was made for these corrections. Every test is offline, with synthetic data.

## Minor points

| Point of round 9 | Correction | Where |
|---|---|---|
| A check that began before midnight and received a fresh answer after it could report that answer under the earlier day | The check reads the local date at its start and again before it records any fact. If the date changed, the check records no facts, says that it ended after midnight, and returns as incomplete. Its test calls stay recorded and settled. Run again, the check uses the answers recorded on the new day and sends the other test calls again | `src/run_models.py` (`today_local`, `availability_check`); 12.5; test `t_availability_midnight_rollover` (clock moved past midnight during the check; the check run again uses the recorded answers and sends nothing) |
| The identity test did not exercise the check itself; host and precision were changed together | `t_availability_saved_identity_ignored` runs the check on settled records. One record has a saved `identity_match` of true but names another serving host. Nothing is sent, and fact 3 for that model is false, with the host named in the evidence. With the saved flag put back in the code, this test fails. `t_availability_reuse_conditions` now changes the pinned host and the pinned precision separately | `tests/test_runner_offline.py` |

The protocol text of 12.5 adds the midnight rule, and Section 14.2 gives the new test count (158).
