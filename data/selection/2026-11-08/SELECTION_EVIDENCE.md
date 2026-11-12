# Selection evidence, 8 November 2026

This file checks the 22-model panel (`docs/STUDY_PROTOCOL_v2.md`, Section 6.2) against the selection rules, using only the files in this folder. Each stratum gives the rule, the ranked candidates with their numbers, the models the rule picks, and MATCH / MISMATCH against the panel. Excluded candidates and their reasons are listed in `EXCLUSIONS.md`.

## Sources and capture times

All files are kept as downloaded. File times are local EST (UTC-5) and are given here in UTC.

| Files | Saved (UTC, 8 Nov 2026) | Used for |
|---|---|---|
| `or_market_share_month.json`, `or_models_month.json`, `or_v1_models.json`, `aa_models_raw.json`, `aa_open_sizes.json`, `ollama_tags.json`, AA and OpenRouter `raw_pages` | about 17:12 | most used, most capable, OpenRouter uncensored |
| `ollama_tags_small.json`, `open_models_gpqa_hle_rank.txt`, `raw_pages/olq_*`, `olq2_*`, `olt_*` | about 17:44 | consumer GPU |
| `raw_pages/ols_*` (Ollama search pages), `olm_huihui_ai_*` (model pages) | about 21:07–21:08 | matched abliterated, Ollama uncensored |
| `raw_pages/hf_dolphin3.0-llama3.1-8b_README.md` | about 21:09 | Dolphin qualifies as uncensored |

**Timing caveat.** The Ollama search pages (`ols_*`) and model pages (`olm_*`) were captured on 8 Nov 2026 at about 21:07 UTC, after the panel was chosen the same day. Their download counts are therefore a check made after the selection, not the data the selection was made from. For example, `eriktonon/granite4.2-uncensored` shows 2,499 downloads in `olq_granite` (17:44 UTC) and 2,524 in `ols_abliterated` (21:07 UTC).

**What the data are, and what they are not.**
- `or_market_share_month.json` has one record per week. Each week lists only the nine largest named authors plus an `others` bucket, so an author outside the top nine in a week counts as 0 for that week. The week of 2 Nov runs to the capture day, so it may be incomplete.
- `or_models_month.json` is **not daily data**. It has one row per (model, variant), 742 rows. Each row is a total over OpenRouter's "month" view, and its `date` field (9 Oct to 7 Nov) appears to be the last day with traffic. For example, the single row for `deepseek/deepseek-v4.1-flash-20261017` holds 135.40 T tokens, more than DeepSeek's whole-developer total for the week of 2 Nov (77.82 T). The model-level window is therefore about 9 Oct–7 Nov, not the weeks of 12 Oct–2 Nov. Within a developer, models cannot be ranked on the exact rule window.
- OpenRouter prices below are the **standard** endpoint (not `:batch` or `:free`), as `pricing.completion` × 1e6 in `or_v1_models.json`.

## Summary

| Stratum | Panel | Rule result | Status |
|---|---|---|---|
| Pre-registered (1–6) | fixed on 7 Nov | not subject to the rules | n/a |
| Most used (7–10) | DeepSeek V4.1 Flash, GLM-5.3-Flash, GPT-6 Luna, Hy3 | same four. Anthropic's slot is empty because its pick, Sonnet 5.5, is already in the panel | **MATCH** on models. **MISMATCH** on the DeepSeek checkpoint: the rule picks `-1017`, but `config/models.json` calls `deepseek/deepseek-v4.1-flash`, which is the 0910 checkpoint |
| Most capable within cap (11–14) | GPT-6.1 Sol, Kimi K3.1 Pro, Grok 4.7, Hy4 | with the OpenRouter list price (the stated rule): GPT-6.1 Sol, **Gemini 4 Argon**, Kimi K3.1 Pro, Grok 4.7. With the AA price: the panel exactly | **MISMATCH** under the stated rule (Gemini 4 Argon instead of Hy4). MATCH only with AA prices |
| Consumer GPU (15–17) | qwen3.5:4b, granite4.2:8b, lfm2.5:8b-a1b | same, if "official" means `ollama.com/library` | **MATCH**, but the wording is ambiguous (see below) |
| Matched abliterated (18–19) | huihui_ai qwen3 8b-v2, huihui_ai qwen3.5 4B | same repositories. Llama's match is already in the panel (#6). Granite: `eriktonon/granite4.2-uncensored` has a card that says "Abliterated" | **MATCH** for 18–19. **AMBIGUOUS** for Granite. *Superseded for 19 (round 3, PI decision): model 19 is `kaineone/qwen3.5-4b-abliterated:latest`; the huihui_ai Qwen3.5 build is fine-tuned per its card. See the round-3 section below* |
| Ollama uncensored (20–21) | dolphin3, dolphin-mistral | dolphin3, then dolphin-mixtral (1,989,941), unless it is over 20 GB. No size is recorded | **MATCH, conditional**: excluding dolphin-mixtral is not documented in the snapshot |
| OpenRouter uncensored (22) | Venice Uncensored | Venice Uncensored (7.223 G tokens) | **MATCH** |

---

## 1. Most used (panel 7–10)

**Rule.** Take the top five developers by OpenRouter tokens summed over the weeks of 12 Oct to 2 Nov 2026, excluding `openrouter` and `others`. Each contributes its most-used generally available text chat model in that window, within the price cap of US$10 per 1M output tokens (OpenRouter list price), with free and paid variants counted together. Previews are excluded, no model enters twice, and derived models count toward the base developer.

**Developer ranking** (`or_market_share_month.json`, weeks 2026-10-12, -19, -26, 11-02):

| Rank | Author bucket | Tokens in the 4 weeks (T) | Weeks in the weekly top 9 | Model-file month total (T) |
|---|---|---|---|---|
| 1 | deepseek | 256.02 | 4/4 | 270.66 |
| 2 | z-ai | 76.36 | 4/4 | 83.05 |
| 3 | openai | 71.75 | 4/4 | 77.02 |
| 4 | anthropic | 56.90 | 4/4 | 61.41 |
| 5 | tencent | 53.28 | 4/4 | 55.24 |
| 6 | nvidia | 30.87 | 4/4 | 34.13 |
| 7 | google | 25.99 | 4/4 | 28.25 |
| 8 | stepfun | 25.43 | 3/4 | 36.67 |
| 9 | minimax | 22.77 | 2/4 | 29.89 |
| 10 | xiaomi | 20.41 | 2/4 | 33.61 |
| – | others (excluded) | 101.48 | – | – |

The top five are robust. Any author missing from a week had less than that week's ninth author (about 6–7 T), so no author can reach Tencent's 53.28 T. Sixth place is not robust. On the truncated weekly data NVIDIA is sixth (30.87 T), but StepFun could reach about 31.9 T and MiniMax about 35.8 T. On the model-file month totals StepFun is sixth (36.67 T). Sixth place matters only if an empty slot were refilled from the next developer, which the rules do not say.

**Model choice per developer** (`or_models_month.json`, all variants summed per canonical slug; standard OpenRouter output price):

| Developer | Candidates (tokens, US$/1M out) | Rule pick | Panel |
|---|---|---|---|
| DeepSeek | V4.1 Flash **1017** `-20261017` 135.400 T, $0.50; V4.1 Flash 0910 `-20260910` 97.634 T, $0.57; V4 Flash 0731 17.381 T, $0.28 | V4.1 Flash 1017 (`deepseek/deepseek-v4.1-flash-1017`) | #7 "DeepSeek V4.1 Flash". The AA score cited (32.6) is the 1017 record. `config/models.json` uses `deepseek/deepseek-v4.1-flash` (price_out 0.567), which is the **0910** checkpoint |
| Z.ai | GLM 5.3 Flash 58.010 T, $0.08; GLM 5.3 19.466 T, $1.40; GLM 5.2 4.122 T, $6.80 | GLM-5.3-Flash | #8, MATCH |
| OpenAI | GPT-6 Luna 33.931 T, $0.50; GPT-6.1 Sol 13.036 T, $10.00; GPT-5.6 Luna 11.086 T, $1.20 (pre-registered) | GPT-6 Luna | #9, MATCH |
| Anthropic | Claude Opus 5.5 29.499 T, **$20.00 (over cap)**; Claude Sonnet 5.5 10.986 T, $10.00; Claude Haiku 5.5 10.738 T, $0.50; Claude Sonnet 5 2.413 T, $10.00 | Claude Sonnet 5.5, which is already panel #1 | none added, MATCH |
| Tencent | Hy4 preview 32.381 T (**preview, excluded**); Hy3 12.769 T, $0.33; Hy4 (GA 4 Nov) 10.060 T, $1.25 | Hy3 | #10, MATCH |

**Why four, not five.** Anthropic is in the top five (56.90 T). Its most-used model, Claude Opus 5.5, is over the cap ($20.00 on OpenRouter, $20 on AA). Its most-used in-cap model is Claude Sonnet 5.5 at exactly $10.00, which is already pre-registered (#1). "No model enters twice" leaves the slot empty. Haiku 5.5, the next in-cap model, is also pre-registered.

**How the pre-registered developers were treated.** Anthropic and OpenAI were ranked like any other developer. Their pick entered unless it was already in the panel. OpenAI's pick, GPT-6 Luna, differs from the pre-registered GPT-5.6 Luna, so it was added. Anthropic's pick duplicates #1, so nothing was added. Neither the 6th developer nor Anthropic's next model (Claude Sonnet 5, 2.413 T) was used as a substitute. The rules allow neither, but they do not forbid them either.

**Ambiguities found.**
1. **Window.** The developer ranking uses the 4 weeks, but the model choice can only use the ~9 Oct–7 Nov month totals. The picks most sensitive to this: DeepSeek 1017 (released 17 Oct) vs 0910, and Tencent Hy3 (12.77 T) vs Hy4 (10.06 T, released 4 Nov). The month window adds 9–11 Oct, when Hy4 did not exist.
2. **Checkpoint vs model name.** "DeepSeek V4.1 Flash" covers two OpenRouter checkpoints with separate IDs. The rule picks 1017. The config calls 0910.
3. **Derived models.** OpenRouter author buckets are publishers, not base developers (for example, Venice is under `venice`/`cognitivecomputations`, Lunaris under `sao10k`). The market-share data cannot reassign them. The amounts are small (under 0.03 T per model), so the top five do not change.
4. **Price source.** The panel's "Out US$/1M" column uses Artificial Analysis prices, not OpenRouter list prices. DeepSeek V4.1 Flash is 1.20 in the panel vs 0.50 on OpenRouter (1017) or 0.57 (0910). GLM-5.3-Flash is 0.50 vs 0.08, Hy3 0.56 vs 0.33, Hy4 2.50 vs 1.25. None of these changes a most-used pick.

---

## 2. Most capable within cap (panel 11–14)

**Rule.** Take the top five developers ranked by the AA Intelligence Index v5 score of their best generally available API model priced at most US$10/M output (OpenRouter list price). Each contributes that model.

**Developer ranking.** Best AA v5 score at any reasoning setting, cap applied with each price source:

| Rank (OR price) | Developer | Best model ≤ cap | AA v5 | OR out $ | AA out $ | Rank (AA price) |
|---|---|---|---|---|---|---|
| 1 | OpenAI | GPT-6.1 Sol (Max) | 54.61 | 10.00 | 10 | 1 |
| 2 | Anthropic | Claude Sonnet 5.5 (Max) | 54.54 | 10.00 | 10 | 2 (in panel as #1) |
| **3** | **Google** | **Gemini 4 Argon (High)** | **50.41** | **10.00** | **20** | excluded (over cap) |
| 4 | Kimi / Moonshot | Kimi K3.1 Pro | 46.45 | 10.00 | 10 | 3 |
| 5 | SpaceXAI / xAI | Grok 4.7 (Xhigh) | 35.49 | 6.00 | 6 | 4 |
| 6 | Tencent | Hy4 | 34.56 | 1.25 | 2.501 | 5 |
| 7 | Alibaba | Qwen3.8 Max (0902) | 33.65 | 6.00 | 6 | 6 |
| 8 | DeepSeek | DeepSeek V4.1 Flash 1017 (Max) | 32.59 | 0.50 | 1.2 | 7 |
| 9 | Z AI | GLM-5.3 (Max) | 31.65 | 1.40 | 4.4 | 8 |
| – (Google already 3rd) | Google, AA price only | Gemini 3.8 Flash (High) | 30.85 | 4.125 | 3.75 | 9 |
| – (not on OpenRouter) | Thinking Machines | Inkling 2 Small | 30.63 | – | 1 | 10 |
| 10 | Xiaomi | MiMo-V2.6-Pro | 29.89 | 0.87 | 0.87 | 11 |

Removed before ranking: Gemini 4 Carbon (60.03; AA $20, not listed on OpenRouter), Claude Opus 5.5 (59.11; $20), GPT-6 Astra (56.85; $50), Meta Muse Wonder Full (50.08; no AA price, not on OpenRouter), Meta Muse Wonder (43.57; $20).

**Rule picks.**
- **Stated rule (OpenRouter list price).** GPT-6.1 Sol, Gemini 4 Argon, Kimi K3.1 Pro and Grok 4.7. Anthropic's pick, Sonnet 5.5, is already in the panel. Hy4 is sixth (34.56) and is **not** picked.
- **AA price.** GPT-6.1 Sol, Kimi K3.1 Pro, Grok 4.7 and Hy4. Anthropic's pick is already in the panel. This is the panel exactly.

**Status: MISMATCH under the stated rule.** Gemini 4 Argon costs $10.00 per 1M output on OpenRouter (`google/gemini-4-argon`; internal reasoning also $10/M) but $20 in the AA record. The panel's price column (Hy4 2.50 = AA 2.501) shows that AA prices were used. That alone explains the difference.

**Why four, not five.** As in most used, Anthropic's in-cap best, Sonnet 5.5 at exactly $10.00, is already panel #1. Anthropic has no other AA-scored model at or under $10 apart from Sonnet 5.5 and Haiku 5.5, both pre-registered.

**Ambiguities found.**
1. **Price source.** OpenRouter and AA disagree for Gemini 4 Argon ($10 vs $20), and this decides the stratum.
2. **Cap edge.** Four candidates sit exactly at $10.00: GPT-6.1 Sol, Sonnet 5.5, Kimi K3.1 Pro and Gemini 4 Argon. The rule must say "≤", and the protocol's "at most" does.
3. **Reasoning setting.** The ranking uses each model's best AA setting (usually Max), but runs use the provider default effort (Section 6.3). Defaults on OpenRouter: GPT-6.1 Sol medium (AA 46.35), Sonnet 5.5 high (41.52), Kimi max (46.45), Grok high (35.21), Gemini 4 Argon medium (no AA score; AA has High only). Ranking by default-effort scores gives the same top-five set, so this does not change the picks.

---

## 3. Consumer GPU (panel 15–17)

**Rule.** Take the top three developers whose best open-weight model has an official Ollama default 4-bit build of 5.5 GB or less, ranked by the mean of GPQA Diamond and HLE (AA scores).

**Ranking**, with "official" read as `ollama.com/library/...` and "best open-weight model" read as the best among those with a fitting build. This is the reading the panel follows.

| Rank | Developer | Best fitting model | Mean GPQA/HLE | GPQA | HLE | Official build (default tag, size) |
|---|---|---|---|---|---|---|
| 1 | Alibaba | Qwen3.5 4B (Reasoning) | 43.49 (non-reasoning 39.59) | 77.07 | 9.92 | `qwen3.5:4b`, 3.3 GB |
| 2 | IBM | Granite 4.2 8B | 36.41 | 63.13 | 9.68 | `granite4.2:8b` = latest, `f586c02fdecd`, 5.3 GB |
| 3 | Liquid AI | LFM2.5-8B-A1B | 29.09 | 51.31 | 6.86 | `lfm2.5:8b-a1b` = latest, `9cf756159fc2`, 5.2 GB |
| 4 | Allen Institute | Olmo 3 7B Think | 28.80 | 51.62 | 5.98 | `olmo-3:7b-think` = latest, 4.5 GB |
| 5 | NVIDIA | Nemotron 3 Nano 4B | 28.09 | 51.31 | 4.87 | `nemotron-3-nano:4b`, 2.8 GB |
| 6 | Google | Gemma 4 E2B (Reasoning) | 24.05 | 43.33 | 4.77 | `gemma4:e2b`, 4.6 GB |
| 7 | Mistral | Ministral 3 3B | 20.57 | 35.76 | 5.38 | `ministral-3:3b`, 3.0 GB |
| 8 | Microsoft | Phi-4 Mini Instruct | 18.79 | 33.13 | 4.45 | `phi4-mini`, 2.5 GB |

Removed before ranking (no `/library` build, or the build is over 5.5 GB): Nanbeige4.1-3B 47.92, Qwen3.5 9B 47.76 (`qwen3.5:9b` 6.6 GB), K2 Horizon 7B 46.73 and 3.7B 41.52, Ling 3.0 Tiny 41.37, MiniCPM5-2B 39.57, Falcon-H1R-7B 38.52, LFM2.5-2.6B 30.98, Gemma 4 E4B 30.66 (6.6 GB; QAT 6.1 GB), Exaone 4.0 1.2B 28.75, Ministral 3 8B 25.67 (6.0 GB). Details are in `EXCLUSIONS.md`.

**Rule picks:** Alibaba (qwen3.5:4b), IBM (granite4.2:8b), Liquid AI (lfm2.5:8b-a1b). **Status: MATCH** under this reading.

**Ambiguities found** (each would change the result):
1. **"Official" build.** Developers publish under their own Ollama namespaces: `/ifm/k2-horizon` (886 downloads; tags 0.9b, 3.7b, 7b, 32b, 36b; sizes not in the snapshot), `/openbmb/minicpm5-2b` (14,171) and `/LiquidAI/lfm2.5-2.6b` (2,684). If these count as official, the ranking becomes IFM K2 Horizon 7B 46.73, Alibaba 43.49, OpenBMB MiniCPM5-2B 39.57, and only then IBM 36.41. Liquid's pick would also become LFM2.5-2.6B (30.98). That would change two of the three picks, though the K2 Horizon 7B size cannot be checked here.
2. **"Best open-weight model".** Read literally, the developer's single best open model must fit. Alibaba's best (Qwen3.8 27B, mean 62.2) is 18 GB, IBM's (Granite 4.2 30B, 37.81) is 18 GB, and Liquid's (LFM2.5-2.6B, 30.98) has no `/library` build. All three panel developers would be out. The panel uses "best among fitting models".
3. **Margin.** Liquid AI (29.09) leads Allen Institute (28.80) by 0.29 points.
4. **Reasoning setting.** Qwen3.5 4B is run with thinking off (39.59) but ranked on the reasoning score (43.49). Either way it ranks first.
5. **"Default 4-bit build".** `qwen3.5:4b` (digest `492e37dc6907`) is not the same digest as `qwen3.5:4b-q4_K_M` (`d8b0f5e9760c`), although both are 3.3 GB. The config uses `granite4.2:8b-q4_K_M` and `lfm2.5:8b-a1b-q4_K_M`, which match their `latest` digests.

---

## 4. Refusal-removed, matched abliterated (panel 18–19)

**Rule.** For each open instruct model in the panel (4, 5, 15, 16, 17), take the most-downloaded Ollama build of the exact same checkpoint whose name or card says "abliterated". If no such build exists, take none.

| Base (panel #) | Candidates (downloads; source page) | Rule pick | Panel | Status |
|---|---|---|---|---|
| Llama 3.1 8B Instruct (4) | `mannix/llama3.1-8b-abliterated` 66,961; `richardyoung/llama-3.1-8b-instruct-abliterated` 5,571; `AutumnAurelium/llama3.1-abliterated` 1,055 (`ols_llama3.1_abliterated`) | mannix, already panel #6 | no new entry | MATCH |
| Qwen3 8B (5) | `huihui_ai/qwen3-abliterated` **406.4K** (repository total; `olm_*` page, tag `:8b` 5.0 GB, last update shown 7 Aug 2025); `richardyoung/qwen3-8b-abliterated` 5,800 (`ols_qwen3-abliterated_8b`) | huihui_ai/qwen3-abliterated, 8b | #18 `huihui_ai/qwen3-abliterated:8b-v2-q4_K_M` | MATCH on the repository. The `8b-v2` tag does not appear on the captured page, and the card says only "uncensored version of Qwen/qwen3 created with abliteration", without naming the 8B checkpoint. *Resolved in round 3: the tag is captured (`raw_pages/olm_huihui_ai_qwen3-abliterated_tags*`), and the Hugging Face card `huihui-ai/Huihui-Qwen3-8B-abliterated-v2` documents abliteration* |
| Qwen3.5 4B (15) | `huihui_ai/qwen3.5-abliterated` **729.5K** (729,483 in search; `:4B` 3.3 GB); `kiwi_kiwi/qwen3.5-abliterated` 5,144 (4b, 9b); `kaineone/qwen3.5-4b-abliterated` 1,580 (card names `Qwen/Qwen3.5-4B`, "Not fine-tuned"); `HammerAI/qwen3.5-abliterated` 1,478 | huihui_ai/qwen3.5-abliterated:4B | #19 (superseded) | MATCH as first recorded. The card names only the Qwen3.5 collection, not the 4B checkpoint. The protocol's open 4.5B-vs-4.2B parameter question cannot be checked from the snapshot, because parameter counts were not captured. *Superseded (round 3, PI decision: abliteration only): the build is fine-tuned per its Hugging Face card; #19 is `kaineone/qwen3.5-4b-abliterated:latest`, whose page names `Qwen/Qwen3.5-4B` and orthogonalisation and says "not fine-tuned"* |
| Granite 4.2 8B (16) | `eriktonon/granite4.2-uncensored` 2,499 (`olq_granite`, 17:44 UTC) / 2,524 (`ols_abliterated`, 21:07 UTC). Card: "UNCENSORED (Abliterated + SecOps LoRA) — IBM Granite 4.2 Uncensored (8B Compact & 30B Flagship…)". Size of `:8b` not captured | qualifies by the literal text (card says "Abliterated"); fails "exact same checkpoint" if the LoRA counts as a change | none ("no matched abliterated build within the rules") | **AMBIGUOUS**. The protocol gives no reason |
| LFM2.5 8B-A1B (17) | `virtuanista/lfm2.5-8b-a1b-uncensored` 365 ("Versión GGUF sin censura…"; says uncensored, not abliterated) | none | none | MATCH |

**Caveats.**
- Ollama reports downloads per repository, summed over all sizes, not per tag. "Most downloaded build of the exact checkpoint" is therefore measured at repository level.
- Search pages show about 20 results each, ordered by relevance rather than downloads. For example, `huihui_ai/qwen3-abliterated` does not appear in `ols_qwen3_abliterated`. A more-downloaded build could be missing from the snapshot.
- The mannix card says "Ablitered v3 llama-3.1 8b **with uncensored prompt**". This suggests a built-in system prompt, which is not pure abliteration. The Modelfile is not in the snapshot.

---

## 5. Refusal-removed, most downloaded uncensored on Ollama (panel 20–21)

**Rule.** Take models whose Ollama description or developer card states that they are uncensored or do not impose their own alignment. The Dolphin series qualifies through the Dolphin 3.0 card, whose lines 149 and 154 say "Dolphin does not impose its ethics or guidelines on you" and link to "uncensored-models". Rank by Ollama download count, one per base developer, with a download size of 20 GB or less.

| Rank | Build | Downloads | Base (developer) | Qualifies by | Result |
|---|---|---|---|---|---|
| 1 | `library/dolphin3` (8b) | 4,247,904 | Llama 3.1 8B pretrained (Meta; card `base_model: meta-llama/Llama-3.1-8B`) | Dolphin 3.0 card. The Ollama description does not say "uncensored" | **pick 1 (Meta)** = #20 |
| 2 | `library/llama2-uncensored` | 2,765,259 | Llama 2 (Meta) | description | Meta already used |
| 3 | `library/dolphin-llama3` | 2,230,566 | Llama 3 (Meta) | Dolphin series | Meta already used |
| 4 | `library/dolphin-mixtral` (8x7b, 8x22b) | 1,989,941 | Mixtral (Mistral) | description "Uncensored" | **pick 2 (Mistral) if ≤ 20 GB.** No tag size in the snapshot |
| 5 | `library/dolphin-mistral` (7b) | 1,881,526 | Mistral 7B (Mistral) | description "uncensored" | pick 2 if dolphin-mixtral is over 20 GB = #21 |
| 6 | `library/dolphin-phi` (2.7b) | 1,634,268 | Phi-2 (Microsoft) | description | third developer |
| 7 | `library/wizard-vicuna-uncensored` | 1,338,472 | Llama 2 (Meta) | description | Meta |
| 8 | `library/dolphincoder` | 1,070,928 | StarCoder2 | description | – |
| – | `huihui_ai/qwen3.5-abliterated` | 729,483 | Qwen3.5 (Alibaba) | card "uncensored version" | below the top two |

**Status: MATCH, conditional.** dolphin3 is a clean pick. dolphin-mistral is correct only if dolphin-mixtral is excluded for size. No dolphin-mixtral (or dolphin3, dolphin-mistral) tag size is recorded in the snapshot. The search card lists only the 8x7b and 8x22b sizes.

**Ambiguity.** The protocol (Section 6.1) says "one per base **family**", but the intended rule says "one per base **developer**". Under "family", `llama2-uncensored` (Llama 2 family, 2,765,259) would be second, ahead of every Mistral build. The search covered only the queries "uncensored", "dolphin" and "abliterated", about 20 results each, so the candidate pool is not exhaustive.

---

## 6. Refusal-removed, most used uncensored on OpenRouter (panel 22)

**Rule.** Take the uncensored model with the most tokens in the window.

Only two OpenRouter models state "uncensored" in their `or_v1_models.json` description:

| Model | Tokens (month file) | Out $ | Description |
|---|---|---|---|
| `cognitivecomputations/dolphin-mistral-24b-venice-edition` (permaslug `venice/uncensored`) | **7.223 G** | 0.90 | "designed as an 'uncensored' instruct-tuned LLM" |
| `thedrummer/cydonia-24b-v4.1` | 6.416 G | 0.50 | "Uncensored and creative writing model…" |

**Rule pick:** Venice Uncensored = #22. **Status: MATCH.**

**Caveats.**
- The lead is 12.6%, measured on the ~9 Oct–7 Nov month totals, not the rule window.
- OpenRouter descriptions in the snapshot are truncated ("…"). Higher-traffic role-play models whose saved text does not say "uncensored", such as `sao10k/l3-lunaris-8b` (20.163 G), `nousresearch/hermes-3-llama-3.1-70b` (4.332 G) and `nousresearch/hermes-4-405b` (4.090 G), cannot be fully checked.
- The protocol does not define "uncensored" for OpenRouter.

## Resolution (8 November 2026, before any answer from the affected models existed)
- **Most capable within the cap.** PI decision: the price source is the standard OpenRouter list price in `or_v1_models.json`, the price the study pays. Under that rule, Gemini 4 Argon (index 50.41, US$10.00) replaces Hy4 (34.56). Gemini 4 Argon is removed from the frontier-judge list, which keeps Claude Opus 5.5, GPT-6 Astra and Muse Wonder.
- **DeepSeek checkpoint.** `config/models.json` now calls `deepseek/deepseek-v4.1-flash-1017`. That is the checkpoint the rule selects, and the one whose index score (32.6) the protocol cites.
- **dolphin-mixtral:** excluded because its smallest library tag is 26 GB, over the 20 GB limit (`raw_pages/olm_dolphin-mixtral_tags.html.gz`, captured 8 November 2026).
- **Granite:** no matched abliterated build, because the only candidate (`eriktonon/granite4.2-uncensored`) adds a SecOps LoRA.
- **Rule wording** was tightened in protocol v2.2, Section 6.1, following the recommendations above.
- **Model 19 method.**
  - Its card (`raw_pages/hf_huihui-ai_Huihui-Qwen3.5-4B-abliterated_README.md`, captured 8 November 2026) names Qwen/Qwen3.5-4B as the base and documents refusal removal by fine-tuning with TRL, not abliteration.
  - PI decision: model 19 stays in the panel, and pair 15–19 is a secondary contrast outside T4. *Superseded in round 3: the matched rule was narrowed to abliteration only, model 19 was replaced by `kaineone/qwen3.5-4b-abliterated:latest`, and pair 15–19 is the third T4 pair.*
  - The cards of models 6 (via `mlabonne/Meta-Llama-3.1-8B-Instruct-abliterated`) and 18 (`huihui-ai/Huihui-Qwen3-8B-abliterated-v2`) document abliteration.
- **Model 6 build.**
  - The Ollama page (`raw_pages/olm_mannix_llama3.1-8b-abliterated.html.gz`) says the weights were "Abliterated by Maxime Labonne", with an "Uncensored prompt based on GuruBot".
  - The manifest confirms a 676-character built-in system prompt.
  - Judge build: `agentscontrol/llama3.1-8b-abliterated-judge` (same weights, model 4's template). See protocol v2.2, Section 8.3.
- **Default layers of all local models:** `ollama_default_layers.json` (8 November 2026).

## Round-3 clarifications and the model-19 replacement (8 November 2026)
Written after the snapshot had been seen and before any answer from the affected models existed.
- **Common rules (protocol Section 6.1).** Price = `pricing.completion` of the un-suffixed OpenRouter ID in `or_v1_models.json`. Size of a build = its `ollama.com/library/<name>:<size>` tag without a quantisation suffix. Re-applied to the snapshot, these reproduce every panel slot: slot 21 stays `dolphin-mistral` (dolphin-mixtral's `8x7b` is 26 GB), and the consumer-GPU Qwen build is `qwen3.5:4b` (3.3 GB).
- **Matched rule narrowed to abliteration only** (PI decision). Model 19 is `kaineone/qwen3.5-4b-abliterated:latest` (digest `4ad997605828`, Q4_K_M, 2.8 GB, text only), replacing `huihui_ai/qwen3.5-abliterated:4B` (fine-tuned per its card). See `EXCLUSIONS.md`, Resolutions.
- **Pinned digests** of every local model, from `/api/tags` on 8 November, are in `config/models.json`; rendering checks are in `ollama_default_layers.json` (`_render_checks_2026-11-08`).

## Round-4 additions (8 November 2026)
- **Token-level check of the T4 pairs** (`scripts/check_t4_tokens.py`, benign synthetic text): summary in `ollama_default_layers.json` (`_t4_token_check_2026-11-08`), full log in `results/logs/t4_token_check_2026-11-08.json`. All three pairs share the tokenizer and render identical prompt token IDs in both single-turn layouts; `think: false` is honoured. Model 19's GGUF has one extra multi-token-prediction block (`nextn_predict_layers` = 1); every shared tensor matches in name and shape, and greedy outputs share long identical prefixes.
- **Explicit tags** for models 16 and 17 (`granite4.2:8b-q4_K_M`, `lfm2.5:8b-a1b-q4_K_M`) resolve to the same digests as the size tags (`tag_note` in `config/models.json`).
