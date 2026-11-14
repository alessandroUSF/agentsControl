# Provider terms

Protocol v2.3, Sections 3.3, 16.2 to 16.5 and 19.1 (decisions D1 and D2).

- **Status: filled on 13 November 2026. The PI decided on notice to Anthropic and OpenRouter on 12 November 2026 (point 4 of their blocks, and Section 16.4 of the protocol). The other points were drafted by the AI assistant on 13 November 2026 from the facts file below, the PI's decisions D1 and D2, and the settings of the three accounts, checked by the PI on 13 November 2026. PI's initials after checking: AA. Open: Tencent's clause on publishing benchmark results (model 10), decided before publication; the licences of the local models other than Llama (optional, before the freeze).** Facts copied by the AI assistant from public pages on 12 November 2026, with eleven open questions, are in `docs/PROVIDER_TERMS_FACTS_2026-11-12.md`, for the PI to verify.
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
- Facts to verify: section 1 of `docs/PROVIDER_TERMS_FACTS_2026-11-12.md` (questions Q2, Q3, Q9 and Q10 there).

1. **Pages read.** The usage policy in force from 12 November 2026, the Commercial Terms, and the pages on data retention, batch processing, model training, API safeguards, enforcement and conversation turns. Addresses and dates: section 1 of the facts file (12 November 2026). Read by the PI (decision D1, 12 November 2026).
2. **Is this use allowed?** The usage policy forbids requests of certain kinds and has no exception for research or evaluation. The PI's reading (decision D1): the study's prompts, published benchmark prompts sent as published, are not of those kinds, and the most extreme prompts were left out of the study. Sending answers back for classification is a content-moderation use, which the batch documentation names.
3. **Inserted assistant turn.** The Messages API documents synthetic assistant turns: earlier turns need not come from the model. The study's inserted turn is followed by a user turn, so it is not a prefill. No page asks for notice or permission.

4. **Notice.** Decided by the PI on 12 November 2026: no authorization is asked.
   - The usage policy in force from 12 November 2026 asks for prior authorization to bypass safeguards by instructing a model to produce harmful outputs (for example, jailbreaking). It has no research exception (question Q2 of the facts file).
   - The PI's reading: the study evaluates the safeguards and does not get around them. The benchmark prompts are sent as published, with no jailbreak or other technique to get around a refusal, and a refusal is data. The inserted assistant turn asks only for a classification of an answer written earlier. At any warning every call to Anthropic stops (Section 16.5 of the protocol).
   - Drafted by the AI assistant from the PI's decision.

5. **Retention.** The developer documentation says that conversation content is not retained by default for models 1 and 2; the Privacy Center says that inputs and outputs are deleted within 30 days. Batches are kept up to 29 days; the study deletes each batch after settlement and logs the deletion. Requests flagged by Anthropic's safety systems may be kept up to 2 years, and their classification scores up to 7 years; the study assumes that this can apply to some of its requests. The account has no zero-retention agreement. No setting was changed.
6. **Training.** The Commercial Terms bar training on customer content. The account has not joined the Development Partner Program (checked by the PI on 13 November 2026).
7. **Automated enforcement.** Real-time safeguards run on every request; a refusal comes back as a normal response with `stop_reason` `refusal` and is data of the study. On a suspected violation Anthropic may warn, throttle, limit, suspend or end access. Notices go to the account's e-mail address or the Console, which the PI watches during the runs. Every call stops at a warning (Section 16.5 of the protocol).
8. **Spending limit.** Prepaid credit of US$15.00, with no purchase fee; auto-reload off (checked by the PI on 13 November 2026). Calls stop when the credit runs out.
9. **Conclusion of the PI.** Every row of the table above runs for models 1 and 2 (decisions D1 and D2). No row is switched off.

## OpenAI research account (models 3, 9 and 11)

- Key variable: `AC_OPENAI_API_KEY`.
- Every call sets `store=false`. Main-run answering calls use the batch endpoint. Batch files are deleted after settlement, and each deletion is logged.
- Model 11 is also the reviewer of the design (Section 17.3).
- Pessimistic cost on 11 November 2026: US$23.33.
- Facts to verify: section 2 of `docs/PROVIDER_TERMS_FACTS_2026-11-12.md` (questions Q4 and Q9 there). Several OpenAI policy pages refused automated reading; they are marked as search excerpts.

1. **Pages read.** The Services Agreement, the Usage Policies, the Sharing and Publication Policy, and the pages on data controls, conversation state, batch, safety checks, safety enforcement, spend limits, error codes and prepaid billing. Addresses and dates: section 2 of the facts file (12 November 2026). The pages that refused automated reading were read by the PI in a browser (decision D1, 12 November 2026). A new version of the Usage Policies takes effect on 20 November 2026; the version in force on the date of each run is recorded.
2. **Is this use allowed?** The Usage Policies allow research and model evaluation within their limits and forbid requests of certain kinds. The PI's reading (decision D1): the study's prompts, published benchmark prompts sent as published, are not of those kinds, and the most extreme prompts were left out of the study.
3. **Inserted assistant turn.** The documentation shows hand-written assistant turns as conversation history. No page asks for notice or permission.
4. **Notice.** None is given: no page read asks for it (13 November 2026). The Researcher Access Program offers subsidised access and is not a permission.
5. **Retention.** Every call sets `store=false`. Abuse-monitoring logs are kept up to 30 days whatever `store` says. Batch input and output files are kept until deleted and are not zero-retention; the study deletes them after settlement and logs the deletion. Zero retention needs OpenAI's approval and is not in place. No setting was changed.
6. **Training.** API data is not used for training unless the organization opts in to share it. Sharing of inputs and outputs is off, the default (checked by the PI on 13 November 2026).
7. **Automated enforcement.** Safety checks can place requests in risk thresholds; repeated high thresholds bring an error and a warning e-mail, and access can stop after about seven days. OpenAI may limit or suspend access for a violation, with notice to the account's e-mail address where it can. The PI watches that inbox during the runs. Every call stops at a warning (Section 16.5 of the protocol).
8. **Spending limit.** Prepaid credit of US$15.00, with no purchase fee; auto-recharge off (checked by the PI on 13 November 2026). Access may run briefly past zero credit and leave a negative balance; the study's own ledger holds the cap (Section 12.4 of the protocol).
9. **Conclusion of the PI.** Every row of the table above runs for models 3, 9 and 11 (decisions D1 and D2). No row is switched off.

## Google research account (model 14, decision D2; not used since decision D17)

- **Not used.** Model 14 left the study on 12 November 2026, before any call (decision D17). No model of the study is called at Google, and this account receives no call. The block below is kept as the record of decision D2.

- Key variable: `AC_GOOGLE_API_KEY`, the key of a Google AI Studio project created for this study, with billing enabled. The project does not join the Contributor tier.
- Calls go to the Gemini API (`generateContent`), one at a time; no batch interface. No safety settings are sent, so the adjustable filters keep the API's default.
- Pessimistic cost on 11 November 2026, at the November price: US$21.23. At the price from 1 December 2026: US$42.46. This rise led to decision D17.

Facts copied by the assistant on 11 November 2026 from Google's public pages, for the PI to verify:

| Point | What the page says | Page |
|---|---|---|
| Use of the data | For paid services, Google does not use prompts or responses to improve its products | https://ai.google.dev/gemini-api/terms |
| Retention | For paid services, prompts and responses are logged for a limited period, solely to detect violations of the Prohibited Use Policy and for required legal or regulatory disclosures. The usage policy names 55 days | https://ai.google.dev/gemini-api/terms and https://ai.google.dev/gemini-api/docs/usage-policies |
| Contributor tier | Optional. In exchange for lower prices, Google may use the data to improve its products | https://ai.google.dev/gemini-api/docs/logs-policy |
| Safety settings | The adjustable filters are off by default for Gemini 2.5 and later models. Built-in protections against core harms, such as content that endangers child safety, cannot be adjusted | https://aistudio.google.com/docs/safety-settings |
| How blocks are reported | `generateContent` returns a block inside a normal response: `promptFeedback.blockReason` for a blocked prompt, `finishReason` for a stopped answer. The finish reason `PUP_LIMITED_DISABLED` means that the account is limited or disabled under the Prohibited Use Policy | https://aistudio.google.com/docs/api/generate-content |
| Price | US$2.00 in and US$10.00 out per million tokens through 30 November 2026; US$4.00 and US$20.00 from 1 December 2026. Thinking tokens are billed as output | https://aistudio.google.com/docs/pricing |
| Spending limit | Prepaid credit: calls stop when the balance reaches zero, after a billing delay of about ten minutes, so a small overrun is possible. Prepaid credit expires after twelve months. A monthly spend cap can be set per project; Google calls it experimental | https://aistudio.google.com/docs/billing |

Not filled: the account receives no call (decision D17).

## OpenRouter research account (models 7, 8, 10, 12, 13, 22 and 23)

- Key variable: `AC_OPENROUTER_API_KEY`.
- Calls are limited to OpenRouter's zero-retention endpoints, one pinned endpoint per model, with no fallback to other endpoints (`zdr`, `provider_order`, `allow_fallbacks`; decision D16).
- OpenRouter's zero-retention list also admits endpoints that keep data for a limited time for safety review (`safety_retention`), unless the account accepts zero-retention endpoints only. In the snapshot of 11 November 2026 only the endpoints of model 14 were so marked. Model 14 has left the study (decision D17), and the account accepts zero-retention endpoints only (point 5).
- Pessimistic cost at the prices of the pinned endpoints of 11 November 2026: US$54.99 on 11 November; US$54.95 since decision D17 (12 November), as model 14 no longer judges the answers of these models.
- Besides OpenRouter's own terms, the terms of each upstream provider apply. Fill points 2, 3, 5 and 6 for each line of the table.

The third column is the endpoint snapshot of 11 November 2026 (`data/selection/2026-11-11/`), copied by the assistant for the PI to verify.

| Model | Developer | Pinned endpoint (decision D16), snapshot of 11 November | Zero-retention endpoint available: yes or no, date checked | Receives harmful prompts (decision D2) |
|---|---|---|---|---|
| 7 | DeepSeek | `morph/fp8`; on the zero-retention list, no safety retention. The developer's own endpoint is not on the list | Yes, the pinned endpoint, without safety retention; 13 November 2026 | Yes (decision D2) |
| 8 | Z.ai | `z-ai/fp8`; on the list, no safety retention | Yes, the pinned endpoint, without safety retention; 13 November 2026 | Yes (decision D2) |
| 10 | Tencent | `tencent/fp8`; on the list, no safety retention | Yes, the pinned endpoint, without safety retention; 13 November 2026 | Yes (decision D2) |
| 12 | Moonshot | `moonshotai/mxfp4`; on the list, no safety retention | Yes, the pinned endpoint, without safety retention; 13 November 2026 | Yes (decision D2) |
| 13 | xAI | `xai/zdr`; on the list, no safety retention | Yes, the pinned endpoint, without safety retention; 13 November 2026 | Yes (decision D2) |
| 22 | Mistral lineage, uncensored fine-tune (Dolphin line, Venice) | `venice/fp16`; on the list, no safety retention; the only listed endpoint | Yes, the pinned endpoint, without safety retention; 13 November 2026 | Yes (decision D2) |
| 23 | Mistral lineage, uncensored fine-tune (Cydonia line, TheDrummer) | `parasail/bf16`; on the list, no safety retention; the only listed endpoint | Yes, the pinned endpoint, without safety retention; 13 November 2026 | Yes (decision D2) |

- A model without a zero-retention endpoint receives safe prompts only, unless the PI records here the decision to run it under stated retention terms (Section 3.3).
- If model 22 or 23 cannot be run, the study follows the rule of Section 10.4 and the matching control assignment of Section 6.5.
- Facts to verify: section 3 (OpenRouter) and sections 4 to 10 (the seven upstream providers) of `docs/PROVIDER_TERMS_FACTS_2026-11-12.md` (questions Q1, Q5, Q6, Q7, Q9 and Q10 there).

1. **Pages read.** OpenRouter's Terms and Privacy Policy, the pages on zero data retention, privacy and logging, provider logging, provider selection, the FAQ, pricing and limits, and the terms of the seven upstream providers. Addresses and dates: sections 3 to 10 of the facts file (12 November 2026). Read by the PI (decision D1, 12 November 2026).
2. **Is this use allowed?** OpenRouter's terms bind users to each provider's terms. The upstream terms forbid requests of certain kinds, such as harmful, violent or illegal content, with no research exception found (table below). The PI's reading (decision D1): the study's prompts, published benchmark prompts sent as published, are not of those kinds, and the most extreme prompts were left out of the study. On red teaming, see point 4.
3. **Inserted assistant turn.** Not addressed on any page read.

4. **Notice.** Decided by the PI on 12 November 2026: no approval is asked.
   - The terms (§7(11) and §8) ask for prior written approval for "Red Teaming of Models", defined as prompt injection, jailbreaking, or any other adversarial action designed to compromise a model (question Q1 of the facts file).
   - The PI's reading: the study is not red teaming. It sends benchmark prompts as published, with no attack, and asks for answers and classifications. A later study with adversarial prompts would ask for approval first. At any warning every call to OpenRouter stops (Section 16.5 of the protocol).
   - Drafted by the AI assistant from the PI's decision.
- **Open: Tencent (model 10).** Its AI Service Terms (§4.1) bar publishing performance or benchmark tests without written consent (question Q7 of the facts file). The PI decides later.

5. **Retention.** OpenRouter does not log prompts or completions unless the account opts in, and keeps request metadata. The account accepts zero-retention endpoints only, for every model group, and the option that lets OpenRouter use inputs and outputs is off (set and checked by the PI on 13 November 2026). Every call also asks for zero retention, no data collection, the pinned endpoint and no fallback (`src/providers.py`). On 13 November 2026 OpenRouter's public zero-retention list held all seven pinned endpoints, none with safety retention (checked by the AI assistant from `https://openrouter.ai/api/v1/endpoints/zdr`, with no key and no model call). The providers' own sites describe other defaults (table below). The study relies on OpenRouter's listing and states the difference as a limitation.
6. **Training.** OpenRouter does not train on inputs or outputs. Routing to endpoints that train on request data is off for paid and free models, and so is routing to free endpoints that publish prompts (checked by the PI on 13 November 2026).
7. **Automated enforcement.** OpenRouter may screen, block or remove inputs, restrict access to a model, or end the account. Upstream providers can file abuse reports, which OpenRouter's trust and safety team reviews. Where a warning would arrive is not stated; the PI watches the account's e-mail and dashboard during the runs. Every call stops at a warning (Section 16.5 of the protocol).
8. **Spending limit.** Prepaid credit of US$10.00, with a purchase fee of US$0.80 recorded in the ledger; key limit US$20.00; auto top-up off (checked by the PI on 13 November 2026). The balance can go slightly negative; the study's own ledger holds the cap.
9. **Conclusion of the PI.** Every row of the table above runs for models 7, 8, 10, 12, 13, 22 and 23 (decisions D1 and D2). No row is switched off.

Points 2, 3, 5 and 6 for each upstream provider, from sections 4 to 10 of the facts file (12 November 2026). The PI's reading of these terms is that of decision D1.

| Model | Provider | 2. Use | 3. Inserted turn | 5. Retention on the provider's own site | 6. Training |
|---|---|---|---|---|---|
| 7 | Morph | Bars generating illegal, harmful, threatening or offensive content and malicious code (§18.1) | Not addressed | Deleted within 30 days; flagged prompts kept for review; its own zero retention on enterprise tiers only | No training, on any tier |
| 8 | Z.ai | Bars violent, murderous, terroristic or criminal-incitement content and self-harm instructions (III.3) | Not addressed | Content not stored (data processing addendum); automatic context caching, period not stated | No training without consent |
| 10 | Tencent | Bars violative outputs, among them the promotion of self-harm, violence and illegal conduct; publishing benchmark tests needs written consent (§4.1) | Not addressed | Usage data, output information included, up to 30 days; no zero-retention option on its site | No training without opt-in |
| 12 | Moonshot AI | Bars harmful or violent content and attempts to evade safety detection (§3.1, §3.3) | Not addressed | Kept while the account is active; zero retention for enterprise customers on request | Content may be used to improve the services unless agreed otherwise in writing |
| 13 | xAI | Bars circumventing safeguards without written consent, and weapons of mass destruction | Not addressed | 30 days by default; OpenRouter's `xai/zdr` endpoint is the zero-retention one | No training without permission |
| 22 | Venice | Bars illegal use and outputs expected to cause death or serious harm (§12) | Not addressed; Venice may add a system prompt (decision D26) | Prompts and responses not stored or logged for normal inference | No training |
| 23 | Parasail | Bars illegal or unauthorized use and other harmful actions (§2.2) | Not addressed | Content kept only as long as needed; batch inputs 30 days | No training |

## Local models

- Models 4, 6 and 20 are bound by the Llama 3.1 Community License and its Acceptable Use Policy (Section 16.6, decision D3).
- Optional: the licences of the other local models, with the date read.
- Facts to verify: section 11 of `docs/PROVIDER_TERMS_FACTS_2026-11-12.md` (question Q8 there).

| Model | Licence | Date read | Anything that limits this use |
|---|---|---|---|
| 4, 6, 20 | Llama 3.1 Community License and Acceptable Use Policy | | |
| 5, 15, 18, 19 | | | |
| 16 | | | |
| 17 | | | |
| 21 | | | |
