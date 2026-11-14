# Journal fit review (Claude agent, 13 November 2026)

Reviewer: a Claude Opus 5.5 subagent with web search, given the same request and the same copy as the ChatGPT review (E:/claude/_audit_copy/journal_fit_1113). Saved verbatim in substance; headings kept.

Items tagged [D] would change the registered design and should be decided before the pilot registration.

## 1. TMLR: good fit, the best of the three
- Two acceptance criteria: claims supported by evidence; of interest to some readers. No novelty requirement (https://jmlr.org/tmlr/acceptance-criteria.html). The fixed claim wording (Section 2.4) matches the first criterion well; "a particular configuration, not a new phenomenon" (Section 15.4) does not count against it.
- Rolling submissions; target decision about 9 weeks for a main text of 12 pages or less (https://jmlr.org/tmlr/faq.html). Publishes LLM-safety work (e.g. https://openreview.net/forum?id=oVTkOs8Pka).
- Must: main text of 12 pages or less (question, four arms, screen, theta_S/iota_S/beta_S, crossed delta-delta, detection/false-alarm split, delivery; the rest in appendices); anonymise for double-blind review (anonymised OSF view-only link, anonymised code, no USF details), still disclosing AI-drafted code and text and the reviewer that is also model 11; write the paper in the authors' own words (TMLR treats LLMs as assistive tools and scrutinises submissions that appear largely LLM-generated, https://jmlr.org/tmlr/editorial-policies.html); four bullets in the introduction on what the study adds to Khullar et al. 2026 (harm classification of chat answers; detection/false-alarm split against human labels; controls on the same answers plus the crossed matrix; refusal-removed authors); a broader-impact statement (harmful prompts to commercial APIs, inserted assistant turns, annotator welfare, gated release, notice to developers) and the IRB/HRPP status (https://jmlr.org/tmlr/author-guide.html).
- Should: widen related work (LLM-as-a-judge and self-preference; guard classifiers such as Llama Guard, WildGuard, ShieldGemma; reliability of safety judges, StrongREJECT, arXiv:2603.06594; AI control and trusted monitoring; self-critique and self-correction; prefill attacks); lead with the token-identical reconstruction for local models (Section 2.2); motivate the open panel by real uses (self-hosted small models checking their own output; self-critique pipelines); one table of deviations from version 1 and from the registration; gated access to answer text for reviewers.
- Risks: "so what for deployed monitors?" (effect carried by refusal-removed 4-8B builds; commercial panel descriptive); seen as an increment on Khullar et al.; unreadable or inconclusive ("test not carried out" under D20, or descriptive only under the hosted-model rule of Section 10.4).

## 2. JAIR: moderate to weak fit
- All of AI; open access, no fee, about 3 months to review, no page limit (https://www.jair.org/index.php/jair/about). Judges originality and significance; incremental work or work that merely applies known techniques is likely rejected (https://www.jair.org/index.php/jair/about/submissions). No recent JAIR articles found on LLM-as-a-judge or LLM safety evaluation.
- Must: JAIR format (other templates rejected unreviewed), reproducibility checklist, three cover questions (one asks for the 1-3 closest JAIR papers); a significance argument for a general AI reader; self-contained background and an ethics section; disclosure of AI use.
- Should: possibly a Research Note; otherwise full methods in the main text. [D] closing the gap on deployed models (more commercial prompts, or delta-delta as a confirmatory test) is not recommended under the cash cap.
- Risks: incremental or narrow; a null or descriptive outcome reads as too little; slow.

## 3. Computers & Security: no fit at present
- Elsevier's scope page: since early 2024 a moratorium on submissions that feature AI or ML as significant components; work on the security of AI/ML systems themselves (such as LLMs) is out of scope (https://shop.elsevier.com/journals/computers-and-security/0167-4048). Desk rejection. (Confirmed by the main session on 13 November 2026.)

## 4. Ranking
1. TMLR first; arXiv preprint permitted; plan the 30-day notice to developers (Section 16.9) during the writing. Speed matters less than the authors think: the primary checkpoints (Llama 3.1, Qwen3, Dolphin) are already not current; the pressure falls on the secondary commercial panel.
2. JAIR only if the results are clear-cut.
3. Computers & Security: do not submit.
- For the second target, ACL Rolling Review (ACL or EMNLP) fits better than JAIR: the closest comparable papers (Chen & Goldfarb-Tarrant 2025; Nguyen et al. 2026; Chae et al. 2026) appeared there. Cost: 8-page limit and fixed cycles (https://aclrollingreview.org/dates).

## 5. Design changes to decide before the registration
- [D] Exploratory clause: allow analyses that are not registered, only in a separate section labelled post hoc, never in the abstract or in claim sentences. Recommended; costs nothing.
- [D] Guard-model reference judges: one or two local guard classifiers judge the 567 labelled answers blind, at no cash cost; answers "why not Llama Guard?". Optional; otherwise a limitation in Section 18.3.
- [D] delta-delta as a confirmatory test, or more commercial prompts: not recommended.
- D13 (the panel, chosen at the freeze): one unattempted harmful-frame call of a registered hosted model makes the paper descriptive (Section 10.4); weigh it when D13 is decided.
