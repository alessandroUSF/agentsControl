# Review round 8 of the code of protocol v2.3 (check of the round-7 corrections), by GPT-6.1 Sol

- **Date:** 12 November 2026, 09:10 to 09:16 EST. Codex CLI, model `gpt-6.1-sol`, reasoning effort xhigh, read-only sandbox, connectors off (`--disable apps`), user configuration ignored.
- **Input:** a read-only clean copy of part of the repository (`agentsControl_r19_round8_code`, 149 files) with no answer text, no benchmark prompt file, no label key and no secret, and the diff since the copy of round 7.
- **Prompt:** `docs/audit/2026-11-12_prompt_for_codex_round8_code.md`.
- **Session log audit:** 21 shell commands, all inside the copy; no web action; no read outside the copy.
- **Status:** stored as returned. Its statements are claims to verify, not instructions. Its file:line references point into the review copy; its links to the copy's local path are written as plain references, otherwise unchanged.

---

## 1. F3

**The duplicate-purchase defect is resolved. The complete eligibility check still has a major gap described in §3.**

Conflict: I am commercial-panel model 11, developed by OpenAI. The availability findings concern hosted models 22 and 23; the budget and challenge-analysis test judgments also bear on OpenAI models 3, 9 and 11.

The recovery sequence now works as follows (`src/run_models.py:414`, `:1589`, `:1604`, `:1668`):

| Interruption or restart | Result |
|---|---|
| Before reservation | No paid call has been sent. |
| After reservation, before private record | Reconciliation charges the reservation as nonfinal `interrupted`; the check sends another attempt. Two payments are possible if the first request reached the provider, as §12.5 permits. |
| Between record and ledger settlement | Reconciliation settles the recorded cost; the settled-record scan finds the answer and reuses it. |
| After ledger settlement | The persistent scan finds the answer without needing an open reservation. No repeat purchase. |
| During reconciliation | Before settlement, the reservation remains recoverable. After settlement, restart finds the persistent settlement. A partial, unreadable ledger line stops execution for repair. |
| Completed check repeated that day | Matching final records are reused across run names. |

I found no lost payment or duplicate settlement in these paths. Recorded transient failures remain retryable. A private record without a matching `availability_call` settlement cannot supply fact 3.

The selector rejects different prompt hashes, different dates and different **hashed** configurations (`src/run_models.py:1617`). That last qualification matters: the hash omits part of the pin configuration. There is also a midnight reporting-date edge case.

## 2. The minor points of round 7

The supplied log reports all eleven test files passing (`review_aids/offline_tests_2026-11-12.txt:1`). The following judgments are by inspection, without executing mutations.

- **Stored manifest:** the additions check acceptance and all five stated rejection cases, including changed snapshot bytes with an unchanged repricing-file hash (`tests/test_panel_d13_v23.py:175`). Removing those checks from `stored_manifest_problem` would fail the corresponding assertions. The CLI’s invocation of that function remains verified by inspection.
- **Freeze:** the two new cases distinguish ledger-only cuts and refusal from the manifest gate (`tests/test_runner_offline.py:2001`). Removing the ledger check would fail them.
- **Non-overrun settlement:** the replacement uses a fresh ledger, settles below the reservation, and checks spending, closed reservations and absence of a stop (`tests/test_runner_offline.py:1966`). It now checks its name.
- **Batch overrun:** replay without separate overrun entries meaningfully tests restoration from flags (`tests/test_runner_offline.py:676`). However, the fixture contains both item and aggregate overruns; deleting only the aggregate `batch_settlement` flag can escape this assertion.
- **Challenge variance:** sources are consistent by prompt, p3 contributes nothing, both primary and valid-pair intervals are checked independently, and removing zero-contribution prompts demonstrably changes the reference interval (`tests/test_sim_v23_analyze.py:1178`). Reverting the domain correction would fail.
- **Availability:** the three advertised crash points are now exercised, and the post-settlement and completed-check assertions catch the round-7 defect (`tests/test_runner_offline.py:1234`). A second crash during availability reconciliation is still untested; recovered dollar amounts are not asserted.

The two older availability expectation changes follow §12.5. Fresh scratch studies appropriately preserve the independent run-cap, missing-key, configuration-error and repeated-key checks.

## 3. New problems

**Major — saved identity can survive a changed pin configuration.** The configuration hash excludes `pin` (`src/run_models.py:135`, `:193`). Recovery then trusts the old `identity_match` (`:1705`). Changing the pin’s provider name or recorded precision while retaining its routing tag leaves the hash unchanged. With an updated matching preflight snapshot, the check can reuse the earlier configuration’s answer. It can even print a successful fact alongside different saved serving-provider and current pinned-provider names.

This leaves the “same configuration” requirement of §12.5 incompletely enforced. Bind reuse to the pin’s identity and precision, and validate saved identity against the current pin.

Exact offline diagnostic for the author; **not executed here**:

```bash
python -I -B -X utf8 - <<'PY'
import copy, json, sys
sys.path.insert(0, "src")
import run_models as R
old = next(m for m in json.loads(
    R.CONFIG.read_text(encoding="utf-8"))["models"] if m["n"] == 22)
ts = R.now()
rec = dict(model_key=old["key"], final=True, ts=ts,
           config_sha256=R.config_hash(old),
           prompt_sha256=R.sha256_text(R.AVAILABILITY_PROMPT),
           model_returned=old["model"],
           served_provider=old["pin"]["provider_name"],
           identity_match=True, status="ok")
current = copy.deepcopy(old)
current["pin"].update(provider_name="changed-host",
                      quantization="changed-precision")
got = R.recovered_availability(
    current, {"settled-attempt": rec}, R.local_date(ts))
print("reused:", got is not None)
print("current identity:",
      R.ModelRun(None, current, [], None).identity(rec))
PY
```

Predicted current output: `reused: True`, `current identity: False`. Required: `reused: False`, `current identity: False`.

**Minor — midnight mismatch.** Selection uses the date captured before preflight (`src/run_models.py:1670`), while facts receive a newly computed reporting date (`:1715`). A check crossing midnight can label yesterday’s reused answer as today’s fact. Revalidate the date before publishing facts.

## 4. Verdict

**Do not register yet, apart from the PI’s decisions. No critical point remains; one major point remains.**

Required changes, ranked:

1. **Major:** complete the pin-configuration reuse guard at `src/run_models.py:1617`, with a regression for changed pin identity/precision.
2. **Minor:** enforce agreement between answer date and reporting date at `src/run_models.py:1715`; test midnight rollover.
3. **Minor:** extend `tests/test_runner_offline.py:1234` with a second crash immediately after reconciliation settlement, exact recovered charges, and date/prompt/configuration/unsettled-record exclusion cases.
4. **Minor:** add an aggregate-only batch overrun fixture at `tests/test_runner_offline.py:676`: every item stays within its bound, but unattributed charges exceed the batch reservation. Replay must retain the stop without separate overrun entries.

Run the amended tests with `python -I -B -X utf8 tests/test_runner_offline.py`; expected: zero failures.

**Could not check:**

- Execute tests, the diagnostic or mutations; supplied outputs were inspected.
- Physical crash durability, live provider behavior or billing.
- Pilot-measured inputs, private study material or completion of PI decisions.
