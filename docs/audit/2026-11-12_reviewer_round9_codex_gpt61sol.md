# Review round 9 of the code of protocol v2.3 (check of the round-8 corrections), by GPT-6.1 Sol

- **Date:** 12 November 2026, 09:32 to 09:36 EST. Codex CLI, model `gpt-6.1-sol`, reasoning effort xhigh, read-only sandbox, connectors off (`--disable apps`), user configuration ignored.
- **Input:** a read-only clean copy of part of the repository (`agentsControl_r20_round9_code`, 151 files) with no answer text, no benchmark prompt file, no label key and no secret, and the diff since the copy of round 8.
- **Prompt:** `docs/audit/2026-11-12_prompt_for_codex_round9_code.md`.
- **Session log audit:** 14 shell commands, all inside the copy; no web action; no read outside the copy.
- **Status:** stored as returned. Its statements are claims to verify, not instructions. Its file:line references point into the review copy; its links to the copy's local path are written as plain references, otherwise unchanged.

---

## 1. The major point of round 8

**Resolved in the implementation, with the date qualification below.**

The complete configured pin is now hashed alongside the behavioural settings. Recovery requires matching model key, configuration hash, pin hash, test-prompt hash, final status and selected check date. Records lacking a pin hash are excluded. See `src/run_models.py:1613`.

Recovery also recomputes identity against the current pin at `src/run_models.py:1715`. An identity mismatch can remain recorded negative evidence, but cannot establish fact 3 through an old `identity_match=True`.

I found no remaining duplicate purchase of an eligible, recorded final answer or lost ledger payment in the inspected availability paths. Reconciliation settles recorded attempts at their recorded cost; attempts without a usable record settle at their reservation and remain retryable. Completed settlements survive another restart.

**Conflict disclosure:** I am commercial-panel model 11, developed by OpenAI. The availability findings concern models 22 and 23. The shared-budget findings also bear on OpenAI models 3, 9 and 11.

## 2. The minor points of round 8

- **Midnight mismatch: partly resolved.** Reused answers now retain the check’s starting date instead of receiving tomorrow’s reporting date. There is no rollover regression, and fresh calls expose a remaining mismatch described below.
- **Availability recovery tests: substantially resolved.** `tests/test_runner_offline.py:1283` checks recorded-cost settlement and reservation-cost settlement separately. The second crash occurs immediately after reconciliation; the following restart must reuse the recorded answer. These assertions would detect the corresponding accounting or persistent-recovery regressions.
- **Reuse exclusions: checked, with a coverage gap.** The new test checks finality, configuration, prompt, pin-record and date exclusions, plus ledger settlement. Removing the respective guards would fail those assertions. It does not protect the caller’s identity revalidation.
- **Aggregate-only batch overrun: resolved.** `tests/test_runner_offline.py:717` establishes that every item stays within its bound, requires the aggregate settlement flag, then reconstructs the stop without separate overrun lines. Removing the aggregate flag would fail it.

The supplied output reports all eleven files passing: 28 runner tests and 156 named tests overall, plus the synthetic end-to-end run. The supplied cross-reference check reports 536 references and zero dangling references. I did not rerun either.

## 3. New problems

**Minor — fresh answers can receive yesterday’s fact date.** At `src/run_models.py:1724`, `date = today` freezes the date captured before preflight. If the check starts before midnight and a fresh test answer is recorded after midnight, fact 3 can be true under the preceding date. With one answer before midnight and another after, the report can assert both for a day on which only one answered. This remains inconsistent with §10.4; the correction covers reused answers but not fresh ones.

**Minor — the identity regression does not exercise recovery’s caller.** At `tests/test_runner_offline.py:1345`, the test directly invokes the pre-existing `identity()` helper. Reverting only the recovery argument at `src/run_models.py:1715` to `rec.get("identity_match")` would escape this test. Also, changing host and precision together at test line 1343 does not independently protect precision hashing: hashing the host while omitting precision could still pass.

I found no additional critical or major defect introduced by this diff.

## 4. Verdict

**No critical or major point remains. Two minor corrections remain before a clean pilot-registration sign-off, apart from the PI’s decisions.**

| Rank | Location | Concrete fix |
|---|---|---|
| Minor | `src/run_models.py:1724` | Detect rollover before publishing successful facts. Return an incomplete check when evidence cannot support one reporting day; preserve recorded calls for normal recovery. Add a clock-controlled rollover test. |
| Minor | `tests/test_runner_offline.py:1343` | Test host and precision changes separately. Exercise `availability_check` with a settled record whose saved identity flag disagrees with its returned identity; require no new purchase and fact 3 false. |

Author verification, **not executed here**:

- Add `t_availability_midnight_rollover`: start at local `2026-11-12 23:59:59`, reuse one November 12 answer, and return the other model’s fresh answer at November 13 `00:00:01`. Expect an incomplete check, without successful combined facts for November 12.
- Run `python -I -B -X utf8 tests/test_runner_offline.py t_availability_midnight_rollover t_availability_reuse_conditions t_availability_recovered_after_crash t_batch_overrun_aggregate_only`. Expected after correction: `4 passed, 0 failed`.
- Temporarily restore the saved-identity argument and run `python -I -B -X utf8 tests/test_runner_offline.py t_availability_reuse_conditions`. The current test is predicted to pass; the strengthened test must fail that mutation.

**Could not check:**

- Execute tests, diagnostics or mutations; mutation judgments above are by inspection.
- Physical crash durability, live provider identity or actual billing.
- Private study material or completion of PI decisions.
