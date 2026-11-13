# Corrections after review round 17 (code of protocol v2.3)

- **Report answered:** `docs/audit/2026-11-13_reviewer_round17_codex_gpt61sol.md` (GPT-6.1 Sol, 13 November 2026, a check of the corrections made after round 16).
- **Verdict of the report:** no critical or major point. With a stable draw the repeat gate orders the calls correctly on every path (one or several sessions, a pending call, a deferred pair, `--max-calls`, `--allow-missing`; the longer context does not apply to block 1; `--complete-block` sends nothing and needs the repeats final), and it changes no other call. The report marks output differences, writes no flag, and the texts agree. Four minor points remain.
- **No paid call, no answer and no verdict** was made for these corrections. `src/prepare_data.py` was left out of the reviewed copy; nothing in the round depends on it.

## Minor points

| Point of round 17 | Correction | Where |
|---|---|---|
| The changed-draw stop read only final records and only judges with repeat calls drawn now: a non-final recorded repeat, or a recorded repeat followed by an empty draw, escaped it | The stop reads every recorded attempt (the keys of the final records and of `attempt_state`), for every judge of the session with calls of the round, also when nothing is drawn now | `src/run_judges_v23.py` (`pilot_repeat_gate`, `main`) |
| A local judge with no attempt in the round was left out of the report, so an empty result could read as no difference | The planned repeats are taken for every local judge with own answers to the round's harmful prompts, independently of attempts; a judge that has not started is listed as incomplete | `scripts/pilot_report_v23.py` (`main`) |
| The rule line hid incomplete coverage whenever a judge was to be investigated | Two rule lines, built by `repeat_rules`: the judges to investigate, and the judges with fewer pairs than planned | `scripts/pilot_report_v23.py` (`repeat_rules`, `main`) |
| The report's docstring and Markdown introduction still said "statuses, tokens and costs only" | Both name the counts of repeat pairs that differ (decision D27) | `scripts/pilot_report_v23.py` |

## Tests

- New test `t_pilot_repeat_main`, through `main`: an own answer to a harmful prompt of the round left out holds the 20 repeat calls (`repeat_waits`) while the 198 other calls are made; `--allow-missing` with a reason then sends them, drawn from the answers present; when the left-out answer arrives and enters the draw, the session stops before any call and writes nothing.
- `t_pilot_repeat_gate`: also a non-final recorded repeat of an answer not drawn (stop), a recorded repeat with nothing drawn now (stop), and a non-final recorded repeat of a drawn answer (no stop).
- `t_pilot_report`: every local judge with own answers in the round is listed; those not run in the test are incomplete with 0 pairs and are not marked for investigation; the Markdown and the rule line name them; `repeat_rules` gives investigation and incompleteness on separate lines, also when both apply to one judge, and "none" for a complete judge with no difference.

## After this round

The eleven offline files hold 191 declared tests. Section 14.2, the status lines, decision D27 and the registration summary record the round.
