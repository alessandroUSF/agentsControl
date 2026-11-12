# Round 3, auditor B3 (Claude subagent: AI-safety practice, code, data), 8 November 2026

- **Audited copy:** `E:/claude/_audit_copy/agentsControl_r3` (protocol v2.2 draft, before the PI decisions on the second annotator and the frontier core).
- **Brief:** `AUDIT_PROMPT_R3.md`.
- **Source:** reproduced from the auditor's final message, with the formatting normalised.

**Verdict.** Version 2.2 fixes most of the 27 critical and major round-2 findings: 22 fully, 2 mostly and 3 in part. The in-scope runner code mostly matches Sections 6, 8, 10 and 11.

Section 6.1 was re-run by hand on the snapshot:
- **Reproduced exactly:** the most-used, most-capable and OpenRouter-uncensored strata. Developer totals are 256.02, 76.36, 71.75, 56.90 and 53.28 T, and Gemini 4 Argon is ranked 3rd (index 50.41, US$10.00 on OpenRouter).
- **Reproduced under only one reading:** the consumer-GPU and matched strata.
- **Not reproduced:** under the literal wording, slot 21 is dolphin-mixtral, not dolphin-mistral.

Two further problems:
- The model-6 judge build is not template-identical to model 4, because its Modelfile has Windows line endings. So the T4 pair 4–6 does not "differ only in its weights".
- The US$36 core budget assumes batch calls and prompt caching, and no in-scope code implements either.

**Readiness: do not freeze on the current files.** A 12 November freeze is feasible after blockers B1–B4 are fixed. B2 and M6 must be settled before the 9–11 November local runs.

## Round-2 fix status
**A2 findings**
- C1, accuracy outcome: **fixed** (3.1, 9.2).
- C2, missed-harm bound under weights: **fixed** (9.5, unweighted Clopper–Pearson).
- M1, T4: **fixed** (3.1, 9.3).
- M2, bootstrap: **fixed** (9.1).
- M3, anchors and estimand: **fixed** (8.3, 9.2).
- M4, weights: **mostly fixed** (7.2). The G3 inclusion probability is incomplete (m3).
- M5, instrument rules: **fixed** (8.4, 9.6).
- M6, decision rules: **fixed** (9.5).
- M7, frontier rule: **fixed** (8.1).
- M8, effort and output cap: **fixed** (6.3; `run_models.py:75–89`).
- M9, routing and moderation: **partly fixed** (6.3; `providers.py:54–76`). The marker list is incomplete (M3).
- M10, provenance: **mostly fixed** (`run_models.py:276, 326`). Local digests are not pinned (M5).
- M11, ethics gap: **partly fixed** (10). The README and `judge.json` still claim local-only judging (B3).

**B2 findings**
- C1: **fixed** (9.2).
- C2: **fixed** (3.1, 8.3, 9.2).
- C3: **fixed in the text** (8.3), but the Anthropic adapter cannot send the system message (M4).
- C4: **fixed** (`run_models.py:50, 225`; guard `:30`). See m10 on `sample.jsonl`.
- M1: **fixed** (7.2, 9.5).
- M2: **fixed** (9.3).
- M3: **fixed** (9.5).
- M4: **fixed** (8.1).
- M5: **fixed** (7.2).
- M6: **fixed** (9.1, 9.2, `power_sim.py` docstring).
- M7, ethics: **partly fixed** (10). See B3 and M6.
- M8, answer status: **fixed** (`run_models.py:85–88`; `providers.py:158–160`).
- M9, framing: **fixed** (2).
- M10, timeline: **fixed** (7.4, 13).

## Issues by severity

### Blocking
**B1. The model-6 judge build is not template-identical to model 4.**
- **Where:** 8.3; `scripts/make_judge_alias_m6.py:28`; `config/ollama/Modelfile_m6_judge`; `scripts/check_system_override.py:38–47`.
- **Problem:**
  - `Path.write_text` on Windows writes CRLF line endings: the Modelfile has CRLF on all 52 lines.
  - Its TEMPLATE block hashes to `92018823051f`, which is the judge build's template digest. The same text with LF endings hashes to `948af2743fc7`, model 4's template.
  - The judge build therefore emits `\r\n` where model 4 emits `\n`, for example after every `<|end_header_id|>`.
  - The check compares token counts on a single-turn layout, so it can detect neither this nor any in-context difference.
- **Why it matters:**
  - Pair 4–6 differs in prompt bytes, contrary to 8.3.
  - The note "verified identical prompt rendering" in `models.json` is unsupported.
  - Unusual header tokens may raise judge 6's invalid rate.
- **Fix:**
  - Write the file with `newline="\n"` (or `write_bytes`) and rebuild.
  - Pass criterion (paste): *"the `/api/show` template and parameter SHA-256 of each T4 member equal its base's (948af274…/56bb8bd4… for 4–6; ae370d88…/cff3f395… for 5–18), and `prompt_eval_count` is equal in four layouts: user; system+user; system+user+assistant+user; user+assistant+user."*

**B2. The selection wording does not reproduce the panel.**
- **Where:** 6.1; `EXCLUSIONS.md`; `SELECTION_EVIDENCE.md`.
- **Problem:**
  - **(a) "Smallest tag ≤ 20 GB".** The captured page lists `8x7b-v2.x-q2_K` at 17 GB and `q3_K_S` at 20 GB, so the literal rule picks dolphin-mixtral (1,989,941 downloads, against 1,881,526 for dolphin-mistral). The recorded exclusion reason is false on the snapshot.
  - **(b) "Default tag ≤ 5.5 GB".** `qwen3.5:latest` is the 9B build (6.6 GB). Read as `latest`, the rule drops `qwen3.5:4b`.
  - **(c) Price source.** It is defined only inside the most-capable stratum, and justified as "the price the study pays". The study pays batch prices, and `anthropic/claude-opus-5.5:batch` lists US$10.00 output. Under that reading, Opus 5.5 enters as Anthropic's pick.
- **Why it matters:** a third party can get a different panel, and slot 21 runs on 9–11 November.
- **Fix** (paste into the common rules): *"Prices are the standard OpenRouter list price (`pricing.completion` of the un-suffixed ID; not `:batch` or `:free`). A build's size is that of its `ollama.com/library/<name>:<size>` tag without a quantisation suffix. Consumer GPU: such a tag ≤ 5.5 GB. Uncensored: the tag of the smallest parameter size ≤ 20 GB."*
  - This keeps the current panel, because `dolphin-mixtral:8x7b` is 26 GB.
  - Correct both exclusion texts, and record this as a clarification made after the snapshot was seen.

**B3. Documents that will be published contradict Sections 7 and 10.**
- **Where:** the README ("Responsible design", "Judge"); `config/judge.json:2`; `labels/RUBRIC.md`.
- **Problem:**
  - The README says commercial APIs receive only safe prompts and that harmful answers are judged only by local models.
  - `judge.json` says answers "never leave this machine".
  - The rubric keeps the version-1 harm mapping, schedules edge cases "after the first 30 labels" (contradicting 7.4), and has no harmful-content, hazard or uplift fields.
- **Fix:** rewrite all three in the freeze commit.

**B4. The Section 13 freeze package is missing.**
- **Problem:** none of these exist:
  - `judge.py`, `gold_sample.py`, `relations.csv` and `judge_prompt_v2.txt`;
  - the T1a/T1b/T4, nested-CV, H1–H3 and RQ4 drivers;
  - their output on synthetic labels.
- **Why it matters:** Sections 9.1 and 13 require them at the freeze.

### Major
**M1. The budget relies on batch and caching that are not implemented.**
- **Problem:**
  - The runner has no batch path, and no adapter sets Anthropic `cache_control`.
  - Synchronous respondents cost US$36.40 (expected) and US$65.39 (pessimistic).
  - Without caching, core judging costs US$19.89, not US$13.82.
  - Spending-order items 1–3 cost:

    | Scenario | With batch | Synchronous |
    |---|---|---|
    | Expected | US$35.2 | US$55.6 |
    | Pessimistic | US$66.5 | US$104.8 |

  - Under pessimistic assumptions, the cap therefore stops the run inside items 1–3.
- **Fix:**
  - Implement batch and caching.
  - Reorder (paste): *"1a. API respondents run the common 190-prompt `added_api` subset, which is the G2 frame of every commercial respondent. 1b. After item 3, models 1–3 run their remaining 600 prompts (H2/H3)."*
  - With batch, items 1–3 would then cost US$27.1 (expected) and US$51.8 (pessimistic), and all 11 commercial strata would get identical prompts.

**M2. The spending ledger can undercount.**
- **Problem:**
  - The ledger is written once, after the run. A crash, Ctrl-C, a `ProjectKeyError` re-raised through `f.result()`, or the guard's `terminate()` loses the run's spend.
  - Errored calls, including 180 s client timeouts, are settled at US$0 but may be billed.
  - `cost_reported` is ignored.
  - Concurrent runner and judge processes each read the same total.
- **Fix:**
  - Append one ledger line per settled call, under the write lock.
  - Settle errors at the reserved amount unless the call failed before sending.
  - Use max(list-price cost, `cost_reported`).
  - Add a lock file, and set client timeouts of at least 900 s (or stream).

**M3. Moderation detection is incomplete.**
- **Where:** `providers.py:54–55, 223`.
- **Problem:**
  - Markers are probably missing for provider-specific rejection texts: DeepSeek "Content Exists Risk", Z.ai code 1301 or "sensitive", Alibaba `data_inspection_failed` [unsure].
  - Finish reasons other than `content_filter` are not mapped.
  - Unmatched blocks become `error` and are resent on every re-run, contrary to 5.2.
- **Fix:**
  - Log raw 4xx bodies, and add these markers.
  - On refuse-expected prompts, record any 400/403 without a parameter-error signature as `provider_block_suspected`. Never retry it automatically, and classify it by hand after the pilot.
  - Map `native_finish_reason`.

**M4. Two adapter defects.**
- **Where:** `providers.py:101–102, 140`.
- **Problem:**
  - Anthropic messages are passed with `role: "system"`, which the Messages API rejects, so every Anthropic judge call fails.
  - OpenAI Responses calls keep the default `store=true`.
- **Fix:** move system content to the top-level `system=` parameter, and set `store=False`.

**M5. Local provenance and the T4 contrast.**
- **Problem:**
  - No local digest is pinned or asserted, and the resume key omits the digest.
  - The snapshot's two captured digests disagree for models 15–17.
  - Model 6's `latest` (4.7 GB) is a q4_0 or q4_k_s build, while `llama3.1:8b` is Q4_K_M. So pair 4–6 probably also differs in quantisation.
- **Fix:**
  - Pin and assert a digest for each local model, and add it to the configuration hash.
  - Record each T4 member's quantisation.
  - Pre-specify a local T4 sensitivity with a Q4_K_M judge build.

**M6. Ethics and data handling (Section 10).**
- **(a)** Batch use leaves provider-side files containing harmful text. Delete them after retrieval and say so.
- **(b)** "Harmful prompts come only from public benchmarks" conflicts with the refuse-expected own prompts.
- **(c)** No uplift label exists, but items with actionable uplift are withheld from release. Add an uplift yes/no field.
- **(d)** The judge pilot's harmful answers from the abliterated control would require screening sealed model-6 outputs. Draw them from a new, unsealed run, and exclude those prompts from the G2 and G3 frames.
- **(e)** Muse Wonder is `is_moderated: true` on OpenRouter; disclose this.
- **(f)** Zero data retention is unverified for DeepSeek 1017, GLM, Hy3, Kimi and Venice [unsure]. Pre-specify the fallback.

### Minor
- **m1. Power figures** in 9.2 do not match `power_sim.json`:
  - T1b at 4.8 pp: 0.75–0.86;
  - size at the null: 0.005–0.048;
  - power at 3.4 pp: 0.40–0.63;
  - H1 pass probability: 0.66 / 0.32.

  The Wald-size claim in 9.1 is not in the output.
- **m2. Bootstrap scaling.** `estimators.py:80` uses (n−1)/(n−k) but line 53 uses (n−1)/(n−k−n_fe), so t_obs and t* differ by about 3% (conservative). Use the same adjustment in both.
- **m3. G3 π.** It ignores G1 (35 harmful items from model 6) and pilot removals, and G3 is drawn per model while G2 strata are model × source. Paste: *π_i = π_prior,h(i) + (1 − π_prior,h(i))·n_G3,m/R_m*, with R_m the model's remaining frame.
- **m4. Keyword-enriched draw.** If K < 2, π_flagged = (4 − K)/(N − K). N counts `ok` + `truncated`.
- **m5. Configuration hash.** It includes notes, so editing a note forces re-runs. Use an allowlist of behavioural keys.
- **m6. Pair 15–19.** `presence_penalty` 1.5 is set on model 15 only. Judges must send explicit sampling options. "Render identically" holds for templates only.
- **m7. Selection evidence for models 18 and 19.** The `8b-v2` tag is not on the captured page. "Card" should say the Ollama page or the linked Hugging Face card. Model 19's card never states that it removes refusals only.
- **m8. Effort "low".** Section 8.3 says every API judge supports it, but Venice exposes no reasoning parameter.
- **m9. Recognition probe.** In the in-context presentation, the answer sits in the judge's own turn, so "Did you write this?" cannot measure recognition. Restrict the probe to blind, or relabel it.
- **m10. Sealed and run files.** `sample.jsonl` (sealed hash) is rewritten when own prompts are added (`prepare_data.py:91–95`). `pilot_local` has no recorded hashes, and `manifest_full.jsonl` is not hashed.
- **m11. Memory guard.**
  - `--run` as the last argument raises an IndexError.
  - Unload and reload events are not written to the manifest.
  - A `TimeoutExpired` skips the unload.
  - Matching only `llama-server.exe` may miss Ollama runners [unsure].
- **m12. Stale docstrings.** `run_models.py:21–24` and the `--pilot 50` example are out of date.
- **m13. Optional third T4 pair.** `kaineone/qwen3.5-4b-abliterated` (card: "Not fine-tuned") would make a third true-abliteration pair, raising power at −0.03 from 0.77–0.90 to 0.95–0.99. This is a PI decision before the freeze.

## Item 4 in brief
- **DeepSeek checkpoint:** correct (`-1017`, 135.40 T against 97.63 T).
- **Gemini 4 Argon replacing Hy4:** correct under B2's price wording.
- **T4 restricted to two pairs:** sound.
- **Model 6 disclosure:** accurate. The judge-build idea is right, but its implementation is defective (B1, M5).
- **Additions:** sound. The XSTest v2 transfer set checks the refusal endpoint only. Report the coverage of stated confidence by judge.

## Estimator check
| Function | Status | Note |
|---|---|---|
| `demean_two_way`, `fe_lpm` | OK | CR1 counts nested item FE, so slightly conservative |
| `wild_cluster_bootstrap_p` | OK, minor | Null imposed through FWL; scaling mismatch (m2) |
| `theta_on`, `pooled_pair_difference`, `weighted_mean_cluster_se` | OK | – |
| `tango_null_variance` | OK | Matches a brute-force restricted MLE to about 1e-8 |
| `t4_test` | OK | – |
| `boot_p_*`, `holm`, `cluster_bootstrap_indices` | OK | – |
| `clopper_pearson`, `kish_neff`, κ | OK | – |
| `korn_graubard` | Approximate | Kish n_eff with no df correction |
| `pi_keyword_enriched` | OK | Monte Carlo 0.2488 vs 0.2490, and 0.03452 vs 0.03448 |
| `pi_g3` | Incomplete | m3 |
| `rogan_gladen` | OK | – |

## Cost assessment
- **Reproduction.** The script reproduces Section 11:
  - expected: US$36.46 core, US$43.24 with the exploratory items, US$17.28 for frontier judges;
  - pessimistic: US$68.97 core, US$82.80 with the exploratory items.
- **Prices** match the snapshot.
- **Batch and caching.** The US$36 is credible only with both, which save US$13.9 and US$6.1. Fully synchronous, the core is US$57.4.
- **Worst case for judges.** If every judge call hits the 2,000-token cap, core judging costs US$59 (batch) or US$91 (synchronous). Kimi K3.1 Pro is the costliest judge, at US$6.03, because it has no batch price.
- **Protection by the spending order.**
  - T4 is local, so it is protected.
  - T1a and T1b are protected only in the expected case with batch (M1).
- **Not costed:**
  - unframed re-judging of the own-prompt answers (about 84 items × 12 judges, US$1.8–3.7);
  - frontier retries.

## Requirements for the modules not yet written
- **Template.** One frozen template, with its hash checked at start. The rubric goes in the system message (Anthropic `system`), otherwise at the start of the first user message, the same way in both presentations. The instruction is byte-identical and is the final user content.
- **Presentations.**
  - Blind: one user message.
  - In-context: user (request), then assistant (answer), then user (instruction).
  - Neither states authorship.
- **Answers.** The full answer, never clipped. `context_overflow` is detected.
- **Output and parser.**
  - Free generation.
  - Strict parser: a label from the 3-value enum, a JSON boolean for harm, optional confidence 0–100, and a reason of at most 30 words that is never released.
- **Retries.**
  - One format retry; up to 3 transport retries, not counted as attempts.
  - `provider_block` is never retried.
  - Five invalid reasons.
  - An append-only attempt log; no item is dropped.
- **Settings.**
  - API judges: effort low, cap 2,000.
  - Local judges: cap 600, `num_ctx` 8,192, thinking off, explicit sampling options.
  - Temperature 0 and seed 20261108 where accepted; batch where cheaper.
- **Builds.** Model 6 judges as the fixed judge build. Every local judge passes the B1 rendering check.
- **Item order.** Seed = first 8 hex digits of SHA-256(judge key + "20261108").
- **Coverage.**
  - Blind: all judges on G1 + G2 + G3.
  - On-policy: each item judged by its author (G1 + G2).
  - Anchors: 30 per judge (10 common and 20 judge-specific, seeds 20261113 and 20261113 + panel number), with no relation to the judge.
  - Repeatability: 50 items (seed 20261115).
  - Judge pilot: 30 items outside the gold set.
  - Recognition probe; second wording on 100 items; unframed own-prompt re-judging.
  - External set: 400 completions for local judges, 150 for API judges (seed 20261116).
- **Guards and baseline.** Guards run through their native interfaces, with the stated mappings and native scores kept. The keyword baseline reads the whole answer, gives no harm verdict, and is scored only with design weights.
- **Instrument.**
  - Candidates: juries; the version-1 pipeline, arbitrating on either field; the cascade.
  - Recusal by base developer.
  - A US$20 dry run on 16,470 answers.
- **Logging and spend.**
  - Logged per call: request, configuration and template hashes; served provider; returned model ID; reasoning tokens.
  - Spend goes through the shared per-call ledger.
  - Sealed files are opened read-only, with their hashes verified.
- **G1.** Rebuild the sheet from the stored key with the same seed, IDs and new columns. Verify hashes without opening the key. π is on the frame of all non-error answers.
- **G2.**
  - Frame: `ok` + `truncated` answers, excluding G1 and pilot items.
  - The 7.2 strata and allocation.
  - The keyword-enriched π, including the K < 2 case.
  - Seed 20261111.
- **G3.**
  - The frame and batches of 20; seed 20261112.
  - Stop at 110 or the cap, decided on gold counts only.
  - π from all prior stages.
- **Other draws.** Record the stratum, stage and π for every item. Seed the second-annotator, re-label (70) and holdout draws.
- **`judge.json`.**
  - One entry per judge (22 judges, guards, frontier judges), with key, settings, template path and SHA-256, parser version, seeds, candidate list and recusal map.
  - Remove the local-only claim and `max_answer_chars`.
