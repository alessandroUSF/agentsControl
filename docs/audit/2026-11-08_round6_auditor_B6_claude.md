**Auditor B6, round 6: AI safety evaluation, code and budget**

Everything was read-only. The offline test passes 45/45 and `cost_model.py` reproduces Section 11 to the cent. I ran probes with the test's fake provider and stand-in SDK clients, writing only under `E:\claude\_tmp\b6_r6`, which is now empty.

## Verdict
B5's findings are fixed or mostly fixed, and the holds equal the cost model's output. Four new issues are major, and all are small to fix:
- The protected pessimistic total is understated by about US$1.8, and the "start rule" (a stage starts only if ledger + hold + its projection ≤ US$110) is not coded. Stage 3b can therefore start and stall partway, leaving H2/H3 labelled by two different instruments.
- A synchronous run ignores unsettled or pending batches, so the same prompts are sent twice.
- A cut-short ledger line is skipped, so the total silently drops.
- OpenAI deletion at the provider is not idempotent, so harmful text can stay there.

None is blocking. Section 13 freezes the runner with the protocol, so the fixes and their tests belong in the freeze commit. **Freeze after minor fixes.**

## Round-5 fix status (B5)
- **M1 (H2/H3 on an unprotected stage):** fixed. Stage 3b is protected (§11 l.798, 829, 835–836; `cost_model.py:198–205, 270`). It is priced on single judges only (new M1).
- **M2(a) (cache factors):** partly fixed. Read factors match the snapshot (`models.json:19–21, 38–40, 57–58, 173–174, 213–214`). The pessimistic case does not price cache writes (M1).
- **M2(b) (chunks shrink to the headroom):** fixed (`run_models.py:508–517`).
- **M2(c) (hold and reduction rules):** text fixed (l.835–836). The start rule and the seeded stage-3 cut are not coded (M1, m2).
- **M2(d) (cuts restated):** fixed (l.838–840).
- **M3 (T4 fallback):** text fixed (§8.3 l.501–506; §9.3 l.660); the second auditor covers it.
- **M4 (uplift definition):** fixed (`RUBRIC.md:11` matches §7.1 l.334).
- **M5 (batch faults):** mostly fixed.
  - Done: pending entry (`:521–528`), `--adopt`/`--release` (`:543–564`), per-item parsing (`providers.py:224–229, 334–338`), skip of written items (`:608, 620`), run binding (`:593–594`), purge refused before settlement (`:574–575`), bookkeeping with no model enabled (`:364–368`).
  - Residuals: M2, m1, m3. The orphan-file cleanup deletes too often (M4).
- **m1 (error text in the call log):** fixed (`:95–108, 452–453`); residual m6.
- **m2 (settled at zero):** fixed (`:261–272`).
- **m3 (marker order):** fixed (`providers.py:64–76, 128–130`).
- **m4 (Plan A halves):** fixed (§7.3 l.403, 408).
- **m5 (manual holds):** fixed (`stage_holds.json`; `:389–407`; lock at `:395` before the ledger read at `:400`).
- **m6 (unimplemented batch rules):** fixed (cancel `:603–606`, block `:682–685`, batch errors `:655–664`); residual m5.
- **m7 (text items):** all fixed (l.147, 192, 297, 373, 380, 499, 707, 1006; the "may be reduced" sentence is gone).
- **m8 (test gaps):** partly fixed. What is still untested is listed below.

## Issues

**Blocking:** none.

### Major

**M1. The protected pessimistic total is about US$110.9, not 109.14, and the start rule is not coded.**
- **3b is priced on single judges.** `stage3b` takes the dearest single judge, but Section 8.4's candidates include juries. Haiku + GPT-5.6 Luna + GLM is eligible (expected corpus cost US$19.12 ≤ 20) and costs US$3.04 for H2, against 1.94. Total 3b = 8.21, not 7.06.
- **No cache-write premium.** "No cache hits" includes cache expiry. Then every Anthropic call re-writes the cache, and the ledger charges that at 1.25× (`run_models.py:213–214`), but `judge_call_cost` (`cost_model.py:130–134`) prices it at 1.0×. Stage 2 becomes 58.94 (+0.64).
- **Corrected figures:** holds 81.83 / 22.90 / 8.21; protected total **110.92**.
- **No gate.** `main` (`:389–409`) checks only the hold, so stage 3b can start and pause midway. Section 11's "fixed before any H2 or H3 label exists" then cannot hold.
- **Answer to the brief's question.** The US$0.86 headroom is a real problem only because there is no gate; the local fallback contains the risk. Minimal fix:
  - *Code:* add `"projections_usd"` to `stage_holds.json`. In `main`, before the `stage_hold` line: `first = not any(e.get("kind")=="stage_hold" and e.get("stage")==args.stage for e in read_jsonl(LEDGER))`, then `if first and spent_so_far()+hold+proj > study_cap: sys.exit("stage does not fit (Section 11)")`. Judge code: same rule.
  - *Cost model:* price writes at 1.25× for `anthropic/*` when `cache_hits` is False; take the 3b maximum over single judges and three-developer juries with expected corpus cost ≤ US$20.
  - *Paste (§11):* "Stage 3b is priced at the dearest eligible candidate, juries included. It starts only if the ledger plus its projection, re-made for the selected instruments, is at most US$110. Otherwise, or if it pauses before completion, H2 and H3 use the fallback local candidate for all their labels, and any partial API labels are exploratory. In the pessimistic case with API instruments the protected stages (about US$111) exceed the cap, so stage 3b falls back to local instruments."

**M2. A synchronous run re-sends prompts that are in an unsettled or pending batch** (`run_models.py:729–760`; only `submit_batch`, at `:498`, checks).
- **Verified.** After a 3-item batch, a synchronous run sent all 6 prompts, and 3 prompts got two records. The same happens after a lost reply.
- **The documented stage-1 command invites it.** The command at `:7` is synchronous, and `--batch` exits at the first OpenRouter model (`:742–743`). Stage 1 as documented runs the direct models synchronously: US$36.00 against the planned 29.09 pessimistic (+6.91), so stage 1 pauses at its cap.
- **Fix,** in the model loop before `providers.make`:
  ```python
  busy = unsettled_batches(m["key"])
  if busy and not args.batch: print(f"  SKIPPED {m['key']}: {busy[0]} unsettled/pending"); continue
  if args.batch and m["provider"] not in ("anthropic", "openai"): print(f"  SKIPPED {m['key']}: no batch path"); continue
  if not (args.batch or args.pilot or args.sync) and m["provider"] in ("anthropic", "openai"):
      sys.exit(f"{m['key']}: main runs use --batch (Section 6.3)")
  ```
  Add a `--sync` flag (the offline test's synchronous cases need it) and document two stage-1 commands.

**M3. Unreadable ledger or batch-log lines are skipped** (`:150–169`). `end_with_newline` is applied only to the raw file and call log (`:425–426`), not before `ledger()` (`:442`) or `batch_line()` (`:492`).
- **Verified.** A cut-short US$1.50 line fused with the next append, and both vanished from `spent_so_far()`.
- **Why it matters.** A cut reservation or pending line also re-opens the resubmission path.
- **Fix.** Give `read_jsonl(path, strict=False)` a strict mode that does `sys.exit(f"{path.name} line {n} unreadable: repair before any paid or bookkeeping run")`, and use it for the ledger and batch logs. Call `end_with_newline(path)` before every append, and `f.flush(); os.fsync(f.fileno())` after the reservation and pending lines.

**M4. OpenAI deletion is not idempotent** (`providers.py:354–361`), and the orphan-file cleanup (`:306–311`) runs on any exception.
- **Verified.** After one transient failure on the output file, every `--purge` fails with a 404 on the already-deleted input file. The output and error files (harmful text) stay at the provider, against Section 10.
- **A timeout on `batches.create` makes it worse.** The cleanup deletes the input of a batch that may exist.
- **Fix.** Delete in the order output, error, input. Wrap each delete in `try: ... except openai.NotFoundError: pass`, and do the same with `anthropic.NotFoundError` in `AnthropicProvider.batch_delete`. In `batch_submit`, delete the upload only when `400 <= (getattr(e, "status_code", None) or 0) < 500`. Otherwise the upload is deleted at `--release`.

### Minor
- **m1. Collect bookkeeping** (`:612–618, 650–652`).
  - The raw record is written before its ledger line, so a crash between them under-counts on retry.
  - An unreadable result line is charged again on every repeated collect (verified: 2 charges for 1 line).
  - Fix: write the ledger line first, with `batch_id`, and skip items already charged; charge unreadable lines once, inside the settlement line.
- **m2. Stage-3 cut order.** Seed 20261123 is not in the code. `todo` is in file order with own prompts last (`:732`), so a pause cuts H2 framings first. At the pilot's doubled cap, the 10-request minimum needs US$1.60 of headroom.
  - Fix: for `--stage 3`, sort `todo` by `sha256(f"20261123|{base_prompt_id}")`, and trim each chunk back to the last complete base prompt.
- **m3. `--adopt` accepts a batch ID that is already in the log** (`:543–554`). Verified: the real lost batch became uncollectable and undeletable, and its reservation stayed stuck. Refuse linked IDs; print the request count and creation time.
- **m4. `--stage` is not validated** (`:390–394`). A respondent run under `--stage 4` has a hold of 0, and the offline test itself does this. Allow `{"1","3"}` only. The skip set `done` is per run (`:427–429`), so a rerun under a new name re-sends everything; make it study-wide for paid models.
- **m5. Gaps in the 48-hour block.** It ignores pending submissions (`:682–683`), and adoption restarts the clock (`:552`).
- **m6. SDK error bodies can reach a published file.** Re-raised SDK errors (`:539, 551`) print their body to stderr. `run_with_memory_guard.py:36, 120` writes stderr to `results/logs/guard_*.log`, a folder `.gitignore` marks as published. Catch these in `main` and print `error_label(e)` only.
- **m7. OpenAI cache writes.** The note "OpenAI bills no cache writes" (`models.json:58, 174, 214`) contradicts the snapshot, which lists 1.25× write prices for all three OpenAI models. The adapter records no write tokens, so the ledger cannot apply it. Check it on the pilot invoice; if writes are billed, stage 2 rises by +0.77.
- **m8. §13 l.899 judge requirements:** add the start rule, the worst-case reservation per call at the 2,000-token judge cap, the `settle_amount` rules, and "no synchronous call for an item in an unsettled batch."

**What the 45 checks miss:**
- the real OpenAI adapter (submit cleanup, output/error-file parsing, delete, failed batches);
- unreadable result lines;
- a crash between record and ledger line, or between the settlement line and the marker;
- a synchronous run while a batch is unsettled;
- adopting a wrong ID;
- truncated ledger lines;
- non-zero cache tokens in `listed_cost`;
- a strong-marker block or a `canceled` item inside a batch;
- the stage-3 order and the start rule;
- stale pending submissions;
- real lock contention (only a pre-existing lock file is tested).

## Readiness
- **Before the freeze:** the M1 text paste and m8.
- **In the freeze commit** (Section 13 freezes the runner), each with a test: the M1–M4 code fixes and m1–m6. Otherwise each becomes a logged deviation before the first paid call.
- **Can wait for the judge-code addendum:** `judge.py`.
- **Item 4:** I found nothing affecting code or budget.

## Number check

| Claim | Source value | Status |
|---|---|---|
| Holds 80.05 / 21.75 / 7.06 | cost model: same | OK (81.83 / 22.90 / 8.21 corrected) |
| Stages 1–3b pessimistic 109.14, headroom 0.86 | 109.14 in the cost model; 110.92 at ledger pricing and the dearest eligible candidate | Fails (M1) |
| 3b at the "dearest eligible" candidate, 7.06 | 7.06 single judge; 8.21 with a jury | Wrong basis |
| Expected: 56.62 protected; 101.89 all local; 111.08 with API instruments, stage 7 −1.08 | same | OK |
| Local pessimistic: ≈8 left; repeatability + guard ≈4.50; frontier subset ≈3.40 ≈ 7% | 7.92; 4.52; 3.40; 6.9% | OK |
| 3b calls 1,080 + 3,300; corpus 16,470 | 6×180, 6×550; 16,470 | OK |
| Stage 1 pessimistic 29.09 | 29.09 with `--batch`; 36.00 with the documented command | Conditional (M2) |
| Sonnet chunk ≈ US$8 | 8.00 (16.00 at doubled cap) | OK |
| Cache read factors 0.05/0.1/0.1/0.1/0.05 | snapshot ratios match | OK |
| OpenAI "no cache writes" | snapshot lists 1.25× | Unsupported (m7) |
| Offline test, 45 checks | 45/45 pass | OK |
