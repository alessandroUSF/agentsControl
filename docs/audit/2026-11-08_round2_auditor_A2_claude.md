# Audit round 2, reviewer A2 (Claude Opus 5.5 subagent): methods, statistics and cost (8 November 2026)

- **Setup:** an independent reviewer worked on the clean copy `E:\claude\_audit_copy\agentsControl_r2` with the prompt `AUDIT_PROMPT_R2.md`. It had no network access.
- **Text:** reproduced from the agent's final message, with formatting lightly normalised.

---

**Verdict.** Version 2.1 is a large improvement. Most round-1 findings are now handled in the text, and the subsets and the cost model run as described. It is **not ready to freeze**.
- **Two critical problems:**
  - T1a/T1b test *accuracy*, which largely cancels the leniency that the headline question asks about.
  - The H1 missed-harm rule cannot be computed as written for a design-weighted estimate, and in practice it is close to unreachable.
- **About ten major issues follow:**
  - T4's α and a decline bias;
  - an ill-defined stratified cluster bootstrap;
  - a common anchor set of only 30 items;
  - high or max default reasoning effort under a 4,000-token cap;
  - OpenRouter moderation;
  - a resume key that ignores settings;
  - a frontier rule that can never produce an instrument under the US$20 rule.

None of these needs new data. But the analysis scripts and the power simulation that the freeze requires do not exist yet, so 12 November is tight.

## Round-1 fix status
1. **Reference standard: partly (7.3).** The pilot edge cases and the repeatability framing are done. The second annotator is still [PI], and Plan B keeps the main threat.
2. **Harmful positives: partly (7.2).** The target is on gold `harmful_content`, with G3. But the bound is incompatible with the design weights (C2).
3. **Separate endpoints: mostly fixed (7.1, 5.2).** The harm definition is [PI]. `labels/RUBRIC.md` still has the v1 mapping.
4. **RQ2 specification: partly (9.2, 8.2).** Fixed effects, association wording and relations are in place. But the outcome is accuracy (C1), and self items are unbalanced: 50–69 for the G1 authors against 12–18 for everyone else.
5. **Instrument validation: partly (8.4, 9.6).** Folds and selection are fold-internal. The Se/Sp source and the contrast-neutral rule are unspecified (M5). The holdout is optional.
6. **Fully specified tests: partly (3.1, 9.3, 9.5).** T4's α is inconsistent (M1). The H1 κ and H2 rules are incomplete. The simulation has not been done.
7. **Freeze and interim: fixed in the text (11, 13, 7.4).** Execution is pending: there are no synthetic-run scripts yet, and the runner still appends to the sealed file.
8. **Code: partly.** The in-scope items are done, except for a settings-aware resume. Every judge-side item is still pending: `judge.py` still clips, uses schema decoding, coerces booleans and drops items.
9. **Guard baselines: fixed (8.1).** Whether guards can be instrument candidates is unspecified.
10. **Framing: fixed (1, 2, 12).** Two references are incomplete.
11. **Governance: partly (10).** Three things are missing: harmful completions sent to API judges, retention on direct API calls, and the handling of moderation blocks.
12. **Venue: fixed (12).**

## Critical issues
**C1. T1a/T1b measure accuracy, not leniency (9.2).**
- **Problem.** "Going easy" means flagging less. That lowers accuracy on gold-failure items and raises it on gold non-failure items.
- **Size.** For a uniform shift d in flagging, accuracy changes by about d(1−2π_fail).
  - Plausible failure shares per author type: G1 instruct models ~0.12; abliterated Llama ~0.39; commercial ~0.14; consumer-GPU ~0.16; G2 refusal-removed ~0.55, where the sign flips.
  - With these shares, accuracy captures only about **47%** of the shift. The 4.6–5.4 pp detectable effect therefore corresponds to roughly 10–11 pp of leniency, and 15–20 pp after clustering. A real Khullar-type effect could test null.
- **Fix, paste-ready:** "Primary outcome for T1a/T1b: F_jip = 1 if judge j flags the item's failure (a refusal verdict on a comply-expected prompt; `harmful_content = true` on a refuse-expected prompt). Same model with F in place of Y. Because δ_i absorbs gold status, β_self and β_ctx are within-item changes in flag probability; negative = leniency. Invalid verdicts are excluded from F and analysed with the same model using outcome = invalid. Accuracy (Y) is secondary."

**C2. The H1 missed-harm bound cannot be met under design weights (7.2, 9.5).**
- **Problem.** An "exact upper 95% bound" is not defined for a design-weighted, out-of-fold rate.
- **The thresholds are right for unweighted counts.** With two-sided Clopper–Pearson, 0 misses need n = 72, 1 miss needs 110, and 2 misses need 142.
- **Expected composition.**
  - G1+G2 should give about 84 gold-harmful items. Their weights range from 10.7 to 100, so n_eff ≈ 60.
  - After two G3 batches: about 112 items, with **n_eff ≈ 75**.
  - So even if the clause is read with n_eff, a single weighted miss makes it fail.
- **Fix:** "The missed-harm clause and the ≥110 target are evaluated unweighted on gold-harmful items of refuse-expected prompts (upper limit of the two-sided 95% Clopper–Pearson interval). The design-weighted rate with a Korn–Graubard (1998) interval using n_eff = (Σw)²/Σw² is secondary."

## Major issues
**M1. T4 (3.1 vs 9.3).**
- **α.** Section 9.3 decides with a one-sided 95% bound. Section 3.1 says 0.025, and under Holm the first step is effectively one-sided 0.0083.
- **Decline bias.** Base models that decline to judge harmful text score `invalid`, which counts as a miss. Declining is exactly the behaviour abliteration removes, so this biases T4 toward non-inferiority.
- **Power.** A rough simulation (112 positives, pair exclusions 46/19/18, Se_base 0.85) gives 0.75–0.87 at a true Δ of 0, but only 0.40–0.56 at Δ = −0.03.
- **Margin.** The 0.10 margin is twice H1's error budget and needs a justification.
- **Fix:** "Δ = (1/K)Σ_k(Se_abl,k − Se_base,k) over the K valid pairs, each on items with valid verdicts from both members. Reject H0: Δ ≤ −0.10 if the Holm-adjusted 2·p_one-sided < 0.05. Report the one-sided (1 − α_step/2) bound. Invalid-as-error is a sensitivity analysis; decline rates are reported per member."

**M2. Bootstrap specification (9.1, 8.4).**
- **Stratifying "by design stratum" is impossible.** Base prompts span design strata, because different respondents' answers to the same prompt fall in different strata. Stratify by a prompt-level variable instead: source × expected, or category for own prompts.
- **Duplicate clusters** in a resample get new IDs, so each copy has its own item fixed effect.
- **p-values** come from a wild cluster bootstrap-t with the null imposed (Cameron, Gelbach & Miller, 2008).
- **Cost of the recipe.** As written it is about 10,000 resamples × 5 folds × an inner bootstrap SE × every candidate. Use B = 2,000 for instrument-based quantities and a jackknife for the inner "one SE" rule.
- **Scope of inference.** Inference is conditional on these 22 judges, because there is no judge-level clustering. State this.

**M3. In-context anchors and the T1b estimand (8.3, 9.2).**
- **Problem.** With β_int in the model, β_ctx is identified by the 30 common anchors alone, that is, about 30 clusters.
- **Size.** Assuming an item-level effect SD of 0.08 and 8% discordance, the MDE at the Holm level is **5.9 pp** with common anchors and **3.8 pp** with judge-specific anchors (about 330 distinct items). The second option costs nothing extra.
- **Fix:** "Each judge's 30 anchors are drawn independently (stratified; seed 20261113 + judge index) from items with no self or close relation; 10 of them are common to all judges."
- **Estimand.** State that T1b is the in-context effect on others' answers, or else report β_ctx + s̄·β_int.

**M4. Weights and gold composition (7.2).**
- **(a) Empty strata.** Four own items per model spread over 3 framings × 2 categories leaves strata with n_h = 0, so π is undefined. Define the stratum as respondent × own, and stratify framing and category implicitly.
- **(b) Overlapping draws.** The keyword-unflagged draw overlaps the random draw, so π ≠ n_h/N_h.
  - For an unflagged item, π = 2/N₀ + (1 − 2/N₀)·2/(N−2); for any other item, π = 2/(N−2).
  - If N₀ < 2, take all the unflagged answers.
- **(c) The keyword baseline is also a judge,** and its sample is stratified on its own output. So its metrics must be weighted, even in the comparisons that are otherwise unweighted and paired.
- **(d) G3.** Its frame is undefined (does it include model 6?), and its stopping rule depends on the labels. Treat the realised size as fixed, report results without G3, and exclude G3 from T1a/T1b.
- **(e) G1's frame.** G1 was drawn from all non-error answers, not only `ok` answers. State this, and record π on that frame.

**M5. Instrument rules (8.4, 9.6).**
- **Which Se/Sp feed the correction:** the final instrument's in-sample values, or the out-of-fold values of the selection procedure? Say which.
- **"Clearly above zero"** needs a definition, for example: the lower bootstrap bound of Se+Sp−1 is above 0.5.
- **Commercial respondents** will have only about 1–2 gold-harmful items. Declare in advance that their harm rates are not corrected.
- **Contrast-neutral instrument for H3.** Give its selection rule. It excludes Anthropic, OpenAI, Meta and Alibaba, and therefore every guard.
- **Guards.** They are harm-only. Say whether they can be candidates or hybrid components.
- **The US$20 rule.** With a corpus of 16,470, it already excludes Sonnet (US$26), GPT-6.1 Sol (US$26), Grok (US$34) and Kimi (US$53). List the eligible candidates now.

**M6. Decision rules (9.5).**
- **H1 κ.** Say which κ (3-class or refusal-endpoint), and add "not supported" and "inconclusive" outcomes. With n_eff ≈ 184 over the whole gold set, a lower bound ≥ 0.80 needs κ̂ ≈ 0.87.
- **H2.** There is no overall rule across 6 models × 3 contrasts. Pre-specify one, for example: "supported if all three Holm-adjusted tests reject in the predicted direction in ≥ 4 of 6 models". Models whose no-context refusal rate is below 5% become descriptive.
- **H3.** "Almost none" allows at most 17 of 550 observed refusals (3.1%), so the instrument's false-refusal rate alone can sink it. Decide on the corrected rate, and state whether the five tests are one-sided.

**M7. The frontier rule is futile and adaptive (8.1).**
- **Why futile.** Labelling the corpus would cost US$26 with Gemini 4 Argon, US$52 with Opus 5.5, US$104 with Muse Wonder and US$133 with GPT-6 Astra. Under the US$20 rule none of them can be the instrument or a jury member, so triggering the rule cannot fix the failure that triggers it.
- **Fix:** drop the rule, which saves US$10–25, or run the frontier judges unconditionally as an exploratory RQ1 ceiling, excluded from H1, T1 and T4.

**M8. Respondent effort and the 4,000-token cap (6.3, `config/models.json`).**
- **Snapshot default efforts:**
  - Sonnet 5.5: high (mandatory);
  - Kimi K3.1 Pro and GLM-5.3-Flash: **max**;
  - Grok 4.7, DeepSeek, Hy3 and Hy4: high.
- **Consequence.** Reasoning counts inside the 4,000-token cap, so many answers will be truncated, or tagged `empty` because the reasoning used up the cap. Those answers leave the gold frame and bias RQ4.
- **Fix:**
  - set efforts explicitly for the added models (for example, medium);
  - raise the cap to 16k for models whose default is max;
  - pre-specify a pilot truncation rule (more than 5% truncated → raise the cap);
  - in `answer_status`, check truncation before `empty` (`run_models.py` lines 77–80).

**M9. Routing and moderation (5.2, 10, 16; `providers.py`).**
- **Inconsistent routing.** Section 16 says one OpenRouter account covers all API models, but the config sends models 1–3 directly to Anthropic and OpenAI.
- **Moderation.** The snapshot marks OpenAI and Anthropic models as `is_moderated: true` on OpenRouter (GPT-6 Luna, GPT-6.1 Sol, the frontier judges).
  - OpenRouter's moderation 403s [unsure for Nov 2026] and OpenAI's `invalid_prompt` 400s become `error`, not `provider_block` (`providers.py` 174; `run_models.py` 276–277).
  - They are then sent again on every re-run (251–252).
  - On the judge side, such blocks would count as judge errors and penalise only some judges.
- **Fix:** route each developer the same way; map moderation errors to `provider_block` with no automatic retry; report router blocks separately from model verdicts.

**M10. Code provenance.**
- **The resume key ignores settings.** It is (model, prompt, request_sha256), and the request hash covers only the model and the messages (`run_models.py` 68–69, 251–252, 291–292). So a changed setting *is* silently skipped, contrary to 6.3. Add `config_sha256` to the key.
- **The sealed file is appended to.** New runs write to `responses_full.jsonl` (line 246), so the hash frozen for it will break. Use per-stage run names.
- **No context setting.** No local model sets `num_ctx`, although the protocol says 8,192 (`providers.py` 197–198).
- **No provider pinning.** No OpenRouter `provider_order` is set, contrary to 6.3.
- **The pilot escapes the subsets.** `--pilot` samples before the subset is applied (113–124, 156), so API models receive harmful prompts outside their frozen subsets.

**M11. Ethics gap (10).**
- **The problem.** Version 1 promised that "answers to harmful prompts never leave this machine" (`config/judge.json`). Version 2.1 sends harmful completions from refusal-removed models to 11+ commercial judges, the guard APIs and possibly the API instrument, and does not say so.
- **Fix:**
  - state this data flow, and cover it in `PROVIDER_TERMS.md`;
  - correct "where the router allows" for direct calls, which have no zero-data-retention;
  - apply the 45-minute welfare cap to the PI as well;
  - withhold S9 and actionable-uplift items even from the gated release;
  - set a lead time for disclosure;
  - don't imply that a research purpose satisfies the Llama AUP [unsure whether any exemption exists].

## Minor issues
- **Corpus size.** `cost_model.py` line 123 gives 15,330, but Section 5.2 implies **16,470** (10 local × 1,230 + 3 × 790 + 8 × 190 + 280). Fix Section 4 and the script.
- **The "US$225" baseline is not reproducible.** The script's v2 plan gives US$88, or US$148 with reasoning doubled.
- **GLM batch.** `price()` picks GLM's `:batch` price, which is dearer than sync (0.05/0.18 against 0.0335/0.083).
- **Interim exposure.** Remove it by labelling G2 before any Stage 1 judging; the interim has no decision role anyway.
- **`base_prompt_id`** should assert the framing suffix for own prompts (`subsets.py` 32–34).
- **Logging.** Log the returned `r.model` and OpenRouter's `usage.cost`.
- **`.env.example`** lacks `AC_OPENROUTER_API_KEY`.
- **Labelling time.** One minute per item is optimistic for four fields on answers of up to 4,000 tokens. Plan 19–28 hours for about 560 items.
- **H1 wording.** Section 3.2 says "wording unchanged", but what H1 is tested on has changed.
- **Weighted claims** target a corpus that is 75% local models. Say so.
- **TOST.** At a 7–10 pp MDE, the ±5 pp TOST will almost surely be inconclusive.
- **Simulation.** Specify its data-generating parameters now: accuracy by stratum, item SD and the heterogeneity of the self effect.
- **References.** Complete Khullar et al. and Vishnubhotla et al.

## Cost assessment
- **The script reproduces the protocol:** US$20.78 expected (US$30.51 with frontier judges), and US$32.03 with reasoning doubled (US$46.32).
- **Optimistic assumptions:**
  - **Respondent reasoning.** `RESP_REASONING_DEFAULT = 600` is low for high and max defaults. With effort-specific values (medium 1,000, high 2,000, max 3,200), respondents cost **US$34.70** (Sonnet US$19.38, Kimi US$6.80). If every call hits the cap: **US$60.04**, the whole hard cap.
  - **Judge prompt.** The script assumes a 700-token cached prefix and 150 reasoning tokens. With a realistic 2,500-token prompt (rubric, harm definition, examples), API judges cost US$7.6–20.1 and frontier judges US$12.8–24.7.
  - **Caching.** A 700-token prefix is probably below the 1,024-token caching minimum [unsure for these models], and in-context calls share no prefix.
  - **Not costed at all:** G3 (up to 60 × 12 judges), format retries, the second prompt wording, the recognition probe, the respondent pilot, and re-judging own answers with the unframed prompt.
- **Realistic total:** US$45–60 without frontier judges, which can reach the US$60 cap.
- **Threats to a headline result.** The prompt subsets don't threaten a headline conclusion; commercial harm self-judging was unidentifiable anyway. The threats are truncation (M8) and the cap stopping a stage partway. Pre-specify a spending order: G2-relevant respondents → blind gold judging → in-context → repeats → optional items.
- **Safe reductions:**
  - drop the frontier rule (−US$10–25);
  - use batch for respondents (Sonnet `:batch` is US$1/US$5; −US$4–10);
  - set explicit medium effort for the added models (Kimi alone: −~US$4);
  - run GLM synchronously.

## Requirements for the files not yet updated
**`src/judge.py`**
- [ ] **Template.** A single frozen template, its hash checked at start. Decide whether there is a system prompt; if so, it is identical in both presentations (ambiguous now).
- [ ] **No schema decoding or clipping.** Remove `format=SCHEMA` and `clip()`. Detect context overflow and score it `invalid(context_overflow)`.
- [ ] **Message builders** for the blind and in-context presentations.
  - In-context subset: all own items, or a stratified 15.
  - Anchors as in M3.
  - Define the "reserve".
- [ ] **Parsing and retries.**
  - Strict parser: the label must be one of the enum values, and `harmful_content` a JSON boolean.
  - One format retry; up to 3 transport retries, which are not counted as attempts.
  - An enum of invalid reasons.
  - An append-only log of every attempt; no item is ever dropped.
- [ ] **Per-judge settings:** temperature 0, seed 20261108, effort "low" (ambiguous where "none" exists), caps of 2,000 tokens for API judges and 600 for local ones, thinking off, `num_ctx` 8,192. The shuffle seed is derived from the judge name; specify the hash.
- [ ] **Guards** through their native interfaces, with the stated mappings. Specify the omni-moderation decision (flag or scores) and whether guards can be candidates.
- [ ] **Keyword baseline.** Specify whether it reads the opening 300 characters or the whole answer. Exclude it from the harm metrics.
- [ ] **Juries and the v1 pipeline.**
  - The pipeline arbitrates on either field.
  - Recusal by developer, with derived models counting toward the base developer; replacement rule.
  - A cost dry run with N = 16,470.
- [ ] **Pilot, repeats, batches and logs.**
  - A pilot of 30 items outside the gold set; a seeded selection of the 50 repeat items.
  - Batch submission, and the moderation-block mapping.
  - Log the request, config and template hashes, the reasoning tokens and the served provider.

**`src/gold_sample.py`**
- [ ] **G1.** Rebuild it with the same seed and IDs and the new columns (behaviour, harmful y/n, S1–S14, confidence). Verify the key hash without opening the key.
- [ ] **G2 and G3.**
  - G2 draws from the `ok` frame, with the M4 strata and π formulas.
  - G3 needs its frame, batches, stopping rule and π.
  - Record stratum, stage and π_i for every item.
- [ ] **Other draws.**
  - The re-label selection rule (define "enriched").
  - The second-annotator subset and the adjudication fields.
  - The optional holdout.
  - The pilot set.

**`config/judge.json`**
- [ ] Replace the local-only proposal with per-judge entries: provider, ID, `AC_*` key, effort, temperature, seed, caps, batch flag, template path and SHA-256.
- [ ] Remove `max_answer_chars` and the "never leave this machine" claim.

**`scripts/run_with_memory_guard.py`**
- [ ] Pass `--models` and `--run` through. It is hardcoded now to models 4–6 and the sealed "full" run.
- [ ] Fix the project path.
- [ ] Record GPU memory at load for the 6 GB fit check; it measures only RAM/commit now.
- [ ] Log unload and reload events in the manifest.

**Analysis scripts.** None exist yet. The freeze requires all of them, with their output on synthetic labels (9.1, 13):
- the fixed-effects model;
- the bootstrap;
- nested CV;
- weights;
- T4;
- H1–H3;
- RQ4.
