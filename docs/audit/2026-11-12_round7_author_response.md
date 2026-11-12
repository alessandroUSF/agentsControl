# Corrections after review round 7 (code of protocol v2.3)

- **Report answered:** `docs/audit/2026-11-12_reviewer_round7_codex_gpt61sol.md` (GPT-6.1 Sol, 12 November 2026, a targeted check of the corrections of round 6).
- **Verdict of the report:** do not register yet. No critical point remains. One major point remains: F3, the availability check after a crash, is partly resolved. The minor points are gaps in the tests.
- **How the point was checked.** Before the correction, the reviewer's diagnostic (an availability check killed just after its ledger line) sent the recorded test call again: `repeat: 1`. The new test reproduces it.
- **No paid call, no answer and no verdict** was made for these corrections. Every test is offline, with synthetic data.

## Major point

| Point of round 7 | Correction | Where |
|---|---|---|
| F3. A recorded test answer whose ledger line was already written before the crash was bought again; only answers of reservations still open were reused | After the reconciliation, the check reads every private test-call record that has a ledger line (`settled_availability_records`). For each model it uses the first final answer of the day made under the same configuration and test prompt, and does not send the call again. This now holds whether the check that made the call stopped before its ledger line, after it, or ran to the end. The evidence names the time and run of the recorded call. A call killed before its record is still settled at its reservation and sent again | `src/run_models.py` (`settled_availability_records`, `recovered_availability`, `availability_check`); 12.5 (text unchanged: "whose answer was recorded that day under the same configuration is not sent again"); test `t_availability_recovered_after_crash`, three crash points (before the ledger line, after it, before the record) and a check run again the same day |

Two existing tests ran the check twice on the same day in one scratch study and expected new paid calls the second time. Under the rule above, the second check uses the recorded answers. The repeated-key case and the run-cap, key and configuration cases now run in fresh scratch studies, and the same-day reuse is asserted (`t_availability_pilot_and_d2`, `t_availability_call_failures`).

## Minor points (tests)

| Point of round 7 | Correction | Where |
|---|---|---|
| No test of the holds' check against the stored manifest | `t_repricing` checks `stored_manifest_problem`. A matching manifest passes. Five cases are refused: the registered manifest beside repriced holds, no manifest, another total, another cut saving, and a price snapshot file changed after the manifest was written (same repricing file, so the same file hash) | `tests/test_panel_d13_v23.py` |
| The freeze test covered only the manifest gate | Two cases added: the manifest fits but the ledger needs a cut (recorded by the ledger check), and the manifest fits but the ledger does not fit (refused) | `tests/test_runner_offline.py` (`t_freeze_checks_ceiling`) |
| The "no stop" assertion did not check a real settlement; batch overrun crashes were not covered | A reconciliation that settles below its reservation leaves no stop and no overrun flag. In the batch test, the ledger replayed without its overrun lines (as after a crash before each) still holds the stop, from the flags on the batch call lines | `tests/test_runner_offline.py` (`t_overrun_survives_crash`, `t_batch_item_kinds_overrun_and_stale`) |
| The challenge fixture did not test prompts without a contribution and gave a prompt conflicting sources | Sources are now consistent by prompt. One prompt has no answer that enters the change, and the test asserts that dropping it from the domain would give another interval. The interval of the valid pairs is checked by hand too | `tests/test_sim_v23_analyze.py` (`test_change_interval_support`) |
| The F3 test claimed a before-record case it did not run | It runs it now (above) | `tests/test_runner_offline.py` |

## Not changed

- **Physical durability.** The tests inject exceptions with fsync disabled, as the reviewer notes. Every ledger line, and the private record of each paid call sent alone, is written with `fsync` (`durable=True`). A batch answer is charged before its record, and the collection is idempotent. A power cut cannot be simulated offline.
