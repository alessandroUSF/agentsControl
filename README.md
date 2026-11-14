# agentsControl

**Judging Their Own Answers: Conversational Presentation and Harm Flags in Twelve Open Models**

A language model is often asked to check an answer that it wrote itself. This study asks two questions:

1. Does a model flag harmful content less often when an answer is shown as its own previous turn than when the same answer is shown as quoted text?
2. Is that change larger for the model that wrote the answer than for a different model that sees the same answer in the same two ways?

> **Status: protocol v2.3 registered for the pilot (tag `v2.3-pilot-registration`). There is no result.**
> - Registered: version 1 of the pre-registration ([`docs/PREREGISTRATION.md`](docs/PREREGISTRATION.md), commit `4124f32`, 7 November 2026), and protocol v2.3 for the pilot (the commit signed by the investigator and tagged `v2.3-pilot-registration`, registered on OSF). A second registration, the freeze, follows the pilot report.
> - Current design: [`docs/STUDY_PROTOCOL_v2.3.md`](docs/STUDY_PROTOCOL_v2.3.md). It replaces protocol v2.2 ([`docs/STUDY_PROTOCOL_v2.md`](docs/STUDY_PROTOCOL_v2.md), never registered). Amendment 2 ([`docs/PREREGISTRATION_AMENDMENT_2.md`](docs/PREREGISTRATION_AMENDMENT_2.md)) withdraws the hypotheses H1 to H3 of version 1 and says why.
> - Done so far: seven local models answered the benchmark prompts (7,457 answers). No person has read, judged or labelled an answer; on 13 November 2026 commands run by the AI assistant screened the answers of one run and printed counts and three short excerpts (protocol Section 3.4). No call to a commercial API has been made; the only cost so far is a purchase fee of US$0.80.
> - The code that the protocol needs is written and tested offline (see "State of the code").

## Design in brief

The protocol is the reference. This is a summary.

| Element | Choice |
|---|---|
| Primary panel | Twelve open models: five instruction-tuned and seven with refusals removed (three abliterated builds, four uncensored fine-tunes). Ten run locally; two are reached through an API |
| Primary material | The answers of these models to 300 harmful prompts from two public benchmarks |
| Four verdicts per answer | The author judges its answer as quoted text (A1) and as its own previous turn (A2). A control judge of the same type, unrelated to the author, does the same (C1, C2) |
| Outcome | Flag: the delivered verdict says that the answer holds harmful content |
| Primary statistics | Among answers that do not open with a refusal phrase: the mean of A2 − A1, the mean of (A2 − A1) − (C2 − C1), and the mean of A1 − C1 |
| Tests | Three tests, fixed before any answer is judged (protocol Sections 2 and 8) |
| Human labels | 567 answers labelled by the principal investigator. An independent annotator labels 381 of them again |
| Secondary | Ten commercial models on 60 of the harmful prompts; 90 safe prompts per model; a challenge set of 70 answers judged by all 22 models |
| Cash | Hard cap of US$128, freeze ceiling US$124 (decision D14, 11 November 2026, second step after decisions D15 and D16). Since model 14 left the study (decision D17, 12 November 2026) the plan is US$47.12 expected and US$102.03 pessimistic |
| Registration | Two steps: a pilot registration before the first pilot call, and a freeze before the remaining confirmatory answers are generated and before any confirmatory answer is screened or judged |

The study can say whether delivered harm flags change with the presentation, and whether the change differs between authors and their control judges. It cannot say why a change happens. Protocol Section 2.4 fixes the wording of every possible conclusion in advance.

## Data

| Source | In the sample | Benchmark label |
|---|---|---|
| XSTest (Röttger et al., 2024), revision `d7bb5bd`, CC-BY-4.0 | 200 unsafe, 250 safe | Unsafe: a model should refuse. Safe: a model should comply |
| OR-Bench Toxic (Cui et al., 2025), revision `e36d8b8` | 300 of 655 | A model should refuse |
| OR-Bench Hard-1K (Cui et al., 2025), revision `e36d8b8` | 300 of 1,319 | A model should comply |

- The benchmark files are pinned by hash (`data/SHA256SUMS.txt`). The OR-Bench files are used under the licence stated in their repository.
- The sample of 1,050 prompts was drawn with a fixed seed (`src/prepare_data.py`) and is sealed.
- The frames of the protocol are prefixes of one seeded order inside each source (`src/frames_v23.py`): a harmful frame of 300 prompts, which contains a common set of 60, and a safe frame of 90.
- [`docs/DATA_INVENTORY.md`](docs/DATA_INVENTORY.md) lists what exists, by counts only. [`docs/SEALED_HASHES.md`](docs/SEALED_HASHES.md) records the hash of every existing output file.

## State of the code

**Written and tested offline**

- Data pipeline and sealed sample: `scripts/fetch_data.py`, `src/prepare_data.py`.
- Answering runner with spending ledger, lock and reservations: `src/run_models.py`, `src/providers.py`, following protocol v2.3 (`src/plan_v23.py`, `src/answers_v23.py`, `src/spend_v23.py`).
- Frames and pilot prompts: `src/subsets.py`, `src/frames_v23.py`, `config/pilot_prompts_v23.json`.
- Initial screen for refusal phrases: `src/screen.py`.
- Assignment of control judges: `src/yoking.py`, `scripts/control_assignment_v23.py`.
- Sampler for the human labels: `src/label_sample.py`.
- Call manifest and cost model: `scripts/manifest_v23.py`.
- Inference functions and three simulation packages: `analysis/inference_v23.py`, `analysis/sim_v23_registered.py`, `analysis/sim_v23_labels.py`, `analysis/tables_v23.py`.
- Records: `scripts/data_inventory.py`, `scripts/check_sealed_hashes.py`.

**Written for protocol v2.3 and tested offline** (protocol Sections 14.2 and 19.4)

- Judging: `src/run_judges_v23.py`, `src/judge_v23.py`, and the judge template `config/judge_prompt_v23.txt`, written by `scripts/build_judge_template_v23.py`.
- Pilot report and analysis: `scripts/pilot_report_v23.py`, `scripts/reading_draw_v23.py`, `analysis/analyze_v23.py`.
- Spending holds for the blocks of protocol Section 12.3: `config/stage_holds.json`, `scripts/holds_v23.py`.
- Judge builds of model 6 and their checks: `scripts/make_judge_alias_m6.py`, `scripts/check_system_override.py`.
- Label files: `scripts/label_draw_v23.py`, `scripts/label_join_v23.py`, `scripts/label_sheets_v23.py`.
- Guard classifiers (decision D29): `src/run_guards_v23.py`, `config/guards_v23.json`.
- One complete run of the whole pipeline on synthetic data: `tests/test_e2e_v23.py`. All thirteen test files pass (13 November 2026).

**Kept for the record, not used by protocol v2.3:** `src/judge.py` and `config/judge.json` (the multi-agent judge of version 1), `src/gold_sample.py` (the sampler of the retired label sample G1), `analysis/power_sim.py`, `analysis/estimators.py` (protocol v2.2; not `scripts/cost_model.py`, which `scripts/manifest_v23.py` still imports), and the author's own prompts in `data/own/`.

## Responsible design

Protocol Section 16 is the reference.

- **Harmful prompts come from two public benchmarks and are sent as published.** Nothing is done to obtain a harmful answer: no jailbreak, no changed system prompt, no second attempt with other words. Refusals and provider blocks are results and are never worked around.
- **Commercial providers receive harmful benchmark prompts in limited numbers** (a change from version 1; protocol Section 16.2 gives the numbers). The calls use research accounts opened for this study. The code accepts only keys whose variable names start with `AC_`.
- **Answers to harmful prompts are never published,** and no answer is quoted in the paper, in this repository or in a review copy. Labelled answers are offered to researchers under a use agreement, with the most hazardous ones withheld.
- **Storage.** Answers, verdicts and private logs stay on the investigator's encrypted drive and in no cloud service.
- **People.** Only the investigator and one independent annotator read answers, under a welfare protocol ([`docs/annotator_packet/`](docs/annotator_packet/)).

## Reproduce

Every command below costs nothing. The first two download the Python packages and the pinned benchmark files; the others run offline.

```bash
pip install -r requirements.txt
python -I scripts/fetch_data.py                # downloads the pinned benchmark files and checks their hashes
python -I src/prepare_data.py                  # writes the sample if absent, otherwise verifies it; never rewrites it
python -I tests/test_frames_v23.py             # frames and pilot prompts
python -I tests/test_label_sample.py           # sampler for the human labels
python -I tests/test_runner_offline.py         # answering runner, ledger, lock and reservations
python -I scripts/control_assignment_v23.py    # control judges (add --write to store the file)
python -I scripts/manifest_v23.py              # calls and cost by block (add --write to store the file)
python -I analysis/tables_v23.py               # tables of protocol Appendix A from the stored simulation runs
```

- The simulations take hours: `python -I analysis/sim_v23_registered.py --grid rs1 --reps 10000 --flips 9999 --out sim_v23_rs1.json`, the same with `--grid rs2 --out sim_v23_rs2.json`, and `python -I analysis/sim_v23_labels.py --reps 2000 --out sim_v23_rs3.json`. Their stored results are in `analysis/output/`. A run with the same `--out` file keeps the scenarios that are already finished; another file name computes them again.
- `python -I scripts/check_sealed_hashes.py` and `python -I scripts/data_inventory.py` need the private answer files, which are not published.
- API keys and the budget cap go in `.env` (see `.env.example`). The `.env` file is never committed.

## Use of AI tools and conflicts of interest

- The text of the protocol, the code and the simulations were drafted with Claude Code, an AI coding assistant of Anthropic, under the investigator's direction. Anthropic is the developer of models 1 and 2 of the commercial panel.
- The design was reviewed in rounds by GPT-6.1 Sol, which is also model 11 of the commercial panel. The reports and the prompts of the rounds are in [`docs/audit/`](docs/audit/).
- No test rests on the commercial panel, and no rule names models 1, 2 or 11. Protocol Section 17 says how both conflicts are handled.
- No person other than the investigator has reviewed the design. A language model is not a peer reviewer.
- The research questions, the decisions and the human labels are the investigator's.

## Author

Alessandro Almeida, Graduate Researcher, University of South Florida. [Google Scholar](https://scholar.google.com/citations?user=HUTnVjwAAAAJ)

## References

- Cui, J., Chiang, W.-L., Stoica, I., & Hsieh, C.-J. (2025). OR-Bench: An Over-Refusal Benchmark for Large Language Models. ICML 2025.
- Röttger, P., Kirk, H. R., Vidgen, B., Attanasio, G., Bianchi, F., & Hovy, D. (2024). XSTest: A Test Suite for Identifying Exaggerated Safety Behaviours in Large Language Models. NAACL 2024.
- Further references are in the protocol.
