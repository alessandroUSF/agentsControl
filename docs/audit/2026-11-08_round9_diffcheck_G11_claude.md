**Verdict:** The diff fixes all five F10 issues and the nit. The offline test passes 113 of 113, which matches the protocol's figure (l.836). I found no blocking issue. The two small fixes below need no new audit round; after them, ready to freeze once the [PI] items are written.

**F10 status**
- **1:** fixed. Protocol hunk `@@ -846`, l.850, now allows `--cut` for a stage that was reduced, fell back or was not run, and bans it for budget in stages 1 and 2. Both rules it cites exist (l.854, l.855).
- **2:** fixed as F10 specified. Runner hunk `@@ -857` reads the latest line, needs `missing` to be a dict, and accepts all-zero counts. §11 l.849 and §13 l.926 match. Tests: `judge_stage_latest_check_governs`, `judge_stage_closes_with_check`. One case F10 cited can still happen (new issue 1).
- **3:** fixed. With `--cut`, the latest line's non-zero counts go into `unanswered_at_close`, and §11 now says "if one exists". Test: `judge_stage_cut_keeps_counts`.
- **4:** fixed. Hunk `@@ -451` filters pilots on `model == m["model"]`, skips models with no prompts in the run, and reads the raw files once. §11 l.833 matches. I found no case where it wrongly blocks or passes a batch: errors, provider blocks and missing IDs are filtered out, and the prompt filter is the same as the main loop's.
- **5:** fixed. The "do not start with" branch, non-zero `missing`, and refund equal to `reserved_usd` are all tested now (test hunks `@@ -195`, `@@ -555`, `@@ -589`).
- **Nit:** fixed (`@@ -13`, `@@ -378`).

**New issues**

*Minor*
1. **What the check line covers is not defined, so stage 2 can still close before gold judging** (§13 l.926). The runner trusts the latest line. Suppose `judge.py` counts only the calls of the run that writes the line. Then the zero line written after the judge pilot is still the latest one, and `--complete-stage 2` passes before gold judging starts. That is F10's own example.
   - The reverse can also happen. A line written while batches were still out shows non-zero counts after they are collected. That refuses a legitimate closure, and the only way out is a `--cut` that records counts that are wrong.
   - *Fix:* in §13, add "counted over every call the stage plans (all its items × judges), not only the writing run's; written on demand and after each collect".
   - Optional runner guard: refuse when a `stage_hold` line for the stage comes after the latest check line.
2. **The check accepts lines that do not show "zero for every judge"** (l.869–870). The filter `if v` treats `None` as zero, and an empty `{}` passes. A judge left out of the dict is not noticed.
   - *Fix:*
     ```python
     ok = isinstance(miss, dict) and miss and all(type(v) is int and v == 0 for v in miss.values())
     ```
     Then use `left = {k: v for k, v in miss.items() if v != 0}`, and add a test that `{}` and `{"j1": None}` are refused.
3. **Test gap.** Nothing tests the new rule that skips models with no prompts (§11 l.833), so a regression there would go unnoticed.
   - *Fix:* add an enabled direct model with no pilot whose subset is empty under `--outside` (for example `stage1_whole_subset`). Then check that the batch run gets past the pilot-ID check.

*Nits*
- Header l.21 says F10 "found two closure gaps". It found two major and three minor issues plus a nit, all fixed. Reword it.
- Old wording remains in the module docstring (l.42, "with nothing missing") and the `release_pending` docstring (l.690, "created no batch").

**Test run:** I followed your steps exactly. `E:\claude\_tmp\g11` is empty again, and the diff folder is unchanged, with no `__pycache__`. I opened nothing outside the two folders and made no network or model calls.
