**Auditor A6 (methods and statistics), round 6: targeted check, 8 November 2026**

Everything was read-only. I ran `scripts/cost_model.py` (it only prints, `AC_TEST_TMP` set to my scratchpad) and `python -I -B -c` checks on synthetic data. I made no model, API or network call and wrote no file.

## Verdict
Every round-5 A5 paste is in the draft, and the statistics in it are sound. Own-item π is exact, the intersection–union H1 is correct (Berger, 1982), the gate now changes only the label, and the K ≥ 0 rule is coherent. Every cited number I checked matches `power_sim.json`, `selfcheck_estimators.json` or the cost-model output. The fixes leave three text gaps that matter:
- the own-item random key can still be read as one key per base prompt, which brings back the A5-M1 collapse;
- the new cluster-bootstrap H1 bound is degenerate at 0–2 misses;
- the frontier re-labels can be used to replace gold labels item by item, which brings back the A5-m4 drift.

None of these is blocking and none changes a confirmatory test. **Freeze after minor fixes.**

## Round-5 fix status (A5)
- **M1 (own-item draw):** fixed (7.2 l.360). The key wording is still ambiguous (minor 1).
- **M2(a) (trigger too broad):** fixed. The check is blind-only, and a multi-turn mismatch removes no pair (8.3 l.503–504).
- **M2(b) (no local pilot):** fixed. Local judges are now in the judge pilot (l.527).
- **M2(c) (pilot verdicts):** fixed. The check runs "before the first gold-item verdict" (l.503).
- **M2(d) (missing triggers):** thinking text is now a trigger (l.504). The invalid-rate trigger was declined, with a sound reason: T4 already conditions on items valid for both members (9.3 l.656). Accepted.
- **M2(e) (K = 1 or 0):** fixed (l.505; 9.3 l.660).
- **m1 (second annotator):** fixed (7.3 l.403, l.408). The terminology is off (minor 5).
- **m2 (H1 disclosure):** fixed. Version-1 sizing (l.380, l.707); "round-4 audit simulations" (l.1006); "easier" stated, the κ change disclosed, the round-3 verdict reported alongside (l.707, l.1006); error mix aligned (l.709).
- **m3 (miss-or-invalid, clustering):** fixed in the text (l.707). The clustered bound as specified does not work (minor 2).
- **m4 (frontier adjudication):** two-phase design, re-labeller named, hours added (l.691, l.398, l.1026). It creates a new problem (minor 3).
- **m5 (T4 heterogeneity and gate):** fixed. Per-pair `t4_test` with K = 1, the low-sensitivity caveat, the gate as a label, Holm on 2·p₁ (l.659–661).
- **m6 (gaps):** zero retention fixed (l.297); self-ID fixed (l.487); call list fixed (l.486), but it conflicts with the staged judging (minor 4).
- **m7 (stale text):** all four fixed. Section 4 (l.147), G2 timing (l.356), prefixes (l.497), three decimals (l.630–636).
- **m8 (code and rubric):** all four fixed.
  - `RUBRIC.md:11` matches 7.1.
  - Venice runs its whole subset in stage 1 (`models.json:414`; `run_models.py:244–247`).
  - Clopper–Pearson self-checks for 0/58–0/59, 1/92–1/93, 2/123–2/124 and 0/72 are in the output.
  - Stage-3 hold added (11 l.835; `stage_holds.json`).

## Issues by severity
**Blocking:** none. **Major:** none.

**Minor**, in priority order:

**1. Own-item random key (7.2 l.360).** "A seeded random key" could be implemented as one key per `base_prompt_id`, for example a hash of the ID. I simulated 4,000 draws for models 4–6 (N = 180, interval 30):
- with a key per base prompt, every draw gave exactly 2 base prompts, each in all 3 framings (the A5-M1 collapse);
- with a key per item, the mean was 5.80 distinct base prompts out of 6.

Paste: *"…then a random key drawn independently for every answer (respondent × prompt × framing; seed 20261111), never a key shared by the framings of a base prompt."*

**2. Clustered H1 bound (9.5 l.707).** A percentile cluster bootstrap cannot be stricter than the exact bound unless misses cluster. With 124 items in 105 clusters, 10,000 replicates gave upper bounds of 0, 0.024 and 0.038 at 0, 1 and 2 misses, against exact one-sided limits of 0.024, 0.038 and 0.050. So it is lenient, not a check on clustering.

Paste: *"…a clustered bound is secondary: the one-sided 95% Clopper–Pearson limit at n_eff = n/DEFF, DEFF = 1 + (m̄ − 1)·max(ρ̂, 0), where m̄ is the mean number of gold-harmful items per `base_prompt_id` and ρ̂ is the ANOVA intra-cluster correlation of the miss-or-invalid indicator (DEFF = 1 when there is no miss). It uses x_eff = x·n_eff/n (`estimators.korn_graubard`). A percentile bootstrap is not used, because it is degenerate at 0 misses."*

**3. Frontier re-labels in the sensitivity analysis (9.4 l.691).** "The re-labels also feed the adjudication sensitivity analysis" lets gold labels be replaced item by item. U is re-labelled in full but S and A only in part, so replacement moves the reference toward the frontier judges: the A5-m4 drift again, now inside the H1, T4 and RQ1 sensitivity analyses. The strata also use behaviour verdicts only, and invalid verdicts are unhandled.

Paste: *"Re-labels enter any analysis only through the two-phase estimator, M = Σ_s (N_s/N)·M̂_s, with M̂_s computed on the re-labelled items of stratum s against their re-labels. No gold label is replaced item by item. Strata are formed per endpoint (behaviour; harm on refuse-expected prompts) on items with three valid frontier verdicts; an invalid verdict counts as disagreement. U is re-labelled in full up to 60 items, otherwise by a simple random sample of 60 (seed 20261122). If stage 4 is reduced, the design covers only the items the frontier judges judged; if stage 4 does not run, it is not reported."*

**4. "One call list per judge" against the staged schedule (8.3 l.486; 11 l.864–865).** G1 is judged in the interim, before G2 exists, and G3 comes later. The text also does not say that each anchor's two calls are adjacent, and β_int needs the same drift protection as θ_on.

Paste: *"Each judge has one call list per judging wave (G1 in the interim; G2 with its 30 anchors; G3, blind only). Within a wave, items follow the judge's shuffled order. An item judged in both presentations (own items and anchors) has its two calls adjacent, in an order drawn with seed 20261120, in the same session and mode."*

**5. Plan A reporting (7.3 l.408).** In the agreement literature, "positive agreement" means 2a/(2a+b+c) (Cicchetti &amp; Feinstein, 1990). A Clopper–Pearson interval implies the protocol means a/(a+b). Hazard category is undefined in the second half, because the first annotator gives no category to items labelled not harmful.

Paste: *"Harm: the confirmation rate P(second = harmful | first = harmful) in the first half and P(second = not harmful | first = not harmful) in the second, each with a Clopper–Pearson interval; over both halves, design-weighted κ and specific positive and negative agreement, with a bootstrap stratified by half and second-half stratum. Behaviour: κ within each half and design-weighted. Hazard category: κ on items both annotators label harmful."*

**6. T4 edge cases (8.3 l.505; 9.3 l.659).** Paste:
- *"The K = 2 sensitivity analysis is run only if pairs 4–6 and 5–18 both pass."*
- *"Pair k's one-sided upper bound is Δ̂_k + 1.645·SE_k, with SE_k from `t4_test` with K = 1 at δ₀ = −0.10, so 'below −0.10' is a one-sided 5% test of Δ_k ≥ −0.10."*

**7. Seed collisions (8.3 l.479).** The anchor seed "20261113 + panel number" maps judges 1–10 onto 20261114–20261123. Those are the bootstrap, repeatability, external-set, power, Plan A, judge-pilot, paired-order, stage-4, frontier re-label and stage-3 seeds; the last two are new in this draft. For example, judge 2's anchors and the repeatability set both draw gold items with seed 20261115.

Paste: *"seed = int(SHA-256('anchors' + judge key + '20261113')[:8], 16)."*

**8. Judge-pilot prompts (8.3 l.527).** If an own prompt is among the 10, it leaves every own frame. N_h becomes 179 and the one-item-per-framing-×-category balance claimed in 7.2 fails. Paste: *"10 refuse-expected benchmark prompts (no own prompts)."*

**9. Consistency nits:**
- "Stage 1/2" is used both for schedule phases (7.3 l.417, 7.4 l.423, 11 l.864–865) and for spending stages (7.2 l.356). Rename the phases "Phase 1/2".
- The schedule row (l.860) says "no blocking or major issue"; the rule (l.856) says "no blocking issue".
- The Section 14 blocks at l.962 and l.972 still say "(this draft)".
- The 9.2 table header (l.640) should read "true miss-or-invalid rate".
- Section 13 (l.889) freezes a "fold seed" that no section defines.
- In the pessimistic case with API instruments, stage 4 does not run, so there is no API-judge repeatability (8.3 l.483 relies on it for stochastic judges) and no frontier reference. State that these are then not reported.
- On budget and runner code (items 2–3): nothing else I saw changes a statistical conclusion.

## Readiness
- **Before the freeze commit (text only):** minors 1–4 first, then 5–8, then the nits. None needs new code or simulation. Once the [PI] items are written, the draft can be frozen.
- **What can wait for the Section 13 addendum:**
  - `gold_sample.py`: per-item keys, the order in which draws use seed 20261111, per-stratum starts, Plan A stratum allocation, the two-phase samples, π stored for every item.
  - `judge.py`: call lists per wave with adjacent anchor calls, the T4 rendering log, the self-ID and zero-retention checks.
  - Analysis driver: H1 as an exact test plus the round-3 verdict and the DEFF bound; per-pair upper bounds; K fallback with p = 1; gate as a label; the two-phase estimator; Plan A measures.

## Number check
| Claim | Source value | Status |
|---|---|---|
| Holds 80.05 / 21.75 / 7.06; protected pessimistic total 109.14 | 58.30+14.69+7.06; 14.69+7.06; 7.06; 29.09+80.05 | OK |
| Local, pessimistic: ≈US$8 left; repeatability + guard ≈4.50; frontier subset ≈3.40 (≈7%) | 7.92; 4.20+0.32; 3.40/49.58 = 6.9% | OK |
| Expected, API instruments: total 111, stage 7 cut ≈US$1 | 111.08 | OK |
| Stage 3b: 1,080 and 3,300 calls | 6×180; 6×550 | OK |
| H1 thresholds 0/59, 1/93, 2/124 | 0.0495, 0.04999, 0.0499; one item fewer &gt; 0.05 | OK |
| Version-1 zero-miss sizing: one-sided 59, two-sided 72 | 58.4 → 59; 71.9 → 72 (0/72: 0.04994) | OK |
| Pass 0.86 vs 0.65 at 1% | 0.8575 / 0.65 (harmful rate 0.7); 0.73 / 0.645 at 0.5 | OK |
| H1 table and pass rate at 5% (0.02–0.06) | all cells match; 0.0225–0.0575 | OK |
| T4 size column, 3 decimals | matches; 0.0325 → 0.033 but 0.0625 → 0.062 (print 4 decimals) | OK, nit |
| Sign-flip 0.011/0.045, 0.016/0.051; heterogeneous T4 size 0.016–0.028 | `selfcheck_estimators.json` | OK |
| G2 = 282, own items 84, on-policy API calls ≈150 | 132+42+90+18; 44+12+10+18; 132+18 | OK |
| Labeling hours 16–31 (+2–5) = 18–36; second annotator 4–8 | 15.6–31.1; 3.75–7.5 | OK |
| 4–6 greedy prefixes 5/0/5; Ollama 0.40.15 | `ollama_default_layers.json` | OK |

(About 1,450 words.)
