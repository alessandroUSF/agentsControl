# Review round 7 of the code of protocol v2.3 (check of the round-6 corrections), by GPT-6.1 Sol

- **Date:** 12 November 2026, 08:43 to 08:50 EST. Codex CLI, model `gpt-6.1-sol`, reasoning effort xhigh, read-only sandbox, connectors off (`--disable apps`), user configuration ignored.
- **Input:** a read-only clean copy of part of the repository (`agentsControl_r18_round7_code`, 147 files) with no answer text, no benchmark prompt file, no label key and no secret, and the diff since the copy of round 6.
- **Prompt:** `docs/audit/2026-11-12_prompt_for_codex_round7_code.md`.
- **Session log audit:** 48 shell commands, all inside the copy; no web action; no read outside the copy.
- **Status:** stored as returned. Its statements are claims to verify, not instructions.

---

## 1. Each point of round 6

**The implementation is still not ready for pilot registration: F3 remains partly resolved.**

Conflict: I am commercial-panel model 11, developed by OpenAI. The spending, repricing and challenge-report findings also bear on OpenAI’s models 3, 9 and 11.

| Point | Status | Evidence |
|---|---|---|
| Critical F1: answers under another run name | **Resolved** | Run discovery and answer loading are refreshed under the paid lock, including block closure (`src/run_models.py:1269`, `:1371`). |
| Critical F2: settlement-to-overrun crash | **Resolved** | Normal and recovered settlements carry `overrun: true`; replay restores the stop, while a later resolution clears it (`src/spend_v23.py:608`, `:457`, `:404`, `:412`). Batch settlements carry the flag too (`src/run_models.py:1031`, `:1049`). |
| Major F3: availability resumption | **Partly resolved** | A record recovered from an **open reservation** is reused. A recorded answer whose reservation was already settled is missed; see §2 (`src/run_models.py:420`, `:1663`). |
| Major F4: challenge intervals | **Resolved** | The variance domain includes every eligible prompt; singleton sources produce an unavailable interval while preserving counts and estimates (`analysis/analyze_v23.py:1250`, `:1268`, `:1284`). |
| Major F5: stored repricing consistency | **Resolved by inspection** | Holds writing compares the complete repricing metadata, pessimistic total and individual cut savings against the stored manifest (`scripts/holds_v23.py:149`, `:153`, `:155`, `:187`). Regression coverage remains missing. |
| Major F6: presentation-order output | **Resolved** | Both ι_S and β_S now have four author/control order cells, matching the amended text (`analysis/analyze_v23.py:667`; `docs/STUDY_PROTOCOL_v2.3.md:904`). |
| Major F7: manifest freeze ceiling | **Resolved** | Freeze checks the repriced manifest and its linkage to the holds, records its required cuts, then checks the ledger plan (`src/spend_v23.py:722`, `:726`, `:770`, `:778`). |
| Minor: zero-denominator residual explanation | **Resolved** | The text distinguishes absent contributions from signed cancellation (`docs/STUDY_PROTOCOL_v2.3.md:490`). |
| Minor: power-generator test | **Resolved** | The test executes `rs1()` and checks generated values against the specified quantile (`tests/test_sim_v23_analyze.py:1115`, `:1128`). |
| Minor: independent challenge adjacency | **Resolved** | Adjacency is checked using answer identifiers and accounting parts, independently of declared pair identifiers (`tests/test_e2e_v23.py:566`). |
| Additional test limitation: invalid final pilot verdicts | **Resolved** | Model 22 supplies invalid finals; the test requires their inclusion in the judged denominator and zero flags (`tests/test_judges_v23.py:804`, `:841`). |

Of the round-5 points previously marked partly resolved: **crash recovery remains partly resolved** because of F3; **missing outputs** and **repricing** are now resolved by inspection.

The crash windows are now:

- **Before durable reservation:** no call has been sent.
- **Reservation before send:** recovery conservatively charges the reservation and retries; it can overstate spending for an unsent attempt.
- **Send before private record:** recovery charges the bound and retries. Two provider payments remain possible under §12.5, but the first attempt remains accounted for.
- **Recorded final answer/verdict before settlement:** reconciliation settles its recorded cost. Respondent discovery now sees another session’s newly registered run; judge completion reads the shared verdict file under lock (`src/run_judges_v23.py:165`, `:673`). Neither resends that recorded final result.
- **Settlement before separate overrun entry:** the settlement’s flag preserves the stop, including reconciliation and batch collection.
- **Batch collection:** charges precede answer records. Restart recognizes charged and written items separately; final batch settlement prevents a second reservation release (`src/run_models.py:929`, `:953`, `:1027`, `:1043`). I found no payment lost or duplicated by these collection windows.
- **Availability:** the post-settlement window still resends a recorded answer, described below.

I found no reviewed recovery window retaining two final judge verdicts for one call. Unreadable ledger lines stop execution for repair (`src/spend_v23.py:155`).

**Freeze:** yes, the new implementation enforces the two numerical checks specified by condition 3 and §12.4 for artifacts generated by the builders. They can disagree because actual pilot spending, unused pilot reservations and fees differ from the manifest estimate. The text now explicitly requires both checks and records cuts needed by either (`docs/STUDY_PROTOCOL_v2.3.md:1156`). That disagreement is covered.

## 2. New problems and incomplete corrections

**F3 remains incomplete; its recovery state disappears after settlement.**

`availability_check` starts with an empty `found` dictionary. `reconcile` populates it only from reservations still open (`src/run_models.py:420`, `:432`, `:1663`). Therefore:

1. A successful test answer is recorded.
2. Its `availability_call` settlement becomes durable.
3. The process crashes before recording the availability facts.
4. On restart, no reservation is open, so `found` remains empty.
5. The runner sends another paid test call (`src/run_models.py:1698`, `:1707`).

A second crash after reconciliation settles the saved attempt creates the same problem. Both payments are accounted for, but the recorded answer is purchased again, contrary to §12.5 (`docs/STUDY_PROTOCOL_v2.3.md:1033`).

Recover same-day, matching-configuration results from persistent records even when their reservations have already settled. Keep the existing prompt/configuration/date checks.

This author-run offline regression reproduces the missed window using the existing fake provider and scratch-study harness:

```bash
python -I -B -X utf8 - <<'PY'
import sys
sys.path.insert(0, "tests")
import test_runner_offline as T

_, models = T.setup("round7_after_settlement")
K, _ = T.keymap(models)
hosted = [K[22], K[23]]
T.ledger(kind="registration", tag="test")
T.run(["--run", "p", "--block", "1", "--round", "1",
       "--run-cap", "100", "--models", ",".join(hosted)])
T.run(["--run", "close", "--block", "1", "--complete-block",
       "--models", ",".join(hosted)])
T.judge_pilot(hosted)

original = T.R.settle_outside_plan
def settle_then_die(*args, **kwargs):
    original(*args, **kwargs)
    raise T.Crash()

T.R.settle_outside_plan = settle_then_die
start = len(T.Fake.sent)
try:
    T.run(["--run", "a", "--availability-check", "--run-cap", "1"])
except T.Crash:
    pass
finally:
    T.R.settle_outside_plan = original

first = T.Fake.sent[start][0]
start = len(T.Fake.sent)
T.run(["--run", "b", "--availability-check", "--run-cap", "1"])
print("repeat:", sum(m == first for m, _ in T.Fake.sent[start:]))
PY
```

Predicted current final line: `repeat: 1`. Required after correction: `repeat: 0`.

I found no other runtime defect introduced by the corrections.

## 3. Tests

The supplied log reports all eleven files passing (`review_aids/offline_tests_2026-11-12.txt:1`); the cross-reference check reports 536 references and no dangling references (`review_aids/xref_check.txt:3`). I did not execute either.

By inspection, reverting F1, ordinary/reconciled F2, pre-settlement F3, singleton handling, F6, the power quantile or challenge pairing would fail their new assertions. Limits remain:

- **F3:** the new test crashes before settlement only. Its docstring also claims a before-record case that it never exercises (`tests/test_runner_offline.py:1191`, `:1202`).
- **F5:** no test calls `stored_manifest_problem` or exercises holds `--write`. Reverting F5’s persisted-artifact protection would survive the supplied suite (`tests/test_panel_d13_v23.py:158`).
- **Freeze:** the six cases test the manifest gate, including manifest-only cuts. They omit a passing manifest with a ledger requiring additional cuts or refusal; deleting the retained ledger check would evade these cases (`tests/test_runner_offline.py:1957`).
- **Challenge variance:** removing only the zero-contribution-domain correction would survive the new fixture: every prompt still has a contributing answer. Each prompt is also assigned conflicting sources, and valid-pair intervals are not independently checked (`tests/test_sim_v23_analyze.py:1178`, `:1183`, `:1195`).
- **F2:** the assertion named “at or below its reservation stops nothing” examines an overrun ledger and never checks `overrun_open == False` (`tests/test_runner_offline.py:1933`). Batch settlement-to-overrun crashes are not injected.

Exception injection with fsync disabled establishes control-flow behavior, not physical crash durability (`tests/test_runner_offline.py:90`, `:99`).

## 4. Verdict

**Do not register yet, apart from the PI’s decisions.**

- **Critical:** none remaining in the corrections checked.
- **Major — F3:** recover already-settled availability answers and test crashes after settlement and during resumed reconciliation (`src/run_models.py:1663`, `:1698`).
- **Minor — regression coverage:** exercise stored-manifest mismatch rejection, ledger-only freeze failure, batch overrun crashes, an actual non-overrun settlement, and entirely noncontributing challenge prompts with consistent sources (`tests/test_panel_d13_v23.py:158`; `tests/test_runner_offline.py:1933`, `:1957`; `tests/test_sim_v23_analyze.py:1178`).

**Could not check:**

- Execute tests, the diagnostic, mutations or simulations.
- Verify physical durability or live provider billing and behavior.
- Verify future pilot-measured repricing inputs or omitted private study material.
