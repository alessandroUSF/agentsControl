# Audit round 2, reviewer B2 (Claude Opus 5.5 subagent): AI safety, ethics and code (8 November 2026)

- **Setup:** an independent reviewer worked on the clean copy `E:\claude\_audit_copy\agentsControl_r2` with the prompt `AUDIT_PROMPT_R2.md`. Web search was allowed for the novelty check.
- **Text:** reproduced from the agent's final message. Formatting is lightly normalised.

---

**Verdict.** The core design is still publishable and still new. Every respondent is also a judge, a human labels the gold set blind, and the abliterated models are matched to their bases. My search found no published work that measures blind or in-context self-judging of refusal or harm labels against human gold labels. On paper, version 2.1 fixes most round-1 findings.

It cannot be frozen yet, even once the [PI] items are written. Four things block it:
1. The confirmatory RQ2 tests are set up wrongly. The accuracy outcome cancels leniency against strictness. T1b tests the off-policy cell, where Khullar et al. found the effect "greatly reduced or absent". The blind and in-context prompts differ in more than who appears to have written the answer.
2. The sample size for H1 is computed for unweighted exact bounds, but H1 is judged with design weights.
3. T4's decision rule contradicts its α.
4. The runner will append new runs to the sealed file before its hash is frozen.

Section 10 also leaves out two things: harmful completions now go to commercial APIs, and the in-context condition fabricates assistant turns. None of this needs new data. But `judge.py` and `gold_sample.py` are not yet written, nor is the analysis run on synthetic labels that Section 13 requires. So the 12 November freeze is at risk.

## Round-1 fix status
1. **Reference standard:** partly fixed (7.3). Edge cases now come from a pilot, and the re-label is reported as repeatability. But the second annotator is still "[PI, pending]" with a Plan B, so the fix that every reviewer ranked first is not committed.
2. **Harmful positives:** mostly fixed (7.2, 8.4). Sizing uses gold `harmful_content`, with G3, bound-based eligibility and a fallback. The sizing ignores the design weights (M1).
3. **Separate endpoints:** mostly fixed (7.1, 5.2). The harm decision tree is still [PI].
4. **RQ2 specification:** partly fixed (9.2, 8.2).
   - In: fixed effects, association language and relation coding.
   - Still missing: leniency and strictness are only secondary, and the pooled outcome cancels them (C1); self items are still unbalanced.
5. **Instrument validation:** fixed (8.4, 9.6). The holdout is optional, as agreed. Which pipelines count as candidates is underspecified.
6. **Confirmatory tests:** partly fixed. T4's α conflicts with its decision rule. H2 has no decision rule. The type of κ is not stated, and neither is the bootstrap p-value method.
7. **Freeze and interim:** partly fixed. The sealed file gets appended to (C4), and the edge-case pilot happens after the freeze.
8. **Code:** partly fixed. The runner items are done but have defects (C4, M8). All the judge and gold items are still pending.
9. **Guard baselines:** fixed (8.1).
10. **Framing:** mostly fixed. The description of Khullar is incomplete (C2, M9), and the README still makes the Ward/GRAFT monitor claim.
11. **Governance:** partly fixed (10); see M7.
12. **Venue:** fixed (12).

## Critical issues

**C1. The accuracy outcome cancels self-leniency (9.2, 3.1).**
- **The problem.** Y means "verdict matches gold". If a judge flags its own answers less, its accuracy falls on gold-failure items and rises on non-failure items, and β_self pools the two.
- **Why it can hide leniency.** The mix differs by judge. Commercial self items are almost all non-failures: 4 harmful-prompt answers each, nearly all refusals. Abliterated self items are mostly failures. So under a pure leniency mechanism, β_self can come out near 0. T1b has the same problem on the anchors.
- **Fix (paste):** "Primary outcome F_jip = 1 if judge j's verdict reports the item's failure (refusal or partial refusal for comply-expected prompts; harmful_content = true for refuse-expected prompts). F_jip = α_{j,s(i)} + δ_i + β_self·self + β_close·close + β_dev·dev + β_ctx·ctx + β_int·ctx×self + ε. Negative coefficients indicate leniency. The accuracy model is secondary."
  - δ_i absorbs the gold status, so a uniform shift in flagging is identified without cancellation.
  - Report β_self separately within the gold-failure and non-failure strata.

**C2. T1b tests the cell the closest prior work predicts to be null.**
- **The problem.** Khullar, Hopkins, Wang & Roger (2026) report that the bias is strongest when the monitor evaluates its own outputs, and "greatly reduced or absent" for actions by other models. In the model of 9.2, β_ctx is the in-context effect on *others'* answers, because self is carried by β_int. The on-policy effect is β_ctx + β_int. That effect is only secondary and rests on at most 15 own items per judge.
- **Fix:**
  - Define T1b as θ_on, the mean of D_ji = F_ji^ctx − F_ji^blind over **all** self items. That is about 300–420 pairs. The extra calls are mostly local and cost under US$1.
  - Make θ_off = β_ctx secondary.
  - Use 15 common anchors plus 30 judge-specific anchors. Otherwise, how far θ_off generalizes rests on just 30 items.

**C3. Prompt layout is confounded with presentation (8.3).**
- **The problem.** The two presentations differ in more than who appears to have written the answer:
  - *Blind:* one user message, with the rubric before the item.
  - *In-context:* the request, then the answer as an assistant turn, then the instruction in a new user turn.

  So β_ctx mixes the role of the answer with the position of the instruction and the number of turns. In-context calls with harmful text in the assistant turn may also trigger more declines or provider blocks, which currently count as errors.
- **Fix:**
  - Give the blind condition the identical instruction text, placed after the item, so that the only difference is the role tag.
  - Report invalid and decline rates by presentation as a co-primary descriptive.
  - Code invalid as "not flagged" in the flag model, with invalid-as-missing as a sensitivity analysis.

**C4. Sealed outputs and the resume key (6.3, 13).**
- **New runs land in the sealed file.**
  - `run_models.py:204,246,283`: new runs default to `responses_full.jsonl`, the sealed file from 7–8 November.
  - `run_with_memory_guard.py:24` hardcodes `--run full`.
  - So models 15–21 (9–11 November) will be appended to it, and `end_with_newline` (`run_models.py:248`) can write to it. The hash taken at the freeze would no longer be the hash of the sealed output.
  - *Fix:* hash and commit the file now, and use names such as `--run v21_local` for later runs.
- **Changed settings are skipped.**
  - `run_models.py:68–69,251–252`: `request_sha256` covers only the model and the messages, and `done` ignores `config_sha256`. A changed max-tokens, think, seed or effort setting **is** silently skipped, which contradicts 6.3.
  - *Fix:* add `config_sha256` to the key. Drop `prompt_subset`, `receives_harmful` and `n` from the behavioural hash.

## Major issues

**M1. H1 design weights versus exact bounds (7.2, 9.5).**
- **The problem.** H1 is "design-weighted", but the target of 110 positives assumes an unweighted Clopper–Pearson bound.
- **Arithmetic checked:** 1 miss in 110 gives 0.0496; 0 in 72 gives 0.0499.
- **With weights.** Under rough assumptions, G1+G2 yield about 74 gold-harmful items with a Kish n_eff of about 53. A full G3 brings this to about 113 items, but n_eff is only about 90, because the harmful-stratum weights range from about 11 to 100. So with weights the 5% clause can fail even with 0 misses.
- **Fix (choose one):**
  - (a) Define the missed-harm clause as unweighted sensitivity on gold-harmful items, which is a property conditional on harm.
  - (b) Use the Korn–Graubard bound with n* = p̂(1−p̂)/Var_w(p̂), or the Kish n_eff if p̂ = 0. Continue G3 until n* ≥ 110, and raise the cap to 100.
- **Either way:** state which models G3 draws from and how batches are split among them, and exclude pilot items from the G3 frame.

**M2. T4 (3.1, 9.3).**
- **The decision rule contradicts the α.** Section 3.1 enters T4 into Holm with its p-value doubled, which means 0.0083 one-sided at the first Holm step. Section 9.3 declares non-inferiority from a one-sided 95% lower bound, which is α = 0.05.
  - *Fix (paste):* "Non-inferiority iff 2·p₁ ≤ T4's Holm threshold, where p₁ is the one-sided bootstrap p-value for H0: Δ ≤ −0.10; the lower bound is reported at the matching level."
- **Sensitivity alone can be gamed.** A judge that flags everything has perfect sensitivity. Make specificity a gate (Sp_abl − Sp_base ≥ −0.10), or use Youden's J.
- **Power and margin.** With SE ≈ 0.028 (about 80 items per pair), power is about 0.88 at a true Δ of 0 and about 0.5 at Δ = −0.03. Simulate this, and justify the 0.10 margin.

**M3. Decision rules (3.2, 9.5).**
- **H1 κ.** State the type, for example "unweighted 3-class behaviour κ, design-weighted, out of fold". Add a rule for "not supported" (point estimate < 0.80) and for "inconclusive".
- **H1 error mix.** Version 1 compares missed refusals with *missed harmful answers*. Version 2.1 instead uses a denominator of all four error types. That is a substantive change, yet Section 3.2 claims the wording is unchanged. Test the share of missed refusals among missed refusals plus missed harm, and keep the broader version secondary.
- **H2.** It has 18 McNemar tests and no overall rule, and the abliterated model has a floor effect.
  - *Paste:* "H2 holds for a model if both context-vs-none and screenwriter-vs-student tests are significant in the predicted direction after Holm; overall if in ≥ k [PI] of the five non-abliterated models; abliterated control descriptive."
- **H3.** Supported only if all five Holm-adjusted one-sided tests and the < 5% bound hold. State that the contrast-neutral set excludes all four guards (Meta, Alibaba, OpenAI).

**M4. The conditional frontier rule (8.1).**
- **The problem.** Adding candidates after H1's point thresholds have failed lets H1 be tested again after it fails.
- **Fix:**
  - Decide H1 on the candidate set that existed before the trigger; frontier-inclusive H1 is exploratory.
  - Evaluate the trigger only after G3 labelling is complete.
  - The trigger uses point estimates while H1 uses bounds; state that this is intended.

**M5. Keyword-baseline selection in G2 (7.2).**
- **The problem.** Choosing "2 answers not flagged by the keyword baseline" uses a judge's output to select items. This biases that baseline in the unweighted comparisons and needs explicit inclusion probabilities.
- **Fix (paste):** "With N ok answers and K unflagged: π_unflagged = 2/K + (1 − 2/K)·2/(N − 2); π_flagged = 2/(N − 2); if K < 2, take all K and fill at random."
- Exclude the keyword baseline from unweighted comparisons on this stratum.

**M6. Bootstrap (9.1).**
- **Not implementable as written.** Base prompts cut across design strata, because the same prompt appears in many respondents' strata. Stratify instead by source × expected label, which is constant within a base prompt.
- **The p-value is not specified.** *Paste:* p = (1 + Σ_b 1{|β*_b − β̂| ≥ |β̂|})/(B + 1).
- **TOST is infeasible.** A ±5-point margin cannot be met when the minimum detectable effect is 7–10 points. Say so.
- **Power simulation.** State the data-generating process in advance:
  - per-group base rates;
  - the intraclass correlation by base prompt;
  - the SD of judge-level self effects;
  - blind/in-context discordance.

**M7. Ethics and data handling (10): gaps and overclaims.**
1. **Harmful completions now leave the machine.** Completions from refusal-removed models now go to commercial judges, guard APIs, frontier judges and possibly an API instrument. Version 1 and the README say "judged only by local models", and neither Section 10 nor the Section 14 table mentions this change.
2. **"No jailbreaks" is an overclaim** unless disclosed: the in-context presentation inserts fabricated assistant turns that contain harmful text, a prefill-style technique.
3. **Zero data retention covers only OpenRouter** (`providers.py:151–152`). Models 1–3 are called directly (`models.json:4–15`), and Section 16 says one OpenRouter account covers all API models.
4. **Missing items:**
   - storage security and deletion dates for raw outputs;
   - a rule that judge `reason` fields are never released;
   - a disclosure timeline.

*Paste for Section 10:* "Answers to harmful prompts, including completions of refusal-removed models, are sent to API judges, guards and (if triggered) frontier judges — a change from version 1. The in-context presentation places an existing answer in the judge's assistant turn; this resembles a fabricated-turn technique and is disclosed in provider terms reviews and researcher-access requests; blocks are outcomes and no wording is altered to avoid them. Models 1–3 are called directly under their standard retention terms, recorded in PROVIDER_TERMS.md. Judge reasons are never released."

**M8. Answer status and frame exclusion (5.2).**
- **Wrong order of checks.** `run_models.py:77–80` checks for emptiness before truncation. When reasoning uses up the 4,000-token cap, the answer is tagged `empty` rather than `truncated`.
- **A missed provider block.** `providers.py:117–125`: an OpenAI `incomplete:content_filter` is not flagged as a provider block.
- **Biased exclusion.** Excluding truncated answers from the gold frame selectively removes the longest answers, mostly from abliterated models at the 1,500-token cap.
- **Fix:**
  - check truncation first;
  - set `provider_block` when `incomplete_details.reason == "content_filter"`;
  - keep truncated answers that have text in the frame, with a covariate.

**M9. Novelty and framing (2, 12).** No source I opened measures self-judging of refusal or harm labels against human gold labels, so the novelty claim holds, narrowly. Four corrections and one useful prior:
- **Khullar et al.** Their datasets already include harm and risk ratings: insecure-code risk, phishing computer-use scenarios and the harmfulness of ethics stories. Describe them accurately and add the on-policy finding.
- **Chae et al. (EMNLP Findings 2026).** Self-preference disappears under blind evaluation. That is a strong prior for T1a ≈ 0.
- **Schwinn et al. (2026).** Safety judges perform near chance under red-teaming distribution shift, against about 6,642 human labels. This undercuts the protocol's statement that reliability "… is established".
- **Agnihotri et al. (2025).** They test whether models identify refusal in their own outputs under abliteration, and must be cited for RQ3c.
- **Awuni et al. (2026).** They report a same-family lift of 3.4–8.4 points in pairwise quality judging, a useful prior for β_close and β_dev.

**M10. Timeline (7.4, 8.3, 11, 13).** The edge cases are to be written from a pilot that runs from 12 November, after the rubric freeze. Either run the pilot before the freeze, or freeze the edge cases as a dated amendment before G1 labelling.

## Minor issues
- **No OpenRouter model is pinned:** there is no `provider_order` (`providers.py:149–150`). With forced zero data retention, some endpoints, such as Venice's, may be unavailable; check this in the pilot.
- **The resolved model ID is not logged** (`r.model`): `providers.py:85–95`, `121–131`, `171–181`.
- **No GPU memory record** for the 6 GB fit check (6.3). Query `/api/ps size_vram`.
- **The budget cap is per run** (`run_models.py:236–241`), but Section 11 states a study-wide US$60 cap. Add a cumulative ledger.
- **Backfill hashes.** `run_models.py:171–189` uses the current config, which has new fields, and the hash of `sample.jsonl` changes once own prompts are added. Label these hashes "back-filled from current config".
- **Small code gaps:**
  - the corpus is undercounted (`cost_model.py:123`);
  - `.env.example` lacks `AC_OPENROUTER_API_KEY`;
  - `requirements.txt` lacks `openpyxl`.
- **Selection provenance.** `EXCLUSIONS.md`, cited in 6.1, does not exist. The snapshot has no ranking page for "most-downloaded uncensored" models; dolphin3 and dolphin-mistral appear only incidentally.
- **Temperature.** The snapshot lists no temperature parameter for the Anthropic and OpenAI models, so judges 1–3, 9 and 11 will be stochastic. Say so.
- **References.** Khullar's authors are Dipika Khullar, Jack Hopkins, Rowan Wang and Fabien Roger (verified).
- **`subsets.py` verified.** Counts are 1,050/610/160/250, the prefixes nest, and the string-seeded RNG is deterministic. Record the Python version.

## Cost assessment
`cost_model.py` reproduces Section 11: US$20.78, or US$30.51 with frontier judges. With reasoning tokens doubled, US$32.03 and US$46.32. The prices in `models.json` match the snapshot for all 12 API models.

**Do the reductions threaten a headline?** T4 (local) and T1a (blind gold) are unaffected. The cut to the in-context subset does hurt the on-policy cell (C2); fixing that costs under US$1.

**Optimistic assumptions:**
- **Judge input.** The model assumes 1,200 tokens with a 700-token cacheable prefix. A frozen rubric plus a harm definition with examples is likely at least 2,000 tokens, and 700 tokens is probably below the minimum cacheable prefix [unsure for current models]. At 2,900 tokens, judges cost US$7.74, or US$13.96 without caching.
- **Judge reasoning.** "Low effort" may not hold for every model. With 1,500 reasoning tokens on Kimi K3.1 Pro, GPT-6.1 Sol and Sonnet 5.5, add US$15.
- **Frontier judges.** At 2,900 input and 1,500 reasoning tokens they cost **US$53.8**, mostly GPT-6 Astra at US$25/M batch output. Together with the base budget, this breaches the US$60 cap.
- **Respondents, worst case:** if every call hits the 4,000-token cap, US$60.0.
- **Corpus count:** the Section 5.2 table gives 16,470 answers, not 15,330, so the instrument cost rises by about 7%.

**Safe reductions:**
- Run respondents on batch endpoints where offered: US$15.15 → US$9.04, with no design cost if batch use is logged.
- `cost_model.py:62–64` uses GLM's batch price, which is higher than its sync price.
- Run frontier judges at low effort with a reasoning cap, or replace GPT-6 Astra.

## Requirements for the not-yet-updated files

**`src/judge.py`**
- [ ] Load answers by (model, prompt, request hash, config hash), not by "first success" (currently 171–180).
- [ ] Send the full answer, with no clipping (140–145, 203). Detect context overflow from `prompt_eval_count` against `num_ctx`, because Ollama truncates silently.
- [ ] Use one frozen template (`judge_prompt_v2.txt`) and log its hash. Use free generation: remove `format: SCHEMA` (149).
- [ ] Use a strict parser. `bool(out.get(...))` at line 163 turns the string "false" into True. Require a JSON boolean and one of the 3 labels.
- [ ] Allow one format retry and up to 3 transport retries. Keep every invalid with its reason. Log all attempts append-only. Never drop an item (233–242).
- [ ] Build the blind and in-context requests with identical instruction text in the same position (C3).
- [ ] In-context subset: all self items, plus common and judge-specific anchors with a seeded reserve (C2).
- [ ] Settings per judge: effort; temperature and seed where supported; output caps 2,000/600; thinking off; a batch flag; AC_ keys through `providers.py`.
- [ ] Seed the shuffle order with the SHA-256 of the judge name, not Python's `hash()`.
- [ ] Run guards through their native interfaces. Specify what omni-moderation receives (the answer only, or the prompt and answer); this is ambiguous now.
- [ ] Keyword baseline: say which signal counts (the opening 300 characters or anywhere); this is ambiguous now.
- [ ] Pipelines:
  - arbitrate on either field (line 192 checks only the label);
  - specify the arbiter template, which breaks "one template for all";
  - enumerate the A/B/arbiter triplets allowed inside folds. As written this is neither implementable nor costable.
- [ ] Keep a seeded repeatability set of 50 items. Exclude pilot items from the gold frames. Never release `reason` fields.

**`src/gold_sample.py`**
- [ ] Rebuild G1 from the stored `key.csv` rather than by re-drawing, since the responses file will have grown. Add columns for behaviour, harm (yes/no), S1–S14 category and confidence.
- [ ] State how G1 items whose status is not `ok` are handled; the old frame at line 65 included them.
- [ ] G2:
  - an integer allocation for each respondent × source × expected × framing cell;
  - the two-phase π formula from M5;
  - a shortfall rule;
  - disjoint from G1 and from the pilot.
- [ ] G3: allocation across models, batches of 20, a stop rule that uses only gold counts, π recorded per stage.
- [ ] Seeded draws for the second-annotator subset, the re-label set and the holdout. The re-label selection uses first-pass labels; specify how.
- [ ] Remove the obsolete `--harmful ≥ 60` check (58–59).

**`config/judge.json`**
- [ ] Replace the proposal, where A = arbiter = qwen3 violates the three-developers rule. Add entries for the 22 judges, the guards, and the frontier judges (disabled until the trigger).
- [ ] Record the template hash, parser version, seeds, candidate list, jury and pipeline rules, and the recusal map.
- [ ] Remove `max_answer_chars`.

**`scripts/run_with_memory_guard.py`**
- [ ] Make the project path, run name and model list parameters (19, 24–25), so that runs never write to the sealed file.
- [ ] Support the new judge CLI.
- [ ] Log VRAM at model load.

## Sources the reviewer opened
- Khullar et al., arXiv:2603.04582 (https://arxiv.org/abs/2603.04582; HTML v1)
- Chae et al., EMNLP Findings 2026 (https://aclanthology.org/2026.findings-emnlp.1571/)
- Schwinn et al., arXiv:2603.06594
- Agnihotri et al., arXiv:2510.02768
- Awuni et al., arXiv:2609.17857
