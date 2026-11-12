# Amendment 2 to the pre-registration: withdrawal of H1–H3 and replacement of the design (DRAFT)

> Draft of 10 November 2026, revised on 11 November with the PI's decisions D12, D14, D15, D16 and the part of D2 on model 14, and on 12 November with D1, the rest of D2 and D17. Committed locally on 11 November 2026, except the changes made since then; not registered and not pushed. It becomes effective only when it is
> committed and pushed together with protocol v2.3 and registered on OSF, before the pilot of protocol v2.3
> starts (protocol v2.3, Section 14.1). Nothing is pushed or registered without the explicit instruction of the
> principal investigator. Section numbers below refer to `docs/STUDY_PROTOCOL_v2.3.md`.

## 1. What is public and what is not

| Record | Date | Status | Content |
|---|---|---|---|
| Pre-registration v1 (commit `4124f32`) | 7 November 2026 | Public on GitHub | H1, H2, H3; six models; gold set of about 150 answers; commercial APIs receive only safe prompts and the author's own non-harmful prompts. |
| Amendment 1 (commit `e95a932`) | 8 November 2026 | Committed locally, never pushed | Criteria for added models and for independent judges. Revised the same day; the revision was never committed. |
| Protocol v2.0–v2.2 | 8–10 November 2026 | Working copy only | Expanded design (22 models, instrument selection, RQ4, self-judging tests T1–T4). Never registered. |
| Protocol v2.3 | 10 to 12 November 2026 | Working copy; registered together with this amendment | The design that replaces v1 and v2.2 (Section 4 below). On 11 November the PI added model 23, pinned one endpoint for each model reached through OpenRouter, and moved model 14 to Google's own API (decisions D15, D16 and D2). On 12 November model 14 left the study before any call, because its price doubles on 1 December 2026 (decision D17). |

Amendment 1 is reproduced unchanged in the appendix of this amendment, together with its uncommitted revision,
so that the public record shows how the model panel was chosen. The push that publishes this amendment also
publishes commit `e95a932` for the first time. The dates of the model selection, from the public version 1 to the decisions of 11 November, are listed in Section 3.2 of the protocol. On 11 November 2026 the list of hashes of the selection files was stamped with OpenTimestamps (protocol Section 19.2, action 22).

## 2. Withdrawal statement

Before any confirmatory answer was inspected, judged or labelled, the author withdrew H1–H3 and the
instrument-selection/RQ4 programme from this execution because the expanded design exceeded available
resources. These hypotheses remain publicly documented and are not tested in this paper. Any future execution
will receive a separate registration identifying this amendment and all intervening data exposure.

## 3. Hypothesis by hypothesis

| Item of v1 | Registered text (short) | Status | Why | Data that existed at withdrawal |
|---|---|---|---|---|
| H1 | The multi-agent judge agrees with the author's blind gold labels (kappa of at least 0.80; missed harmful compliance under 5%; errors mostly missed refusals). | Withdrawn from this execution. Not tested, not reported as a result. | The multi-agent judge is not run. The study now measures how each model judges its own answers. | The 150 answers of the gold sample had been drawn (8 November, seed 20261109) and sealed. No label existed. No judge had run. No person had read an answer. |
| H2 | On the author's own prompts, a stated context ("adult screenwriter", "student") lowers refusals; the screenwriter context lowers them more. | Withdrawn from this execution. | The own prompts leave this paper; they need their own design and budget. | The 60 base prompts existed (written 9 November). No model had answered any of them. |
| H3 | On the safe prompts, the two Claude models over-refuse most, then GPT-5.6 Luna, then the two standard open-weight models (Llama above Qwen); the abliterated control refuses almost nothing. | Withdrawn from this execution. | The commercial models now answer 150 prompts each, not the 550 safe prompts that H3 needs, and no refusal classifier is validated in this paper. | Answers of the three local models to the 550 safe prompts existed, sealed and unread. No commercial model had been called. |
| Gold set | About 150 answers, labelled by the author, blind to the judge. | Replaced by a probability sample of 567 answers. The author labels all of them and a second annotator labels 381 (Section 9). | Labels by one person who also designed the study are not an adequate reference for harm. | As for H1. The 150-answer sample is retired. It was never labelled. |
| Commercial APIs | Receive only safe prompts and the author's own non-harmful prompts; harmful benchmark prompts run only on local models. | Replaced (Sections 5.2 and 16). | Self-judging of harmful answers cannot be measured on commercial models without harmful prompts. Calls use separate research accounts and are limited to the frames of protocol v2.3. | No commercial model had been called. |
| Models | Six models (`config/models.json`). | Extended to 23 selected models (Section 3). Model 23 was added on 11 November 2026 (decision D15). Model 14 left on 12 November 2026, before any call (decision D17), so 22 models take part. | See the appendix (Amendment 1) and Section 3.2. | Seven local models had generated 7,457 answers (see `docs/DATA_INVENTORY.md`), sealed and unread. |

Everything that v1 did not list was to be "reported as exploratory". This amendment replaces that rule with the
confirmatory tests, the registered secondary analyses and the descriptions listed in protocol v2.3
(Sections 8.2 and 8.5).

Data exposure between v1 and this amendment, in full (Section 15.3):

- Answers generated and sealed: 7,457, by seven local models. No person has read, screened, judged or labelled
  one. The principal investigator signs this statement with the registration (Section 19.3).
- Retired sample G1: 150 answers of three local models, drawn under protocol v2.2 on 8 November 2026 and
  sealed. The sampler copied each drawn request and answer into a labelling sheet and printed counts only. On
  10 November 2026 scripts read the response identifier of each row of the key, to find its prompt, and
  printed counts only (`docs/SEALED_HASHES.md`). No label exists.
- Earlier technical pilot (7 November): 50 prompts, three local models, 150 answers; only errors, truncation,
  latency and length were checked.
- Judging calls, API calls and labels: none. Money spent on model calls: none.

## 4. What replaces the withdrawn design

The replacement is protocol v2.3. This table is a guide to it, not a second registration: where the two
differ, the protocol is the registered text.

| Element | Protocol v2.3 | Sections |
|---|---|---|
| Questions | Does a model flag harmful content less often when an answer is shown as its own previous turn than when the same answer is shown as quoted text? Is that change larger for the model that wrote the answer than for an unrelated model of the same type that sees the same answer in the same two ways? | 1, 2 |
| Primary panel | Twelve open models: five instruction-tuned and seven with refusals removed. Each model answers the prompts and judges answers. Whether each of the two hosted models (22 and 23) belongs to the registered panel is fixed at the freeze. | 3, 10.4 |
| Commercial panel | Ten commercial models, described on a common set of 60 harmful prompts. No test rests on them. | 3, 8.6 |
| Material | 300 harmful prompts from two public benchmarks (150 XSTest unsafe, 150 OR-Bench Toxic) and 90 safe prompts. | 4, 5 |
| Verdicts | Four per answer: the author blind and in context, and a control judge of the same type, unrelated to the author, blind and in context. | 6, 11 |
| Outcome | Flag: a delivered valid verdict that says the answer has harmful content. An undelivered verdict counts as no flag. | 2, 10 |
| Confirmatory tests | P1 (the author's change from blind to in context is zero) and P2 (that change equals the control's change), two-sided, Holm at .04. P3 (the author's blind flag rate is 7 points or more below the control's), one-sided at .01. All among screen-positive answers. | 2, 8 |
| Inference | Stratified cluster ratio estimator with a t test; the prompt is the cluster and the two sources are the strata. | 8, Appendix A |
| Human labels | A probability sample of 567 answers. The author labels all of them; a second annotator labels 381. Without a committed second annotator the statements that depend on labels are withdrawn before the freeze. | 9, 14.4 |
| Money | Hard cap of US$128 for all API calls; freeze ceiling US$124. | 12 |
| Registration | Two steps: a pilot registration before the first pilot call, and a freeze before any confirmatory answer is generated, screened or judged. Only the changes listed in Section 14.3 may happen in between. | 13, 14 |
| Existing answers | The 7,457 sealed answers are kept and used under the rules of Sections 3.4 and 15.3. | 3.4, 15.3 |

## 5. Review and conflicts of interest

- The design was reviewed in rounds by a language model, GPT-6.1 Sol, which is also model 11 of the commercial
  panel.
- The text, the code and the simulations were drafted with an AI coding assistant, Claude Code of Anthropic,
  the developer of models 1 and 2.
- No person other than the principal investigator has reviewed the design.
- The PI's decisions of 11 November 2026 (D12, D14, D15, D16 and the part of D2 on model 14) and of 12 November 2026 (D1, the rest of D2 and D17) came after review round 4. No review round has checked them yet; the next one, of the code and a synthetic run, does (protocol Section 17.1).
- Section 17 of the protocol gives the record of each review round and the safeguards. Section 19 lists what
  the principal investigator still has to decide and do.

## Appendix. Amendment 1 and its unpublished revision

Both texts are reproduced unchanged, as blocks of plain text. Neither is in force: the rules that produced the
panel are those of Section 3.2 of protocol v2.3, and the panels, judge pairs and gold plan of Amendment 1 are
not used (Section 15.1).

| Text | Source | Lines | SHA-256 of the reproduced text |
|---|---|---|---|
| A.1 Amendment 1 as committed | `docs/PREREGISTRATION.md` at commit `e95a932` (8 November 2026, never pushed), from the heading "Amendment 1" to the end | 45 | `5a41049208897554223890c66436df55b72bdb287b87985f191de31032f2aa90` |
| A.2 Revision of the same day, never committed | Working copy of the same file on 10 November 2026, from the heading "Amendment 1" to the end | 76 | `d4465548c2f221371fb5cbcfae3d680e0a4604034f7b237549eb46b4278dddd0` |

- The whole working copy is kept as `docs/audit/2026-11-08_PREREGISTRATION_working_copy_with_unpublished_revision.md` (SHA-256 `d0e31cf9c27832d63d3638968021b3bfed502e3daef7e66b9035c4c69d24ec8a`).
- After that copy was made, `docs/PREREGISTRATION.md` was restored to its committed state, so that the file
  holds version 1 and Amendment 1 exactly as committed.
- Version 1 (commit `4124f32`) is the first part of both files and is unchanged in the committed file.

### A.1 Amendment 1 as committed (commit `e95a932`)

````text
## Amendment 1: how models and judges are selected (8 November 2026)
> Written before any answer was scored, read or labeled, and before these criteria were applied. The lists they produce are committed separately, together with the source snapshots. Some candidate names were discussed informally before this amendment. The lists are decided by these criteria, not by those discussions. Every model the criteria produce is kept unless it fails for a documented technical reason (for example, the API rejects the request).

**Common rules**
- **Ranking:** the Artificial Analysis Intelligence Index v5.
  - It is independent of the developers, combines about ten evaluations, and puts closed and open models on the same scale.
  - A model without a v5 score is not eligible.
  - Scores refer to the original model. Local runs use Ollama's default 4-bit build.
- **Snapshot:** the index and the usage ranking below are saved under `data/selection/` on the day the criteria are applied. Their date is recorded in the files.
- **One model per developer in each group.** A model counts toward the developer that trained it. Models derived from another developer's model (distilled or fine-tuned) count toward that other developer.
- **Exclusions and ties:** preview and experimental releases are excluded. Ties go to the more recent release.
- **No reruns:** a model already evaluated in an earlier group is not run again. Its answers are reused.

**Evaluated models**
1. **Pre-registered panel (unchanged):** Claude Sonnet 5.5, Claude Haiku 5.5, GPT-5.6 Luna, Llama 3.1 8B, Qwen3 8B and the abliterated control.
   - They were chosen on 7 November for cost and as common references. Llama 3.1 8B is also the base of the abliterated control.
   - H3 concerns only these models.
2. **Frontier panel (exploratory, API):** the five developers whose best model scores highest on the index. Each one contributes its highest-scoring model that is generally available through a public API.
3. **Most-used panel (exploratory, API):** the five developers with the most tokens on OpenRouter in the four weeks before the snapshot.
   - Each developer not already in the frontier panel contributes its most-used model in that window.
   - Free and paid variants of a model are counted together, and only text chat models count. If the most-used model is a preview, the next generally available model is taken.
   - *Why:* exposure. A refusal pattern matters in proportion to how many people meet it, and a heavily used developer can fall outside the top five of the index.
   - *Limitation:* OpenRouter is the only public per-model usage ranking. It over-represents developers and coding tools and leaves out first-party apps.
   - Local models get no usage panel, because downloads are not use and local use cannot be observed.
4. **Local panel (exploratory):** the three developers whose best open-weight model runs in 6 GB of video memory.
   - That means Ollama's default 4-bit build is at most 5.5 GB, leaving about 0.5 GB for the context.
   - Models come only from the official Ollama library, and the exact build (digest) is recorded.
   - *Why 6 GB:* laptop and entry-level GPUs. On such a device no server-side filter exists, so the model's own refusal is the only safeguard.
- **Which prompts each panel gets:** groups 2 and 3 receive only the safe prompts and Alessandro's own prompts, as in the rule above. Group 4 receives all prompts.

**Judges**
- **Independence:** no judge comes from a developer of any evaluated model, in any group. Judges are selected after the evaluated models.
- **Eligibility:** open weights, the official Ollama library, the same 6 GB rule and an index v5 score. Each candidate must also return valid output on a five-answer format check that uses safe prompts only. A model that fails the check is replaced by the next one in the ranking.
- **Primary pair (tested in H1):** the two highest-scoring eligible models from different developers.
  - The higher-ranked of the two is also the arbiter.
  - This pair judges every answer.
- **Small pair (exploratory):** the two highest-scoring eligible models of at most 2 GB (about 3B parameters).
  - Both come from different developers, and neither is in the primary pair. The arbiter is chosen in the same way.
  - It judges only the gold-labeled answers, which is where blind spots are measured.
  - The question is whether a much smaller monitor has more blind spots, or different ones.
- Both pairs use the same rule signals and the same prompts (`src/judge.py`).

**Gold labels**
- H1 is tested on the 150 answers drawn on 8 November (seed 20261109) from the three local models, because the commercial runs had not started yet.
- When the later models' answers exist, a supplementary blind batch is drawn: 8 answers per model. This covers the pre-registered API models and the exploratory groups. It is labeled the same way, and H1 is also reported on the combined set.
````

### A.2 Revision of 8 November 2026, never committed

````text
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
````
