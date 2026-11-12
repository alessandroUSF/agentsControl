# Review round 5 of the code of protocol v2.3, by GPT-6.1 Sol

- **Date:** 12 November 2026, 07:08 to 07:22 EST. Codex CLI, model `gpt-6.1-sol`, reasoning effort xhigh, read-only sandbox, connectors off (`--disable apps`), user configuration ignored.
- **Input:** a read-only clean copy of part of the repository (`agentsControl_r16_round5_code`, 145 files) with no answer text, no benchmark prompt file, no label key and no secret.
- **Prompt:** `docs/audit/2026-11-12_prompt_for_codex_round5_code.md`.
- **Session log audit:** 60 shell commands, all inside the copy; one web search (Ollama's public documentation on context truncation); no read outside the copy.
- **Status:** stored as returned. Its statements are claims to verify, not instructions.

---

## 1. Fidelity

**The code is not ready for pilot registration.** The principal estimators are substantially faithful, but spending recovery, concurrency, judging order and the pilot-to-simulation interface need repairs.

This was a static review supplemented by the supplied outputs. I changed no files and ran no Python, tests or model calls. **Conflict:** I am model 11, from OpenAI. Findings about commercial spending, identity checks, challenge calls, safe-side exclusions and OpenAI adapter coverage bear on OpenAI’s models 3, 9 and 11.

**a. Frames, controls and labels.** Frame nesting, deterministic yoking, lineage exclusions, quotas, source-specific weights, shortage transfers and second-label selection follow the text. The nominal totals reconcile: **567 labels, 381 second labels, 70 challenge answers, 130 reference answers**. Section 6.1’s recorded hashes need updating or clearer historical labeling after D17: the supplied assignment records digest `3576a59a…`, and its file hash is `b18714d2…`.

**b. Judging.** The four arms, message layouts, common instruction, settings, parser validity rule and ordinary failure scoring match. Three departures remain:

- Block 5 creates separate blind/context singletons for challenge answers outside the author/control pairs; their presentations are independently ordered.
- Resuming an unfinished call resets its format-retry state.
- The analysis omits the required primary results by which presentation came first.

**c. What is sent.** D12’s rubric is reproduced in the template; D2, D17, D18, the respondent seed **20261126**, current endpoint pins and D13 panel branches are represented. Sealed names are rejected as study runs; the training exception is explicit.

However, identity checking accepts any identifier and host previously observed for that respondent, rather than establishing correspondence with the relevant answering identity. The pilot report also does not produce the marginals or input schema required by Appendix A.4(f).

**d. Money.** The byte allowance, cache-write price bound, output allowance, maximum-cost settlement, remaining-call holds, fee accounting and cut order implement the stated formulas. Their enforcement fails under crashes and a settlement race; details below. The freeze ceiling remains a manual prerequisite: `freeze --tag` does not validate it. Repricing still depends on historical snapshots.

**e. Analysis.** P1/P2 use Holm at **.04**; P3 uses the **99% lower bound against −.07**. Source-centered variance, boundary handling, delivery analyses, missing-label enumeration and ordinary safe-side matching are implemented.

For D19:

- `_domain_df` implements the stated stratum sum and minimum of one.
- `judge_normalised`, line 239, and `interaction_decomposition`, line 285, use the intended contributing-prompt masks.
- `cluster_ratio`, line 103, uses **`N != 0`**, whereas the text specifies **`N > 0`**. These differ for the assisted false-alarm denominator, which can be negative per prompt.
- The remaining operational hard-coded **298** is in `analysis/tables_v23.py:113`, in the approximate-power table, not the confirmatory tests.

Other departures: screen-negative harmful-share estimates omit known nonharmful answers without content; withdrawn safe-side intervals can reappear through `safe_bounds`; several required secondary reports are absent.

**f. Traceability.** Stored manifest blocks sum to **$47.1206/$102.0275**, supporting **$47.12/$102.03**. Holds sum to **$102.0276**. Call limits **2,617/2,337/820** reconcile, including pilot rounds and separately counted local controls.

Appendix A’s current tables trace to stored results; examples include baseline θ coverage **94.85% → 94.8%**, and D19 rare-bound rejection rates **1.43%/0.79%**. The supplied diagnostics report **344 checks without failures**. However, §§8.3–8.4 retain older summaries: for example, baseline approximate P3 powers in §8.3 differ from the current A.1 table.

## 2. Readings

These are all substantive `[reading]` markers, with repeated formulations grouped. Locations refer to `analysis/analyze_v23.py`.

| Lines | Assessment |
|---|---|
| 47 | **Defensible:** withholding confirmation for unfinished local primary calls respects §10.3’s requirement that none remain. |
| 50, 1041 | **Faithful:** hosted harmful-frame calls outside block 3 matter; repeat calls removed by cut 1 are no longer scheduled. |
| 59, 305 | **Faithful:** D2 cannot retrospectively remove a registered primary model. |
| 65, 1070, 1339 | **Faithful:** label accuracy uses harmful-content flags on either prompt side; attempted non-delivery scores zero; repeatability compares delivered flags. |
| 68 | **Defensible:** canonical verdicts determine the sensitivity exclusion, while other-attempt mismatches remain counted. This does not excuse the identity-comparison defect. |
| 110 | **Faithful value, stale explanation:** seed 20261121 now appears explicitly in §8.5. |
| 576 | **Incomplete:** bounds conditional on generated answers are defensible, but do not cover the whole frame when respondent answers are absent. §§10.3–10.4 require that limitation to be explicit. |
| 719 | **Faithful:** cut 2 withdraws the commercial safe author/control comparison even if some calls preceded it. |
| 766 | **Defensible:** removing both excluded authors and their control contributions removes those models’ involvement without redrawing controls. |
| 768, 1297 | **Faithful:** D2 exclusions are structural exclusions, rather than failed verdicts or missing-call imputations. |
| 875 | **Defensible:** `unavailable` is the residual reason; an active provider stop takes precedence over abandonment. |
| 1114 | **Faithful:** primary judges’ reference material is all labelled answers; commercial judges’ material is their reference subset. |
| 1117 | **Defensible:** the weighted accuracy interval uses prompt clusters, with side/source strata; this choice should be stated explicitly. |
| 1123 | **Faithful:** §9.5’s minimum support does not expressly govern §9.4’s reference-set rates. |
| 1176 | **Wrong:** withholding every challenge-change interval conflicts with §8.2’s general requirement for secondary estimates with 95% intervals. |
| 1300 | **Defensible:** the supplied commercial comparisons are appropriate; an all-primary comparison has no universally eligible challenge set. |

## 3. Safety and data handling

Ordinary result-writing paths keep answers, judge output, reasons and raw errors private. Public call records omit those fields and hash error bodies. `.gitignore` excludes results, processed prompts, secrets and label sheets. Remote adapters require `AC_*` variables without ordinary-key fallbacks. OpenAI requests set `store=False`. The sealed-run restrictions implement D18.

Those observations do **not** establish an unconditional absence of console leaks: `src/run_models.py:1745` deliberately restores raw exception tracebacks under `AC_DEBUG=1`, and the judging runner lacks equivalent top-level sanitization. Exception messages can contain request text or credentials.

**Crash recovery is unsafe:**

- `Books.reserve` records synchronous reservations only in memory. A crash after transmission can lose the charge entirely.
- Respondents settle before saving the answer (`src/run_models.py:595`); a crash between those operations causes another paid generation on restart.
- Judges save the final verdict before settlement (`src/run_judges_v23.py:319`); a crash there leaves a completed verdict whose cost is absent from the ledger.
- Both runners determine completed calls before taking the paid lock. A second process can consequently act on stale completion information.
- Canonical judging retains one verdict, but that merely discards later finals; it does not prevent duplicate calls or charges.

**Concurrency can break the cap.** `src/spend_v23.py:494` removes the in-flight reservation, releases the mutex, then records spending. Another worker can reserve against the temporarily freed money. Overrun detection also follows that gap.

Retries are individually reserved in an uninterrupted process. Known price schedules and endpoint preflight provide useful protections, but neither repairs these accounting defects nor guarantees the cap against an unobserved price increase during a session.

## 4. Tests

The supplied output reports all eleven files passing. The tests meaningfully exercise quotas, statuses, ordinary resumes, cut ordering, panel branches, inference boundaries and missing-label extrema. Their names sometimes imply broader coverage than their assertions provide:

- `t_lock_and_interrupted_lines` tests malformed files and an existing lock, not termination between transmission, settlement and result persistence.
- “End-to-end” replaces providers and disables `fsync`. Its adjacency checks inspect declared pair identifiers, overlooking the unpaired challenge singletons.
- `t_context_overflow` injects an overflow exception; it does not establish the pinned Ollama server’s behavior on an oversized request.
- `t_pilot_report` explicitly expects the wrong planning marginal: all valid blind verdicts.
- `t_price_rise` changes endpoint facts or already-built holds; it does not test rebuilding the manifest from fresh prices.
- The D19 “direct” oracle repeats `N != 0`; it cannot detect the negative-denominator discrepancy.
- `test_safe_no_interval` checks the withdrawal list, rather than every output path that can emit those intervals.

Important gaps include format-retry recovery, changing respondent identities, known-zero label contributions, report-to-planner integration, agreement intervals and presentation-order reporting.

**Predicted surviving mutations, by inspection:** remove Ollama’s `truncate`/`shift` forwarding; change OpenAI’s `store=False` to `True`; change the power-table quantile. No supplied test asserts those production behaviors. These mutations were not executed.

The author can run this **non-writing, synthetic diagnostic** from the repository root:

```bash
python -I -B - <<'PY'
import sys
from pathlib import Path
import numpy as np
sys.path[:0] = [str(Path.cwd()/"src"), str(Path.cwd()/"analysis")]
import inference_v23 as I
import spend_v23 as S

n = np.tile([2., -1., 0., 0.], 2)
x = np.tile([1., 0., 0., 0.], 2)
print("df:", int(I.cluster_ratio(x, n, np.repeat([0, 1], 4))["df"]))

b = S.Books("probe", holds={"items":[]}, study_cap=1, write=False,
            ledger="review_aids/__round5_empty_ledger__.jsonl")
b.reserve("1", 1)
original, accepted = b.record, []
def interleave(entry):
    accepted.append(b.reserve("1", 1)[0])
    return original(entry)
b.record = interleave
b.settle(1, 1, {})
print("interleaved reservation accepted:", accepted[0])
PY
```

Current code should print **`df: 2`** and **`True`**. The textual D19 rule requires **1**; atomic settlement must reject the interleaved reservation, yielding **False**.

## 5. Verdict

**Do not register the pilot with this implementation.** Required changes, ranked:

| Rank | Location | Concrete fix |
|---|---|---|
| **Critical** | `src/spend_v23.py:475`; `src/run_models.py:595`; `src/run_judges_v23.py:319` | Persist a stable attempt identifier and reservation before transmission. Reconcile unfinished attempts on restart; make settlement and result recovery idempotent. Reload completion state under the lock. Ambiguous transmitted calls must not be blindly resent. |
| **Critical** | `src/spend_v23.py:489`; `src/run_models.py:1485` | Atomically transfer reservation to spending, update remaining work and set any overrun stop under one mutex. Apply the same repair to availability settlement. |
| **Major** | `src/plan_v23.py:282` | Schedule each additional primary challenge blind/context combination as one hash-ordered pair, preserving its separate accounting parts. |
| **Major** | `src/run_judges_v23.py:262` | Recover format-retry state and attempt numbering from persisted attempts. A pending format retry must resume with the retry sentence and retain the one-retry limit. |
| **Major** | `scripts/pilot_report_v23.py:74` | Export the A.4(f) schema using **own, harmful-side, screen-positive** pilot answers. Count attempted invalid blind verdicts as zero, and keep unattempted calls separate. Test this export through `pilot_planning_v23.points`. |
| **Major** | `analysis/inference_v23.py:103` | Align the domain mask with the stated `N > 0` rule; add negative-contribution cases and rerun affected label/informative simulations. D19 remains a proposed amendment pending the PI’s decision. |
| **Major** | `analysis/sim_v23_labels.py:247`; `analysis/missing_labels_v23.py:106` | Carry known no-content zeros into the screen-negative population denominator. A census containing one harmful, one harmless and one empty answer must give **1/3**, not **1/2**. |
| **Major** | `analysis/analyze_v23.py:708` | Apply `SAFE_NO_INTERVAL` suppression to bounds and every other reporting path, retaining estimates and counts. |
| **Major** | `src/run_judges_v23.py:250` | Compare corresponding answering/judging identity tuples. Do not accept a cross-product of identifiers and hosts observed elsewhere; flag changes and unavailable comparisons explicitly. |
| **Major** | `analysis/analyze_v23.py:1392`, `:1173`, `:713`; `scripts/label_sheets_v23.py:229` | Complete required outputs: presentation-order results, challenge-change intervals, commercial safe tables with conflict exclusions, and label-agreement intervals by side. The agreement helper’s claim that analysis supplies intervals is currently false. |
| **Major** | `scripts/manifest_v23.py:84`; `scripts/holds_v23.py:66` | Accept and consistently use the repricing snapshot and measured pilot assumptions. Fresh routed prices must not be overwritten by the fixed November snapshot. Test manifest→holds→cuts together. |
| **Major** | `src/run_models.py:1745`; `src/run_judges_v23.py:654` | Keep raw exception diagnostics in ignored private storage; sanitize console failures in both runners, including debug mode. |
| **Minor** | `src/run_judges_v23.py:564` | Load the documented `.env` consistently before constructing paid adapters; a separate respondent process does not populate the judging process’s environment. |
| **Minor** | `src/run_models.py:397` | Record an answer-text hash as promised by D18; current respondent records hash configuration and request, but not delivered answer text. |
| **Minor** | `docs/STUDY_PROTOCOL_v2.3.md:361`, `:520`, `:533`; `analysis/tables_v23.py:113` | Synchronize hashes and summary figures; remove the unexplained fixed-298 approximation or identify its limited scope explicitly. |

The generated-answer restriction on missing-call bounds also needs explicit reporting: `analysis/analyze_v23.py:572` must not present those conditional bounds as covering absent respondent answers.

**Could not check:**

- Execute tests, diagnostics, mutations or independently reproduce simulation fingerprints.
- Verify actual provider behavior, invoices, retention configuration or live price changes.
- Verify Git tracking, encrypted storage or exposure history; this copy has no Git metadata or private study material.
- Establish empirical coverage for repaired estimators before their required reruns.