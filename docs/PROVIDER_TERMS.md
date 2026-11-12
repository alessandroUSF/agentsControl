# Provider terms

Protocol v2.3, Sections 3.3, 16.2 to 16.5 and 19.1 (decisions D1 and D2).

- **Status: template. No terms have been read into this file yet.**
- The principal investigator (PI) reads the terms and fills each block before the pilot registration. An AI assistant can prepare a summary, but the reading and the conclusions are the PI's.
- Every entry carries the date on which the page was read and its address. Terms change: a page is read again before the freeze, and the date is added.
- The study describes the in-context presentation to each provider as it is: an answer written earlier, by the same model or by another one, is placed in the assistant turn of a new conversation and the model is asked to classify it (Section 16.3).
- The research accounts are not a way around enforcement (Section 16.4). At any warning, every call to that provider stops (Section 16.5).

## What each provider receives

Per commercial model (Section 16.2). The PI can switch a row off for a provider and never on.

| Row | Per model |
|---|---|
| Harmful benchmark prompts as requests | 60, and 10 per pilot round |
| The model's own answers to them, for classification in both presentations | 60, and 10 per pilot round |
| Answers of another commercial model, in both presentations | 60 |
| Labelled answers as quoted data | 130 |
| The challenge set as the model's own previous turn (block 7, decision D1) | 70 |
| Answers of local refusal-removed models to pilot prompts, in both presentations (decision D1) | 10 per pilot round |

Models 22 and 23 (through OpenRouter) are models of the primary panel: each answers all 300 harmful prompts and makes all judging calls of Section 12.1.

## Block to fill for each account

Copy the questions under each account heading.

1. **Pages read.** Terms of service, usage policy, research or safety-testing provisions, data retention page. Address and date for each.
2. **Is this use allowed?** Sending harmful benchmark prompts as published; receiving the answers; sending answers with likely harmful content back for classification.
3. **Inserted assistant turn.** Do the terms say anything on prefilled or inserted assistant turns? Is notice or permission asked for?
4. **Notice.** Was notice given or permission asked? To whom, when, and with what answer?
5. **Retention.** What is retained by default and for how long? Which settings were changed, and how was the change verified?
6. **Training.** Are inputs or outputs used for training? Which setting excludes it?
7. **Automated enforcement.** What happens after a flagged request: warning, suspension, review? Where would a warning arrive?
8. **Spending limit.** Prepaid credit or hard limit set on the account, and its amount. Fees and taxes paid on the purchase (they count against the cap, Section 12.4).
9. **Conclusion of the PI.** Rows of the table above that run for this provider, and the reason for each row switched off.

## Anthropic research account (models 1 and 2)

- Key variable: `AC_ANTHROPIC_API_KEY`.
- Main-run answering calls use the batch endpoint. Batch files are deleted after settlement, and each deletion is logged.
- Pessimistic cost on 11 November 2026: US$23.75.

(Fill the nine points here.)

## OpenAI research account (models 3, 9 and 11)

- Key variable: `AC_OPENAI_API_KEY`.
- Every call sets `store=false`. Main-run answering calls use the batch endpoint. Batch files are deleted after settlement, and each deletion is logged.
- Model 11 is also the reviewer of the design (Section 17.3).
- Pessimistic cost on 11 November 2026: US$23.33.

(Fill the nine points here.)

## OpenRouter research account (models 7, 8, 10, 12, 13, 14, 22 and 23)

- Key variable: `AC_OPENROUTER_API_KEY`.
- Calls are limited to OpenRouter's zero-retention endpoints, one pinned endpoint per model, with no fallback to other endpoints (`zdr`, `provider_order`, `allow_fallbacks`; decision D16).
- OpenRouter's zero-retention list also admits endpoints that keep data for a limited time for safety review (`safety_retention`), unless the account accepts zero-retention endpoints only. Record the account setting under point 5.
- Pessimistic cost on 11 November 2026, at the prices of the pinned endpoints: US$76.22.
- Besides OpenRouter's own terms, the terms of each upstream provider apply. Fill points 2, 3, 5 and 6 for each line of the table.

The third column is the endpoint snapshot of 11 November 2026 (`data/selection/2026-11-11/`), copied by the assistant for the PI to verify.

| Model | Developer | Pinned endpoint (decision D16), snapshot of 11 November | Zero-retention endpoint available: yes or no, date checked | Receives harmful prompts (decision D2) |
|---|---|---|---|---|
| 7 | DeepSeek | `morph/fp8`; on the zero-retention list, no safety retention. The developer's own endpoint is not on the list | | |
| 8 | Z.ai | `z-ai/fp8`; on the list, no safety retention | | |
| 10 | Tencent | `tencent/fp8`; on the list, no safety retention | | |
| 12 | Moonshot | `moonshotai/mxfp4`; on the list, no safety retention | | |
| 13 | xAI | `xai/zdr`; on the list, no safety retention | | |
| 14 | Google | `google-vertex/global`; on the list, **with safety retention**, like every listed endpoint of this model | | |
| 22 | Mistral lineage, uncensored fine-tune (Dolphin line, Venice) | `venice/fp16`; on the list, no safety retention; the only listed endpoint | | |
| 23 | Mistral lineage, uncensored fine-tune (Cydonia line, TheDrummer) | `parasail/bf16`; on the list, no safety retention; the only listed endpoint | | |

- A model without a zero-retention endpoint receives safe prompts only, unless the PI records here the decision to run it under stated retention terms (Section 3.3).
- If model 22 or 23 cannot be run, the study follows the rule of Section 10.4 and the matching control assignment of Section 6.5.

(Fill the nine points here.)

## Local models

- Models 4, 6 and 20 are bound by the Llama 3.1 Community License and its Acceptable Use Policy (Section 16.6, decision D3).
- Optional: the licences of the other local models, with the date read.

| Model | Licence | Date read | Anything that limits this use |
|---|---|---|---|
| 4, 6, 20 | Llama 3.1 Community License and Acceptable Use Policy | | |
| 5, 15, 18, 19 | | | |
| 16 | | | |
| 17 | | | |
| 21 | | | |
