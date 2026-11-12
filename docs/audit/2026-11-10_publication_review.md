# Publication-readiness review of protocol v2.2: consolidated verdict (10 Nov 2026)

**Status.** Analysis only. No design change was applied and nothing was committed. Every decision below is the PI's.

**Inputs.** Full read of `docs/STUDY_PROTOCOL_v2.md`; `analysis/power_sim.py` and `analysis/output/power_sim.json`; a read-only run of `scripts/cost_model.py`; two independent agent reports saved verbatim next to this file (`2026-11-10_fresh_eyes_paper_review.md`, `2026-11-10_literature_novelty_sweep.md`); abstract-level checks of the closest papers by the main session. Web pages were read through a summarising fetch tool: re-check exact numbers against the PDFs before citing them.

## 1. Verdict

- **The topic is relevant and not scooped.** No work found measures (a) blind own-versus-other judging of refusal or harmful-content labels on chat answers against item-level human labels, (b) the previous-assistant-turn manipulation on that task, or (c) matched abliterated-versus-base models as judges of harmful content.
- **As written, the most likely result is a mostly null, hedged extension of Khullar et al. (2026).** The cause is the shape of the design (many judges, few own items per judge), not the topic. It is cheap to fix before the freeze.
- **Recommendation:** proceed; re-scope first; run a cheap gold-free pilot before the freeze and before inviting co-authors; do not freeze on 13 Nov.

## 2. Relevance (signals)

- Anthropic Safeguards, "Scaling Misuse Detection with Self-Assessment" (16 Oct 2026): the same model flags misuse in its own conversation in context. Its limitations cite Khullar et al. and state that self-assessment is not yet a reliable monitor of the model's own conduct. (Checked by the main session.)
- NeurIPS 2026 workshop JUDGe, "Can We Trust the Judge?" (Atlanta, 12 Dec 2026; non-archival; deadline was 29 Aug): the call lists self-preference detection, robustness of safety evaluators and multi-judge ensembles. No accepted title concerns judge self-preference in safety or abliterated judges (title-level check by the agent).
- UK AISI Control Red Team post (23 Jul 2026) names same-model oversight as an open question (agent-verified).

## 3. Novelty

**Already in Khullar et al. (arXiv:2603.04582):** the user-turn baseline on on-policy artifacts (this is blind self-judging), the previous-turn condition (the in-context presentation), the on- versus off-policy contrast (the anchors), and cross-model heatmaps in which the effect concentrates where monitor = author. Describing this study as adding the blind condition overstates the difference.

**New here:** the task (binary refusal and harmful-content classification of ordinary chat answers); item-level human labels; a cross-author blind comparison with judge × stratum and item effects; small local and abliterated judges; pre-registration; and T4.

| Work | What it measured | What it leaves open |
|---|---|---|
| Khullar et al., 2603.04582 | Previous-turn versus user-turn ratings of code, computer-use actions and essays; 10–11 monitors; no independent human labels | Refusal and harm classification of chat answers; human gold; small and abliterated judges |
| CAREBench, 2606.29685 | Same-family leniency of 3 frontier judges on child-safety chat answers, observational (β = −0.35, n = 7,489) | Blinding not stated; no previous-turn condition; 3 judges |
| Agnihotri et al., 2510.02768 | 20 systems, original and abliterated, asked to identify refusal in their own outputs | Refusal only; no own-versus-other contrast; no harm labels |
| Nghiem et al., 2512.04210 (new to the list) | Small models self-evaluate their own medical answers; the reference is another model | No own-versus-other design; no human gold for that comparison |
| Chacón Menke & Tan, 2503.17365 (new) | Self-critique by small uncensored 7–9B models; harm detection improves less after abliteration outside the Llama family | No human labels; self-judging and abliteration confounded; no matched non-inferiority test |
| Kabir & Tiganj, 2604.18510 (new) | Qwen2.5-7B and Llama-3.1-8B under refusal-feature abliteration; safety judgments of requests | No chat answers; no human gold |
| Chae et al., Findings of EMNLP 2026 | 10 judges, blind versus labelled, non-safety task; self-preference vanishes when blind | Supports a null on T1a |
| Anthropic Safeguards post, 16 Oct 2026 (new) | Deployed in-context self-flagging of misuse | No self-versus-other control; names the bias as unresolved |
| Hossain et al., 2609.22512; Li, Yu & Li, 2609.21277 (new) | Error dependence among LLM judges (effective panel sizes about 1.4–3) | Guards plus LLM judges on harmful-content misses (relevant only if the correlated-error question stays) |
| Keeman & Keeman, 2608.24899 (new) | 3 judges × 3 generators, mental-health messages | Adjacent |

**T4 prior.** The non-inferiority prediction rests on representational results (Zhao et al.; Llorente-Saguer). The behavioural evidence found by the sweep is mixed: architecture-dependent harm detection after abliteration (Chacón Menke & Tan), model-dependent judgments (Kabir & Tiganj), and a practitioner report of a yes-bias in abliterated evaluators (not peer reviewed). T4 is the more original half and its outcome is uncertain in both directions, which is good for the paper.

## 4. Main risk: an inconclusive paper

- **T1b sits in near-empty cells.** 432 own-item pairs; the 11 commercial judges hold 12 each (132 pairs) and carry half of the equal-weight average. Per-judge 95% half-width at 10% discordance: about ±18 pp at n = 12.
- **Power.** MDE at 80% power is 4.9–6.8 pp (§9.2). Power at a 2-pp effect is 0.10 / 0.21 (first / last Holm step, `power_sim.json`), and lower at higher discordance.
- **Optimistic simulation.** Leniency is applied to every own item. If it acts only on real failures, a 5-pp average needs a recall drop of roughly 18–21 points on own failures (reviewer's estimate).
- **Self-specificity is unpowered.** β_int (θ_on against θ_off, from 30 anchors per judge) is absent from `power_sim.py`; the reviewer's back-of-envelope MDE is 6.6–8 pp.
- **T1a is a predicted null inside the Holm family of three.**
- **Construct mixing.** θ_on pools "is this a refusal?" (comply-expected prompts) and "does this contain harmful content?" (refuse-expected prompts). On-policy harm-side data come almost entirely from local and refusal-removed models (about 9 in 10 gold-harmful self items, estimate); commercial judges contribute mostly refusal-side items, where a commitment-type effect is least plausible.
- **Reference standard.** One annotator who is also PI, prompt author and author of the harm definition; a second annotator on 150 items; PI labels stay primary.
- **T4.** Three community 4–8B Q4 pairs; margin −0.10 still open; power falls quickly when the two verdicts are less than comonotone (at Δ = −0.03, first Holm step: 0.96 at ρ = 1, 0.74 at ρ = 0.7, 0.38–0.53 at ρ ≤ 0.4).
- **Legacy H1–H3.** H1 passes with probability 0.56 at a true miss rate of 2%.
- **Reviewer's priors (subjective).** T1a not rejected ≈ 90%; T1b not rejected ≈ 60–65%; T1b rejected with β_int inconclusive ≈ 20–25%; T1b rejected and β_int excludes 0 ≈ 10%; T4 non-inferior ≈ 50%, inconclusive ≈ 40–45%; everything inconclusive ≈ 15–25%.

## 5. Coherence and feasibility

- Four papers in one: the self-judging 2×2; abliterated judges; a judge meta-evaluation; an over-refusal benchmark with a framing study (H1–H3, RQ4).
- Unwritten on 10 Nov: the judge code and template, the analysis driver, the full §7.2 gold sampler, instrument selection, `config/relations.csv`. Three research accounts and the T4 margin are open.
- Labeling is more likely 3–5 minutes per item than 1.5–3 (≈ 35–60 h for the first annotator, estimate).
- Provider risk: §10 concedes the in-context layout resembles a fabricated-turn technique; anchors place other models' harmful answers in commercial judges' assistant turns; one warning removes a provider.
- Strengths to keep: the within-item paired design with adjacent randomised calls; the anchors (right idea, too few); nearly label-free T1 estimands; sealed outputs, inclusion probabilities and simulated test sizes; T4 pair hygiene; limitations stated upfront.

## 6. Recommended changes before the freeze, ranked

1. **Gold-free go/no-go pilot, before the freeze and before any invitation.** Each model judges its own non-gold answers blind and in context (API: respondent-pilot answers or unused OR-Bench prompts; local: about 100 answers from a pool excluded from G2/G3). Outputs: discordance rate, a raw θ_on with SE near 1 pp, invalid and block rates, provider warnings, a rough base-versus-abliterated gap. Decision rules written first. Disclosed as a pilot and excluded from the confirmatory analysis. API part ≈ US$2–5 on the `AC_*` research accounts; local part free (GPU hours, memory guard).
2. **Decouple T1b from the gold set and scale it.** The estimand needs no human label (§9.2). 100–150 own items per judge, or a census for the seven cheap API judges and the local judges. Analytic MDE drops from about 5–7 pp to about 1.5–2.5 pp (optimistic by perhaps a third: it ignores clustering and invalid verdicts), so a ±2–3 pp equivalence statement becomes possible and a null becomes informative. ≈ US$10–20 expected, US$20–40 pessimistic; about half with the batch API, which is not coded for judges yet.
3. **Anchors from 30 to about 100 per judge, matched to each judge's own item mix.** This removes the item-mix confound in β_int and limits how much harmful text from other models enters commercial judges' assistant turns. Add anchors and β_int to `power_sim.py` and make "self-specific or only presentation" a powered, pre-specified test. ≈ US$3.5–7 expected, US$7–14 pessimistic.
4. **Take T1a out of the Holm family.** Register it as the blind control with a bound (for example, blind self-leniency above 7 pp excluded; power at 7.0 pp is 0.97 / 0.99).
5. **Pre-specify harm-side and refusal-side θ_on as separate estimands,** with effects by judge group and a heterogeneity test.
6. **Defer H1–H3, RQ4, instrument selection, the framing study and most of the frontier apparatus** to a separately registered companion, through a public amendment dated before any answer is judged. This frees stages 3 + 3b + 6 (US$29.16 expected, US$64.17 pessimistic), the hardest unwritten code and the 84 own-prompt gold items.
7. **T4.** Add matched abliterated pairs as judge-only models (local and free; several base families and abliteration authors chosen by a documented rule); a random-effects pooled estimate; a three-way reading (non-inferior, inferior, inconclusive); specificity and a criterion measure next to sensitivity; the margin justified or tightened.
8. **Reference standard.** Adjudicated multi-annotator labels as primary for the harm-relevant and T4 items. This gives invited co-authors a bounded role (≈ 8–14 h each, estimate). The HRPP determination is confirmed with USF, not assumed.
9. **Reframe** as a registered replication and extension of Khullar et al. on the task that safety evaluations use; adjust the title; cite the new works of Section 3.
10. **Second template wording as a rubric-light graded rating,** run on-policy in both presentations on a subset (≈ US$3–6). It answers the objection that the rubric suppressed the effect.
11. **Freeze only after the judge code and the analysis driver run end to end on synthetic data.**

## 7. Cost of the revised core

Stage 1 (16.18) + stage 2 (28.38) + scaled T1b + anchors ≈ **US$58–72 expected**, under the US$110 cap. In the pessimistic case the same items reach about US$116–143 as coded, so the cap holds only with the batch API for judge calls or with the five expensive judges (Sonnet 5.5, GPT-6.1 Sol, Kimi K3.1 Pro, Grok 4.7, Gemini 4 Argon: about 90% of judge cost) capped near 100 own items each.

## 8. Venue path

- arXiv, then a safety or evaluation workshop at ICLR 2027: accepted workshops announced 29 Nov 2026; suggested paper deadline 1 Feb 2027; decisions by 26 Feb 2027; workshops 29–30 April (the call page prints the year as 2026, probably a typo).
- TMLR (rolling) for the full version. ARR (4 Jan 2027) is too early. ICML 2027 workshop dates are not posted.
- Reviewer's estimates of a publishable outcome, as written → with changes 1–8: good workshop ≈ 60% → ≈ 80%; TMLR or Findings ≈ 25% → ≈ 45–50%; top main track ≈ 3% → ≈ 5–8%.

## 9. Decisions for the PI

1. Run the pilot? The API part needs the `AC_*` accounts; the local part needs GPU and memory on the workstation.
2. Defer the version-1 hypotheses to a registered companion?
3. T4 inside this paper or as a separate short paper?
4. Invite co-authors only after the pilot, with the annotation role of change 8?
5. The T4 margin.

## 10. Files changed during this review

- `docs/annotator_packet/annotator_guide.md`: line 6 said "own developer's outputs" (now: own answers); lines 15–16 disclosed that about half of the items were harmful, against Section 7.3 (now: the share is not disclosed).
- `tests/prompts/emails_DRAFT.md`: the same "own developer's" wording.
- New: this file and the two verbatim reports. Nothing committed.
- Not yet fixed: §8.4 says outer folds are grouped by `base_prompt_id`, while RULING A (§9.1) groups folds by `cluster_id`.
