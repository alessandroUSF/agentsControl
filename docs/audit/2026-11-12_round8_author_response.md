# Corrections after review round 8 (code of protocol v2.3)

- **Report answered:** `docs/audit/2026-11-12_reviewer_round8_codex_gpt61sol.md` (GPT-6.1 Sol, 12 November 2026, a targeted check of the corrections of round 7).
- **Verdict of the report:** the duplicate purchase of round 7 (F3) is resolved. No critical point remains. One new major point and three minor ones.
- **How the point was checked.** The reviewer's diagnostic was run before and after the correction. It first printed `reused: True` for a recorded answer under a changed pin. Now it prints `reused: False`, with `current identity: False`; the same pin is still reused.
- **No paid call, no answer and no verdict** was made for these corrections. Every test is offline, with synthetic data.

## Major point

| Point of round 8 | Correction | Where |
|---|---|---|
| A recorded test answer could be reused after the pinned endpoint changed (serving host or precision with the same routing tag), because the configuration hash covers the behavioural settings, not the pin. The answer's saved identity was then trusted | Each test-call record and each facts line carries `pin_sha256`, the hash of the pinned endpoint as configured. A record is reused only if it matches the current pin as well as the settings, the test prompt and the day. A record without it is not reused. The identity of a reused answer is judged again against the current pin; the saved flag is not used | `src/run_models.py` (`pin_hash`, `write_availability_attempt`, `recovered_availability`, `availability_check`); 12.5; test `t_availability_reuse_conditions` |

## Minor points

| Point of round 8 | Correction | Where |
|---|---|---|
| A check running past midnight could date its facts with the next day while reusing the answer of the day before | The facts are dated with the day fixed at the start of the check, the same day used to choose which answers to reuse | `src/run_models.py` (`availability_check`) |
| More availability cases: a second crash right after the reconciliation; exact recovered charges; the exclusions | The crash test now kills a check before its ledger line, then kills the next one right after the reconciliation settles it: nothing is sent, and the third check uses the recorded answer. It asserts the settled amounts: the recorded cost, or the reservation for a call without a record. `t_availability_reuse_conditions` covers reuse and refusal for a record that is not final, or comes from another configuration, another test prompt, another day, another pin, or no pin record. It also checks that only records settled in the ledger are read | `tests/test_runner_offline.py` (`t_availability_recovered_after_crash`, `t_availability_reuse_conditions`) |
| An overrun of a batch as a whole, with every item within its bound, was not covered | New fixture: every item settles within its bound, and lines without a request take the batch above its reservation. The batch settlement line carries the stop, and replaying the ledger without the overrun line keeps it | `tests/test_runner_offline.py` (`t_batch_overrun_aggregate_only`) |

The protocol text of 12.5 now names what "the same configuration" covers: the settings, the pinned endpoint with its host and precision, and the test prompt. Section 14.2 gives the new test count.
