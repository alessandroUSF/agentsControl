# Exclusions, 8 November 2026 selection

This file lists every candidate the selection rules would pick, or that ranks above a panel pick, but that is not in the panel, with the reason found in the snapshot (`data/selection/2026-11-08/`). Where the snapshot holds no reason, the entry says **reason not documented**. Numbers and rankings are in `SELECTION_EVIDENCE.md`.

The Ollama search and model pages (`raw_pages/ols_*`, `olm_*`) were captured on 8 Nov 2026 at about 21:07 UTC, after the panel was chosen. Download counts taken from them are a later check.

## A. Rule picks that differ from the panel

| Stratum | Candidate the rule picks | Numbers | Panel instead | Reason |
|---|---|---|---|---|
| Most capable within cap | **Gemini 4 Argon (High)**, Google (`google/gemini-4-argon`) | AA v5 50.41, 3rd of the developers; OpenRouter list price **$10.00**/1M out (within cap); AA price $20 | Hy4 (34.56), which is 6th under OpenRouter prices | Over the cap **only by the AA price** ($20). With the OpenRouter list price, the stated cap source, it is within the cap. The panel's price column follows AA prices (Hy4 2.50 = AA 2.501; OpenRouter 1.25). **Resolved (see Resolutions): Gemini 4 Argon is model 14** |
| Most used (DeepSeek) | **DeepSeek V4.1 Flash 1017** (`deepseek/deepseek-v4.1-flash-1017`, canonical `-20261017`) | 135.400 T tokens, $0.50; the 0910 checkpoint has 97.634 T, $0.57 | `config/models.json` calls `deepseek/deepseek-v4.1-flash` (= canonical `-20260910`, price_out 0.567). The protocol table says only "DeepSeek V4.1 Flash" and cites the 1017 AA score (32.6) | **Reason not documented.** The two checkpoints have different OpenRouter IDs. The rule picks 1017. **Resolved: the config calls the 1017 checkpoint** |
| Ollama uncensored (Mistral slot) | **`library/dolphin-mixtral`** | 1,989,941 downloads, ahead of dolphin-mistral at 1,881,526; sizes on the card are 8x7b and 8x22b only | `dolphin-mistral` (#21) | **Reason not documented** in the first snapshot. **Resolved (see Resolutions):** the build of its smallest parameter size, `dolphin-mixtral:8x7b`, is 26 GB, over 20 GB |
| Matched abliterated (Granite 4.2 8B) | **`eriktonon/granite4.2-uncensored:8b`** (if "card says abliterated" is read literally) | 2,499 downloads (`olq_granite`, 17:44 UTC), 2,524 (`ols_abliterated`, 21:07 UTC). Card: "UNCENSORED (Abliterated + SecOps LoRA) — IBM Granite 4.2 Uncensored (8B Compact & 30B Flagship…)" | none (protocol: "Granite and LFM2.5 have no matched abliterated build within the rules") | **Reason not documented** in the first snapshot. **Resolved (see Resolutions):** it adds a SecOps LoRA, and the matched rule admits abliteration only |

## B. Slots left empty because the rule's pick is already in the panel

| Stratum | Developer / base | Rule pick | Numbers | Reason |
|---|---|---|---|---|
| Most used | Anthropic (4th, 56.90 T) | Claude Sonnet 5.5 | most-used in-cap Anthropic model, 10.986 T, $10.00 | **Already in panel** (#1, pre-registered). No model enters twice. Next in-cap model: Haiku 5.5 (10.738 T, also pre-registered). The rules provide no substitution, so the stratum has 4 models |
| Most capable within cap | Anthropic (2nd, 54.54) | Claude Sonnet 5.5 (Max) | AA v5 54.54, $10.00 | **Already in panel** (#1). Anthropic has no other AA-scored model at or under $10 apart from Haiku 5.5 (#2). The stratum has 4 models |
| Matched abliterated | Llama 3.1 8B Instruct (#4) | `mannix/llama3.1-8b-abliterated` | 66,961 downloads, top of `ols_llama3.1_abliterated` | **Already in panel** (#6, pre-registered) |

## C. Higher-ranked candidates removed by a filter before the pick

### Most used (OpenRouter)
| Candidate | Numbers | Reason |
|---|---|---|
| Claude Opus 5.5 (Anthropic's most-used model) | 29.499 T | **Over cap**: $20.00 OpenRouter, $20 AA |
| Tencent Hy4 preview (Tencent's most-used model) | 32.381 T | **Preview**. Next is Hy3 (12.769 T), then Hy4 GA (10.060 T, released 4 Nov) |
| NVIDIA (6th developer by weekly data, 30.87 T) or StepFun (6th by model-file month totals, 36.67 T) | – | **Outside the top five.** These would matter only if empty slots were refilled from the next developer, which the rules do not provide. StepFun's top model, Step 5 Preview (35.791 T), is a preview |

### Most capable within cap (AA Intelligence Index v5)
| Candidate | AA v5 | Reason |
|---|---|---|
| Gemini 4 Carbon (High), Google | 60.03 | **Over cap** (AA $20). **Not listed on OpenRouter** |
| Claude Opus 5.5 (Max), Anthropic | 59.11 | **Over cap** ($20) |
| GPT-6 Astra (Max), OpenAI | 56.85 | **Over cap** ($50) |
| Muse Wonder Full (Max), Meta | 50.08 | **No price**: AA price null, not on OpenRouter (no API list price) |
| Muse Wonder (Max), Meta | 43.57 | **Over cap** ($20 on AA and OpenRouter) |
| Qwen3.8 Max (0902), Alibaba | 33.65 | 6th by AA price, 7th by OpenRouter price. **Outside the top five** |

### Consumer GPU (mean of GPQA Diamond and HLE; build ≤ 5.5 GB)
| Candidate | Mean GPQA/HLE | Reason |
|---|---|---|
| Nanbeige4.1-3B, Nanbeige | 47.92 | **No official Ollama build**: only third-party builds such as `tomng/nanbeige4.1` (7,680 downloads) in `olq_nanbeige` |
| Qwen3.5 9B (Reasoning), Alibaba | 47.76 | **Over 5.5 GB**: `qwen3.5:9b` is 6.6 GB. Alibaba enters with Qwen3.5 4B |
| K2 Horizon 7B / 3.7B, Institute of Foundation Models | 46.73 / 41.52 | **No `/library` build.** It exists only in the developer namespace `/ifm/k2-horizon` (886 downloads; sizes not in the snapshot) |
| Ling 3.0 Tiny, InclusionAI | 41.37 | **No Ollama build found** (`olq2_ling`) |
| MiniCPM5-2B, OpenBMB | 39.57 | **No `/library` build.** It exists only in the developer namespace `/openbmb/minicpm5-2b` (14,171 downloads) |
| Falcon-H1R-7B, TII | 38.52 | **No official build** (third-party `sam860/falcon-h1` only) |
| LFM2.5-2.6B, Liquid AI | 30.98 | **No `/library` build.** It exists only as `/LiquidAI/lfm2.5-2.6b` (2,684). Liquid enters with LFM2.5-8B-A1B (29.09) |
| Gemma 4 E4B (Reasoning), Google | 30.66 | **Over 5.5 GB**: default `gemma4:latest`/e4b q4_K_M is 6.6 GB, QAT 6.1 GB. Google's best fitting model is Gemma 4 E2B (24.05), ranked 6th |
| Exaone 4.0 1.2B (Reasoning), LG AI Research | 28.75 | **No official build** (`/library` has exaone-deep and exaone3.5 only; `ingu627/exaone4.0` and `sam860/exaone-4.0` are third-party) |
| Olmo 3 7B Think, Allen Institute | 28.80 | Fits (`olmo-3:7b-think`, 4.5 GB) but ranks **4th**, 0.29 points behind Liquid AI (29.09) |
| Ministral 3 8B, Mistral | 25.67 | **Over 5.5 GB**: `ministral-3:8b-instruct-2512-q4_K_M` is 6.0 GB |

### Matched abliterated (other builds considered)
| Base | Candidate | Downloads | Reason not chosen |
|---|---|---|---|
| Qwen3 8B | `richardyoung/qwen3-8b-abliterated` | 5,800 | Fewer downloads than `huihui_ai/qwen3-abliterated` (406.4K, repository total) |
| Qwen3.5 4B | `kiwi_kiwi/qwen3.5-abliterated` (4b, 9b); `kaineone/qwen3.5-4b-abliterated` (card names `Qwen/Qwen3.5-4B`) | 5,144; 1,580 | First snapshot: fewer downloads than `huihui_ai/qwen3.5-abliterated` (729.5K). **Superseded:** under the abliteration-only rule, huihui is excluded and kaineone is model 19; kiwi_kiwi has no card naming a base checkpoint or method (see Resolutions) |
| LFM2.5 8B-A1B | `virtuanista/lfm2.5-8b-a1b-uncensored` | 365 | **Not abliterated by name or description** ("sin censura" = uncensored; method not stated) |

### Most downloaded uncensored on Ollama
| Candidate | Downloads | Reason |
|---|---|---|
| `library/llama2-uncensored` (Llama 2, Meta) | 2,765,259 | **One per base developer**: Meta is already taken by dolphin3 (4,247,904). Under the protocol's wording "one per base family" it would be picked second |
| `library/dolphin-llama3` (Llama 3, Meta) | 2,230,566 | **One per base developer** (Meta) |
| `library/dolphin-mixtral` (Mixtral, Mistral) | 1,989,941 | **Over 20 GB:** `dolphin-mixtral:8x7b` is 26 GB (see Resolutions) |
| `library/dolphin-phi` (Phi-2, Microsoft) | 1,634,268 | **Third developer**, outside the top two |

### Most used uncensored on OpenRouter
| Candidate | Tokens | Reason |
|---|---|---|
| `thedrummer/cydonia-24b-v4.1` | 6.416 G | **Fewer tokens** than Venice Uncensored (7.223 G). Both are on month totals, not the rule window |
| `sao10k/l3-lunaris-8b`, `nousresearch/hermes-3-llama-3.1-70b`, `nousresearch/hermes-4-405b` | 20.163 G, 4.332 G, 4.090 G | **Not stated as uncensored** in the saved (truncated) OpenRouter descriptions. Their full cards are not in the snapshot |

## Resolutions (8 November 2026)
- **Gemini 4 Argon vs Hy4.** PI decision: the price source is the OpenRouter list price. Gemini 4 Argon is in the panel as model 14, and Hy4 is excluded because it ranks 6th.
- **dolphin-mixtral.** Excluded. Under the size rule (common rules, protocol Section 6.1: the `ollama.com/library/<name>:<size>` tag without a quantisation suffix), its smallest parameter size, `8x7b`, is 26 GB, over the 20 GB limit (`raw_pages/olm_dolphin-mixtral_tags.html.gz`). *Correction after audit round 3:* the tags page also lists quantised tags of that size at 17 GB (`8x7b-v2.x-q2_K`) and 20 GB (`q3_K_S`). Under the earlier wording ("smallest tag ≤ 20 GB") those would have qualified and dolphin-mixtral would have taken slot 21. The size definition was written after the snapshot had been seen and before any answer from slot 21 existed.
- **Why 20 GB** (technical reason, round-4 audit). The limit comes from version 1 ("no single model download may exceed 20 GB"). The study machine has 32 GB of RAM, an 8 GB GPU and limited free disk. A build over 20 GB would run mostly from system memory, next to the operating system and the judge processes, with too little headroom and at a fraction of the speed. On 8 November the PI considered raising the limit to 30 GB and kept 20 GB.
- **eriktonon/granite4.2-uncensored.** Excluded from the matched stratum because it adds a SecOps LoRA. The rule (protocol v2.2, Section 6.1) admits refusal removal only.
- **huihui_ai/qwen3.5-abliterated (first model 19).** First kept as a secondary contrast, because its card documents refusal removal by fine-tuning (TRL). **Superseded (PI decision, 8 November 2026, before any answer from either build existed):** the matched rule admits abliteration only, so this build is excluded.
- **kaineone/qwen3.5-4b-abliterated (model 19).** The most-downloaded eligible build: its Ollama page names `Qwen/Qwen3.5-4B`, describes orthogonalisation of the refusal direction and says "not fine-tuned" (`raw_pages/olm_kaineone_qwen3.5-4b-abliterated*`). Text-only, 2.8 GB, digest `4ad997605828`.
- **kiwi_kiwi/qwen3.5-abliterated.** More downloads (5,144) than kaineone, but its page names neither a base checkpoint nor a method (`raw_pages/olm_kiwi_kiwi_qwen3.5-abliterated*`), so it is not eligible.
- **"Card"** means the Ollama page, or the Hugging Face card it links.
- **huihui_ai/qwen3-abliterated:8b-v2-q4_K_M (model 18).** The `8b-v2` tag is now captured (`raw_pages/olm_huihui_ai_qwen3-abliterated_tags*`).
- **Qwen3.5 consumer-GPU size.** Under the size rule, `qwen3.5:4b` (3.3 GB) is the build; `qwen3.5:latest` is the 9B build (6.6 GB) and is not the size tag.
