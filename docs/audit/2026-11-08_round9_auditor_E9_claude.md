**Auditor E9, round 9: check of the D8 fixes**

All work was read-only (`python -I -B`, no network, no model calls). The offline test passes 104/104. `cost_model.py` reproduces all 52 cells of the §11 table and both vectors in `stage_holds.json`. I ran six probes with the test's `FakeProvider` in `E:\claude\_tmp\e9`, which is now empty. All 153 files listed in `SHA256SUMS_COPY.txt` still match, and no `__pycache__` was created.

## Verdict
Every D8 finding was acted on. The code diff is small and matches §11, §13 and §14, and the numbers agree everywhere. The probes show the new closure check counts provider blocks, answers recorded under other run names and the no-zero-retention filter correctly. However, it skips disabled models, and judge stages can still be closed with no check. These two gaps leave the D8-M2 fix incomplete. Each needs a few lines (§13 text and code), and neither is blocking. Another full audit round is not needed: once these fixes are applied, a diff check and a passing offline test are enough. **Freeze after minor fixes.**

## D8 fix status
- **M1:** fixed (`run_models.py:119, 466, 837`; §11 l.846; §13 l.920; `_what` in `stage_holds.json`).
- **M2:** partly fixed (l.388, 843–859; §11 l.847). Two gaps remain (new M1 and M2).
- **m1:** fixed: IDs at l.622–623, request count at l.658–659, line kinds at l.746–758. Residuals are new m1 and m3.
- **m2:** fixed (l.120, 449–450; §11 l.850).
- **m3:** fixed (l.484–488; §11 l.831; §13 l.922).
- **m4:** fixed (§8.3 l.480; §9.2 l.615).
- **m5:** fixed (§11 l.851). A wording residual remains (m6).
- **m6:** (a) fixed (l.48, §11 l.850, §13 l.921); (b) fixed (§8.4 l.559, §11 l.851); (c) fixed (§11 l.848, schedule l.883); (d) fixed (§11 l.852), but a cut stage 1 or 3 is not covered (m2).
- **m7:** fixed: all five missing tests were added, and §13 l.921–922 was updated.
- **Nits:** fixed (`--undeletable` at l.389, 683–693; `unattributed_lines` at l.743–750, 800; "after round 7").
- **GPT-6 Luna figure:** fixed (l.855).

## Issues
### Blocking
None.

### Major
**M1. The closure check covers only enabled models** (`run_models.py:846–848`; §11 l.847).
- *Problem.* In a probe, model B was disabled with 3 of its 6 stage-1 prompts unanswered. `--complete-stage 1` closed the stage with no `--cut` and `unanswered_at_close: null`. When no model is enabled, the runner suggests `--cut`, and the closing line then records no counts at all.
- *Why it matters.* `models.json` keeps every API model `enabled: false` until its pilot, and the documented pilot uses `--models`. Running the main runs the same way is natural, and it silently disables the D8-M2 guard.
- *Fix.* Replace the filter with `resp = [x for x in models_all if providers.is_remote(x)]`. All 12 remote entries are panel respondents; a dropped model is closed with `--cut`, which records its count. Delete the "no API respondent is enabled" branch. In §11, change "an enabled API respondent" to "any API respondent in `config/models.json`". Add a test with a disabled model.

**M2. Judge stages close with no check** (l.829–859; §13 l.920–922).
- *Problem.* `--complete-stage 2` or `3b` only checks for unsettled batches, and §13 does not require `judge.py` to check that a stage is complete.
- *Why it matters.* This is the D8-M2 failure in the protected stages: stage 2 carries T1a, T1b, H1 and instrument selection, and stage 3b carries H2 and H3. Closing a stage cannot be undone.
- *Fix.* Paste into §13: "– it writes a `judge_stage_check` ledger line with per-judge counts of scheduled calls that have no recorded verdict (`invalid` counts as recorded); `--complete-stage` for stages 2 and 3b–7 needs that line with nothing missing, or `--cut REASON`." Code, after l.842:
  ```python
  if n not in ("1", "3") and not args.cut and not any(e.get("kind") == "judge_stage_check"
          and e.get("stage") == n and not e.get("missing") for e in led):
      sys.exit(f"stage {n}: no judge_stage_check line with nothing missing (src/judge.py); or pass --cut REASON")
  ```
  Test 14b then passes `--cut` or writes that line.

### Minor
- **m1. The `model_returned` prefix check (l.751) can discard genuine answers.** The OpenRouter canonical slugs (`claude-sonnet-5.5-20260928`, `gpt-5.6-luna-20260709`) suggest the direct APIs return the alias plus a date, which passes (probe). An ID not prefixed by the alias, such as `claude-sonnet-5.5-…`, discarded the whole chunk in a probe: it was charged at worst case and must be sent again. Nothing verifies the format before the first batch, and the test fixtures carry no `model_returned`. *Fix:* refuse a model's first `--batch` unless its pilot records' `model_returned` start with `m["model"]`, and add a test fixture with a dated ID.
- **m2. What `--cut` may be used for, and how a cut is analysed** (§11 l.847, 852). *Paste:* "`--cut` is used only for prompts that still fail after two re-runs (comply-expected suspected blocks are errors), or for a model dropped under a logged deviation. It is never used for budget in stage 1. A reduced stage 3 closes with `--cut`. If stage 1 or 3 closes with prompts of models 1–3 unanswered, H2 and H3 use the reduced-stage-3 set, counting base prompts with *every framing* answered."
- **m3. An OpenAI batch that failed validation reports 0 requests for good.** The adoption message tells the PI to retry. `--release` is the correct path, since nothing is billed (probe), but §11 says release is only for a submission "that created no batch". *Fix:* add "…or, if the console shows it failed or was cancelled before validation, `--release REF`".
- **m4. §10 does not define the open item created by `--undeletable`.** *Paste:* "An input that cannot be deleted through the API is deleted in the provider console within 7 days. The date is logged, and any upload still undeleted is reported."
- **m5. §13 omits the new batch rules and a judge pilot cap.** *Paste:* "custom IDs unique per submission; adoption only with a matching, non-zero request count; lines with no or an unknown ID, or another model's answer, charged once and never recorded; judge pilots at most 30 items per judge."
- **m6. Wording.**
  - For RQ4, write "the local fallback of the main (H2) instrument", since there are two fallbacks.
  - For β_int, state the primary criterion: "the pooled β_int's 95% CI excludes 0, and the G2-only estimate has the same sign". Under the null, sign agreement alone is a coin flip.
- **m7. Tests.**
  - There is no positive closure test: closing with every prompt answered, including blocks and answers under other run names, and no `--cut`. My probe passed it.
  - There is no check that IDs match `[A-Za-z0-9_-]{1,64}`; the IDs are 27 characters and valid.
  - `ledger_usd` is checked for presence only, not value.
  - The refund on an `--undeletable` release is not checked.

## Number check
| Claim | Source value | Status |
|---|---|---|
| §11 table (13 × 4) | cost model output | OK, 52/52 |
| Holds 74.39 / 14.69; projections 29.09 / 59.70 / 14.69 / 11.00 / 55.86 / 4.64 / 38.48 / 47.75 | cost model and `stage_holds.json` | OK |
| Stages 1–3: about US$53 / 103 | 52.75 / 103.48 | OK |
| 3b adds about US$5.60 / 11; US$58 / 114 in all | 5.58 / 11.00; 58.32 / 114.48 | OK |
| Local instruments: about US$102; API instruments: about US$123, stage 7 cut about US$13 | 101.89; 122.86; 12.86 | OK |
| About US$1.30 if GPT-6 Luna | Luna stage 6 3.87 → total 111.34 | OK |
| Pessimistic: 6.50; 4.60; 1.90; about 4% | 6.52; 4.29 + 0.32; 1.91; 1.91 / 51.25 = 3.7% | OK |
| 104 checks | 104/104 pass | OK |

**Readiness.** Nothing blocks the freeze. Priority order: M1, then M2 (with tests), then m1, then m2–m5 text, then m6–m7, then the [PI] items. After that the draft can be frozen without another audit round.
