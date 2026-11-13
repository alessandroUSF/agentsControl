## 1. The major point

**D26 is implemented; the round-14 major point is closed.** One minor edge case remains below.

The sending path enforces registration and absence of a freeze, checks the pinned endpoint, and uses model 22’s respondent adapter and configuration. Each attempt reserves against the run cap and all unfinished holds, settles outside every block, and writes the private record before settlement. Public records exclude answer text and error bodies.

Recovery follows D13: a recorded attempt settles at its recorded cost; an attempt without a record settles at its reservation as interrupted and may be retried. A matching final, settled record prevents another call. Counts and readings reach both report formats.

The D13 defaults, retry handling, ledger kind, paths, reuse conditions and identity checks remain unchanged.

**Conflict disclosure:** I am commercial-panel model 11, developed by OpenAI. The remaining D26 findings concern model 22. My assessment of shared runner regressions also bears on OpenAI models 3, 9 and 11.

## 2. The minor points

All four round-14 corrections are right:

- Protocol and summary now distinguish the doubled local caps: **4,000** for models 16/17 and **1,200** otherwise.
- Section 9.1 no longer calls `clarification` exclusive to labellers.
- `statistics.median` replaces the upper-middle selection. Independently reading the supplied rows gives **508.5** for model 17 and **64.5** for model 16; summaries and repeated figures agree.
- The strengthened assertions pin both overrides to **2,000** and check the requested context-fit boundary.

## 3. The tests

The supplied output contains **187 named passing tests across eleven files**, plus a passing synthetic end-to-end run. I did not execute them.

The cap assertions would detect reverting either override. Reverting context-fit accounting to a doubled common cap would produce **2,088**, rather than **−712**, for models 16/17, failing the new assertions.

`t_provider_prompt_check` meaningfully checks registration/freeze gates, model selection, successful settlement, private answer storage, ordinary reuse and reading branches. Its protection is incomplete:

- Removing D26 reconciliation would leave this test passing: it injects no crash.
- Its generous caps do not demonstrate refusal when the reservation cannot fit.
- `Fake.sent` distinguishes benchmark prompts from other prompts, but does not prove the exact sentinel or complete configuration.
- Reference counts are stubbed. The invalid-file check fails on the first file, leaving independent validation of the other two untested.
- It checks the report reader; successful D26 content is not exercised through generated JSON and Markdown.

## 4. Consistency and fingerprints

The substantive corrections agree across code, protocol, registration summary and decisions, subject to the remaining points below. Dropping the requirement to precede round-1 responses is reflected in the current protocol.

The supplied cross-reference result reports **806 references, zero dangling**.

**No input of the stored simulation rows changed in the complete supplied diff.** The fingerprinted modules, panel/frame/control inputs, scenarios and stored run arguments are untouched. This confirms unchanged inputs relative to round 14; it is not a fresh fingerprint recomputation.

## 5. Verdict

**No critical or major point remains.** Finish these minor corrections before pilot registration, apart from the PI’s outstanding decisions and actions:

1. **Minor — declare the new dependencies.** [requirements.txt:10](E:/claude/_audit_copy/agentsControl_r26_round15_code/requirements.txt:10), [src/run_models.py:1829](E:/claude/_audit_copy/agentsControl_r26_round15_code/src/run_models.py:1829). `d26_counts` imports `jinja2` and `tokenizers`, but neither is declared in the documented installation requirements. Add their tested, pinned versions. Validate in a fresh environment after installing requirements: `python -I -c "import jinja2, tokenizers"`; expect exit 0.

2. **Minor — retain counts from empty responses.** [src/run_models.py:1948](E:/claude/_audit_copy/agentsControl_r26_round15_code/src/run_models.py:1948). A parsed response with `text=""`, `stop_reason="stop"` and `input_tokens=566` is recorded as final, but its counts line substitutes `None`, reports `no_count` and returns 3. Reuse repeats that result indefinitely. Preserve the reported count independently of answer status and compare valid counts for `empty`/`truncated_empty`, retaining status alongside the reading. Add this stub case; expect 566, `template_default`, exit 0 and no second call.

3. **Minor — strengthen D26 regression coverage.** [tests/test_runner_offline.py:2201](E:/claude/_audit_copy/agentsControl_r26_round15_code/tests/test_runner_offline.py:2201). Add D13-style crash cases before the private record, before settlement and after settlement; cap-refusal cases; exact request/configuration assertions; separate corruption of each pinned file; and successful report generation. Recorded final calls must never be resent; unrecorded interrupted calls must settle conservatively before retry. Removing reconciliation or the relevant guard should fail these tests.

After extending the tests, run:

```text
python -I -X utf8 tests/test_runner_offline.py t_provider_prompt_check
python -I -X utf8 tests/test_judges_v23.py t_template_layouts t_context_fit
```

Expect all selected tests PASS and exit 0.

**Could not check:**

- Python execution or actual mutation runs.
- The absent tokenizer files. Author check, using their directory as `DIR`:
  `python -I -c "import sys,datetime;sys.path.insert(0,'src');import run_models as r;print(r.d26_counts('DIR',date=datetime.date(2026,11,13)))"`
  Expected: `{'request': 12, 'template_default': 566, 'date': '2026-11-13'}`.
- Live provider behaviour or complete stored-fingerprint recomputation.

No files were changed and no model/API calls were made.