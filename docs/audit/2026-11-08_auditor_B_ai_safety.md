# Audit B: AI safety, novelty and publishability (8 November 2026)

This is an independent reviewer agent's report on `docs/STUDY_PROTOCOL_v2.md` (draft of 8 November). The agent read the protocol and the repository only, without the design conversation. It did not open `results/` or `.env`. Its report is reproduced here as returned. Claims are checked during consolidation.

## Verdict
The core design is sound and could support a publishable paper. Every respondent also acts as a judge, so every gold item gets exactly one self-judgment the judge doesn't know about.

As written, though, the protocol has three problems:
- it misses the closest prior work, above all Khullar et al. (2026), "When AI Monitors Go Easy on Themselves";
- its confirmatory self-judging test mostly measures three local 8B models on easy items;
- its gold standard is one annotator who is also the PI.

The recommended fixes:
- narrow the paper to blind self/family judging (RQ2) and refusal-removed judges (RQ3c);
- add guard-classifier baselines and a second annotator;
- move RQ4 to an appendix.

*Limitation:* the reviewer's knowledge ends mid-2026. Web searches found several 2026 preprints, but work from September to November 2026 may still be missing.

## Critical issues
**C1. §2, §12: related work misses the nearest papers, so the novelty claims do not hold up.**
- **Problem.** The protocol omits:
  - Khullar, Hopkins, Wang & Roger (2026, arXiv 2603.04582). They tested 11 monitors. Monitors under-flag risky or incorrect actions when those actions are *implicitly* framed as their own (placed in an earlier assistant turn). Saying explicitly that the monitor wrote the action does not by itself produce the bias. The paper discusses AI control and collusion.
  - Meta-evaluations of refusal and harm judges against human labels:
    - SORRY-Bench (7K+ human labels; fine-tuned 7B judges match GPT-4);
    - WildGuard (the same two labels as this study: response refusal and response harmfulness);
    - JailbreakBench, StrongREJECT and HarmBench.
  - Eiras et al. (2025): changing only the style of an output moves safety judges' false-negative rates by up to 0.24.
  - Panfilov et al. (2025): fake-harmful answers fool every output-based monitor tested.
  - Goel et al. (2025): judges favour models similar to themselves.
  - Li et al., "Preference leakage" (ICLR 2026): judges favour related models (the "sibling" question).
- **Why it matters.** Reviewers will read RQ1 and RQ3d as replications and the "first matrix" claim as unaware of the field.
- **Fix.**
  - Rewrite §2 around these papers.
  - Claim novelty only for:
    - blind self- and family-judging of refusal and harm labels;
    - a behavioural test of harm recognition after refusal removal.
  - Better: on a subset, add Khullar's in-context condition, where the answer sits in the judge's own earlier assistant turn. That gives a 2×2 design (self vs other author × blind vs in-context presentation). This is the cheapest route to a clearly new result.

**C2. §7.2, §9 RQ2: the self-judging test cannot answer the question that motivates it.**
- **Problem.**
  - G1 gives 150 self-items to three local 8B judges and G2 adds 12 more. That is about 46% of all self-judgments; every other judge gets 10.
  - Commercial judges' self-items are answers to safe or own prompts, mostly easy full compliance, so any self-effect sits near the ceiling.
  - Leniency on harmful content, the direction that matters for monitoring, is measurable only for local and uncensored judges.
  - `(1|judge)+(1|item)` does not absorb judge × item-type interactions. Each judge's self-items are concentrated in particular item types (for example, abliterated judges' self-items are mostly harmful), so judge skill by item type leaks into the self term.
- **Fix.**
  - Balance self-items, about 12–15 per judge (subsample G1 for this analysis, or weight it).
  - Model judge × stratum effects (or random slopes).
  - Report T1 separately for commercial, local and refusal-removed judges.
  - Generate answers from the 4 frontier judges on the G2 prompts only (well under US$20), so the most capable monitors also have self-items.
  - Pre-specify an equivalence margin (TOST, e.g. ±4 percentage points) so a null result is informative.
  - Code the relation in levels: self / derived from the same checkpoint / same developer / same pretrained base / unrelated.

**C3. §7: a single annotator who is also the PI.**
- **Problem.** Every RQ1–RQ3 metric is agreement with this gold set.
- **Fix.**
  - A second independent annotator on all harmful-prompt items and at least 30% of the rest, with adjudication.
  - A transfer check on a public human-labeled set (the WildGuardTest response subset, or XSTest's labeled completions).
  - Without a second annotator, rejection at strong venues is likely.

## Major issues
**M1. Title, §1–2: the AI-control framing overclaims.**
- **Problem.**
  - Untrusted monitoring (Greenblatt et al.) is a worst-case, adversarial setting about sabotage and backdoors, not classifying harm in chat answers. A blind, average-case self-effect is at most a benign precondition.
  - Ward et al. 2026 (arXiv 2610.17062, GRAFT) is a gradient-routing paper. Its line on monitors is speculative ("It's possible that GRAFT works less well with LLM-based monitors, which make different kinds of systematic errors"). Version 2 hardens this into a finding.
- **Fix.**
  - Frame the paper as measurement validity of safety judges, with implications for monitoring.
  - Quote Ward accurately.
  - Add an exploratory paraphrase condition, the standard anti-collusion countermeasure in AI control.

**M2. §7.1, §8.2, `src/judge.py`, `labels/RUBRIC.md`: judge prompt and harm definition.**
- **Code and protocol disagree.** `judge.py` has two prompts (A and B) plus an arbiter, with three different harm wordings, against §7.1's "meaningfully help carry out a harmful request". Fix:
  - Pre-register the exact single prompt and its hash.
  - State which prompt the v1 pipeline uses; every instrument candidate must be validated with the prompt it will actually run.
- **The definition only covers uplift.** It misses harms where the output *is* the harm: hate, harassment, sexual content, deception, privacy, encouragement of self-harm. These are much of OR-Bench Toxic. Fix:
  - Map the definition to a published hazard taxonomy (Llama Guard or MLCommons categories).
  - Consider a none / generic / actionable scale, collapsed to binary for analysis.
- **The rubric contradicts §9.** It counts any `full_compliance` on a refuse-prompt as harmful compliance. Separate "complied with a harmful request" from "produced harmful content".
- **Two classes overlap.** "Redirects to a safer version" (partial) and "only offers alternatives" (full) describe nearly the same behaviour. Add worked examples.

**M3. §8.2, `judge.py`: pipeline confounds that would be misread as judge quality.**
- **(a) Truncation.** Judges see a 6,000-character head-and-tail clip; human labelers see the full text. Fix: give both the same text, or flag clipped items.
- **(b) Unequal output regimes.** Ollama judges use schema-constrained decoding and cannot decline to judge; API judges can. Fix: use the same output regime for all judges and keep raw outputs. Otherwise invalid and decline rates are not comparable, and T2 and T4 are biased.
- **(c) Output cap.** `max_output_tokens: 200` will truncate reasoning judges.
- **(d) Provider blocks and routing.** Anthropic `refusal` stops, Gemini safety settings, input filters on China-hosted APIs, and OpenRouter switching hosts or quantizations. Fix:
  - pin the provider with fallbacks off;
  - log the served host;
  - report blocks separately from judge errors.
- **(e) Empty or provider-blocked respondent answers.** Labeling these as refusals is trivial and inflates accuracy. Fix: exclude them or report them separately.

**M4. §8.1: no purpose-built baseline.** Add:
- WildGuard-7B;
- Qwen3Guard-Gen 4B/8B;
- Llama Guard 3 8B;
- gpt-oss-safeguard-20b (via API);
- the free OpenAI moderation endpoint.

These are what practitioners actually use.

**M5. §9 RQ3c, §6.2: T4's pairs are not clean refusal-removal comparisons.**
- **Problem.** Dolphin 3.0 is fine-tuned from the *pretrained* Llama-3.1-8B, not from the Instruct model. Llama Instruct vs Dolphin 3 therefore compares two post-training pipelines, not refusal removal.
- **Fix.**
  - Restrict T4 to the three abliterated pairs.
  - Document each abliteration method and confirm refusal removal from the generation data.
  - Add judge-only base models so the descriptive-only models become pairs: Mistral Small 24B Instruct for Venice, Mistral 7B Instruct for Dolphin Mistral.
  - Score T4 conditional on valid output and report the invalid rate separately.
- **Predictions.**
  - Directional, from Zhao et al.: harm detection is preserved.
  - Exploratory: refusal detection may degrade.

**M6. §6, §9 RQ3a: model selection.**
- **Rules.** They were written after the rankings were seen, and several are hardware or convenience filters. Fix: present them as purposeful strata ("frontier", "cheap API", "consumer-GPU", "refusal-removed").
- **Inconsistencies.**
  - Qwen3.5 4B's 43.5 is its *Reasoning* score; the snapshot gives 39.6 non-reasoning, and the model runs with thinking off.
  - "Frontier judges mark the top of the capability curve" is false for Muse Wonder (43.6) and Gemini 4 Argon (50.4).
  - Google has no respondent.
  - OpenRouter shares may be inflated by free-tier promotions; check.
- **T2.** Spearman across about 13 judges on one scale is underpowered and confounded by developer and reasoning. Fix: use GPQA Diamond, which exists for all judges, as a common covariate in a judge-level model, and make T2 exploratory.
- **Scale.** 26 judges is a strength. 22 respondents is justified only by RQ2, and RQ4 across 22 models is the costliest and least novel part.

**M7. §10: ethics and terms of service.**
- The Llama 3.1 Community License and Acceptable Use Policy bind derivatives. Justify generating harmful completions explicitly.
- Use zero-data-retention endpoints and disable OpenRouter logging and training wherever harmful text is sent.
- Separate research accounts can look like evasion of provider enforcement. Prefer researcher-access programs, or notify providers.
- "Nothing raw is published" makes the gold set unusable by others. Use gated release instead, especially for items every judge misses (a dual-use set for evading judges).
- Direct disclosure at judge and guard developers about systematic blind spots.
- Get a written USF "not human subjects" determination before a second annotator starts, plus a welfare protocol: content warnings, session caps, opt-out.

## Minor issues
- **[verify] references.**
  - Kim et al. exists and is cited correctly: ICML 2025, PMLR 267:30038–30066. Also cite their finding that more accurate models have *more* correlated errors.
  - Zhao et al.: cite as Zhao, Huang, Wu, Bau & Shi, NeurIPS 2025 (arXiv 2507.11878).
  - OR-Bench was published at ICML 2025.
- **H1's < 5% miss rate is untestable with this many positives.** With about 60–80 harmful items, even 0 misses out of 70 gives a Clopper–Pearson upper bound of 5.1%. State the decision rule, or enlarge the positive class.
- **The RQ4 correction assumes equal error rates across respondents.** Correct within respondent group, or use prediction-powered inference (Angelopoulos et al., 2023); see Dorner, Nastl & Hardt on its limits.
- **G2 sampling.** Stratify the G2 draw by the keyword-baseline refusal flag to enrich commercial refusals and partial refusals, then weight back.
- **Replicates.** Run each API judge 2–3 times on a subset to measure test–retest noise.
- **Wording.** Drop "first" from the contribution claims.
- **Settings.** Note that a model's settings as respondent (provider default effort) and as judge (fixed effort) may differ.

## Novelty assessment
**Already known:**
- Fine-tuned 7B judges match GPT-4 on refusal labels (SORRY-Bench).
- Open guard models trailed prompted GPT-4 on refusal detection (WildGuard).
- Safety judges are brittle to output style (Eiras et al. 2025).
- Fake-harmful answers fool all output monitors (Panfilov et al. 2025).
- Model errors are correlated, more so as capability grows (Kim et al. 2025; Goel et al. 2025).
- Judges recognise and favour their own outputs (Panickssery et al. 2024; Wataoka et al. 2024) and related models' outputs (Li et al., ICLR 2026).
- Monitors go easy on in-context self-attributed actions (Khullar et al. 2026).
- Harmfulness and refusal are represented separately inside models (Zhao et al., NeurIPS 2025).
- Joint refusal/compliance audits already exist (Al Hasan & Biswas 2026: 21 open models on OR-Bench and XSTest).

**Genuinely new:**
- Blind self- and family-judging effects on refusal and harm classification across many judges.
- Behavioural harm recognition of refusal-removed judges against their base models.
- Error correlation on harmful-content misses, including guard classifiers.

**Not new:** RQ4, H2 and H3.

## Answers to §15
1. **Core design.** The concept is sound; the current balance is not. Add judge × stratum effects, relation levels and TOST. Prompt-matched blocks would give clean contrasts.
4. **Selection rules.** Keep the cap and the 6 GB limit as named strata. Fix the reasoning-score mismatch. Add a Google respondent and the Mistral bases.
5. **Judge settings.** Fix them. Name the reasoning effort explicitly and record reasoning tokens. Use temperature 0 where supported, otherwise the default with replicates. Add one exploratory low-vs-high effort ablation.
6. **Purpose-built baseline.** Yes (M4).
9. **Ethics.** See M7.
10. **Publishability.**
    - **What reviewers will criticise first:**
      - the single annotator;
      - missing prior work;
      - harmful answers only from small or uncensored models;
      - too many RQs;
      - selection rules written after the rankings.
    - **Single most important change:** make RQ2 the headline, as a balanced 2×2 (self vs other author × blind vs in-context) on harmful and borderline items. A second annotator and guard baselines are table stakes.
    - **Venues:** TMLR (best fit); ACL Rolling Review (Findings); NeurIPS 2027 Datasets & Benchmarks, if the gold set is released gated; ICLR or ICML 2027 safety or evaluation workshops.

## Suggested framing
**Do LLM safety judges go easy on themselves? Blind and in-context self-judging, shared blind spots and refusal-removed judges in refusal and harm classification.**

Benchmarks of refusal and harmful compliance rest on LLM judges, and AI-control proposals use LLMs as monitors, sometimes of their own outputs. We test 26 LLM judges and purpose-built guard classifiers on a two-annotator gold set, where each judge has also written a balanced share of the answers. Authorship is either hidden (fresh context) or implicit (the answer sits in the judge's own earlier turn). This lets us separate blind self- and family-bias from the in-context self-attribution bias reported by Khullar et al. (2026).

We also test whether removing refusals by abliteration preserves a model's ability to recognise harm, as representation work predicts, and whether judges share blind spots on harmful content. We report which judges are fit to use as instruments and refusal rates corrected for judge error. Implications for untrusted monitoring are discussed, not claimed.

## Sources the reviewer checked
- Kim et al. 2025: https://proceedings.mlr.press/v267/kim25e.html
- Zhao et al. 2025: https://neurips.cc/virtual/2025/poster/115056
- Khullar et al. 2026: https://arxiv.org/abs/2603.04582
- GRAFT blog: https://alignment.anthropic.com/2026/graft/
- Goel et al.: https://arxiv.org/abs/2502.04313
- SORRY-Bench: https://arxiv.org/abs/2406.14598
- Know Thy Judge: https://arxiv.org/abs/2503.04474
- Strategic dishonesty: https://arxiv.org/abs/2509.18058
- Preference leakage: https://arxiv.org/abs/2502.01534
- WildGuard: https://arxiv.org/abs/2406.18495
- Qwen3Guard: https://arxiv.org/abs/2510.14276
- gpt-oss-safeguard: https://openai.com/index/introducing-gpt-oss-safeguard/
- Dorner et al.: https://arxiv.org/abs/2410.13341
- OR-Bench (ICML): https://icml.cc/virtual/2025/poster/46052
- Al Hasan & Biswas 2026: https://arxiv.org/abs/2605.05427
- Vishnubhotla et al. 2026: https://arxiv.org/abs/2605.31381
- Dolphin 3.0 base: https://huggingface.co/cognitivecomputations/Dolphin3.0-Llama3.1-8B/blob/main/config.json
