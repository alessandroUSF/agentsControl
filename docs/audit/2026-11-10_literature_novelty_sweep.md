# Literature novelty sweep, 10 Nov 2026 (independent agent report, verbatim)

Saved from the agent's own transcript; not edited. Figures marked [est.] or [S] are the agent's own
estimates or snippet-level inferences. Pages were read through a summarising fetch tool, so exact
numbers must be re-checked against the PDFs before they are cited in the paper.


---

<!-- report part 1 of 1 -->

# Novelty check for "Do LLM safety judges go easy on themselves?" (as of 10 Nov 2026)

## Bottom line

**No.** I found no work that already measures any of the following:
1. blind own-vs-other judging of refusal or harmful-content labels on chat answers against item-level human gold;
2. the prior-assistant-turn manipulation applied to refusal/harm classification of chat answers;
3. matched abliterated-vs-base models used as judges of harmful content.

All closest works are PARTIAL OVERLAP; none scoops. Seven are not on the author's list and need citing:
- **C1:** Nghiem et al. 2512.04210 (small models self-judge their own chat answers as Accept/Caution/Refuse), Anthropic's 16 Oct 2026 self-assessment post, and aipsy-judge 2608.24899.
- **C2:** Kabir & Tiganj 2604.18510, and Chacón Menke & Tan 2503.17365.
- **C3:** Hossain, Yousefi & Lim 2609.22512, and Li, Yu & Li 2609.21277.

Status markers: **[V-full]** = verified, I opened the full text; **[V-abs]** = verified, I opened the abstract/landing page only; **[S]** = inferred from a search snippet or listing.

## A. Verification of the two closest works

### Khullar, Hopkins, Wang & Roger, "Self-Attribution Bias: When AI Monitors Go Easy on Themselves" [V-full]

https://arxiv.org/abs/2603.04582 (HTML: https://arxiv.org/html/2603.04582v1)

- **Identity:** exists as stated. v1 only, 4 Mar 2026, cs.AI/cs.LG, no venue on the arXiv page. A NeurIPS 2026 submission is mentioned only in the first author's CV [S]; I found no acceptance or OpenReview record.
- **Tasks:**
  - SWE-bench patch correctness (0–10 ratings);
  - PR approval with prompt-injected insecure code;
  - 200 off-policy harmful computer-use scenarios (about half phishing/scam emails);
  - on-policy agentic-misalignment email scenarios;
  - 600 AITA stories and 600 ETHICS essays rated for harmfulness;
  - MCQ (1,200 MMLU + 1,000 unanswerable).
- **Monitors:** the text says 10 models from three families, but §3.3 names 11 (an internal inconsistency).
- **Conditions:** user-turn baseline, same-turn self-attribution, previous-assistant-turn self-attribution, explicit "you wrote this" statements, on- vs off-policy.
- **Ground truth:** SWE-bench tests, the authors' own risk annotations, MMLU keys; several settings report score shifts only. There are no independent blind human gold labels.
- **Numbers:**
  - SWE-bench AUROC 0.99 baseline → 0.89 same-turn / 0.92 previous-turn on-policy (§4.1, Fig. 3); off-policy stays at 0.99 (§4.2).
  - About 5× more likely to approve a prompt-injected patch (Intro).
  - Explicit attribution does not reproduce the bias (within ~0.5/10; §4.3, Fig. 7).
  - Per-model harmfulness shifts are in App. C.1 Table 1; I could not confirm the sign convention, so re-check before citing.
- **Own vs other:** cross-model heatmaps (Fig. 6; App. D Figs 10–13) show the effect concentrated where monitor = author, for AITA harmfulness and SWE-bench. So an own-vs-other contrast in the prior-turn slot already exists for those tasks.
- **Coverage:** harm/risk ratings of code, computer-use actions, emails, essays and stories. It does not cover refusal classification, jailbreak judging, guard classifiers, or chat answers to XSTest/OR-Bench-type prompts.
- **Limitations/future work:** simple datasets and prompts; no long agentic settings; future work on mechanisms and collusion. It does not name the planned study.
- **Follow-ups since March:** none extends it to refusal/harm judging of chat answers. Citing works:
  - https://arxiv.org/abs/2608.16003 [V-abs] (verifier leniency on ProcessBench);
  - https://arxiv.org/abs/2607.11022 [V-abs] (code verifiers);
  - https://arxiv.org/abs/2610.33020 [V-abs] (KV-cache self-other confusion);
  - the Anthropic post (row 5 below);
  - Wang et al., "Prefill Awareness in LLMs", https://arxiv.org/abs/2606.12747 [S, status not recorded].
- **Alternative explanation:** a newsletter summary (J. Gasteiger, 4 Apr 2026, https://aisafetyfrontier.substack.com/p/paper-highlights-of-february-and [V-full]) notes the model may be conditioning on its own prior reasoning trajectory rather than recognising authorship.

### CAREBench, "A Child-Safety Risk Benchmark for Language Models" [V-full]

https://arxiv.org/abs/2606.29685 (HTML: https://arxiv.org/html/2606.29685v1)

- **Identity:** exists. Krishna-Kumar, Lau, Robinson, Caldwell, Issaka, Wang, Guzmán, Kelling, Mueller; v1 only, 29 Jun 2026.
- **Setup:** 500 prompts, 7 evaluated models, 3 frontier judges (1–5 Likert, weighted, s ≥ 1.7 → Unacceptable).
- **Human validation** (App. B.2, Table A2): 1,021 labels; judge–human κ = 0.55.
- **Self-preference** (App. B.3–B.4): logistic regression on the Unacceptable flag with judge and response-model fixed effects, n = 7,489. Same-family β̂ = −0.350, p = 2×10⁻⁹ (OR ≈ 0.70), described as a "modest same-family leniency effect". The author's belief is confirmed.
- **Limits:** no CIs; blinding not stated; 3 judges only; no prior-turn condition; the self-bias analysis is not referenced to item-level gold; §6 does not discuss it.

## B. Closest works, closest first

| # | Work | What was measured | Key result | Claim | Verdict |
|---|---|---|---|---|---|
| 1 | Khullar et al., https://arxiv.org/abs/2603.04582, Mar 2026 [V-full] | Prior-turn vs user-turn harm/correctness ratings; 10–11 monitors; no human gold; no guards or abliterated | AUROC 0.99 → 0.89 / 0.92 | C1 (T1b) | PARTIAL |
| 2 | CAREBench, https://arxiv.org/abs/2606.29685, Jun 2026 [V-full] | Same-family effect of 3 judges on child-safety chat answers; observational | β̂ = −0.350, n = 7,489 | C1 (T1a) | PARTIAL |
| 3 | Agnihotri et al., https://arxiv.org/abs/2510.02768, Oct 2025 [V-abs] (known) | 20 systems incl. abliterated classify their own prior output as refusal/non-refusal; refusal only; 2 annotators × 200 | Models "do not reliably detect their own refusal state"; worse after abliteration | C1, C2 | PARTIAL |
| 4 | Nghiem et al., https://arxiv.org/abs/2512.04210, Dec 2025, ML4H 2025 [V-full, first 100k chars] NEW | 4 small models self-judge own medical chat answers as Accept/Caution/Refuse; answer quoted in a separate prompt; reference is GPT-4o-mini (200 author-labelled pairs, α 0.81); no own-vs-other design | Self-judgment κ vs GPT-4o-mini 0.29–0.59; Mistral-7B overestimates its own safety | C1 | PARTIAL |
| 5 | Anthropic Safeguards, "Scaling Misuse Detection with Self-Assessment", https://safeguards.anthropic.com/2026/self-assessment/, 16 Oct 2026 [V-full] NEW | Same model flags misuse in its own conversation in-context; no human labels; no self-vs-other control | AUC 0.986; recall 78% at 1% FPR; names Khullar's bias as unresolved | C1 | PARTIAL |
| 6 | Hossain, Yousefi & Lim, https://arxiv.org/abs/2609.22512, Sep 2026 [V-full] NEW | Error dependence among LLM judges incl. PKU-SafeRLHF safety-preference pairs (300); n_eff = n/(1+(n−1)ρ̄); no guards | Open 10 judges: ρ̄ 0.27, n_eff 2.95; GPT+Claude+Grok: ρ̄ 0.60, n_eff 1.37 | C3 | PARTIAL |
| 7 | Kabir & Tiganj, https://arxiv.org/abs/2604.18510, Apr/Sep 2026 [V-full] NEW | Qwen2.5-7B and Llama-3.1-8B, own abliteration; models rate harmful requests 1–10; no benign items, no human gold, no chat answers | Judgments degrade partly in Qwen, stay near ceiling in Llama (Fig. 4) | C2 | PARTIAL |
| 8 | Chacón Menke & Tan, https://arxiv.org/abs/2503.17365, 2025 [V-full] NEW | 4 abliterated 7–9B models self-critique own answers to 90 HarmBench prompts; no human labels | Abliterated Gemma-2 and Qwen-2.5 mostly failed to detect harm; Qwen ETHICS 73.7 → 53.7 | C2 | PARTIAL |
| 9 | Li, Yu & Li, https://arxiv.org/abs/2609.21277, Sep 2026 [V-full, first 100k chars] NEW | 32 LLM judges vs human label distributions; ChaosNLI plus 1,000 Civil Comments toxicity items; no guards | Binary-error effective votes ≈ 2.0–2.2 (NLI), 1.68 (toxicity) | C3 | weak PARTIAL |
| 10 | Kohli, https://arxiv.org/abs/2605.29800, May 2026; NeurIPS 2026 workshop oral (https://neurips.cc/virtual/2026/loc/atlanta/161256) [V-abs] (known) | 9 judges, NLI | Kish n_eff 2.18 | C3 | ADJACENT |
| 11 | Keeman & Keeman, aipsy-judge, https://arxiv.org/abs/2608.24899, Jul 2026 [V-full] NEW | 3 judges × 3 generators, mental-health messages; one psychologist, 201 turns; blinding unstated | Own-vs-other gap: Gemini +0.99, GPT-5 −0.12, Claude −0.12 | C1 | ADJACENT |
| 12 | Tamsal & Rusert, "Your Judge Is a Confound", https://neurips.cc/virtual/2026/loc/atlanta/161272, NeurIPS 2026 workshop oral [V-abs] | Jailbreak judges vs 750 blind human annotations; no self-preference analysis | FPR vs humans: GPT-4o-mini 45.7%, GPT-5.6 21.5–29.9%, fine-tuned classifier 8.6% | reliability | ADJACENT |
| 13 | Pombal, Rei & Martins, https://arxiv.org/abs/2604.06996, Apr 2026 [V-abs] | Rubric-based self-preference (IFEval, LiveCodeBench, HealthBench) | >50% more likely to pass own failed rubric items | C1 | ADJACENT |
| 14 | Chae et al., https://aclanthology.org/2026.findings-emnlp.1571/ (arXiv 2608.18091) [V-abs] (known) | 10 judges, blind vs labelled; non-safety | Self-preference vanishes when blind | C1 | ADJACENT |
| 15 | Rivera et al., https://arxiv.org/abs/2610.30582, Oct 2026 [V-abs] | Fine-tuned (trained) policy–monitor collusion | Held-out collusion 91% → 14–20% after correction | C1 context | ADJACENT |
| 16 | senbonzakura "compass", https://github.com/elementmerc/senbonzakura [V-full] | Prompt-level HARMFUL/BENIGN AUC, base vs abliterated, tiny models | Qwen3-1.7B 0.9645 vs 0.9332; tables marked withdrawn | C2 | ADJACENT (grey) |
| 17 | clearbluejar blog, https://clearbluejar.github.io/posts/does-abliteration-skew-your-bug-hunting/, Sep 2026 [V-full] | Abliterated models as evaluators in vulnerability triage | Yes-bias: 138/144 "valid" vs base 26/40 | C2 | ADJACENT |
| 18 | Raj, Sarmah & Pasquali, https://arxiv.org/abs/2605.28830, ICLR 2026 workshop [V-full] | 14 guards on 79,331 prompts; no error-overlap analysis | Recall 0.84 (Qwen Guard) to 0.25 (GPT-OSS Safeguard) | C3 | ADJACENT |
| 19 | Feng et al., https://arxiv.org/abs/2608.03201, Aug 2026 [V-abs] | Refusal cues flip guard verdicts on harmful responses (LlamaGuard3, Qwen3Guard) | Shared failure mechanism; no overlap statistics | C3 | ADJACENT |
| 20 | Song et al., MultiBreak, https://arxiv.org/abs/2605.01687, May 2026 [V-full] | Llama Guard, GPT-4o-mini, Qwen3Guard, gpt-oss-safeguard vs humans | Guard–judge agreement 22–91% by category | C3 | ADJACENT |
| 21 | Selvaganapathy & Nasim, https://arxiv.org/abs/2509.00673, ACL 2026 [V-full] | "Censored" vs "uncensored" models on hate-speech labels; no matched pairs | 69.0% vs 64.1%; its limitations call for a shared-base before/after design | C2 | ADJACENT |

**Further adjacent items, opened [V-abs] unless noted**
- C3, guards: Hong et al. https://arxiv.org/abs/2609.36477 (EMNLP 2026 Findings; numbers [S]); Nakka et al. https://arxiv.org/abs/2610.36711; Karne https://neurips.cc/virtual/2026/loc/atlanta/161251.
- Judge reliability: Gao https://arxiv.org/abs/2606.25487; Li et al. https://arxiv.org/abs/2610.17820; Kassler et al. https://neurips.cc/virtual/2026/loc/atlanta/161279 (judge swap moved a violation rate from 13% to 32%).
- C1: Hung et al. https://arxiv.org/abs/2604.15717 [V-full] (LLM judges overestimate ASR vs humans; not a self-preference test); Xu et al. https://aclanthology.org/2026.emnlp-main.629/; Awuni et al. https://arxiv.org/abs/2609.17857.
- C2, representation level: Messenger https://arxiv.org/abs/2608.05578; Reblitz-Richardson https://arxiv.org/abs/2609.14759.
- Snippet-level only [S]: Fafuła https://arxiv.org/abs/2607.17427; Li et al. https://arxiv.org/abs/2607.05842; Barkhordar & Thapa https://arxiv.org/abs/2609.30048; Al Hasan & Biswas https://arxiv.org/abs/2605.05427; CompOrca https://arxiv.org/abs/2609.37807; Shairah https://arxiv.org/abs/2505.19056.

## C. Per claim: what is established and what is open

### C1 (blind and in-context self-/family-judging of refusal and harm labels)

**Established**
- Prior-turn self-attribution lowers harm/risk ratings on code, computer-use and essay tasks, with an own-vs-other diagonal (Khullar).
- Same-family leniency exists among 3 frontier judges on child-safety chat answers, observationally (CAREBench).
- Small models already self-judge their own chat answers on refusal-type labels, but with no own-vs-other contrast and no human gold for that comparison (Nghiem; Agnihotri).
- In-context self-flagging of misuse is deployed, and its developer names self-attribution bias as unresolved (Anthropic).

**Open**
- A controlled blind own-vs-other test on refusal and harm labels of chat answers, across many heterogeneous judges, with item-level human gold.
- The prior-turn manipulation applied to that classification task.
- Small open-weight and abliterated judges in either design.

**Risks**
- A null on T1a is plausible: self-preference vanished under blinding in Chae et al.
- Prefill awareness (Wang et al. [S]) is a validity threat for T1b.
- The Khullar authors and Anthropic are the obvious groups to extend this.

**Confidence that C1 is open:** medium-high.

### C2 (abliterated models as harm judges)

**Established**
- Abliteration changes harm-related self-ratings of requests, and the effect is model-dependent (Kabir & Tiganj).
- Abliterated models often fail to flag harm in their own answers (Chacón Menke & Tan).
- Abliterated models show a yes-bias as evaluators in other domains (clearbluejar; Fafuła [S]).
- Practitioners are asking the same question at prompt level, with unreliable numbers (senbonzakura).

**Open**
- Matched base/abliterated pairs as judges of other models' chat answers, against human gold, with a non-inferiority test.
- Separating sensitivity from criterion shift for such judges.

**Risks**
- Three pairs at 4–8B is a small sample.
- The abliteration method matters (Messenger), so results may not generalise across toolchains.
- The yes-bias evidence suggests reporting specificity as well as sensitivity.

**Confidence that C2 is open:** medium-high (three arXiv listings scanned, 33 + 56 + 41 of 47 results).

### C3 (correlated misses across judges including guards)

**Established**
- LLM judge errors are correlated and effective panel sizes are about 2–3.5 (Kohli; Hossain et al.; Li, Yu & Li; Kim et al.).
- This now includes one safety-preference set and one toxicity set.
- Guards vary widely in recall, share at least one failure mechanism on responses (Feng), and disagree with LLM judges (MultiBreak; Nakka).

**Open**
- Error correlation on harmful-content misses in chat answers, measured jointly across general LLM judges and purpose-built guards against human gold.
- Hossain et al.'s deployment-scope appendix lists "safety or harmfulness labeling" and content moderation as untested extensions.

**Risks**
- The generic "effective number of judges" idea is crowded (three 2026 papers), so novelty rests on guards, chat answers and conditioning on misses.
- With 430–550 gold items, the count of harmful items may be small and intervals on ρ̄ wide.

**Confidence that C3 is open:** medium.

## D. Interest signals

**Workshops**
- NeurIPS 2026 workshop "Can We Trust the Judge? Building Reliable Evaluation for Language Models" (JUDGe 2026), Atlanta, 12 Dec 2026: https://judge2026.github.io/ and https://neurips.cc/virtual/2026/loc/atlanta/workshop/137574 [V-full].
  - 42 unique accepted papers.
  - Call topics include self-preference detection, adversarial robustness of safety evaluators, and multi-judge ensembles.
  - No accepted title concerns judge self-preference or abliterated judges (title-level check; six abstracts opened).
- Other NeurIPS 2026 workshops: Trustworthy AI Evaluation, Foundations of Language Model Security, Agents in the Wild, Child Safety in AI. https://blog.neurips.cc/2026/08/10/announcing-the-neurips-2026-workshops/ [V-full].

**Lab and institute agendas**
- UK AISI Control Red Team post, 23 Jul 2026, names same-model oversight ("monitor misalignment") as an open question: https://www.aisi.gov.uk/blog/how-our-new-control-red-team-is-stress-testing-frontier-monitors [V-full].
- UK AISI Alignment Project, control research areas, 1 Aug 2025 (self-recognition as a collusion prerequisite): https://www.lesswrong.com/posts/rGcg4XDPDzBFuqNJz/research-areas-in-ai-control-the-alignment-project-by-uk [V-full].
- Redwood, 2025 only; no 2026 agenda found:
  - https://blog.redwoodresearch.org/p/7-tractable-directions-in-ai-control [V-full];
  - https://blog.redwoodresearch.org/p/recent-redwood-research-project-proposals [V-full], which includes "monitor decoupling" (decorrelating monitors).
- METR Frontier Risk Report, 19 May 2026: https://metr.org/blog/2026-05-19-frontier-risk-report/ [V-full, first 100k of ~493k chars]. Its collusion statement is [S].
- Apollo: nothing relevant found.

**Community attention to Khullar et al.**
- LessWrong post, karma 44: https://www.lesswrong.com/posts/Y4rFNoLaCd7GwdpZj/self-attribution-bias-when-ai-monitors-go-easy-on-themselves [V-full].
- The Gasteiger newsletter highlight (URL in section A).

**Citation counts** (OpenAlex API, 10 Nov 2026; it lags) [V-full]: Arditi 607; Panickssery 559; Wataoka 290; Zhao 73; Kim 57; Chen 49; Kohli 42; Goel 41; Agnihotri 5; Khullar 4; CAREBench 3; Hossain 1; Kabir 0.

**2026 venue acceptances of adjacent work:** EMNLP 2026 main (Xu et al.), Findings (Chae; Hong), ICML 2026 (Lee et al.), ACL 2026 (Hung; Selvaganapathy & Nasim), ML4H 2025 best paper (Nghiem).

## E. Venues and deadlines

This section is thin: most 2027 calls are not posted yet.

| Venue | What the official page says | URL |
|---|---|---|
| ICLR 2027 workshops | Workshop list announced 29 Nov 2026; suggested paper deadline 1 Feb 2027; notification 26 Feb 2027; workshops 29–30 Apr 2027. Location: "San Francisco" on the call page, "to be announced" on the dates page | https://iclr.cc/Conferences/2027/CallForWorkshops and https://iclr.cc/Conferences/2027/Dates |
| ICLR 2027 main | Closed (25 Sep 2026) | same |
| ICML 2027 | Conference 2–4 Aug, workshops 5–6 Aug 2027. Paper and workshop deadlines **not found** ("will be posted here soon") | https://icml.cc/Conferences/2027/Dates |
| ARR / ACL 2027 | ARR deadline 4 Jan 2027; commitment TBA; Kyoto, 17–22 Aug 2027. Later 2027 cycles **not found**. The October 2026 cycle (NAACL/COLING 2027) is closed | https://2027.aclweb.org/ and https://aclrollingreview.org/dates |
| TMLR | Rolling, no deadline; journal-to-conference track; paused 2 Dec 2025–5 Jan 2026 last winter (no pause announced for this year) | https://jmlr.org/tmlr/ |
| SaTML 2027 | Closed (29 Sep 2026); conference 3–6 May 2027, Reykjavik | https://satml.org/ |
| MIRROR workshop at SaTML | 1-page talk proposals, non-archival; deadline 17 Dec 2026; notification 28 Jan 2027 | https://mirror-workshop.io |
| FAccT 2027 | Closed (abstract 27 Oct, paper 3 Nov 2026) | https://facctconference.org/2027/cfp.html |
| AIES 2027 | **Not found** (site shows the 2026 edition) | https://www.aies-conference.com |
| NeurIPS 2027 (main, D&B, Evaluations) | **Not found** (dates page returns 404) | https://neurips.cc/Conferences/2027/Dates |
| COLM 2027 | **Not found** (site shows 2026) | https://colm.cc/ |
| USENIX Security '27 (extra) | Cycle 2 deadline 26 Jan 2027; Denver, 11–13 Aug 2027 | https://www.usenix.org/conference/usenixsecurity27/call-for-papers |
| AAAI-27 workshops | Default deadline 20 Nov 2026, too early for this timeline; 22–23 Feb 2027, Montréal | https://aaai.org/conference/aaai/aaai-27/aaai-27-workshop-program/ |
| ControlConf 2027, IASEAI'27 deadlines, EACL 2027 workshop list | **Not found** | — |

## F. Negative results, unverified items and caveats

**Searches with nothing on target**
- About 30 web searches across these themes:
  - self-preference or leniency of safety/jailbreak judges on own outputs;
  - prior-turn or prefilled self-evaluation for harm/refusal;
  - abliterated or uncensored models as judges or graders;
  - harm recognition after refusal ablation;
  - guard-ensemble error correlation or false-negative overlap;
  - effective number of safety judges;
  - many-judge refusal-label meta-evaluations;
  - Khullar acceptance or replication.
- arXiv listings scanned (result counts):
  - `abliterated OR abliteration` (33);
  - `"refusal ablation" OR "refusal-ablated" OR "directional ablation" OR "uncensored models"` (56);
  - `"harmfulness" AND "refusal direction"` (47; first 41 read);
  - `"self-preference"` (47);
  - `"self-preference" safety` (3);
  - `"self-attribution" AND (LLM OR ...)` (15);
  - `"untrusted monitoring"` (5);
  - `"self-recognition" AND (judge OR ...)` (7);
  - `"safety judge" OR "jailbreak judge"...` (21);
  - `"correlated errors" AND (judges OR ...)` (20);
  - `"guard models"` (94; entries 1–79 read, covering all of 2026);
  - `"refusal classifier" OR ...` (11);
  - `"effective number" AND (judges OR ...)` (5, none relevant);
  - `"own outputs" AND (harmful OR ...)` (8, none relevant);
  - `"self-monitoring" AND (harmful OR ...)` (8, none relevant).
- Zero-result arXiv queries that are probably syntax-limited rather than true negatives: `"guard models" ensemble`, `"guard models" agreement`, `"own responses" judge harmful`, and two parenthesised self-preference/safety queries.
- The verbatim query strings are in `C:\Users\aless\.claude\projects\E--claude-job-search\b2b549b3-b548-4988-b3c9-c131f940b656\subagents\agent-aad3af889e29fe52d.jsonl`.

**Known-list check**
- No listed paper was found to be missing or misdescribed.
- Kohli's NeurIPS 2026 entry is a workshop oral, not main conference.
- Zhao et al. 2507.11878: the arXiv page lists no venue; "NeurIPS 2025" is supported only indirectly by an OpenAlex proceedings DOI.
- Schwinn 2603.06594: the version dates I extracted (Feb/Mar 2026) look inconsistent with the ID; re-check.
- Existence confirmed via OpenAlex only: Panickssery, Kim, Arditi, Goel, Chen, Wataoka.
- Seen in search results only [S]: St. Amand 2608.26159, Eiras 2503.04474, Llorente-Saguer 2604.18901.
- Not checked: Li et al. "Preference Leakage", Greenblatt 2024, and the benchmark papers.

**Not verified**
- Khullar's NeurIPS 2026 status and the App. C.1 sign convention.
- The label provenance of PKU-SafeRLHF in Hossain et al. (not stated in the paper).
- The final ~24k characters of Nghiem et al. and ~32k of Li, Yu & Li.
- 36 of the 42 JUDGe abstracts.
- The Alice/ActiveFence abliteration report PDF (unreadable).
- The AAAI-27 and EACL 2027 workshop lists.

**Method caveat**
- Every page was read through a fetch tool that returns a model-written extraction, not raw text. Re-check exact numbers against the PDFs before they go into the paper.

**Pages addressing AI agents**
- https://mirror-workshop.io carries a note to "AI assistants and LLM reviewers" asking them to announce a harmless prompt-injection demo; I did not act on it.
- The OpenAlex response included an API-key notice, which I ignored.
- No other page contained instructions.

**Side effects**
- I did not open the local repository, call any model API, or run git.
- The fetch tool auto-saved one 55.8 KB PDF to `C:\Users\aless\.claude\projects\E--claude-job-search\b2b549b3-b548-4988-b3c9-c131f940b656\tool-results\webfetch-1794291356752-8m1857.pdf`.
