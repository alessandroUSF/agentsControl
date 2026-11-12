# Literature check and proposed additions (Claude Opus 5.5 research subagent), 8 November 2026

- **Setup:** web search was allowed. The subagent read only the protocol (v2.1) and the round-2 reviews, opened no data and changed no files.
- **Text:** a summary of the agent's final message. The URLs are the sources it opened.

## (A) References the round-2 reviewers cited, verified
| Cited as | Title; authors; venue | Finding | Notes |
|---|---|---|---|
| Chae et al. | "Self- and Other-Labels Induce Bidirectional Bias in LLM Judges"; Songeun Chae, Min Kim, Donghoon Jung, Seojin Choi, Seohyon Jung; Findings of EMNLP 2026, pp. 33466–33482 (https://aclanthology.org/2026.findings-emnlp.1571/) | Ten LLMs judged narrative tasks. Self-preference vanishes under blind evaluation, and a small residual runs against self-preference. | Not a safety task. |
| Schwinn et al. | "A Coin Flip for Safety: LLM Judges Fail to Reliably Measure Adversarial Robustness"; Schwinn, Ladenburger, Beyer, Mofakhami, Gidel, Günnemann; arXiv:2603.06594 (2026) | Four safety judges score 0.51–0.59 accuracy on JudgeStressTest under joint shift. | The paper gives two label counts (6,442 and 6,642). It is a hard, filtered set (about 78% harmful). |
| Agnihotri et al. | "A Granular Study of Safety Pretraining under Model Abliteration"; Agnihotri, Jakubassa, Dey, Goyal, Schiele, Radhakrishnan, Keuper; NeurIPS 2025 Lock-LLM workshop; arXiv:2510.02768 | Models do not reliably detect their own refusal state, and less so after abliteration. | Qualitative. Human labels on only 10 prompts × 20 systems. About refusal, not harm. |
| Awuni et al. | "Who Judges Matters: Measuring Family-Conditioned Preference in LLM-as-Judge Panels"; arXiv:2609.17857 (2026) | Same-family lift of 3.4–8.4 pp in 9,312 pairwise judgments; perplexity explains 61%. | Measures quality, not safety. |

Khullar et al.: Dipika Khullar, Jack Hopkins, Rowan Wang, Fabien Roger (arXiv:2603.04582). An earlier version, "Language Models Rate Their Own Actions As Safer", was a NeurIPS 2025 workshop paper.

## (B) Further related work
- **Self-preference and recognition:**
  - Spiliopoulou et al. 2025 (arXiv:2508.06709): self- and family bias against expert labels.
  - Chen et al. 2025 (arXiv:2504.03846): long reasoning reduces harmful self-preference.
  - Wataoka et al. (arXiv:2410.21819): self-preference tracks perplexity.
  - Mahbub & Feng 2025 (arXiv:2512.05379): obscuring authorship only partly removes self-preference.
  - Bai et al. 2025 (arXiv:2510.03399): self-recognition is rarely above chance.
  - St. Amand et al. 2026 (arXiv:2608.26159): role-tag placement changes recognition.
  - Yang et al. 2026 (arXiv:2604.22891).
- **Monitoring:**
  - Gardner-Challis et al. 2026 (arXiv:2602.20628): passive self-recognition as a collusion route.
  - Phute et al. (arXiv:2308.07308) and Brown et al. 2024 (arXiv:2407.03234): an LLM screening text for harm as a defence.
- **Safety-judge evaluation:**
  - CAREBench 2026 (arXiv:2606.29685, Appendix B.4): same-family leniency on "Unacceptable" flags, β = −0.35, p = 2×10⁻⁹, n = 7,489, three judges.
  - Liu et al., ICLR 2025 (arXiv:2410.10414): guard models are miscalibrated and transfer poorly.
  - HarmMetric Eval (arXiv:2509.24384).
- **Abliteration:** Llorente-Saguer 2026 (arXiv:2604.18901): harmful-intent probes score the same AUROC after abliteration.
- **Juries and inference:**
  - Kohli 2026 (arXiv:2605.29800): nine judges give about two effective votes.
  - Lee et al., ICML 2026 (arXiv:2511.21140): CIs for the misclassification correction that include calibration uncertainty.
  - Dorner et al., ICLR 2025 (arXiv:2410.13341): limits on the savings from LLM judges.
  - PPI++ (arXiv:2311.01453); stratified PPI (NeurIPS 2024).
  - Gligorić et al., NAACL 2025.
  - Jung et al., "Trust or Escalate", ICLR 2025.

## (C) Recommended additions, as proposed
1. **The flag outcome F primary for T1a/T1b** (confirmatory).
2. **A confidence field in the judge output, and the guards' native scores:** for calibration and cascades (exploratory).
3. **External transfer check with published human labels:**
   - XSTest v2 completions (5 models × 450 prompts; two annotators and a final label; same three-class scheme);
   - optionally JBB `judge_comparison` (300 items, 3 humans, MIT) and WildGuardTest (gated).
   - Cost: US$2–6 and 6–8 GPU hours (exploratory).
4. **Cost–accuracy frontier and cascade simulation** on the gold verdicts. One cascade becomes an instrument candidate.
5. **RQ4 correction:** Lee et al. CIs and stratified PPI.
6. **Gold-anchored Dawid–Skene sensitivity analysis,** with one judge per developer (exploratory).
7. **Effective number of independent judges** (descriptive).
8. **Refined recognition probe** (exploratory).
9. **Plan B only:** the PI labels 50 external items to anchor the rubric (about 1 hour).
10. **Skip:**
    - the paraphrase condition (it creates new harmful text);
    - representation probes;
    - choosing gold items by judge disagreement.

## (D) Novelty
- **Khullar et al. already cover harm and risk ratings,** so "extends Khullar to safety labels" overstates the gap. The new parts are narrower:
  - refusal and harm classification of chat answers against item-level human gold;
  - many judges, including small and refusal-removed ones;
  - the blind cell;
  - guards in the error-correlation analysis.
- **Related results already exist:**
  - self- and family bias against human gold (Spiliopoulou 2025, general quality);
  - same-family leniency on safety flags (CAREBench 2026, at appendix level).
- **Expected outcomes:**
  - T1a is expected to be null (Chae 2026; Bai 2025);
  - T4 is expected to show non-inferiority (Zhao 2025; Llorente-Saguer 2026).
- **Section 2 needs rewording:** "judge reliability … is established" contradicts Schwinn 2026.
- **Low judge effort** may inflate self-bias (Chen 2025). It is a moderator and a limitation.
- **No paper found** measures blind and in-context self-judging of refusal or harm labels against human gold.
