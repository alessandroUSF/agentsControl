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

## Amendment 1: how models and judges are selected (8 November 2026, revised the same day)
> **First version.** It was written before any answer was scored, read or labeled, and was committed (e95a932) before it was applied.
>
> **This revision.** Applying the first version on 8 November showed that it could not be applied as written. The reasons are listed under "Revision" at the end. The criteria below were revised after the candidate rankings had been seen. At that point none of the newly selected models had been run, and no answer had been scored, read or labeled.
>
> **Lists and exceptions.** The lists these criteria produce are committed separately, together with the source snapshots (`data/selection/2026-11-08/`). Every model the criteria produce is kept unless it fails for a documented technical reason (for example, the API rejects the request).

**Common rules**
- **Snapshot:** the sources were downloaded on 8 November 2026 and are kept as downloaded in `data/selection/2026-11-08/`.
- **One model per developer in each group.** A model counts toward the developer that trained it. Models derived from another developer's model (distilled or fine-tuned) count toward that other developer.
- **No reruns:** a model already evaluated in an earlier group is not run again. Its answers are reused.
- **Exclusions and ties:** preview and experimental releases are excluded. Ties go to the more recent release.
- **Disk:** no single model download may exceed 20 GB.

**Rankings and prices**
- **API models:** the Artificial Analysis Intelligence Index v5 (v5.0.1). It is independent of the developers, combines about ten evaluations, and puts closed and open models on the same scale.
- **Open models run locally (the local panel and the judges):** the mean of Artificial Analysis's GPQA Diamond and Humanity's Last Exam scores.
  - On the snapshot date, v5 had scored only 12 of the 102 small and tiny open-weight models listed by Artificial Analysis. These two evaluations had been run on 99 of them.
  - When Artificial Analysis lists several settings of one model (for example, reasoning on and off), the model's highest listed score is used.
- **Prices:** the Artificial Analysis list price per 1M output tokens on the snapshot date. This is the standard price; temporary promotions are not used.

**Evaluated models**
1. **Pre-registered panel (unchanged):** Claude Sonnet 5.5, Claude Haiku 5.5, GPT-5.6 Luna, Llama 3.1 8B, Qwen3 8B and the abliterated control.
   - They were chosen on 7 November for cost and as common references. Llama 3.1 8B is also the base of the abliterated control.
   - H3 concerns only these models.
2. **Price cap for every added API model:** at most US$10 per 1M output tokens. That is the price of Claude Sonnet 5.5, the most expensive pre-registered model, so no added model costs more per token than one already pre-registered.
   - *Why:* cost, and the most expensive models are not the focus of this study.
3. **Most-used panel (exploratory, API):** the five developers with the most tokens on OpenRouter in the four weeks before the snapshot (OpenRouter weeks of 12 October to 2 November).
   - Each one contributes its most-used model in that window that meets the price cap and is generally available.
   - Free and paid variants of a model are counted together, and only text chat models count.
   - *Why first:* exposure. A refusal pattern matters in proportion to how many people meet it.
   - *Limitation:* OpenRouter is the only public per-model usage ranking. It over-represents developers and coding tools and leaves out first-party apps.
4. **Most-capable panel (exploratory, API):** the five developers whose best model within the price cap scores highest on the index. Each one contributes that model.
   - A developer may appear in both API panels, with its most-used model in one and its most capable affordable model in the other.
5. **Local panel (exploratory):** the three developers whose best open-weight model runs in 6 GB of video memory, ranked by the open-model ranking above.
   - That means Ollama's default 4-bit build is at most 5.5 GB, leaving about 0.5 GB for the context.
   - Models come only from the official Ollama library, and the exact build (digest) is recorded.
   - *Why 6 GB:* laptop and entry-level GPUs. On such a device no server-side filter exists, so the model's own refusal is the only safeguard.
   - Local models get no usage panel, because downloads are not use and local use cannot be observed.
- **Which prompts each panel gets:** groups 3 and 4 receive only the safe prompts and Alessandro's own prompts, as in the rule above. Group 5 receives all prompts.
- **Settings:**
  - API models run with the provider's default settings, like the pre-registered API models.
  - Local models run with thinking turned off where it can be switched off, like Qwen3 8B in the pre-registered panel.

**Judges**
- **Independence:** no judge comes from a developer of any evaluated model, in any group. Judges are selected after the evaluated models.
- **Eligibility:**
  - open weights, the official Ollama library and the 6 GB rule;
  - a score in the open-model ranking;
  - valid output on a five-answer format check that uses safe prompts only. A model that fails the check is replaced by the next one in the ranking.
- **Primary pair (tested in H1):** the two highest-ranked eligible models from different developers.
  - The higher-ranked of the two is also the arbiter.
  - This pair judges every answer.
- **Second pair (exploratory):** the next two eligible models in the ranking, from two further developers. The arbiter is chosen in the same way.
  - It judges only the gold-labeled answers, which is where blind spots are measured.
  - The question is whether a less capable monitor has more blind spots, or different ones.
- **Shared design:** both pairs use the same rule signals and the same prompts (`src/judge.py`). Judges use the same thinking setting as the local models.

**Gold labels**
- H1 is tested on the 150 answers drawn on 8 November (seed 20261109) from the three pre-registered local models, because the commercial runs had not started yet.
- When the later models' answers exist, a supplementary blind batch is drawn: 8 answers per model. This covers the pre-registered API models and the exploratory groups. It is labeled the same way, and H1 is also reported on the combined set.

**Revision: what changed from the first version, and why**
- **Ranking for open models.**
  - *Before:* the first version used the v5 index for every group.
  - *Problem:* v5 had scored too few small open models. Applied as written, it left two local developers (three were required) and one eligible judge (two were required).
  - *Change:* the GPQA Diamond and Humanity's Last Exam mean replaces v5 for open models only.
- **Second judge pair.**
  - *Before:* the two best eligible models of at most 2 GB.
  - *Problem:* every eligible model of that size came from a developer already being evaluated.
  - *Change:* the second pair is now the next two in the ranking.
- **API panels.**
  - *Change 1:* a price cap was added.
  - *Change 2:* the most-used panel now comes before the capability panel, and a developer may appear in both.
  - *Before:* the capability panel came first and was ranked without a price cap. The usage panel only added developers missing from it.
- **Additions:** the 20 GB disk limit, the thinking setting and the price source are now stated explicitly.
