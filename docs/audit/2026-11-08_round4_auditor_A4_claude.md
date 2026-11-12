# Round 4, auditor A4 (methods and statistics), Claude subagent, 8 November 2026
Prompt: `AUDIT_PROMPT_R4.md` on the sanitised copy `E:\claude\_audit_copy\agentsControl_r4`.

**Verdict.** Every round-3 statistical fix is in place, and the ones I could test hold up. The G3 and keyword-draw inclusion probabilities, the wild-bootstrap studentisation and re-projection (t* with all weights +1 equals t_obs to 1e-15), the Tango variance (matches a brute-force restricted MLE to about 1e-10) and the T1b sign-flip test all behave correctly, and Section 9.2 matches `power_sim.json`. I found no blocking issue. Five major issues remain, and each can be fixed by pasting text or making a small code change:
- the G2 split across sources is undefined;
- pair 15–19 has not been shown to render prompts identically;
- the batch worst-case reservations defeat the stage-3 protection;
- a second `--collect` can under-count the ledger;
- the H1 missed-harm clause drops sharply below 110 items.

**Readiness: freeze after minor fixes.** Once the [PI] items exist and the pastes below are applied, a targeted check of those edits should be enough; a full new round is not needed.

## Round-3 fix status
**A3**
- B1, code not yet written: **fixed** (13, addendum text).
- M1, G3 π: **fixed** (7.2; `estimators.py:309–316`).
- M2, DGP optimism: **mostly fixed**. Independent T4 coupling and the tests actually used are not simulated (m3, m4).
- M3, cap and target: **fixed** (7.2).
- M4, bootstrap studentisation: **fixed** (`estimators.py:81, 85`), verified.
- M5, text against json: **fixed** in 9.2. The T4 sizes in 9.1 are still the two-pair figures (m4).
- M6, spending order: **partly fixed** (M3 below).
- m1 keyword draw, m2 two-sided wording, m3 Korn–Graubard, m4 3×4 κ (0.589, checked by hand), m5 sign-flip, m6 pooled residuals, m9 strata assert, m10 Venice cap, m12 additions, m13 ethics: **fixed**.
- m7, T4 heterogeneity: **fixed**, but the rule misfires (m5).
- m8, render check: **partly fixed** (M2 below).
- m11, selection: **mostly fixed**. `SELECTION_EVIDENCE.md` rows are stale (m11).

**B3**
- B1, CRLF: **fixed** (`make_judge_alias_m6.py:52`; the Modelfile has 0 CRLF; the build is identical to model 4's).
- B2, selection wording: **fixed** (6.1).
- B3, published documents: **fixed**. The `src/judge.py` draft still says "never leave this machine".
- B4, freeze package: **deferred**, accepted (13).
- M1, batch and caching: **fixed** (`providers.py:146–147, 168–279`).
- M2, ledger: **fixed** (`run_models.py:205–222, 360–364, 463`), with a new collect bug (M4 below).
- M3, moderation: **fixed** (`providers.py:61–99`), with a false-positive risk (m12).
- M4, adapters: **fixed** (`providers.py:144–147, 226`).
- M5, provenance: **fixed** (digests pinned; `run_models.py:233–235`).
- M6, ethics: **fixed**, except that the zero-retention fallback covers respondents only (m10).
- m1–m5, m7–m13: **fixed**.
- m6, pair 15–19 sampling: **fixed**. Rendering is not (M2 below).

## Issues by severity
**Blocking:** none.

### Major
**M1. The G2 allocation across sources is undefined** (7.2 strata and table; `subsets.py:21–25`).
- **Problem.** The strata are respondent × source × expected behaviour, but the table allocates odd totals (5, 14) per respondent × expected cell, and only the commercial harmful cell is pooled. So n_h, and with it π = n_h/N_h, is undefined in the governing text.
- **Paste:** *"Benchmark strata are respondent × expected behaviour, pooled over sources (source is a covariate); simple random sampling within strata, keyword-enriched for the commercial harmful cell. Own-prompt strata use fractional-interval systematic sampling with one uniform start (seed 20261111) on the list sorted by framing and category, so π_i = n_h/N_h exactly. N_h excludes G1, pilot and judge-pilot items."*

**M2. Pair 15–19 is not shown to render prompts identically** (8.3 "differ only in their weights"; `check_system_override.py:57–58`).
- **The count check cannot tell templates apart.** `llama3.1:8b`, `qwen3:8b`, `qwen3.5:4b` and kaineone all give the same counts, 16/29/53/48/72/35, in all six layouts. Equal counts therefore cannot separate a Llama rendering from a Qwen one, and the two members of this pair have different template hashes.
- **Thinking was not tested.** The check sends no `think` option, but judges run with thinking off, and the built-in Qwen3.5 renderer and a GGUF Jinja template may handle that differently [unsure].
- **Why it matters:** this is one of the three confirmatory T4 pairs.
- **Paste:** *"Before judging, each T4 member's rendered token sequence is captured for the six layouts with the exact judge options (think off, num_ctx 8,192, explicit sampling options). A pair passes only if the sequences are identical. If 15–19 fails, a judge build of model 19 with model 15's renderer and parameters is made and re-checked. If identity still fails, T4 uses pairs 4–6 and 5–18 (K = 2), decided before any judge output, and 15–19 is secondary."*
- Include the Q4_0 sensitivity build of model 6 in the same check.

**M3. As coded, the spending order does not protect stage 3** (11; `run_models.py:381, 391`).
- **Problem.** Each batch reserves its full worst case (16,000 output tokens per request). Stage 3 therefore reserves US$48.0 for Sonnet, US$5.76 for GPT-5.6 Luna and US$2.40 for Haiku, US$56.2 in all, against a projection of US$14.69. If the pilot rule doubles Sonnet's cap, its batch alone reserves US$96.
- **Consequences:**
  - In the pessimistic case the ledger holds about US$74.85 after stages 1–2, so Sonnet's stage-3 batch is refused (74.85 + 48 > 110).
  - In the expected case it is also refused if stage 4 ran first (40.79 + 35.41 + 48 = 124 > 110).
  - In the pessimistic case stage 4 can get at most US$20.46 of its US$70.19, and stages 5–7 get nothing. Section 11 does not say this.
  - The API anchors, which identify θ_off and β_int, sit in stage 7.
- **Fix.** Submit batches in chunks of at most 100 requests, each collected before the next (a Sonnet chunk reserves US$8). **Paste:** *"Stage 3 runs before stage 4. A stage's reservation is the larger of its pessimistic projection and the worst case of its largest batch chunk. API-judge anchors (US$1.24 expected / 2.30 pessimistic) and API-judge repeatability (2.06 / 3.84) move to stage 2. Pessimistic: stages 1–3 ≈ US$90; stage 4 is reduced to ≈ US$20 [state the order]; stages 5–7 do not run."*
- Also use the existing batch path for blind frontier judging on the direct APIs. For Opus and Astra this halves stage 4: about US$25 to 12.5 expected, and 51.8 to 25.9 pessimistic.

**M4. A second collect can under-count the ledger** (`run_models.py:398–444`).
- **Problem.** The "collected" marker is written only after the settlement line (438–439) and after `batch_delete` (440). If deletion fails, a second `--collect` passes the check at line 398. It then writes the per-call lines again and a second −reserve. The net is 2·actual − reserve, about −US$10 for a Sonnet stage-1 batch, so the cap is silently breached.
- **Fix.**
  - Write a "settled" marker right after line 439.
  - Refuse a collect if the ledger already holds a `batch_settlement` line for that batch ID.
  - Make deletion a separate, idempotent, logged step.
  - Keep the result kind (expired or canceled) in the error field instead of `batch:None`.

**M5. The H1 missed-harm clause** (7.2 "Why 110"; 9.5).
- **Problem.** A two-sided 95% Clopper–Pearson interval (one-sided α = 0.025) allows 0 misses for 72–109 items and 1 miss for 110–141. At a true miss rate of 1%, the pass probability is 0.70 at n = 110 but 0.35 at n = 105, and at a harmful rate of 0.5, P(n < 110) = 0.32. Adding items also lowers the pass rate (0.59 at n = 140).
- **Recommendation:** keep the registered three-outcome rule and restate it. **Paste:** *"Tested by an exact one-sided binomial test of H0: rate ≥ 5% at α = 0.05 (one-sided 95% Clopper–Pearson upper limit < 5%); H1's clauses form an intersection–union test, so no adjustment is needed. G3 target 124 (cap 100): with 93–123 items one miss is allowed, with 124–152 two. The point estimate and its two-sided 95% Clopper–Pearson interval are the primary report, and the operating characteristics are printed in 9.2."*
- **Effect:** pass probabilities at true miss rates of 1/2/3% rise from 0.67/0.32/0.13 (n = 117 now) to 0.87/0.54/0.27 (n = 125). Under-filled runs (n ≥ 93) still allow one miss.
- For consistency, the κ clause could use the one-sided 95% lower bound.

### Minor
- **m1 (9.1, 9.2) Exchangeability needs symmetric calls.**
  - Make the two calls of each judge–item pair in a seeded random order, interleaved, in the same mode (synchronous or batch). Without that, serving drift between calls breaks exchangeability.
  - "Randomised-presentation contrast" is wrong as worded; write "within-item crossed contrast".
  - State that a T1b rejection shows a presentation effect; reading it as self-attribution rests on β_int.
- **m2 (`selfcheck_estimators.py:47–53, 81`) The self-checks are too easy.**
  - The π_g3 check is tautological: it draws independent Bernoullis rather than two stages without replacement. Replace it with a real two-stage Monte Carlo plus a check that Σ1/π over the sample ≈ N_m.
  - The sign-flip null draws symmetric D independent of judge and cluster, so it is valid by construction. My re-run on the power-sim DGP rejected at α/3 / α:
    - sharp null, ρ 0.5: 0.012 / 0.042;
    - sharp null, ρ 0.3: 0.023 / 0.057;
    - weak null with heterogeneous judges: 0.013 / 0.047.
  - The test is valid; put these cases into the self-check.
- **m3 (9.2) The MDEs come from z tests.** The sign-flip test loses 2–3 points of power at the first Holm step (0.728 vs 0.748 at ρ 0.7; 0.508 vs 0.540 at ρ 0.5), so the MDEs are about 0.1–0.3 pp optimistic. Say so.
- **m4 (9.1, 9.2) T4 power and sizes.**
  - Add the independent-coupling row (25% discordance): power 0.73/0.84 at Δ = 0 and 0.35/0.52 at Δ = −0.03.
  - Harmful rate 0.5 combined with ρ 0.4 gives 0.88/0.97 and 0.50/0.68.
  - Replace the two-pair Wald and max() sizes in 9.1 with the current three-pair ones: 0.003–0.013 at α/3 and 0.008–0.033 at α.
- **m5 (9.3) The heterogeneity rule misfires.** With pair effects of +0.08, 0 and −0.08 (all non-inferior), the label fires in 29% of runs at Δ = 0 and 45% at −0.03. **Paste:** *"…'heterogeneous' if some pair's one-sided 95% upper bound for Δ_k is below −0.10; a Δ̂_k < −0.10 alone is reported as imprecise."*
- **m6 (9.3) Specificity-gate items.** Define them as gold non-harmful items on refuse-expected prompts (G1 + G2 + G3), with the T4 exclusions. This is what the simulation uses (`power_sim.py:222`).
- **m7 Model 6 and slot 21.** Model 6's answers come from the Q4_0 build with its 676-character built-in prompt, but it judges as Q4_K_M without that prompt, so its "on-policy" turn is attenuated. Pre-specify leave-one-judge-out T1a/T1b; it needs no new data.
  - For slot 21 that is enough beyond the disclosure: the size rule is the natural default-tag convention, it is applied uniformly (it also decides `qwen3.5:4b`), it was fixed before any answer existed, and slot 21 is outside T4. No dolphin-mixtral run is needed.
- **m8 (8.3, 7.4) Judge pilot and G1.**
  - About 1.4 of G1's 70 harmful-prompt items are expected to share a prompt with the 10 judge-pilot prompts. Exclude G1's prompt IDs (taken from the sheet; the key stays closed) from the seed-20261119 draw.
  - "before any judge output exists" should read "…on a gold item".
- **m9 (7.3) Second annotator.**
  - In the harmful half, annotator 1's harm label is constant, so harm κ is undefined there. Report the confirmation rate with a Clopper–Pearson interval for that half, κ on the stratified half, and the design-weighted κ overall.
  - The frame is G1 + G2 + G3.
  - Do not tell the second annotator the sample composition.
  - Adjudicators stay blind to judge outputs, including for items flagged by the frontier judges.
- **m10 (6.3, 10) The zero-retention fallback covers respondents only.** Extend it to OpenRouter-routed judges that receive harmful answers: Muse Wonder (zdr = true against a moderated-only endpoint) and gpt-oss-safeguard.
- **m11 (6.1, `SELECTION_EVIDENCE.md`) Selection text.**
  - Define "the window" for the OpenRouter-uncensored stratum as the month file.
  - Operationalise "abliteration only" as: the card names abliteration or orthogonalisation as the method and mentions no fine-tuning, LoRA, merge or preference training.
  - Rows 31–32 and 156–157 still show huihui as model 19 and "8b-v2 not captured".
- **m12 Code.**
  - The markers "1301" and "flagged" are checked before the parameter-error markers (`providers.py:64, 92`), so a 400 body that contains "13010" becomes a `provider_block`.
  - The stage-1 command `--within added_api` would cut Venice to 60 harmful prompts.
  - The Rubric's uplift definition ("beyond a short web search") differs from 7.1.

## Estimator check
| Function | Status | Note |
|---|---|---|
| `pi_g3` | OK | Sums to n over the frame; the self-check is weak (m2) |
| `pi_keyword_enriched` | OK | K < 2 correct; K = N gives 4/N |
| `wild_cluster_bootstrap_p` | OK | Same CR1 factor; re-projection changes residuals, not the slope |
| `theta_on_signflip_p` | OK | Joint flip within clusters is valid, and studentising about the pooled mean is conservative under the weak null |
| `t4_test`, `tango_null_variance` | OK | Size ≤ nominal under every coupling |
| `weighted_mean_cluster_se`, `theta_on`, `pooled_pair_difference` | OK | Pooled-mean residuals, stated |
| `cluster_bootstrap_indices` | OK | Raises on a varying stratum |
| `korn_graubard`, `kish_neff` | OK (simplified) | Capped at n |
| `clopper_pearson` | OK | 0.04961 / 0.04994 |
| `kappa_from_confusion`, `weighted_confusion` | OK | 3×4 padded |
| `holm`, `boot_p_*`, `fe_lpm`, `rogan_gladen` | OK | – |

## Power and cost
- **Power.** The DGP is now reasonable rather than optimistic. Its remaining optimism:
  - z tests stand in for the sign-flip and wild bootstrap tests;
  - T4 discordance stops at 16%;
  - invalid verdicts are completely at random, and effects are the same for every judge.
  - The claims (T1a about 5.7/4.8 pp; T1b 5.7–7.0 pp at the first Holm step) are supported, with about +0.2 pp for the test actually used.
  - T4 at Δ = 0 should read 0.73–1.00.
- **Cost.**
  - The stage table reproduces exactly.
  - The as-coded column correctly reflects the existing paths for respondents: batch for the direct APIs, Anthropic `cache_control`, automatic OpenAI caching, and OpenRouter uncached.
  - The ledger charges cached tokens at the full input price (`run_models.py:165`; Anthropic's `input_tokens` includes cache reads). If `judge.py` reuses this, the ledger runs about US$15 above billing in stages 2 and 4.
  - The pessimistic cuts are not stated (M3).

## Requirements for the modules not yet written
**`src/judge.py`**
- [ ] Frozen template, hash checked at start. Rubric in the system slot per API. The instruction is byte-identical and is the final user content. Data delimited. Authorship never stated.
- [ ] Full answer, never clipped. Context overflow scored `invalid(context_overflow)`.
- [ ] Free generation and a strict parser; five invalid reasons; one format retry; up to three transport retries; `provider_block` never retried; append-only log.
- [ ] API judges: effort low (Venice none), cap 2,000. Local judges: think off, `num_ctx` 8,192, cap 600, explicit sampling options, logged.
- [ ] Render check for T4 at the token-sequence level with the judge options (M2), including the Q4_0 build of model 6.
- [ ] Pair calls in seeded random order, interleaved, in the same mode (m1).
- [ ] Coverage and seeds as in 8.3. G3 never in-context. Probe blind only, as a separate call. Judge pilot excludes G1 prompts.
- [ ] Per call: hashes, served provider, model ID, reasoning and cache read/write tokens, mode, batch ID.
- [ ] Ledger: cache priced at cache rates; max(list, reported); batches chunked; settlement idempotent; stage-reservation check logged.
- [ ] Zero-retention verified per OpenRouter judge, with the fallback (m10).

**`src/gold_sample.py`**
- [ ] G1 rebuilt with the same seed and IDs, key hash verified, key never opened.
- [ ] G2: frame, pooled strata, systematic draw and keyword-enriched π as in M1; seed 20261111.
- [ ] G3: seed 20261112, batches of 20 in round-robin, stop on gold counts only (target as decided in M5), `pi_g3` for every frame unit.
- [ ] π, stratum and stage stored for every item; check Σ1/π ≈ N.
- [ ] Second-annotator draw (seed 20261118, π recorded); re-label set of 70; Plan B set; holdout.

**`config/judge.json`, `config/relations.csv`**
- [ ] One entry per judge, guard and frontier judge: provider, ID, `AC_*` key, settings, digest, template SHA-256, parser version, candidate list and recusal map.
- [ ] `relations.csv` codes self at the checkpoint level and the frontier judges' developer relations: Opus with 1–2, Astra with 3, 9 and 11, Muse with 4, 6 and 20.

**Analysis driver**
- [ ] T1a, T1b, T4 (with the specificity gate and heterogeneity reading), H1 out of fold, RQ4, and leave-one-judge-out, run on synthetic labels and committed before the G2 draw.
