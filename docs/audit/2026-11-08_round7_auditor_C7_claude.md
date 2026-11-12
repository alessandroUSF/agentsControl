**Auditor C7, round 7: report on the round-6 fixes, budget and runner code**

Everything was read-only. The offline test passes 71/71, and `cost_model.py` reproduces `stage_holds.json` and the Section 11 table to the cent. I ran seven probes with the test's fake provider and checked the real SDK attribute paths offline (anthropic 0.97.0, openai 2.41.0; the real `NotFoundError` classes carry status 404). `SHA256SUMS_COPY.txt` still verifies, and `E:\claude\_tmp\c7` is now empty.

## Verdict
Every A6 paste and every B6 code fix is in place, and they work: strict ledger, durable reservations, charge before record, idempotent deletes, adopt and release, and the 48-hour block. I found no blocking issue, but two major ones remain in the new budget logic. Both are small:
- **Start rule checked too early.** For stages 1 and 2 the rule runs at the pilot, so the re-made, pilot-based projections are never tested.
- **Holds assume a stage order nobody enforces.** The holds are a fixed table that assumes stages 1→2→3→… run in strict order, and neither the code nor the protocol enforces that order.

Both need code plus a test in the freeze commit, because Section 13 freezes the runner with the protocol. **Freeze after minor fixes.**

## Round-6 fix status
**A6**
- **1 (own-item key):** fixed (§7.2 l.361).
- **2 (design-effect H1 bound):** fixed (§9.5 l.712). `korn_graubard(x/n, n_eff, 0.90)` gives the one-sided 95% limit.
- **3 (two-phase frontier re-labels):** fixed (§9.4 l.692–696). Residual: minor m2.
- **4 (call lists per wave):** fixed (§8.3 l.487). It conflicts with §11 l.835 (minor m1).
- **5 (Plan A measures):** fixed (§7.3 l.409). Cicchetti & Feinstein (1990) is missing from the References.
- **6 (T4 edge cases):** fixed (§8.3 l.506; §9.3 l.660). The bound matches `t4_test`.
- **7 (anchor seeds):** fixed (§8.3 l.480). No seed collides with another.
- **8 (judge-pilot prompts):** fixed (§8.3 l.528).
- **9 (nits):** all fixed: "Phase" (l.418, 424, 875–879, 1034), l.871, l.979/989, l.641, the fold seed (l.561, 900), and what is not reported when stage 4 does not run (l.484, 696, 850).

**B6**
- **M1 (protected total and start rule):** numbers fixed (§11 l.800–850; `cost_model.py:136–145, 214–236`). The rule is coded (`run_models.py:443–451`), but checked at the pilot (new M2).
- **M2 (synchronous re-send):** fixed (`run_models.py:818–828`). The docstring at l.11 still shows a stage-3 OpenRouter command that runs nothing (models 1–3 are all direct).
- **M3 (unreadable ledger lines):** fixed (`run_models.py:172–214, 590–594`).
- **M4 (non-idempotent deletion):** fixed (`providers.py:238–244, 302–320, 362–378`).
- **m1 (collect bookkeeping):** fixed (`run_models.py:684–735`). Probe: a crash between the settlement line and the "settled" marker leaves a second collect refused, the books intact, and purge working.
- **m2 (stage-3 order):** fixed for batch (`run_models.py:576–579, 829–831`).
- **m3 (`--adopt` of a linked ID):** fixed (`run_models.py:616`). There is still no check of request count or model (minor m5).
- **m4 (stage validation, study-wide skip set):** fixed (`run_models.py:430, 484–490`). Residual: minor m5.
- **m5 (48-hour block):** fixed (`run_models.py:553–555, 621, 759–766`).
- **m6 (error bodies):** fixed for stop messages (`run_models.py:462–469`). Residual: l.740 (minor m5).
- **m7 (OpenAI cache writes):** partly fixed by design. The projections price writes; the ledger cannot, and the pilot invoice check is stated (§11 l.822).
- **m8 (judge requirements):** fixed (§13 l.910–916). Missing: stage order, "3b never reduced", and pilots not counting as a first run.
- **Test gaps:** mostly closed. What is still missing is listed under major M3.

## Issues
**Blocking:** none.

### Major
**M1. The holds are a fixed table and depend on a stage order that nothing enforces** (`stage_holds.json`; `run_models.py:427–456`; §11 l.843).
- **The problem.** §11 defines the holds as the projections "of the stages among 1–3 not yet complete". The code reads fixed values (1: 74.39; 2: 14.69; 3 and 4–7: 0) and has no "complete" state. Any stage can be run at any time.
- **Probe:** `--stage 3` is accepted after stage 1 with no stage-2 activity, a hold of US$0.00 and a run cap of US$80.91, which leaves stage 2's US$59.70 unprotected.
- **Consequences:**
  - (a) **Stage 2 after an early stage 3.** Stage 2's start rule gives 43.78 + 14.69 + 59.70 = 118.17 > 110, even though 103.48 would fit. A protected stage is blocked.
  - (b) **Judge pilot during stage 1.** The schedule's 12–15 Nov row allows this. The pessimistic judge pilot costs US$7.17, more than the US$6.52 slack. Hold(1) still counts all of stage 2, so stage 1 stalls about US$0.65 short.
  - (c) **Stage 4 before stage 3, expected case.** Its start rule passes (44.56 + 0 + 55.86 = 100.42), and stage 3 then has no protection.
- **Fix, protocol paste (§11):** "Stages run in the spending order. A stage's first run, pilots included, requires a `stage_complete` ledger line for every earlier stage among 1–3. Stages 3b–7 also require stage 3 complete. The PI writes these lines with `--complete-stage N` after checking that the stage's calls are done or logged as cut."
- **Fix, code** (`main`, before the start rule; the judge code does the same):
  ```python
  done_st = {e["stage"] for e in read_jsonl(LEDGER, strict=True) if e.get("kind") == "stage_complete"}
  order = ["1","2","3","3b","4","5","6","7"]
  open_ = [s for s in ("1","2","3") if order.index(s) < order.index(args.stage) and s not in done_st]
  if open_: sys.exit(f"stage {args.stage} needs stage(s) {open_} complete first (Section 11)")
  if args.stage in done_st: sys.exit(f"stage {args.stage} is closed")
  ```

**M2. The start rule is checked at the pilot, so the re-made projections are never tested** (`run_models.py:444–446`).
- **The problem.** `first` is any earlier `stage_hold` line for the stage. The documented respondent pilot (`--pilot 20 --stage 1`, l.6) is stage 1's first run, and the judge pilot will be stage 2's.
- **Probe:** after a pilot I raised projection 1 to 45 (74.39 + 45 > 110). The main `--batch --stage 1` run started with `first_run: false`.
- **Why it matters.** §11 re-makes projections from pilot tokens precisely so that an unaffordable stage does not start and then stall midway. As coded, that check never happens for stages 1 and 2. An accidental early run (for example the dead l.11 command) also uses up stage 3's check.
- **Fix, code:** `first = not any(... and not e.get("pilot"))`, apply the rule only when `not args.pilot`, and add `"pilot": bool(args.pilot), "sync_override": bool(args.sync)` to the `stage_hold` line.
- **Fix, paste:** "The start rule is checked at a stage's first non-pilot run, against projections re-made from that stage's pilot."

**M3. Gaps in the 71 checks that matter before the first paid call.** None of these is tested:
- M1 and M2: stages out of order, overlapping stages, the first run being a pilot;
- OpenAI `batch_results` on output and error files. Probe: an error line without `custom_id` raises `KeyError` at `providers.py:350`, so the collect can never settle;
- `--release` when `delete_upload` fails with a non-404 error;
- printed batch errors;
- adoption with a mismatched request count;
- a smoke test that the real clients build offline with dummy AC_ keys (I ran one: every attribute path exists);
- two-process lock contention.

Add each case.

### Minor
- **m1 (§11 l.835 against §8.3 l.487; §9.2 l.613).** The anchors are judged only in the G2 wave, but θ_on pools G1 pairs (Phase 1) with G2 pairs (Phase 2). So β_int compares effects measured in different waves, and "same time window as the paired calls" is no longer true.
  - Paste in l.835: "(judged in the G2 wave, Section 8.3)".
  - Add to §9.2: "β_int is also reported on the G2 wave alone (G2 on-policy pairs against the anchors)."
- **m2 (§9.4 l.694–695).** Items drawn for one endpoint are re-labelled "in every field". If they also enter M̂_s for the other endpoint, the within-stratum sample is no longer random. Paste: "M̂_s for an endpoint uses only the items drawn for that endpoint's stratum s."
- **m3 (§11 l.845–846; §9.5 l.702; §9.6).** When stage 3b falls back, the protocol does not say which instrument H1 is about, and RQ4's instrument is unclear when stage 6 does not run. Paste: "If stage 3b falls back, H1 is reported for both the selected and the deployed local instrument (the confirmatory verdict stays with the selected one); H3 is corrected with the deployed instrument's out-of-fold Se and Sp; RQ4's corpus labels use the same local instrument if stage 6 does not run."
- **m4 (`--reduce`, l.447).** It is allowed for stage 1, but §11 defines no stage-1 or stage-2 reduction, and these stages carry T1a, T1b and H1.
  - Paste: "Stages 1 and 2 are never run reduced; if either does not fit, the study pauses for a dated amendment."
  - Code: refuse `--reduce` unless the stage is 3.
- **m5 (runner residuals):**
  - *Pilot answers wrongly skipped.* Pilot records in the same run's file count as done (l.489). Probe: a main run under the pilot's run name sent 4 of 6 prompts. Filter `previous` by `not r.get("pilot")`.
  - *`--adopt` checks nothing.* It accepts a batch whose request count differs (probe). Compare `request_counts.total` with `len(items)`.
  - *Batch errors printed.* l.740 prints up to 200 characters of provider batch errors to stdout, which the guard writes to `results/logs`. Print the hash only.
  - *OpenAI error lines.* Use `row.get("custom_id")` at `providers.py:347–350`.
  - *Docstring.* Delete l.11.
  - *Reduced stage 3.* Cuts can differ by model. Analyse H2 and H3 on prompts answered by every model compared.
- **m6 (budget nits):**
  - The 3b ceiling leaves out version-1 pipelines. The dearest eligible H3 pipeline (DeepSeek + Venice, Hy3 as arbiter at ≤50% disagreement) costs 7.57, against 7.23 for the dearest jury. This is harmless, because 3b's projection is re-made for the selected instrument.
  - Stage 6 is priced on the cheapest API judge, while 3b uses the dearest. At the US$20 eligibility ceiling, expected stage 6 can reach about US$14.7, so the "stage 7 reduced by about US$3" can be about US$12.
  - §14 l.1009 ("a start rule for every stage, checked by the code") overstates: the runner checks stages 1 and 3 only.

## Readiness
In priority order:
1. M1 and M2 code, with the M3 tests, in the freeze commit.
2. The M1 and M2 pastes, plus m4 and m3 (text).
3. m1 and m2 (text).
4. m5 code and m6 nits.
5. The [PI] items.

`judge.py` and `gold_sample.py` can wait for the addendum, provided §13 adds: stage order and closure, start rule at the first non-pilot run, and `--reduce` refused for stage 3b.

## Number check
| Claim | Source value | Status |
|---|---|---|
| Holds 74.39 / 14.69 | 59.7016 + 14.6917; 14.6917 | OK |
| Projections 29.09 / 59.70 / 14.69 / 10.67 / 55.86 / 4.64 / 8.58 / 47.75 | cost model output | OK |
| Stages 1–3: 52.75 / 103.48; 1–3b: 58.13 / 114.15 | same | OK |
| Pessimistic start rule, stages 1, 2, 3 | 103.48 ≤ 110 each; 3b 114.15 → fallback | OK only if stages run in order (M1) |
| US$6.50 left; repeatability + guard 4.60; frontier subset 1.90 (≈4%) | 6.52; 4.29 + 0.32; 1.91 / 51.25 = 3.7% | OK |
| Expected, API instruments: total 113, stage 7 −3 | 112.59 | OK (see m6) |
| 3b dearest: H2 3.44, H3 7.23 (juries) | same; pipeline 7.57 | Nit (m6) |
| Judge pilot within the stage-1 slack | 7.17 > 6.52 pessimistic | Fails if the stages overlap (M1) |
| Frontier re-label ≤ about 12 h | 240 items × 3 min | OK |
| Offline test, 71 checks | 71/71 pass | OK |
