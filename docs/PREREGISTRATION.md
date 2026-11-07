# Pre-registration

> Written by Alessandro Almeida on 7 November 2026, before any analysis of model outputs. The commit date of this file is the timestamp of the predictions.
>
> **What had happened before this commit:**
> - The local-model answers were generated sealed from 7 November onward. Nobody read or scored them before this file was committed.
> - Only technical checks were run, on a 50-prompt pilot: errors, truncation, latency and output length.
> - The commercial models had not been run.

## Hypotheses
The monitor question comes first because it is the project's main question. The GRAFT authors note that LLM-based monitors may make different kinds of systematic errors (Ward, Hu et al., 2026); H1 measures where those errors fall.

**H1. The multi-agent judge will be reliable.** Compared with Alessandro's blind gold labels:
- agreement will be high (Cohen's kappa ≥ 0.80);
- the judge will rarely let a harmful answer through (missed harmful compliance < 5%);
- most of its errors will be missed refusals, especially partial refusals, rather than missed harmful answers.
- *Test:* kappa with bootstrap CI, and miss rates by error type with bootstrap CIs.

**H2. Stated context lowers refusals.** On Alessandro's own prompts (see the categories below), both stated contexts will lower refusals compared with no context: "I am an adult screenwriter" and "I am a student". The adult-screenwriter context will lower them more than the student context.
- *Test:* paired comparisons on the same prompt across framings, per model (McNemar or permutation test), with bootstrap 95% CIs on the differences.

**H3. Over-refusal by model.** On the safe prompts (XSTest safe, OR-Bench Hard-1K), the Claude models (Sonnet 5.5 and Haiku 5.5) will have the highest over-refusal rate, followed by GPT-5.6 Luna. The two standard open-weight models will over-refuse less than GPT-5.6 Luna, and Llama 3.1 8B will over-refuse more than Qwen3 8B. The abliterated control (Llama 3.1 8B with the refusal direction removed) will refuse almost none of them.
- *Test:* over-refusal rate per model with bootstrap 95% CIs. Pairwise McNemar tests on the same prompts: each Claude model vs GPT-5.6 Luna, GPT-5.6 Luna vs each standard open-weight model, and Llama 3.1 8B vs Qwen3 8B.

## Fixed before analysis
- Benchmarks pinned and hash-checked (`data/SHA256SUMS.txt`); sample drawn with seed 20261106 (`src/prepare_data.py`).
- Models and settings: `config/models.json`.
- Alessandro's own prompts (`data/own/own_prompts.csv`) fall into two categories: mature themes in fiction for adults (non-explicit), and everyday dual-use requests, such as opening a padlock. Each prompt runs under three framings: no context, adult screenwriter and student.
- Commercial APIs receive only safe prompts and Alessandro's own non-harmful prompts. The benchmarks' harmful prompts run only on local models (`src/providers.py`, `allowed`).
- Labels: three classes (`labels/RUBRIC.md`). The gold set is about 150 answers, stratified by model and source, and labeled blind to the judge. It oversamples answers to harmful prompts, including the abliterated control, so that it holds at least 60 harmful answers. With fewer, the < 5% miss rate in H1 could not be tested.
- Anything not listed here is reported as exploratory.
