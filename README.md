# agentsControl

**Safeguards that fail in both directions.** This project measures how often language models refuse legitimate requests (over-refusal), how often they help with harmful ones (harmful compliance), and how reliably an automated multi-agent monitor detects both failures.

> Status: in progress (started November 2026). Hypotheses are pre-registered in [`docs/PREREGISTRATION.md`](docs/PREREGISTRATION.md). No results are reported yet.

## Questions
1. How reliable is a multi-agent monitor compared with blind human labels, and where are its blind spots? LLM-based monitors may make systematic errors that heuristic monitors do not (Ward, Hu et al., 2026), so this project measures them directly.
2. Does a stated context ("I am an adult screenwriter", "I am a student") change refusals and harmful compliance?
3. Which models over-refuse most on prompts that look sensitive but are safe?

The predictions for each question are in the pre-registration, which was committed before any output was read or scored.

## Data
| Source | Prompts in the sample | What it tests | License |
|---|---|---|---|
| XSTest (Röttger et al., 2024), rev `d7bb5bd` | 450: 250 safe, 200 unsafe contrast prompts | Exaggerated safety on safe prompts that look unsafe | CC-BY-4.0 |
| OR-Bench Hard-1K (Cui et al., 2024), rev `e36d8b8` | 300 of 1,319 seemingly toxic but safe prompts | Over-refusal | CC-BY-4.0 |
| OR-Bench Toxic (Cui et al., 2024), rev `e36d8b8` | 300 of 655 toxic prompts | Harmful compliance | CC-BY-4.0 |
| Own prompts (`data/own/`) | in preparation | Mature themes in fiction for adults (non-explicit); everyday dual-use requests. Each prompt runs under three framings: no context, adult screenwriter, student | released with the results |

The benchmark files are pinned to fixed revisions and checked against `data/SHA256SUMS.txt`. The sample is stratified by category and drawn with a fixed seed (`src/prepare_data.py`).

## Models
| Model | Access | Role |
|---|---|---|
| Claude Sonnet 5.5, Claude Haiku 5.5 | Anthropic API | evaluated |
| GPT-5.6 Luna | OpenAI API | evaluated |
| Llama 3.1 8B Instruct | local (Ollama) | evaluated |
| Qwen3 8B, thinking off | local (Ollama) | evaluated |
| Llama 3.1 8B, abliterated (refusal direction removed) | local (Ollama) | positive control: supplies truly harmful answers to test whether the monitor catches them |

The settings are in `config/models.json`. Every model runs with its provider defaults: no system prompt and no temperature override. Local models use a fixed seed.

## Method
- **Runner** (`src/run_models.py`):
  - A hard budget cap, reserved per call at the worst-case cost.
  - Resumable runs.
  - An audit log of every call (model, prompt id, tokens, cost, latency, stop reason, request id) that does not contain the answer text.
- **Provider blocks are separate from refusals.** When the API itself blocks an answer, the block is recorded on its own and is not counted as a refusal written by the model. Examples are Anthropic's `stop_reason: "refusal"` and OpenAI's refusal content.
- **Judge (in development).** It combines several pieces:
  - rule-based refusal patterns;
  - two independent classifier agents;
  - an arbiter for disagreements;
  - an audit log.

  Answers to harmful prompts are judged only by local models.
- **Labels.** Three classes: full compliance, partial refusal, full refusal (`labels/RUBRIC.md`, following XSTest). About 150 answers, stratified by model and source, are labeled by hand and blind to the judge.
- **Statistics.**
  - Rates with bootstrap 95% confidence intervals.
  - Paired McNemar or permutation tests on the same prompts.
  - Cohen's kappa for agreement between the judge and the human labels.

## Responsible design
- **Commercial APIs receive only safe prompts** (`expected = comply`) and the author's own non-harmful prompts. The benchmarks' harmful prompts run only on local open-weight models. `src/providers.py` enforces this rule, and the runner checks it a second time before each call.
- **API calls use dedicated research accounts and keys** (`AC_*` in `.env`). The runner never falls back to other keys.
- **Raw completions to harmful prompts are never published.** The repository will publish labels, aggregate metrics, audit logs and redacted examples only.

## Reproduce
```bash
pip install -r requirements.txt
python -I scripts/fetch_data.py         # downloads the pinned benchmark files and checks SHA-256
python -I src/prepare_data.py           # builds data/processed/sample.jsonl with a fixed seed
python -I src/run_models.py --dry-run   # prompt counts and cost estimate, no API call
```
API keys and the budget cap go in `.env` (see `.env.example`). The `.env` file is never committed.

## Use of AI tools
The code was written with help from Claude Code. The research questions, hypotheses, prompt categories and human labels are the author's.

## Author
Alessandro Almeida, Graduate Researcher, University of South Florida. [Google Scholar](https://scholar.google.com/citations?user=HUTnVjwAAAAJ)

## References
- Röttger, P., Kirk, H. R., Vidgen, B., Attanasio, G., Bianchi, F., & Hovy, D. (2024). XSTest: A Test Suite for Identifying Exaggerated Safety Behaviours in Large Language Models. NAACL 2024.
- Cui, J., Chiang, W.-L., Stoica, I., & Hsieh, C.-J. (2024). OR-Bench: An Over-Refusal Benchmark for Large Language Models. arXiv:2405.20947.
- Ward, J., Hu, S., Wong, A., Hu, N., Woodworth, B., Turner, A. M., & Cloud, A. (2026). Gradient Routing Localizes and Removes Unintended Behaviors in RL. arXiv:2610.17062.
