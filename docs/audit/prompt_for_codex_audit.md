You are an independent reviewer for a strong journal, with expertise in both research methodology/statistics and AI safety evaluation (LLM-as-a-judge, refusal and over-refusal benchmarks, AI control). A graduate researcher asks for a critical audit of his study protocol before he pre-registers it and runs the study. He intends to publish the result as a scientific paper. Your job is to find what is wrong, weak, missing or not novel, not to praise it. Other reviewers are auditing the same protocol separately; you will not see their reports.

**The working directory** is a read-only copy of the project repository:
- **`docs/STUDY_PROTOCOL_v2.md`:** the protocol under audit, and the main object of this review.
- **`docs/PREREGISTRATION_v1_public.md`:** the public version-1 pre-registration that the protocol revises. The protocol refers to it as `docs/PREREGISTRATION.md` at commit `4124f32`.
- **Other files:**
  - `README.md` and `labels/RUBRIC.md`;
  - `config/`;
  - `src/`: data preparation, the model runner, provider routing, the judge pipeline and the gold-set sampler;
  - `scripts/`;
  - `data/selection/2026-11-08/`: the model-selection snapshot.

Model answers, benchmark prompt files and secrets are deliberately not in this copy.

**Context**
- The study is set in November 2026. Model names you may not recognise (e.g. GPT-6.1 Sol, Claude Sonnet 5.5, Gemini 4 Argon, Kimi K3.1 Pro, Venice Uncensored) and the Artificial Analysis / OpenRouter / Ollama figures are real for that date. Do not flag unfamiliar model names, versions or prices as errors.

**Rules**
- Read-only: do not create, modify or delete any file.
- Do not run any model, API or network command. You may read files and run local read-only commands (e.g. `cat`, `grep`, or `python -c` for quick arithmetic).
- Cite literature only when you are confident it exists. Mark any reference you are unsure of as [unsure]. Never invent a citation.

**Audit both areas below.**

A. **Design, measurement and statistics**
1. **Core design.** Every respondent is also a judge, and a human gold set holds one self-judgment per item. Is the self-judging effect (RQ2) identified? Is the proposed mixed model appropriate? Propose a better specification if needed.
2. **Gold set.** Size, stratification, oversampling of harmful items, the two-stage draw, the harmful-content label, single annotator, re-label. Are design weights needed, and where?
3. **Instrument selection for RQ4.** Cross-validation vs split, the eligibility filter, the recusal rule, the misclassification correction.
4. **Confirmatory tests and power.** T1–T4 and H1–H3: well defined, testable, correctly corrected for multiplicity, adequately powered? Check the power statement with your own calculation.
5. **Metric definitions and the bootstrap design.**
6. **Pre-registration integrity.** The protocol is revised after the model rankings were seen but before any answer was judged or labeled. Is the change log transparent enough? What must be frozen, and when?
7. **Mismatches between the protocol and the code.** Cite file and line.

B. **AI safety relevance, novelty and publishability**
1. **Novelty.** What is already known in this area, and what in this protocol would be genuinely new? Which key references are missing?
2. **Framing.** Is the link to AI control and untrusted monitoring accurate, or overclaimed?
3. **Judge design.** The judge prompts in `src/judge.py`, the rubric, the harmful-content definition. Should a purpose-built safety classifier be a baseline? Which judge settings should be fixed? Are there judge-side confounds?
4. **Model selection.** Are the rules coherent and defensible? Check them against the snapshot data.
5. **Ethics, safety and terms of service.**
6. **Reviewers' first criticisms.** What would reviewers at a strong venue criticise first? What single change would most improve publishability? Which venues are realistic?

**Output** (in English, as your final message)
- **Verdict:** 3–5 sentences.
- **Critical issues** (would invalidate a main conclusion), then **major issues**, then **minor issues**. For each: the protocol section, the problem, why it matters, and a concrete fix.
- **Novelty assessment.**
- **Answers to the protocol's Section 15 open questions,** briefly.
- **Recommended changes,** as specific text or formulas the author can paste.

Be concrete and quantitative where possible. Keep it under about 2,500 words.
