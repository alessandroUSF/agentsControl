# Round 4, auditor B4 (LLM judges, AI-safety practice, research code), Claude subagent, 8 November 2026
Prompt: `AUDIT_PROMPT_R4.md` on the sanitised copy `E:\claude\_audit_copy\agentsControl_r4`.

**Verdict.** I recommend **freeze after minor fixes**. All four of B3's round-3 blockers are fixed. Of B3's six majors, four are fixed, one mostly and one in part. I verified the estimators by hand and by Monte Carlo. I found no new blocking issue. Before the freeze commit, five short text fixes are needed: M3–M6 below and m4. Two runner defects (M1, M2) can break the US$110 cap. They are code fixes and can come as a logged change, but they must be fixed and tested before the first paid batch.

Everything was read-only. The in-memory tests used fake providers and a fake filesystem, with `python -I -B`. No file was written, and no network, model or API was called.

---

### Round-3 fix status

**B3**
- **B1, model-6 CRLF: fixed.** `make_judge_alias_m6.py:52` writes LF. The Modelfile has no CR. Template, parameters and counts match model 4 in all six layouts.
- **B2, selection wording: fixed.** The common rules in 6.1 now define price and size, and `EXCLUSIONS.md:81, 88` discloses the change.
- **B3, README, `judge.json` and rubric: fixed.** One residual: the uplift definition differs between the rubric and 7.1 (m7).
- **B4, freeze package: fixed as a deferral.** Section 13 now commits the missing code in a dated addendum.
- **M1, batch and caching: fixed.** Batch paths are at `run_models.py:376–446` and `providers.py:168–193, 242–279`; `cache_control` at `providers.py:146–147`; the spending order is reordered. The new problem this creates is M2.
- **M2, ledger: mostly fixed.** Per-call lines (`:360–364, 479–480`), the lock (`:216–222`), `settle_amount` (`:205–213`), max(list, reported) (`:463`) and 900 s timeouts are in place. Residuals: M1 and m2.
- **M3, moderation: fixed.** Markers, `SuspectedBlock` and native finish reasons are at `providers.py:61–98, 351–352`. Residual: m1.
- **M4, adapter defects: fixed.** Anthropic `system=` at `:144–147`; `store=False` at `:226`.
- **M5, local provenance: fixed.** Digests are pinned and asserted (`run_models.py:233–235`) and enter the configuration hash. The judge-build digest (`models.json:103`) is not yet asserted by any code; that is now a `judge.py` requirement.
- **M6, ethics: in part.** (a)–(e) are fixed. (f), the zero-retention fallback, is defined for respondents only (M4).
- **Minors m1–m13:** all fixed or adopted, with three residuals:
  - m6 and m8 hold only for token counts (M3);
  - the m12 docstring at `make_judge_alias_m6.py:10` still says "four layouts";
  - the guard's judge mode logs no manifest (`run_with_memory_guard.py:39`).

**A3**
- **B1: fixed** (Section 13 addendum).
- **M1, G3 π: fixed.**
- **M2, DGP: fixed.** Residuals are under "Power".
- **M3, G3 cap: fixed.**
- **M4, bootstrap: fixed.**
- **M5, text against JSON: fixed.**
- **M6, spending order: fixed in the text, partly in code** (M2).
- **Minors m1–m13: fixed.** m5 is adopted as the sign-flip test.

---

### Issues by severity

**Blocking:** none.

**Major**

**M1. Batch settlement can be applied twice, so the ledger can undercount** (`run_models.py:394–446`).
- **Problem.** The "collected" marker is written last (`:441–444`), after `batch_delete` (`:440`). If the delete fails, a second `--collect` writes every record and call line again and subtracts the reservation a second time.
- **Test with a fake provider.** Reservation 0.160, true spend 0.010. After one failed delete and a successful re-collect, the ledger stood at **−0.140**, and 2 prompts had 4 raw records.
- **More gaps.**
  - The reservation line is written only after `prov.batch_submit` returns (`:385–386`), so a crash in between loses a batch that was submitted.
  - With no `--models`, `--collect` runs without the lock (`:316, 328`).
  - Nothing stops a second batch for a model that already has one uncollected.
- **Why it matters.** The cap can be overrun by a whole reservation: the stage-3 Sonnet batch alone reserves US$48.
- **Fix.**
  - Write the reservation before submitting.
  - Append `{"settled": batch_id}` right after the settlement line, and refuse to collect when it exists.
  - Make deletion a separate, retryable `--purge BATCH_ID` that logs what it deleted.
  - Always take the lock.
  - Refuse to submit while a batch for the same model is unsettled.

**M2. The worst-case batch reservation blocks stage 3 in the pessimistic case** (`run_models.py:381, 509–512`).
- **Problem.** Every batched prompt is reserved at the full 16,000-token cap.
  - Stage 3 (600 prompts) reserves Sonnet US$48.02, Haiku US$2.40 and GPT-5.6 Luna US$5.76: US$56.18 in total.
  - After pessimistic stages 1–2 (US$74.85), only US$35.15 is left. Sonnet's batch is refused, and the `break` at `:512` also skips the other two models.
  - If the pilot truncation rule doubles the cap, the Sonnet reservation becomes US$96, and stage 3 fails even in the expected case.
  - The stage-level reservation rule of Section 11 exists in no code.
- **Why it matters.** H2 and H3 sit in stage 3, which Section 11 says is protected.
- **Fix (paste into 11):** *"Batches are submitted in chunks whose worst-case reservation fits the headroom left after the stage reservations; a chunk is submitted only after the previous chunk is settled. Stage reservations are written to the ledger as `stage_reservation` lines and released when the stage starts."*

**M3. Pair 15–19 is not shown to render identically under the judge settings** (8.3; `check_system_override.py:54–60`).
- **Problem.**
  - The check compares token counts only, and it never sends `think`.
  - llama3.1:8b, qwen3:8b and qwen3.5:4b give the same count vector (16/29/53/48/72/35; `ollama_default_layers.json`), so equal counts cannot tell even different model families apart.
  - In 15–19 the templates differ in form: Ollama's built-in renderer against the build's Jinja template. Neither the rendered prompt nor `think: false` was compared.
- **Why it matters.** If model 19 ignored `think: false`, it would hit the 600-token cap and produce invalid verdicts for one member only. T4 is confirmatory, so the claim that the members "differ only in weights" must be shown.
- **Fix (paste into 8.3):** *"Before any judging, each T4 pair is rendered with the exact judge requests (rubric system message, both presentations, think=false, explicit options); the rendered token IDs (or server-logged rendered prompts) and the GGUF architecture, tensor shapes and tokenizer metadata must be identical. A failing pair is removed from T4 before any verdict exists; T4 then runs on the remaining pairs with the same margin and Holm entry, and the failed pair is descriptive."*

**M4. No zero-retention rule for judges** (6.3 line 294; Section 10).
- **Problem.** The fallback ("run only comply-expected prompts") applies to respondents. OpenRouter judges 7, 8, 10, 12, 13, 14 and 22, the API guard and Muse Wonder all receive harmful answers on every gold item. With `zdr` set (`providers.py:325–326`), a missing endpoint returns an error that is retried as a transport error.
- **Fix (paste):** *"A judge, guard or frontier judge with no zero-retention endpoint at its judge pilot judges no item and is reported as missing (dropped from T1a and RQ1), unless before stage 2 the PI records in `PROVIDER_TERMS.md` the decision to run it under the endpoint's stated terms."*

**M5. The specificity gate does not define its items** (9.3 line 638).
- **Problem.** The text says "gold non-harmful items", while the simulation uses non-harmful answers to harmful prompts (`power_sim.py:222, 241–244`). This is an analyst degree of freedom in a confirmatory gate.
- **Fix (paste):** *"Sp_k is the share not flagged as harmful among gold non-harmful items on refuse-expected prompts (G1 + G2 + G3) with valid verdicts from both members, with the T4 author exclusions; the gate uses (1/K)Σ_k(Sp_abl,k − Sp_base,k) ≥ −0.10."*

**M6. Frontier adjudication goes one way, and the frontier judges' relations are misstated** (9.4 line 668; 8.1 line 435).
- **Problem.**
  - Only items where all three frontier judges disagree with gold are re-adjudicated. Corrections can therefore only move gold toward the frontier majority, which inflates agreement for the frontier judges and for judges whose errors correlate with theirs.
  - 8.1 says the frontier judges "inform only the judge × stratum and item effects". In fact Opus 5.5 is same-developer to models 1–2, GPT-6 Astra to 3, 9 and 11, and Muse Wonder to the Meta-derived models 4, 6 and 20. In the T1a sensitivity analysis they therefore also identify β_dev.
- **Fix (paste):** *"Frontier-flagged items are re-labelled blind, mixed with an equal number of random gold items on which the frontier majority agrees with gold, with no judge output shown. `relations.csv` codes the frontier judges' developer relations, and frontier–gold agreement is also reported excluding same-developer items."*

**M7. The published call log can contain harmful text** (`run_models.py:366–372, 476–477`; `.gitignore` says logs are published).
- **Problem.** The call log drops only `text`. `error_body` (up to 2,000 characters) is kept, and OpenRouter moderation errors carry a `flagged_input` excerpt. For a judge call, that excerpt is the harmful answer, so the README claim "WITHOUT the answer text" is overstated.
- **Fix.** Keep `error_body` only in `results/raw/`. In the call log, store its SHA-256, the status and the matched marker.

**Minor**

- **m1.** The marker `"1301"` matches as a bare substring (`providers.py:64, 92`), and moderation markers are checked before parameter errors. In my test, a 400 `max_tokens` error whose request ID contained "1301" became `moderation_block` and would never be retried. Match the code field with a regex instead.
- **m2.** `settle_amount` treats TypeError and ValueError as "failed before sending" (`run_models.py:209`). An OpenRouter 200 response with `choices: null` raised TypeError after the call had gone out, and it was settled at US$0. Settle anything raised after `create()` returns at the reserved amount.
- **m3.** Cache tokens are priced at the full input price (`providers.py:205–208`; `run_models.py:462`). This is conservative, but the ledger runs ahead of the cost model by about US$4 in stage 2. Price cache reads and cache writes (1.25×) explicitly.
- **m4.** Section 8.3 says the judge pilot covers "every API and frontier judge", but Section 11 puts the frontier pilot in stage 4. Move it into stage 2: US$1.89 expected, US$3.75 pessimistic.
- **m5.** There is no judge-cap rule. Opus 5.5 cannot switch thinking off, and thinking counts toward the 2,000-token cap. Paste: *"If >5% of a judge's pilot calls stop at the cap, its cap is doubled before gold judging (logged)."*
- **m6.** Two wording fixes:
  - 9.1 line 560: the sign-flip test is exact only under the sharp null that signs are symmetric within each cluster. Under the stated weak null (θ_on = 0) it is a Rademacher wild cluster bootstrap-t with the null imposed, valid asymptotically.
  - 9.2 line 593: nothing is randomised; every pair gets both presentations. θ_on identifies a presentation effect, so a self-specific reading needs β_int (θ_on against θ_off), which should be reported with its CI next to T1b.
- **m7.** RUBRIC "uplift" adds "beyond what a short web search gives", which 7.1 does not have. Align the two before the freeze, because uplift decides what is withheld from the release.
- **m8.** Plan A: within the half selected because the first annotator labelled it harmful, κ for the harm field is degenerate. Report positive agreement there. The sheet must mix the two halves and not reveal how it was composed.
- **m9.** Model 6's self items come from a respondent build that has a built-in prompt and a different quantisation. Add T1a and T1b sensitivity analyses that exclude judge 6.
- **m10.** `prepare_data.py:40–44, 112–113`: the framing templates are identical placeholders, and `own_sample.jsonl` is rewritten on every run. Assert that the three framings differ, and pin the file's hash at the freeze.
- **m11.** Small inconsistencies:
  - `models.json:292, 309` use quantisation-suffixed tags, against Section 6.2;
  - `make_judge_alias_m6.py:20` defaults to the Q4_0 source;
  - `cost_model.py:144` still uses the old G3 cap of 60.
- **m12.** Batch files are deleted only after a successful collect. Add a purge after 48 h for anything not collected. State that `store=false` does not turn off abuse-monitoring retention.

**Item 5, in brief.**
- The 6.1 rules now reproduce the panel.
- Model 18 passes the narrowed rule through its linked HF card (base Qwen/Qwen3-8B, abliteration).
- Model 19's page states "Not fine-tuned", and kiwi_kiwi is rightly ineligible.
- The disclosure of the post-snapshot size definition is enough. Slot 21 is descriptive and in no confirmatory test, so no sensitivity run is needed. Do add the technical reason (20 GB download limit, 6 GB GPU) to `EXCLUSIONS.md`.

---

### Estimator check
| Function | Status | Note |
|---|---|---|
| `fe_lpm`, `demean_two_way` | OK | CR1 counts nested item FE (conservative, about 3%) |
| `wild_cluster_bootstrap_p` | OK | Same `adj` (`:81`), so the p-value does not depend on the factor; re-projection at `:85` |
| `theta_on` | OK | Equal judge weights |
| `theta_on_signflip_p` | OK | Flipping signs jointly within clusters is right, and needed when one cluster holds several judges' pairs or framings. My simulation with the design's judge sizes and B = 999: size 0.012–0.014 at α = 0.0167; it loses 2–3 power points against z. Wording: m6 |
| `weighted_mean_cluster_se` | OK | Residuals about the pooled mean (conservative; stated) |
| `t4_test`, `tango_null_variance`, `pooled_pair_difference` | OK | Size at the margin with heterogeneous pairs (Δ_k = −.10×3; 0/−.10/−.20; .05/−.05/−.30), couplings 1.0 and 0.4: 0.0175–0.0275 at a nominal 0.025. The gate, the heterogeneity reading and 2·p₁ belong to the unwritten driver |
| `cluster_bootstrap_indices` | OK | Raises when strata vary within a cluster |
| `holm`, `clopper_pearson` | OK | Two-sided; 1/110 gives 0.04961 |
| `korn_graubard` | OK | n_eff capped at n |
| `kappa_from_confusion` | OK | 3×4 matrix padded |
| `pi_keyword_enriched` | OK | Monte Carlo matches for K = 0, 1 and 6. The self-check's K = 1 gap is noise from reading a single unit |
| `pi_g3` | OK | Two-source without-replacement MC: 0.3218/0.3221 and 0.3673/0.3669; weights sum to N |
| `rogan_gladen` | OK | – |

**The self-checks are too easy.**
- The `pi_g3` check is Bernoulli arithmetic, not a draw without replacement.
- The sign-flip null uses i.i.d. symmetric D with B = 199, which cannot resolve α = 0.0167. The output (0.03 at 0.05) is conservative because of that coarseness.
- Add: a stratified two-stage draw without replacement; a weak null with the design's judge sizes and B ≥ 999, reporting rejection at both 0.0167 and 0.05; T4 with heterogeneous pairs; and a double-collect ledger test.

### Power and cost assessment

**Power.**
- The numbers in 9.2 match `power_sim.json`. Interpolating the JSON gives minimum detectable effects of 5.7/4.8 pp (T1a) and 5.7, 6.5 and 7.0 pp (T1b, first Holm step), as stated.
- The DGP is now reasonable. Three optimistic points remain:
  - T1b uses z, not the sign-flip test (about 2–3 points);
  - invalid verdicts are random, drawn only for the blind presentation and only for the base T4 member (`:192, 234`);
  - nothing makes the in-context presentation itself fail.

**H1 missed-harm clause.**
- Under the current two-sided rule, pass probability *falls* as n grows: at a 1% true miss rate it is 0.70 at n = 110 and 0.63 at n = 130, because x ≤ 1 stays the limit.
- Recommendation: keep the three-outcome rule, which carries the version-1 hypothesis, but test "< 5%" with the exact one-sided binomial test at α = 0.05. H1 is an intersection–union test, so no adjustment is needed.
- Set the G3 target to 126 gold-harmful items and the cap to 120 (about 1–1.5 more labeling hours). Two misses then pass, and the pass probability becomes **0.87 at a 1% true miss rate and 0.54 at 2%**.
- Always report the estimate with its two-sided CP interval.

**Cost.**
- `cost_model.py` reproduces the Section 11 table to the cent.
- The "as coded" column matches the code paths: batch for direct respondents only, OpenRouter synchronous, direct judge prefixes cached.
- Anthropic's current reference gives a 512-token cache minimum for the 5.5 models, so the 1,500-token prefix caches. The 1.25× cache-write premium is ignored.
- If every stage-2 judge call hit the 2,000-token cap, stage 2 would cost US$75 (expected) or US$89 (pessimistic). The reservation rule must therefore use the judge cap.

**What is cut.**
- Pessimistic: stage 4 drops to about 29% of its items (about US$20 of US$70), and stages 5–7 are dropped.
- Expected: stage 7 loses about US$6.5 with a local instrument, or about US$14 with an API instrument.
- Section 11 states this honestly, except that the protection of stage 3 fails as coded (M2) and the frontier pilot sits in the wrong stage (m4).

### Requirements for the modules not yet written (checklist; no code, no prompt text)

**`src/judge.py`**
- [ ] Every requirement in the round-3 checklists (B3 and A3).
- [ ] Assert `judge_model_digest` and pass the M3 token-level rendering check before any judging.
- [ ] Send `think` exactly as configured.
- [ ] Never send sampling parameters to Anthropic 5.5 models. Never enable server-side refusal fallbacks. Log `model_returned`.
- [ ] Count a self item for an API judge only if the model ID returned at judging matches the one returned at generation. Report mismatches.
- [ ] Send in-context assistant turns as text only.
- [ ] Interleave blind and in-context calls in a seeded order inside the same time window.
- [ ] Report `provider_block` and invalid rates by presentation and by gold label (Muse Wonder included).
- [ ] Detect context overflow independently. Ollama can truncate without an error, so compare `prompt_eval_count` with a token count made beforehand.
- [ ] Use the shared ledger and lock, reserving at the judge cap; write stage reservations (M2); apply the zero-retention rule of M4.
- [ ] Apply the judge-cap rule (m5). Log memory-guard events in the judge manifest.
- [ ] Run the recognition probe as a fresh call in the blind presentation.

**`src/gold_sample.py`**
- [ ] De-duplicate raw records by (model, prompt, request hash, configuration hash).
- [ ] Exclude the judge-pilot prompts from the G2 and G3 frames.
- [ ] Apply the G3 target and cap as finally set, and record π with `pi_g3` for every frame unit.
- [ ] Plan A sheet: seed 20261118, halves mixed, composition hidden, selection probabilities stored.

**`config/judge.json` and `config/relations.csv`**
- [ ] Code the frontier judges' developer relations (M6).
- [ ] Per judge: `zdr` status, provider pin, digest, render-check result and template SHA-256.

**Analysis driver**
- [ ] Holm entry 2·p₁.
- [ ] The M5 gate, the heterogeneity reading, and a T4 run with K = 2 if a pair fails.
- [ ] β_int reported next to T1b.
- [ ] Sensitivity analyses that exclude judge 6.
