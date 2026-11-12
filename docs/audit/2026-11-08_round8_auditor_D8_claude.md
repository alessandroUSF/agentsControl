**Auditor D8, round 8: check of the C7 fixes**

All work was read-only (`python -I -B`, no network, no model calls). The offline test passes 88/88. `cost_model.py` matches `config/stage_holds.json` and all 52 cells of the Section 11 table. I ran five probes with the test's `FakeProvider` in `E:\claude\_tmp\d8`, which is now empty. I also checked the SDK field names offline (anthropic 0.97.0, openai 2.41.0). All 146 files listed in `SHA256SUMS_COPY.txt` still match, and no `__pycache__` was created.

## Verdict
Every C7 finding has been acted on: the stage gate and closure, the start rule at the first non-pilot run, `--reduce` limited to stage 3, the runner residuals, the re-priced budget and the five text pastes. The numbers agree everywhere except one stale parenthesis. I found no blocking issue. The new closure mechanism brings two small major issues: stage 3b is not gated before stages 4–7, and closing a stage is final and unchecked. Both need a few lines of code in the freeze commit (the runner is frozen with the protocol) and one sentence each in §11 and §13. Priority order: M1 and M2 with their tests; then m1–m3 code; then m4–m6 text; then m7; then the [PI] items. **Freeze after minor fixes.**

## C7 fix status
- **M1 (stage order):** fixed for stages 1–3 (`run_models.py:452–459, 792–809`; §11 l.844; §13 l.916). A residual remains (new M1).
- **M2 (start rule at the first non-pilot run):** fixed (`run_models.py:463–475`; §11 l.846). An oversized pilot still skips it (m2).
- **M3 (tests):** mostly fixed: 19 checks added and 2 replaced (71 + 17 = 88). Gaps are listed in m7.
- **m1 (anchors; β_int on G2 alone):** fixed (§9.2 l.614; §11 l.836). Residual in m4.
- **m2 (per-endpoint M̂_s):** fixed (§9.4 l.695).
- **m3 (H1, H3 and RQ4 under the 3b fallback):** fixed (§11 l.847). One case is not covered (m5).
- **m4 (`--reduce` for stage 3 only):** fixed (`run_models.py:461`; §11 l.846).
- **m5 (runner residuals):** fixed at l.509 (pilot records), l.660–666 (failed release), l.772 (hash-only print), `providers.py:352–358` (`row.get`), the docstring, and the reduced-stage-3 text. The `--adopt` check (l.640–645) is only partly fixed (m1).
- **m6 (budget nits):** fixed (`cost_model.py:215–250, 288`; §11 l.804, 851; §14 l.1014). One figure is stale (see the number check).

## Issues
### Blocking
None.

### Major
**M1. Stage 3b is not gated before stages 4–7** (`run_models.py:457, 801`; §11 l.844; §13 l.916).
- *Problem.* The gate covers only stages 1–3. In a probe, after closing 1–3, `--complete-stage 4` was accepted while 3b was still open. The §13 bullet would also let `judge.py` run stage 4 first.
- *Why it matters.* Stage 3b has no hold: it starts only if ledger + projection ≤ US$110. A reduced stage 4 run first can use up the headroom, and H2 and H3 then fall back to the local instrument. The order the PI happens to run stages in would then choose the confirmatory instrument.
- *Fix.* In code, set `GATED = ("1", "2", "3", "3b")` and use it in both `need` lists. In §11 and §13, paste: "…every earlier stage among 1, 2, 3 and 3b, so stages 4–7 also require stage 3b closed (run, fallen back or not needed)." This cannot deadlock: instrument selection uses only stage-2 gold.

**M2. Closing a stage is final, and nothing checks it** (`run_models.py:792–809`).
- *Problem.* In a probe, `--complete-stage 1` was accepted while both models still had stage-1 prompts unanswered. After that, `--stage 1` is refused for good, and the only way back is editing the append-only ledger.
- *Why it matters.* Stage 1 takes many invocations: a pilot per model, two chunks per direct model, the OpenRouter run and Venice. Closing it early is a plausible mistake, and it would leave G2 frames incomplete, which hurts T1a and T1b.
- *Fix (paste):*
  ```python
  ap.add_argument("--cut", default="", help="REASON, if stage N closes with prompts unanswered")
  # --complete-stage branch, before the ledger line:
  if n in ("1", "3") and not args.cut:
      flt = {"1": {"within": "added_api"}, "3": {"outside": "added_api"}}[n]
      left = {m["key"]: k for m in models_all if providers.is_remote(m)
              for k in [sum((m["key"], r["id"], request_hash(m, r["prompt"]), config_hash(m)) not in done
                            for r in model_rows(m, rows, 0, **flt))] if k}
      if left:
          sys.exit(f"stage {n}: unanswered prompts {left}; finish them or pass --cut REASON")
  ```
  Also add `"cut": args.cut or None` to the `stage_complete` line.

### Minor
- **m1. The `--adopt` count check is weak** (l.642–645; `providers.py:330–332`).
  - OpenAI reports `total` = 0 while a batch validates, and the check is then silently skipped (probe).
  - Full chunks all hold 100 requests, so equal counts prove little. In a probe, a foreign batch of the same size was adopted and its three answers were written under model `fa`.
  - *Fix:* refuse when `not count`. At l.608, make custom IDs unique per submission: `stamp = ref.rsplit("-", 1)[1]`, then `f"{stamp}_{i:05d}"`, which fits Anthropic's ID pattern. A wrong batch then yields unknown IDs, which are charged but never recorded. At collect, stop if `model_returned` does not start with `m["model"]`.
- **m2. An oversized pilot skips the start rule.** In a probe, `--pilot 500 --stage 1` ran both whole subsets (18 calls) with the study cap at US$100, where the main run is refused. The holds still bind, but those answers are paid again in the main run. *Fix:* `if args.pilot > 20: sys.exit("respondent pilots have 20 prompts (Section 6.3)")`.
- **m3. `stage_hold` lines cannot be audited on their own.** They omit the ledger total, the study cap (a `STUDY_BUDGET_USD` override in `.env` leaves no trace), the projections file used, `batch` and the models. *Fix:* add `"ledger_usd"`, `"study_cap_usd"`, `"holds_sha256": sha256(STAGE_HOLDS bytes)`, `"batch"` and `"models"`, and have §13 require the same of `judge.py`.
- **m4. Anchors** (§8.3 l.479, 488).
  - They are drawn from G1 + G2 but judged in the G2 wave, and each anchor's blind and in-context calls must be adjacent. A G1 anchor's blind call already happened in Phase 1.
  - *Paste:* "Anchors are drawn from G2 items only." Alternative: "G1-drawn anchors get a second blind call adjacent to the in-context one; T1a keeps the Phase-1 verdict."
  - Also add: "The self-specific reading needs the pooled and the G2-only β_int to agree in sign."
- **m5. RQ4 has no rule when 3b runs on an API instrument but stage 6 is cut or reduced.** *Paste:* "If stage 6 does not run in full, RQ4 uses the local fallback instrument for every corpus answer; stage-3b API labels are a sensitivity analysis."
- **m6. Wording.**
  - (a) l.846 and §14 say "re-made from that stage's pilot", but stages 3–7 have no pilot of their own. Use "from the pilot of that call type (Hold rule)".
  - (b) l.847 says "juries included"; make it "juries and pipelines included". In §8.4 l.558, write "A jury, pipeline or cascade…" and state the 50% arbiter share the projections assume.
  - (c) Schedule (l.877): stage 3 now runs in Phase 2, after stage 2 closes. H3 for models 1–3 therefore pools answers taken weeks apart: 100 safe prompts from stage 1 and 450 from stage 3. Compare `model_returned` across the two stages and report any mismatch as a deviation.
  - (d) For a reduced stage 3, use "answered (any status but `error`) by all six version-1 models; the same set for every H2 and H3 test".
- **m7. Tests and §13.**
  - Still untested:
    - both real `batch_request_count` methods, with stand-in clients (OpenAI `None`/0);
    - that a later non-pilot run is not re-checked by the start rule;
    - an unknown `custom_id` at collect;
    - closure with a pending submission;
    - the M1 and M2 cases.
  - §13 should add: "stage 2 is never run reduced", and "judge batch logs are `results/logs/batches_<run>.jsonl`", so that `--complete-stage` sees them.
- **Nits.**
  - A `--release` that keeps failing with a non-404 error has no logged way out, and it blocks closure. Add `--undeletable`, which records an open Section-10 item.
  - Charging OpenAI lines without a `custom_id` is conservative and right (at most 0.5 × worst case each, and the item is re-sent), but count them separately as `unattributed_lines`.
  - In `stage_holds.json` `_what`, "round 7" should read "after round 7".

## Number check
| Claim | Source value | Status |
|---|---|---|
| §11 table (13 rows × 4 columns) | cost model output | OK, 52/52 |
| Holds 74.39 / 14.69; projections 29.09 / 59.70 / 14.69 / 11.00 / 55.86 / 4.64 / 38.48 / 47.75 | cost model; `stage_holds.json` | OK |
| 3b adds about US$5.60 / US$11; stages 1–3b US$58 / US$114 | 5.58 / 11.00; 58.32 / 114.48 | OK |
| 3b dearest candidates | expected: pipeline 1.38 + 4.20; pessimistic: jury 3.44 + pipeline 7.56 | OK (C7's 7.57 is rounding) |
| Stage 6 at the dearest eligible candidate | DeepSeek + Venice + Hy3 as arbiter; whole corpus 19.98 ≤ 20 | OK |
| Expected total with API instruments about US$123; stage 7 cut about US$13 | 122.86; 12.86 | OK |
| "About US$3 if GPT-6 Luna" | Luna stage 6 = 3.87 → total 111.33 | **Stale: about US$1.30** |
| Pessimistic: 6.50 left; 4.60; 1.90; about 4% | 6.52; 4.29 + 0.32; 1.91; 1.91 / 51.25 = 3.7% | OK |
| 88 checks | 88/88 pass | OK |
