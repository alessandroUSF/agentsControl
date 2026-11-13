## 1. The repeat gate

For a stable draw, ordering is correct: pending calls and deferred pair halves keep repeats waiting; later sessions rebuild the unfinished set; final calls release it within the session. `--max-calls` cannot bypass it. Missing own harmful answers hold repeats unless `--allow-missing` has a reason; missing safe answers do not.

There is no apparent permanent hold once these conditions are satisfied. Non-repeat calls retain their behavior. Longer-context mode excludes block 1; `--complete-block` sends nothing and requires planned repeats to be final.

The changed-draw check runs before paid or local calls, **when triggered**, but has the omissions listed below.

**Conflict:** I am commercial-panel model 11, developed by OpenAI. The changed-draw finding can permit paid calls to OpenAI models 3, 9 and 11 despite the promised stop. The remaining findings concern local-judge reporting.

## 2. The report

`investigate` now follows flag, status **or output** differences. For included judges, `complete` correctly requires the planned number of matched pairs in both presentations. `min(repeat_answers, own answers with content)` matches the planner.

However, judges without ordinary attempts can disappear, and the rule line omits incompleteness whenever any judge needs investigation. JSON and Markdown otherwise distinguish incomplete coverage correctly.

Repeatability exports difference counts, without individual flags, outputs or hashes. Existing registered blind-rate diagnostics remain.

## 3. The texts

Sections 11.6, 12.1 and 13.1, the registration summary and D27 agree in substance. The corrected totals—220 calls per local pilot round, 2,657 overall and 2,200 local calls per round—are consistent. The summary correctly qualifies 5.4% and gives 8.7%/2.5% for sparser scenarios.

The report’s own introductory wording still omits the repeatability exception.

## 4. The tests

`t_pilot_repeat_gate` exercises the helper and runner loop as claimed. Removing the loop’s gate or suppressing missing-answer detection would fail its assertions.

It manually wires the gate into `JudgeRun`, so it would not detect removal of that wiring from `main`. It also misses empty draws and recorded non-final repeats.

`t_pilot_report` detects output-only differences and incorrect completeness within `repeatability`. It does not test incomplete Markdown/rule output through `main`, mixed investigation/incompleteness, or unstarted judges. One assertion currently requires omission of unstarted judges.

The supplied log contains **190 passing tests and a passing end-to-end run**.

## 5. Verdict

**No critical or major point remains.** Complete these four minor corrections before pilot registration, apart from the PI’s decisions and actions:

1. **Minor — incomplete draw-history check.** `src/run_judges_v23.py:241`. Only final keys are checked, and only judges with current repeat candidates are visited. A recorded final repeat followed by an empty current draw escapes the stop; a non-final recorded repeat outside a changed draw also escapes. Compare all recorded repeat keys for the selected round/judges against the draw, including an empty draw.

2. **Minor — unstarted judges disappear.** `scripts/pilot_report_v23.py:488`. Planned repeats are inferred from attempted ordinary calls. A local judge with eligible answers but no attempts is omitted; an empty result can say “no difference.” Derive expected coverage from the round’s planned judges, independently of attempts.

3. **Minor — rule line hides incomplete coverage.** `scripts/pilot_report_v23.py:513`. A nonempty investigation list bypasses the incomplete branch. Report incomplete judges independently of investigation results.

4. **Minor — stale report wording.** `scripts/pilot_report_v23.py:390` and `:18`. Add the local-repeat comparison exception to both “statuses, tokens and costs only” statements.

**Could not check:**

- Python execution, mutation runs or live providers. No files were changed and no model calls were made.
- Author verification: add fixtures for recorded repeats with an empty/changed draw, an unstarted local judge, and simultaneous differences/incompleteness; run `python -I -X utf8 tests/test_judges_v23.py t_pilot_repeat_gate t_pilot_report`. After correction, expect both PASS, zero failures, exit 0.