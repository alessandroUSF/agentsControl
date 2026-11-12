# Verification of auditor claims (8 November 2026)

These checks were made by the consolidating assistant against primary sources, the code and the data, before consolidation.

## Statistics (scipy, exact Clopper-Pearson)
Upper bounds on the missed-harmful rate for n gold-harmful items (rows); x is the number of misses.

| n | x=0, two-sided 95% | x=0, one-sided 95% | x=1 | x=2 |
|---|---|---|---|---|
| 50 | 7.1% | 5.8% | 10.7% | 13.7% |
| 59 | 6.1% | 4.95% | 9.1% | 11.7% |
| 72 | 4.99% | 4.1% | 7.5% | 9.7% |
| 110 | 3.3% | 2.7% | 4.96% | 6.4% |
| 142 | 2.6% | 2.1% | 3.9% | 5.0% |

0.98^60 = 0.298.

The figures given by auditors A and C are confirmed.

## Code (`src/judge.py`, `src/providers.py`, `src/run_models.py`, `src/gold_sample.py`)
All of the following were confirmed in the code:

- **Harmful flag on agreement.** When A and B agree on the label, the merge takes A's verdict, including A's `harmful_content`, even if B disagrees (C, C4).
- **Parsing.** `bool(out.get("harmful_content"))` turns the string "false" into True, and a missing flag into False (C, C4).
- **Truncation.** `clip()` keeps the head and tail of answers longer than 6,000 characters (A, B, C).
- **Venice routing.** `allowed()` blocks harmful prompts for every API provider, so Venice is blocked (A).
- **Keys.** `api_key_env` has no `AC_` check (A).
- **Resume.** The resume key is (model_key, prompt_id), without a prompt or configuration hash (C, M7).
- **Labeling sheet.** It has no harmful_content column (A).

## Snapshot data
- Qwen3.5 4B: 43.5 with reasoning, 39.6 without (A, B).
- Granite 4.2 8B: v5 index 5.1 (A).
- LFM2.5: the 8B-A1B scores 29.1 on GPQA+HLE; the 2.6B scores 31.0 but has no official Ollama build in the snapshot (A, C).

## Literature
**Verified (all checked on arXiv on 8 November 2026):**
- Khullar, Hopkins, Wang & Roger (2026), "Self-Attribution Bias: When AI Monitors Go Easy on Themselves", arXiv 2603.04582. Monitors under-flag risky actions presented in their own earlier turn; an explicit label alone does not create the bias. Coding and tool-use datasets only.
- Eiras, Zemour, Lin & Mugunthan (2025), "Know Thy Judge", arXiv 2503.04474, ICBINB workshop at ICLR 2025. Style changes raise safety-judge false negatives by up to 0.24.
- Panfilov et al. (2025), "Strategic Dishonesty Can Undermine AI Safety Evaluations of Frontier LLMs", arXiv 2509.18058. Dishonest answers fool all output-based monitors tested.
- Goel et al. (2025), "Great Models Think Alike and this Undermines AI Oversight", arXiv 2502.04313. Similar models rate each other more favourably, and errors converge as capability grows.
- Li et al., "Preference Leakage: A Contamination Problem in LLM-as-a-judge", arXiv 2502.01534, listed as ICLR 2026.
- Al Hasan & Biswas (2026), "The Refusal–Compliance Tradeoff", arXiv 2605.05427. An audit of 21 open models on OR-Bench, XSTest, ToxiGen and BOLD.
- Vishnubhotla et al. (2026), "LLM Judges Inconsistently Disagree Across Safety Criteria and Harm Categories", arXiv 2605.31381.
- Kim et al. (2025), Correlated Errors in LLMs, ICML 2025 (B).
- Zhao et al. (2025), harmfulness and refusal encoded separately, NeurIPS 2025, arXiv 2507.11878 (B).
- Dolphin 3.0 Llama 3.1 8B: its base model is the pretrained meta-llama/Llama-3.1-8B, per the Hugging Face card (B).

**Not found:** auditor C's "Mu's September 2026 paper" (a six-evaluator comparison against human labels). An extended search did not find it. Treat it as unverified, and do not cite it.

**Further related 2026 work found during the check** (titles from search; abstracts not yet read):
- "Style Over Substance: Content-Invariant Wrappers Flip LLM Safety-Judge Verdicts", arXiv 2609.08236.
- "Who Judges the Judges? A Chinese Safety QA Benchmark for Evaluating LLM Responses and Safety Judges", arXiv 2609.01210. It audits 7 automated safety judges against reference labels.
- "Safety is Contextual, LLM-Judges Are Not", arXiv 2606.07874. It scores judges against human labels.
- "Single Canonical Prompts Underestimate LLM Safety's Surface-Form Sensitivity", arXiv 2608.02665.
- "Expected Harm: Rethinking Safety Evaluation of (Mis)Aligned LLMs", arXiv 2602.01600.

*Implication:* meta-evaluation of safety judges against human labels is an active 2026 area. The protocol's novelty has to rest on self- and family-judging (blind vs in-context) and on refusal-removed judges, not on judge reliability as such.
