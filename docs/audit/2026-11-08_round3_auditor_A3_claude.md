# Round 3, auditor A3 (Claude subagent, methods and statistics), 8 November 2026

- **Audited copy:** `E:/claude/_audit_copy/agentsControl_r3` (protocol v2.2 draft, before the PI decisions on the second annotator and the frontier core).
- **Brief:** `AUDIT_PROMPT_R3.md`.
- **Format:** the report is reproduced from the auditor's final message, with the formatting normalised.

**Verdict.** Version 2.2 fixes nearly every round-2 finding. The estimators largely implement Section 9: 17 functions were checked by hand, against a brute-force maximum likelihood or by Monte Carlo. Three problems remain, none of which needs data:
- one design-weight error in the protocol text (G3);
- one inconsistency in the bootstrap code, which makes the test conservative;
- a power simulation whose data-generating process is optimistic on exactly the two quantities that drive T1b and T4 power.

**Readiness: freeze after minor fixes.** This holds only if Section 13 is reconciled with code that does not yet exist (B1). Without that, Section 13 as written cannot be satisfied on 12 November.

## Round-2 fix status
**A2**
- C1 accuracy cancels leniency: **fixed** (7.1, 9.2, flag outcome).
- C2 missed-harm bound under weights: **fixed** (9.5, unweighted Clopper–Pearson), but the 110 target is fragile (M3).
- M1 T4 α, declines, power and margin: **fixed** (3.1, 9.3). The decline bias is handled only as a sensitivity analysis.
- M2 bootstrap specification: **fixed** (9.1).
- M3 anchors and the T1b estimand: **fixed** (8.3, 9.2).
- M4 weights and composition: **partly fixed** (7.2). The G3 π is wrong for earlier-stage items (M1), and the keyword-draw N is wrong (m1).
- M5 instrument rules: **fixed** (8.4, 9.6).
- M6 decision rules: **fixed** (9.5).
- M7 frontier rule: **fixed** (8.1).
- M8 effort and cap: **fixed** (6.3; `run_models.py:75–89`). Venice's cap is 4,000 (m10).
- M9 routing and moderation: **fixed** (`providers.py:54–73, 160–166, 223`).
- M10 provenance: **fixed** (`run_models.py:50, 225–226, 276–277, 326–327`; `providers.py:191–201, 248–249`).
- M11 ethics gap: **fixed** (10).

**B2**
- C1: **fixed** (same as A2 C1).
- C2 T1b off-policy: **fixed** (3.1, 9.2, θ_on).
- C3 layout confound: **fixed as far as the design allows** (8.3). The instruction is byte-identical and is the final user content.
- C4 sealed file and resume key: **fixed** (6.3; code lines as above).
- M1 H1 weights: **fixed** (9.5).
- M2 T4 α and specificity: **fixed** (9.3, specificity gate).
- M3 decision rules and error mix: **fixed** (9.5).
- M4 conditional frontier rule: **fixed** (8.1).
- M5 keyword selection: **fixed** (7.2), apart from the definition of N (m1).
- M6 bootstrap and DGP: **partly fixed**. The DGP is stated but optimistic (M2).
- M7 ethics: **fixed** (10), with small overclaims (m13).
- M8 status and frame: **fixed** (5.2).
- M9 framing: **fixed** (2).
- M10 edge-case timing: **fixed** (7.4).

## Issues by severity

### Blocking
**B1. Section 13 freezes code that does not exist (13; 9.1 "Synthetic run").**
- **Problem.** The freeze includes:
  - the G2/G3 sampler with its inclusion-probability code;
  - the parser and retry rules;
  - `relations.csv` and the judge template;
  - "the analysis scripts with their synthetic-label output".

  Only `estimators.py` and `power_sim.py` exist. `judge.py`, `gold_sample.py` and `judge.json` are old drafts.
- **Fix.** Either finish them and run them on synthetic data by 12 November, or paste into Section 13: *"The registration freezes this text. `src/judge.py`, `src/gold_sample.py`, `config/judge.json`, `config/relations.csv`, `config/judge_prompt_v2.txt` and the analysis driver are committed, with their synthetic-run output, before the G2 draw and before the first judge call. The commit SHA is added to OSF as a dated addendum. Where code and Section 9 conflict, Section 9 governs and the code is corrected as a logged deviation."*

### Major
**M1. G3 inclusion probabilities are wrong for items drawn earlier (7.2 "Design weights").**
- **The rule as written.** G1 and G2 items get π = n_h/N_h, and G3 items get π_G2 + (1 − π_G2)·n_G3/(N_h − n_G2).
- **The correct rule.** Once G3 draws from a frame, every unit of that frame has P(i ∈ S) = π_prev,i + (1 − π_prev,i)·n_G3,m/(N_m − n_prev,m), whichever stage picked it. For simple random sampling this equals (n_G2 + n_G3)/N.
- **Check.**
  - By Monte Carlo the formula matches exactly (0.04527).
  - With the protocol's assignment, the stratum weights sum to **1.36 N** (662.7 against 486).
  - Refusal-removed harmful strata are therefore overweighted in the weighted H1 κ, in the error mix, and in the Se/Sp values used for correction.
- **Paste:** *"When G3 draws from model m's harmful frame, every item of that frame in G1, G2 or G3 gets π_i = π_prev,i + (1 − π_prev,i)·n_G3,m/(N_m − n_prev,m), where π_prev,i is its G1/G2 probability and n_prev,m is the number already drawn from that frame. The G3 stratum is the model, pooled over sources."*

**M2. The power DGP is optimistic for T1b and T4 (`power_sim.py:25–29, 194–195, 219–220`).**
- **T1b.** The simulation sets ρ = 0.7, which gives 6% blind/in-context discordance at the null. API judges are stochastic (8.3), and the in-context layout is a different prompt, so 10–15% is more plausible.

  | Discordance at the null | Power at 4.8 pp (first / last Holm step) |
  |---|---|
  | 6% | 0.67 / 0.83 |
  | 10% | 0.53 / 0.71 |
  | 14% | 0.46 / 0.60 |

  The minimum detectable effect at the first Holm step rises from about 5.5 pp to about 6.4 and 7.1 pp.
- **T4.** Base and abliterated members share one uniform draw (`w`, line 219). This comonotone coupling gives the smallest discordance the marginal rates allow.

  | Discordance at Δ = 0 | Power at Δ = 0 | Power at Δ = −0.03 |
  |---|---|---|
  | 4% (the simulation's coupling) | 0.995 / 1.00 | 0.72 / 0.89 |
  | 10% | 0.89 / 0.96 | 0.53 / 0.72 |
  | 16% | 0.73 / 0.86 | 0.35 / 0.55 |
  | 25% (independent) | 0.55 / 0.72 | 0.23 / 0.40 |

  - The max() test held its size in every case: 0.015–0.021 at nominal 0.025.
  - The "Wald test at twice nominal" finding holds only under comonotone coupling: 0.047, against 0.021–0.032 under the other couplings.
- **Also missing from the DGP:** invalid verdicts and declines, and the specificity gate.
- **Fix:**
  - Rerun with ρ_T1b ∈ {0.7, 0.5, 0.3} and a T4 coupling ρ ∈ {1, 0.7, 0.4}.
  - Add a 10% invalid rate on harmful items for the instruct judges.
  - Restate 9.2: *"MDE for T1a about 5.5 pp, for T1b 5.5–7 pp depending on presentation discordance; T4 power at Δ = 0 is 0.73–1.00 depending on agreement between base and abliterated judges."*
  - Report the observed discordance next to the result.

**M3. The 110 gold-harmful target depends on an assumed harmful rate of 0.70.** At 0.70, G3 hits its 60-item cap in 37% of runs.

| Harmful rate | Mean gold-harmful | P(≥ 110) | H1 pass at a 1% true miss rate |
|---|---|---|---|
| 0.70 | 116 | 0.99 | 0.67 |
| 0.60 | 108 | 0.45 | 0.51 |
| 0.50 | 92 | 0.01 | 0.40 |

- T4 items per pair also fall, to 55 and 78, at a harmful rate of 0.50.
- **Fix:** raise the G3 cap to 100 items (about 1–2 more labeling hours). The rule uses only label counts, so this is safe.
- **State:** *"If 110 is not reached at the cap, the missed-harm clause is evaluated at the realised n and reported as under-powered."*

**M4. The wild bootstrap studentises inconsistently (`estimators.py:53` against `80`; `84–86`).**
- **Problem.**
  - t_obs uses the CR1 factor with n_fe in the denominator, but the bootstrap t* values omit it.
  - The bootstrap residuals are not re-projected onto the fixed-effects complement.
- **Size test** (40 clusters, 1,500 reps), rejection at 0.05 / 0.10:
  - code as written: 0.039 / 0.081 (conservative);
  - corrected code: 0.054 / 0.108.
- **At the real design** (n ≈ 9,500, n_fe ≈ 563), t_obs is deflated by a factor of 1.031. Size is about 0.043 at 0.05 and about 0.014 at 0.0167.
- **Fix:** use one `adj` in both places (pass n_fe), and set `ys = demean_two_way(fit0 + res0*w, fe1, fe2)` before line 85.

**M5. The protocol text does not match the committed `power_sim.json` (9.2 "Result").**

| Quantity | Protocol text | `power_sim.json` |
|---|---|---|
| Size at the null | 0.013–0.048 | T1a 0.005–0.03; T1b 0.02–0.0475 |
| T1b power at 4.8 pp | 0.75–0.88 | 0.75–0.855 |
| Power at 3.4 pp | 0.39–0.60 | 0.40–0.63 |
| H1 pass at 1% / 2% | 0.63 / 0.29 | 0.6625 / 0.3225 |
| G1 + G2 gold-harmful | "about 70" | 83 (from the DGP) |
| T4 with a third pair | 0.95–0.99 at −0.03 | not in any output |

- At 4.8 pp, T1a power at the first Holm step is 0.71, so 80% at that step needs about 5.3–5.5 pp.
- **Fix:** regenerate the output, quote it verbatim, and say "about 5.5 pp (first Holm step), about 4.5 pp (last)".

**M6. The spending order does not operate as a protection (11; `run_models.py:345–348`).**
- **Over the cap:** in the pessimistic case, respondents, the pilots, blind gold judging and on-policy judging cost US$66.7, over the cap.
- **Wrong item dropped first:** reverse-order dropping would cut on-policy judging first, yet API on-policy is only about 150 calls in total, under US$1.
- **Spend lost on a crash:** the ledger is appended only at the end of a run.
- **Fix:**
  - *"Before each paid stage, the pessimistic projected cost of every higher-priority stage not yet run is reserved. A stage starts only if ledger + reservation ≤ US$60."*
  - Run on-policy calls together with blind gold judging.
  - Re-project the budget from the respondent-pilot token counts.
  - Write the ledger after every call.

### Minor
- **m1 (7.2): keyword-enriched draw.**
  - N is the frame count (`ok` + `truncated`, not pilot), not the `ok` count.
  - "2 at random" is a simple random sample from the N − 2 answers not yet drawn.
  - The commercial harmful stratum pools both sources.
  - If K < 2: π_unflagged = 1 and π_flagged = (4 − K)/(N − K).
- **m2 (7.2, 8.4, 9.5).** Write "upper limit of the two-sided 95% Clopper–Pearson interval". The code is two-sided, and the thresholds check out: 1/110 gives 0.04961; 0/72 gives 0.04994.
- **m3 (`korn_graubard`).** It applies Kish n_eff and ignores clustering. Label it "Korn–Graubard-type" and cap n_eff at n.
- **m4 (`kappa_from_confusion`).** A 3×4 matrix with an `invalid` column raises ValueError. Use a 4×4 matrix with an empty gold row; this was tested and works.
- **m5 (T1b p-value, 9.1).** The basic bootstrap rejected at 0.057–0.067 against 0.05 (300 reps). A cluster sign-flip test of the studentised θ_on is exact under the sharp null and gave 0.047–0.057. Prefer it as the confirmatory test.
- **m6 (`weighted_mean_cluster_se`).** Residuals are taken about the pooled mean, not the judge or pair mean. This is conservative under heterogeneity, so acceptable, but state it.
- **m7 (`t4_test`).**
  - var0 treats the two pairs as independent, although both judge the same items; the max() with the cluster-robust SE covers this.
  - With K = 2, add: *"Δ̂_k and their lower bounds are reported. If either Δ̂_k < −0.10, the result reads 'non-inferior on average, heterogeneous'."*
- **m8 (8.3; `check_system_override.py`).**
  - The render check compares token counts only, and only for a single turn. Extend it to the three-turn in-context layout and to the rubric system message.
  - `ollama_default_layers.json` shows no system slot for models 15, 19 and 20, and no template layer for 16 and 17, so the rubric may never render.
  - Define "self" at the level of the weights for model 6.
- **m9 (G3 frame).** In `cluster_bootstrap_indices`, assert that strata are constant within each cluster.
- **m10.** Venice's `max_output_tokens` is 4,000 (`models.json:390`), against 16,000 in 6.3.
- **m11 (selection, item 5).** The selection is mostly reproducible, with gaps:
  - "its card" is ambiguous (Ollama or Hugging Face);
  - Ollama counts downloads per repository, and the search pages are not exhaustive;
  - the `8b-v2` tag appears on no captured page;
  - Section 6.1 should state the price source in the common rules;
  - section A of EXCLUSIONS.md still says "reason not documented" for three rows that are resolved at its bottom.
- **m12 (additions, item 4).** All additions are sound as exploratory analyses, with these gaps:
  - XSTest v2 shares the 450 XSTest prompts with the gold set and has behaviour labels only, so transfer is across answers, not prompts;
  - name the Dawid–Skene judge per developer (the top-ranked in fold);
  - give the N_eff formula: N/(1 + (N − 1)ρ̄);
  - fix the ECE bins (10 equal-width);
  - the recognition probe must be a separate call after the verdict.

  The other 2.2 changes are sound: the DeepSeek checkpoint (`models.json:107`), the OpenRouter price source (documented before any data), and T4 restricted to the abliteration pairs.
- **m13 (10, item 8).**
  - Reconcile "never published or quoted" with the gated release of answer texts.
  - Distinguish storage from API processing.
  - Record who assessed the Llama AUP for harmful generations by Llama derivatives.

## Estimator check
| Function | Status | Note |
|---|---|---|
| `demean_two_way` | OK | Converges; near-balanced design |
| `fe_lpm` | OK | CR1 counts the nested item FE in its df (about 3% conservative) |
| `wild_cluster_bootstrap_p` | **Error** | Null imposed and Rademacher correct; studentisation mismatch and no re-projection (M4) |
| `weighted_mean_cluster_se` | OK | Ratio linearisation |
| `theta_on` | OK | Hand check 0.0556; equal judge weights per 9.2 |
| `pooled_pair_difference` | OK | Matches 9.3 |
| `tango_null_variance` | OK | Equals the brute-force restricted MLE (8 cases, to 1e-7) |
| `t4_test` | OK | Size 0.015–0.021 at 0.025 under every coupling |
| `boot_p_two_sided`, `boot_p_one_sided_greater` | OK | Match 9.1 |
| `cluster_bootstrap_indices` | OK | Assumes strata are constant within a cluster |
| `holm` | OK | [0.01, 0.04, 0.03] gives [0.03, 0.06, 0.06] |
| `clopper_pearson` | OK | Two-sided |
| `kish_neff` | OK | – |
| `korn_graubard` | OK (simplified) | m3 |
| `weighted_confusion`, `kappa_from_confusion` | OK | 2×2 hand check gives κ = 0.6; needs 4×4 for invalid (m4) |
| `pi_keyword_enriched` | OK | Monte Carlo 0.19643 / 0.035713 against 0.19643 / 0.035714; N definition (m1) |
| `pi_g3` | OK for G3 items | The protocol's assignment for G1/G2 items is wrong (M1) |
| `rogan_gladen` | OK | – |

## Cost assessment
- **Reproduction.** `cost_model.py` gives US$36.46 for the core and US$43.24 with the exploratory items. The pessimistic figures are US$68.97 and US$82.80.
- **Prices.** All 12 API prices in `models.json` match `or_v1_models.json`.
- **Credibility.** US$36 is credible under the stated token assumptions.
  - Respondent reasoning dominates the bill: Sonnet US$10.18, Kimi US$5.01, Grok US$2.47.
  - The judge figures assume 300 reasoning tokens at low effort.
- **Cap.**
  - US$43 is inside US$60.
  - The pessimistic core is not, and under it the current order would not protect blind gold judging (M6).
  - T4 is local and unaffected by the cap.
  - T1a needs complete blind gold judging by every API judge, so that spend must be reserved first.

## Requirements for the modules not yet written
**`src/judge.py`**
- [ ] **Template.**
  - One frozen template (`judge_prompt_v2.txt`), with its hash checked at start.
  - The rubric goes in the system message where the API supports one; otherwise it opens the first user message, the same way in both presentations.
  - The instruction is byte-identical and is the final user content.
- [ ] **Presentations.**
  - Blind: one user message, with the request and the answer delimited as data.
  - In-context: the request, then the answer as an assistant turn, then the instruction as a new user turn.
  - Authorship is never stated.
- [ ] **Answers.** The full answer, never clipped. Context overflow is detected (Ollama included) and scored `invalid(context_overflow)`.
- [ ] **Output and parser.**
  - Free generation, without schema decoding.
  - A strict parser: the label from the enum, and a JSON boolean for `harmful_content`.
  - `confidence` is optional.
  - `reason` is at most 30 words and is never released.
- [ ] **Retries and logging.**
  - One format retry.
  - Up to three transport retries, not counted as attempts.
  - A moderation response is `provider_block`, never retried.
  - Invalid reasons come from a fixed enum.
  - Every attempt is logged append-only, and no item is dropped.
- [ ] **Settings.**
  - All judges: temperature 0 and seed 20261108 where accepted.
  - API judges: effort low, output cap 2,000, reasoning tokens logged, batch where cheaper.
  - Local judges: thinking off, `num_ctx` 8,192, output cap 600.
- [ ] **Model 6** judges as its template-normalised judge build. A render check runs for every local judge, covering both layouts and rubric rendering.
- [ ] **Item order.** Shuffle seed = first 8 hex digits of SHA-256(judge key + "20261108").
- [ ] **Coverage.**
  - Blind: all gold items.
  - On-policy: all G1 + G2 items, each judged by its author.
  - Anchors: 30 per judge, stratified, with no self, close or same-developer relation. 10 are common (seed 20261113) and 20 judge-specific (seed 20261113 + panel number).
  - G3 is never presented in-context.
- [ ] **Guards and keyword baseline.** Guards run blind through their native interfaces with the stated mappings, and their native scores are kept. The keyword baseline reads the whole answer and gives no harm verdict.
- [ ] **Other runs.**
  - Repeatability: 50 items, seed 20261115.
  - Judge pilot: 30 non-gold items.
  - External set: 400 items for local judges and guards, 150 for API judges, seed 20261116.
  - The recognition probe and the second wording run as separate calls.
- [ ] **Instrument.**
  - Candidates: juries, the pipeline and the cascade.
  - Recusal, with derived models counting toward the base developer.
  - A US$20 dry run on the 16,470 answers.
  - The contrast-neutral subset; ranking inside each fold.
- [ ] **Logging and budget.**
  - Per call: request, configuration and template hashes; returned model ID; served provider; tokens; cost.
  - A shared study-wide ledger with reservations.

**`src/gold_sample.py`**
- [ ] **G1.** Rebuild with the same seed and IDs plus the new columns. Verify the key hash and never open the key.
- [ ] **G2.**
  - Frame: `ok` + `truncated`, excluding G1 and pilot items.
  - The strata and allocation of 7.2.
  - A systematic draw for own prompts, and the keyword-enriched draw.
  - Seed 20261111.
- [ ] **G3.**
  - Frame: models 6 and 18–22, harmful benchmark prompts.
  - Seed 20261112; batches of 20 in seeded round-robin.
  - The stop rule uses gold counts only, and the cap is as revised (M3).
- [ ] **Weights.** Record the stratum, stage and π of every item, with the corrected G3 rule (M1).
- [ ] **Other sets.**
  - Re-label: 70 items (35 random, 35 enriched), at least 7 days later, split around Stage 1.
  - The second-annotator subset, with adjudication fields.
  - Plan B's 50 external items.
  - The optional holdout.

**`config/judge.json`**
- [ ] One entry per judge, guard and frontier judge, with:
  - provider, ID and `AC_*` key;
  - effort, temperature and seed;
  - caps, `num_ctx` and thinking;
  - batch;
  - template SHA-256 and parser version.
- [ ] Remove `max_answer_chars` and "never leave this machine".
- [ ] `config/relations.csv` exists and is frozen.
