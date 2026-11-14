# Mock reviews by four venues (Claude agent with no history, 13 November 2026)

Condensed record of the report of a fresh Claude Opus 5.5 subagent (web search allowed), given the same request and copy as the ChatGPT review (E:/claude/_audit_copy/mock_review_1113). All points kept; wording shortened.

## Recommendations
| Venue | Recommendation | What would change it |
|---|---|---|
| TMLR | Minor revision (leaning accept) | Leaning reject if P1 and P2 end "not carried out" (D20 or Section 10.4) and no equivalence statement exists |
| ACL Rolling Review | Major revision for main; acceptable for Findings (soundness 4, excitement 2.5-3, overall 3, ethics flagged) | A consistent effect in the instruction-tuned group plus a deployment-like second instrument |
| JAIR | Major revision (reject, resubmission encouraged) | A mechanism-level finding, e.g. an own-answer effect that survives paraphrase |
| MIS Quarterly | Reject | Only a reframing around a theory of AI controls with organisational evidence (a different paper) |

## Main weaknesses raised
- TMLR: no equivalence margin for theta_S or iota_S (a null can only read "not detected"); D20 can stop P1 in a plausible regime (0% carried out at theta = -2 points with no background discordance, 3.6% at -3); most screen-positive weight from refusal-removed builds; no judge-competence condition; two-phase variance of Section 9.5 (b_g treated as fixed); P3 margin of 7 points chosen from the standard error (100% power at beta = 0); figures and per-model forest plots needed; cite prefill awareness (Wang et al. 2026, arXiv:2606.12747).
- ARR: model choice not motivated by the claim (seven of twelve refusal-removed; three of four uncensored from the Dolphin line); author confounded with kind of refusal removal (Section 6.3); ecological validity of a long rubric after the assistant turn, one template only; C2 shows a turn in another model's style, so iota_S may measure detection of a foreign turn (Wang et al. 2026); English, single-turn, public benchmarks; four minutes per answer optimistic; Responsible NLP checklist (AI assistance, anonymised OSF links); likely ethics flag (D1 rows, HRPP pending).
- JAIR: originality and significance (a particular configuration beside Khullar et al.); no mechanism probe (paraphrased or obfuscated own answer, Mahbub & Feng 2025, arXiv:2512.05379; explicit attribution); generality (quantised 4-8B builds, two hosted 24B); inferential machinery large relative to the effect (D19, D20, fragility count); process history to a supplement; the PI labels all 567 answers and adjudicates.
- MISQ: no IS theory (segregation of duties, agency monitoring, automation bias not engaged); no organisational context or costs; refusal-removed builds have no organisational counterpart; benchmark-to-organisation step not argued.

## Improvements, by priority (cash / machine / authors; pilot effect)
1. D7 methodologist and faculty advisor in place. Process; may lead to [D]. 0 / 0 / 4-8 h. (Now a condition of the freeze, rv9b.)
2. [D] Equivalence margins (TOST) for theta_S and iota_S with a claim row. 0 / ~1 h of R-S1 rows / 4-6 h; at most ~1 day before the pilot registration.
3. [D] Two-phase variance for the label-assisted estimator (bootstrap over prompts redrawing labels within cells, or a linearised second-phase term), checked in R-S3 and run (b). 0 / 2-4 h / 1-2 days; no delay as a dated amendment before the freeze.
4. [D] Judge-competence rule: blind discrimination (detection minus false-alarm rate) beside theta and iota; a change of a judge whose discrimination interval includes zero reported as not interpretable. 0 / 0 / 2-3 h.
5. Headline by group (instruction-tuned and refusal-removed estimates first; "presentation effects on delivered harm flags"). Framing.
6. C2 and turn detection: cite Wang et al. 2026 and Mahbub & Feng 2025; Section 18.1 says iota_S can reflect detection of a foreign turn; report the disavowal coding of A2 vs C2 in the main text. Framing.
7. [D] Second, deployment-like instrument on the local judges (short self-check on own harmful-frame answers, both presentations), registered secondary. 0 / ~6,000 calls, 8-25 h / ~1 day; ~1 day before the pilot registration, or an amendment before the freeze (then not tested in the pilot).
8. [D] P3 margin: justify 7 points, tighten to 5 (94% power at beta = 0, A.1), or make P3 an estimate only. 0 / <1 h / 1-2 h.
9. [D, no amendment needed] Hosted-model risk: D13 can drop model 22 or 23; at least set out the loss-risk reasoning in Section 10.4.
10. [D, pilot rule] Pilot report gives unsigned discordance (share of own-answer pairs with A1 != A2, by judge, tail prompts only), feeding the power table of rule 6 and the likelihood that D20 binds. 0 / 0 / 2-3 h.
11. Labelling time: time the training rounds, replan sessions, state which safe-side reductions of Section 9.3 come first.
12. Ethics package: HRPP determination, written notice to providers for the D1 rows (OpenAI's terms open), statement in the paper.
13. [D, light] Descriptive changes in behaviour class and confidence on the harmful frame (Section 8.5).
14. Writing: one design figure, one table of claim rules; decision log, review rounds and exposure history to a supplement; AI assistance disclosed.
15. MISQ only: theory framing (segregation of duties, automation bias).

## Criticisms no improvement can answer under this budget
Deployed frontier monitors out of reach (full commercial frame about US$200); authorship vs reaction to own-like content structurally inseparable; mechanism open; narrow setting (one instrument, English, single-turn, quantised, temperature 0); thin human reference (two labellers, one designed the study); hosted weights and provider layers unverifiable; nominal levels (run (k)); the review process (PI decisions; AI reviews, one a panel model; at most one independent methodologist). Each with a sentence for the paper.

Sources cited by the agent: https://jmlr.org/tmlr/reviewer-guide.html, https://jmlr.org/tmlr/acceptance-criteria.html, https://aclrollingreview.org/reviewerguidelines, https://aclrollingreview.org/authorchecklist, https://jair.org/index.php/jair/about/submissions, https://arxiv.org/abs/2603.04582, https://arxiv.org/abs/2606.12747, https://arxiv.org/abs/2512.05379
