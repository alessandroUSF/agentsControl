# Review round 6 of the code of protocol v2.3 (check of the round-5 corrections), by GPT-6.1 Sol

- **Date:** 12 November 2026, 08:09 to 08:16 EST. Codex CLI, model `gpt-6.1-sol`, reasoning effort xhigh, read-only sandbox, connectors off (`--disable apps`), user configuration ignored.
- **Input:** a read-only clean copy of part of the repository (`agentsControl_r17_round6_code`, 145 files) with no answer text, no benchmark prompt file, no label key and no secret, and the diff since the copy of round 5.
- **Prompt:** `docs/audit/2026-11-12_prompt_for_codex_round6_code.md`.
- **Session log audit:** 25 shell commands, all inside the copy; no web action; no read outside the copy.
- **Status:** stored as returned. Its statements are claims to verify, not instructions.

---

## 1. Each point of round 5

**The code is still not ready for pilot registration.** Most corrections work, but spending recovery remains incomplete and the new challenge intervals introduce an analysis failure.

This was a read-only static review using the supplied outputs. **Conflict:** I am commercial-panel model 11, developed by OpenAI. Spending, identity, challenge reporting, commercial exclusions and adapter tests affect OpenAI’s models 3, 9 and 11.

The identifiers below follow the order of round 5’s verdict table.

| Point | Status | Evidence and remaining issue |
|---|---|---|
| Critical 1: crash recovery | **Partly resolved** | Durable reservations, attempt identifiers and record-first settlement exist (`src/spend_v23.py:567`; `src/run_models.py:624`; `src/run_judges_v23.py:377`). Different-session completion, availability resumption and overrun recovery still fail; see §2. |
| Critical 2: settlement race | **Resolved for threads** | Settlement, final-call counts and the overrun marker remain under one mutex (`src/spend_v23.py:595`). Availability uses the same method (`src/run_models.py:1517`). The separate durability issue is described below. |
| Major 1: challenge pairs | **Resolved** | `_challenge_pairs` creates one hash-ordered pair and retains `label_blind`/arm L and `challenge_context`/arm X (`src/plan_v23.py:295`). Both halves share their sequence and stage (`:378`, `:386`). |
| Major 2: format-retry recovery | **Resolved** | Persisted attempts recover numbering and the retry owed; a resumed malformed retry becomes final (`src/run_judges_v23.py:121`, `:320`, `:330`). |
| Major 3: pilot planning input | **Resolved** | Own, harmful-side, screen-positive answers only; final invalid verdicts contribute zero and unfinished calls are counted separately (`scripts/pilot_report_v23.py:95`). |
| Major 4: domain degrees of freedom | **Resolved as code/text alignment** | Both now specify `N_p ≠ 0` (`analysis/inference_v23.py:105`; `docs/STUDY_PROTOCOL_v2.3.md:490`). D19 remains awaiting the PI (`docs/PI_DECISIONS.md:310`). |
| Major 5: known no-content zeros | **Resolved** | `Z` carries unsampled known zeros into the denominator without inflating labelled support (`analysis/missing_labels_v23.py:130`; `analysis/sim_v23_labels.py:339`). |
| Major 6: withdrawn safe intervals | **Resolved** | The shared suppression also applies inside `safe_bounds` (`analysis/analyze_v23.py:723`, `:751`). |
| Major 7: identity correspondence | **Resolved against the amended text** | Returned identifier/host tuples replace the cross-product; unavailable comparisons are counted (`src/run_judges_v23.py:303`, `:690`; protocol `:897`). |
| Major 8: missing outputs | **Partly resolved** | Agreement intervals and commercial safe exclusions are implemented (`scripts/label_sheets_v23.py:250`; `analysis/analyze_v23.py:788`). Challenge intervals can crash; presentation-order reporting still omits primary quantities. |
| Major 9: repricing | **Partly resolved** | Fresh prices and scenario assumptions drive both builders (`scripts/manifest_v23.py:127`; `scripts/holds_v23.py:67`). Their persisted consistency check is incomplete. |
| Major 10: console exceptions | **Resolved for the reported paths** | Both runners sanitize unexpected exceptions; debug tracebacks go privately (`src/spend_v23.py:112`; `src/run_models.py:1769`; `src/run_judges_v23.py:607`). |
| Minor 1: judging `.env` | **Resolved** | Shared loader runs before judging setup (`src/run_judges_v23.py:603`). |
| Minor 2: answer hash | **Resolved** | Private and public respondent records receive `text_sha256` (`src/run_models.py:397`). |
| Minor 3: hashes, summaries, fixed 298 | **Resolved** | Updated protocol hashes and summaries (`docs/STUDY_PROTOCOL_v2.3.md:361`, `:523`, `:537`); 298 is explicitly limited to approximate power (`analysis/tables_v23.py:24`, `:113`). |
| Scope note: missing-call bounds | **Resolved** | Conditional scope and absent-answer count accompany the bounds (`analysis/analyze_v23.py:572`, `:597`). |

The signed-denominator explanation supports counting negative contributions. It does **not** establish the protocol’s additional statement that `N_p = 0` implies `e_p = 0`: cancellation can leave `X_p`, hence the residual, nonzero. This is an explanatory correction, not a decision on D19. Since the estimator code did not change here, the stated reason for retaining the existing simulation results holds.

For the requested crash windows:

- **Before the reservation line:** no provider call has occurred; no payment is lost.
- **Reservation durable, before send:** recovery conservatively charges the bound and retries. This can overstate spending for an unsent attempt.
- **Send before private record:** recovery charges the bound and resends under amended §12.5. Two provider payments remain possible, but neither disappears from accounting; only the later recorded result survives.
- **Private record before settlement:** saved final judge results prevent resending. Respondent protection has the different-session exception below. Availability always sends again.
- **Thread interleavings:** competing reservations now see either the outstanding reservation or settled spending. There is no temporarily freed-money window.

I found no paid-judge recovery path that retains two final verdicts after a valid final record. Torn ledger lines stop execution for repair (`src/spend_v23.py:149`).

## 2. New problems and incomplete corrections

**F1 — Respondent completion is still stale across different session names.** `Session` captures `sess.runs` before locking (`src/run_models.py:464`). The correction rereads files from that cached list (`:1260`), without refreshing session discovery. If another process finishes under a newly registered run name before this process acquires the lock, its recorded answer remains invisible and is purchased again. The new test writes into the resuming process’s own `e1` file (`tests/test_runner_offline.py:1755`), missing this case.

**F2 — An overrun stop can disappear after a crash.** The settlement line becomes durable before the separate overrun line (`src/spend_v23.py:596`, `:604`). A crash between them leaves no open reservation. Replay recognizes only an explicit `overrun` entry (`:398`), so further calls become possible despite §12.5’s stop rule. The same gap exists during reconciliation (`:450`).

**F3 — Availability recovery resends recorded answers.** Reconciliation correctly settles the saved attempt (`src/run_models.py:1630`), but the subsequent loop unconditionally calls `availability_call` (`:1663`). A crash after its durable answer record causes another paid check on resumption, contrary to the new “call is then done” rule.

**F4 — Challenge intervals can abort the entire analysis.** `change` constructs strata from contributing prompts only (`analysis/analyze_v23.py:1253`). A permitted shortage—or the valid-pairs subset—can leave one prompt in a source. `_stratified_var` then raises `ValueError` (`analysis/inference_v23.py:58`). Previously this report returned its estimate.

**F5 — Repricing provenance does not protect the stored manifest.** Holds writing compares only the outer repricing-file hash (`scripts/holds_v23.py:168`). If a referenced snapshot changes between manifest and holds generation, that hash stays unchanged. Although snapshot hashes are recorded (`scripts/manifest_v23.py:159`), they are not compared. The holds check rebuilds a fresh manifest rather than checking the stored one (`scripts/holds_v23.py:131`), so inconsistent artifacts pass.

**F6 — Presentation-order output remains narrower than §11.4.** The protocol promises the primary quantities (`docs/STUDY_PROTOCOL_v2.3.md:904`). The helper explicitly omits ι_S and β_S (`analysis/analyze_v23.py:646`). Its docstring does not amend that requirement.

**F7 — The new freeze gate checks a different quantity from the manifest condition.** It checks committed spending plus unfinished holds (`src/spend_v23.py:725`), without reading the repriced manifest. Sections 12.4 and 14.4 still require the pessimistic manifest itself to meet the ceiling (`docs/STUDY_PROTOCOL_v2.3.md:1003`, `:1156`). Completed pilot spending and its repriced estimate can differ.

The challenge pairing itself preserves the former calls and accounting parts: excluding challenge rows from ordinary `label_blind` and restoring their blind halves leaves counts and holds unchanged. Agreement bootstrapping follows the newly explicit §9.3 method.

## 3. Tests

The supplied log reports all eleven files passing (`review_aids/offline_tests_2026-11-12.txt:1`); the cross-reference check reports no dangling references.

By inspection, undoing the atomic settlement, persisted retry, tuple comparison, known-zero denominator, interval suppression or agreement-output corrections would fail their new assertions. The repricing tests meaningfully exercise price scaling, endpoint replacement, assumptions and cut totals.

Important limits remain:

- Crash tests inject exceptions with durability disabled; they do not establish filesystem persistence. They omit availability crashes and the settlement-to-overrun crash.
- The respondent concurrency case misses newly discovered run names.
- End-to-end adjacency checks inspect only declared pairs (`tests/test_e2e_v23.py:548`). Reverting challenge calls to singletons would evade them.
- `t_pilot_report` checks the export through the planner, but its checked primary judges do not exercise invalid-final scoring (`tests/test_judges_v23.py:832`).
- Challenge interval tests use adequately populated sources and repeat the production interval construction.
- **The power-quantile mutation still survives.** The test reads stored Markdown and checks `APPROX_DF`; it never executes `rs1()` (`tests/test_sim_v23_analyze.py:1114`). Changing the generator’s quantile alone would pass.
- `t_request_options` does now assert the production request bodies/parameters. This specifically covers OpenAI’s `store=False`.

For the author, this exact non-writing diagnostic exercises F2 and F4:

```bash
python -I -B - <<'PY'
import sys
sys.path[:0] = ["src", "analysis"]
import spend_v23 as S
import analyze_v23 as A

S.read_ledger = lambda *args: [
    dict(kind="reserve", attempt_id="x", reserved_usd=1),
    dict(kind="call", attempt_id="x", reserved_usd=1, spent_usd=2)]
b = S.Books("probe", holds={"items":[]}, study_cap=10, write=False)
print("overrun:", b.overrun_open)

r = dict(answer_id="a", prompt_id="p", source="s")
try:
    A.change([r], {("a","blind"):(0,"valid"),
                   ("a","context"):(1,"valid")})
    print("challenge returned")
except ValueError as e:
    print("ValueError:", str(e))
PY
```

Predicted current output: `overrun: False`, followed by `ValueError: a stratum needs at least two prompts`.

## 4. Verdict

**Do not register this implementation yet, apart from the PI’s decisions.** Required changes:

| Rank | Required fix |
|---|---|
| **Critical — F1** | Refresh run discovery and completion records under the paid lock, including block closure (`src/run_models.py:1260`, `:1362`). Test another completed session with a different run name. |
| **Critical — F2** | Make overrun status recoverable from the durable settlement itself, respecting later resolution records (`src/spend_v23.py:377`, `:596`). Inject termination between the two ledger writes. |
| **Major — F3** | Reuse the recovered final availability result for the resumed check (`src/run_models.py:1663`), retaining its configuration/date evidence. |
| **Major — F4** | Handle insufficient source-cluster support explicitly without aborting analysis; retain estimates/counts and mark the interval unavailable where necessary (`analysis/analyze_v23.py:1261`). |
| **Major — F5/F7** | Verify snapshot fingerprints and generated content against the stored manifest before writing holds; enforce the manifest ceiling promised by the protocol at freeze (`scripts/holds_v23.py:168`; `src/spend_v23.py:723`). |
| **Major — F6** | Complete the promised primary-quantity output, or explicitly reconcile §11.4 with its implemented scope (`analysis/analyze_v23.py:646`). |
| **Minor** | Qualify the zero-denominator residual explanation (`docs/STUDY_PROTOCOL_v2.3.md:490`); test freshly generated power-table output (`tests/test_sim_v23_analyze.py:1114`); assert challenge pair membership independently of declared pair identifiers. |

Could not check:

- Execute diagnostics, tests, mutations or simulation reproductions.
- Verify live provider behavior, billing, retention or actual crash durability.
- Inspect omitted private study material or Git history.
