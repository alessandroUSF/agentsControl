"""Tables of Appendix A of protocol v2.3, built from the three simulation packages.

Reads analysis/output/sim_v23_rs1.json, sim_v23_rs2.json and sim_v23_rs3.json and prints Markdown tables; when
sim_v23_pilot_rs1.json exists (run (f) of Appendix A.4), also the table of Section 8.4 as a range over the pilot
planning grid.
Boundary cases (Section 8.1): a rejection rate counts a test that was not carried out as not rejected; coverage and
half-widths are over the replications that report an interval. Under each table a line gives the replications
with a zero denominator, a zero estimated variance or an iota_W that could not be estimated; "n/a" marks a value
that no replication provides.
Usage: python -I analysis/tables_v23.py            print
       python -I analysis/tables_v23.py --write    also write analysis/output/tables_v23.md
       python -I analysis/tables_v23.py --summary  print the figures that Sections 8.3 and 8.4 quote from table A.1
"""
import json
import sys
from pathlib import Path

from scipy import stats

OUT = Path(__file__).resolve().parent / "output"
LINES = []


# Approximate power table only (Section 8.3): the degrees of freedom when all 300 prompts of the harmful frame have a
# screen-positive answer, as in the baseline scenarios; the registered tests use the domain degrees of freedom.
APPROX_DF = 298

def emit(text=""):
    LINES.append(text)


def pp(x, d=1):
    return "n/a" if x is None or x != x else f"{100 * x:+.{d}f}"   # x != x: NaN (no replication)


def pct(x, d=1):
    return "n/a" if x is None or x != x else f"{100 * x:.{d}f}"


def boundary(rows):
    """One sentence on the boundary cases of Section 8.1 in a list of result rows (sim_v23_registered.py)."""
    parts = []
    for r in rows:
        b = r["summary"].get("boundary")
        if b is None:                           # a result file written before the boundary rules
            return "Boundary cases: not recorded in this result file."
        zv = {k: v for k, v in b["zero_variance"].items() if v}
        bits = []
        if b["zero_denominator"]:
            bits.append(f"zero denominator {b['zero_denominator']:,}")
        if zv:
            bits.append("zero variance " + ", ".join(f"{k.upper()} {v:,}" for k, v in zv.items()))
        if b["iw_not_estimable_with_io"]:
            judges = ", ".join(b["judges_without_control"])
            bits.append(f"ι_W not estimable with ι_S estimable {b['iw_not_estimable_with_io']:,} (judges {judges})")
        if bits:
            parts.append(f"{cell(r['name'])}: " + "; ".join(bits))
    if not parts:
        return ("Boundary cases: in no replication was a denominator zero, an estimated variance zero or ι_W "
                "not estimable.")
    return ("Boundary cases (replications; a test not carried out counts as not rejected): " + ". ".join(parts)
            + ".")


def load(name):
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def cell(name):
    """A name for a table cell. The result files join the two parts of a name with a vertical bar,
    which would split the cell in Markdown; the tables show a slash instead."""
    return name.replace("|", " / ")


def rs1():
    rows = {r["name"]: r for r in load("sim_v23_rs1.json")["rows"]}
    cases = []
    for name in rows:
        c = name.split("|")[0]
        if c not in cases:
            cases.append(c)
    r0 = rows["baseline|null"]
    emit(f"### A.1 Size and power of the registered tests (R-S1; {r0['reps']:,} replications per row)")
    emit()
    emit("| Scenario | Screen-positive answers | Family-wise error, null | P1 power, θ = −5 | P2 error, θ = −5 only "
         "| P2 power, ι = −5 | P1 error, ι = −5 only | P2 power, both −5 | P3 error at β = −7 | P3 power, β = 0 |")
    emit("|---|---|---|---|---|---|---|---|---|---|")
    for c in cases:
        s = {t: rows[f"{c}|{t}"]["summary"] for t in ("null", "theta", "iota", "both", "bound")}
        emit(f"| {c} | {s['null']['screened_answers_mean']:,.0f} | {pct(s['null']['registered']['any'])} "
             f"| {pct(s['theta']['registered']['holm_theta'])} | {pct(s['theta']['registered']['holm_iota'])} "
             f"| {pct(s['iota']['registered']['holm_iota'])} | {pct(s['iota']['registered']['holm_theta'])} "
             f"| {pct(s['both']['registered']['holm_iota'])} | {pct(s['bound']['p3_reject'])} "
             f"| {pct(s['null']['p3_reject'])} |")
    emit()
    emit("Rates in percent; effects in percentage points. Nominal levels: family-wise 4.0, P3 1.0.")
    emit()
    emit(boundary(rows.values()))
    emit()
    emit("| Scenario | Coverage of the 95% interval: θ_S | ι_S | ι_W | β_S | Half-width: θ_S | ι_S | β_S "
         "| Same decision as the sign-flip test: P1 | P2 |")
    emit("|---|---|---|---|---|---|---|---|---|---|")
    for c in cases:
        s = rows[f"{c}|null"]["summary"]
        emit(f"| {c} | {pct(s['th']['cover95'])} | {pct(s['io']['cover95'])} | {pct(s['iw']['cover95'])} "
             f"| {pct(s['be']['cover95'])} | {pct(s['th']['half_width95'])} | {pct(s['io']['half_width95'])} "
             f"| {pct(s['be']['half_width95'])} | {pct(s['signflip']['same_decision_theta'])} "
             f"| {pct(s['signflip']['same_decision_iota'])} |")
    emit()
    emit("Null rows. Half-widths in percentage points.")
    emit()
    emit("**Approximate power of the bound P3 for other margins.** Normal approximation with the simulated "
         "standard error of β̂_S and the 99% quantile of Student's t with 298 degrees of freedom (all 300 prompts with "
         "a screen-positive answer; with fewer, the domain degrees of freedom of Section 8.1 are fewer and the "
         "quantile slightly larger); not a simulation of the test.")
    emit()
    emit("| Scenario | Standard error of β̂_S | Margin 3: β = 0 | β = −1 | Margin 5: β = 0 | β = −1 | β = −2 "
         "| Margin 7: β = 0 | β = −1 | β = −2 | β = −3 |")
    emit("|---|---|---|---|---|---|---|---|---|---|---|")
    z = stats.t.ppf(0.99, APPROX_DF)       # a table of approximations only; the tests use the domain df (Section 8.1)
    for c in cases:
        se = rows[f"{c}|null"]["summary"]["be"]["mean_se"]
        cells = [pct(stats.norm.cdf((m + b) / se - z), 0)
                 for m, bs in ((0.03, (0, -0.01)), (0.05, (0, -0.01, -0.02)), (0.07, (0, -0.01, -0.02, -0.03)))
                 for b in bs]
        emit(f"| {c} | {pct(se, 2)} | " + " | ".join(cells) + " |")
    emit()


def rs2():
    rows = load("sim_v23_rs2.json")["rows"]
    emit(f"### A.2 Heterogeneous judges and delivery failures (R-S2; {rows[0]['reps']:,} replications per row)")
    emit()
    emit("| Scenario | True θ_S | True ι_S | True ι_W | P1 rejected | P2 rejected | P2 rejected and ι_W interval "
         "excludes zero on the same side | Coverage: θ_S | ι_S | ι_W |")
    emit("|---|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        s, ref = r["summary"], r["reference"]
        emit(f"| {cell(r['name'])} | {pp(ref['th'][0], 2)} | {pp(ref['io'][0], 2)} | {pp(ref['iw'][0], 2)} "
             f"| {pct(s['registered']['holm_theta'])} | {pct(s['registered']['holm_iota'])} "
             f"| {pct(s['p2_and_within']['either'])} | {pct(s['th']['cover95'])} | {pct(s['io']['cover95'])} "
             f"| {pct(s['iw']['cover95'])} |")
    emit()
    emit("True values in percentage points, from about one million independent prompt clusters. After the slash, "
         "`zero`: the three calibrated arm shifts are zero, and the judge shifts and invalid verdicts of the "
         "scenario still act; `null`: arm shifts calibrated so that θ_S = ι_S = 0; `both`: θ_S = ι_S = −5 points.")
    emit()
    emit(boundary(rows))
    emit()


RS3_RATES = ("harm_share_pos", "harm_share_neg", "screen_pass_harm", "det_blind_own", "det_blind_ctrl",
             "fa_blind_own", "fa_blind_ctrl")
RS3_STATS = (
    "harm_share_pos|all", "harm_share_neg|all", "screen_pass_harm|all",
    "det_blind_own|all", "det_blind_ctrl|all", "fa_blind_own|all", "fa_blind_ctrl|all",
    "det_change_own_reg|all", "det_change_diff_reg|all", "det_change_own_reg|r", "det_change_diff_reg|r",
    "det_change_own_reg|i", "fa_change_own_reg|all", "fa_change_diff_reg|all",
    "det_change_own|all", "fa_change_own|all")


def rs3():
    """Every interval that Sections 7.4 and 9.5 report, and two direct estimators as a check."""
    data = load("sim_v23_rs3.json")
    reps = sorted({r["reps"] for r in data.values()})
    emit(f"### A.3 Label-conditioned estimators (R-S3; {', '.join(f'{x:,}' for x in reps)} replications per scenario)")
    emit()
    emit("| Scenario | Statistic | Interval | True value | Bias | Replications with an interval | Coverage of the "
         "95% interval | Half-width | Labelled answers in the class (mean; minimum) | Events (mean): positive; "
         "negative | Zero variance | Coverage of the replaced ratio interval |")
    emit("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for name, r in data.items():
        for k in RS3_STATS:
            s = r["stats"].get(k)
            if not s:
                continue
            stat = k.split("|")[0]
            kind = "eff-n" if stat in RS3_RATES else "ratio"
            use = s.get("exact") if kind == "eff-n" else s
            head = f"| {cell(name)} | `{cell(k)}` | {kind} | {pp(s['reference'], 2)} "
            sup = f"{s['support']:.0f}; {s['support_min']:.0f}"
            if not use or use.get("cover95") is None or not use["reportable"]:
                emit(head + f"| n/a | 0 | n/a | n/a | {sup} | n/a | n/a | n/a |")
                continue
            ev = (f"{s['events_pos']:.1f}; {s['support'] - s['events_pos']:.1f}" if kind == "eff-n"
                  else f"{s['events_pos']:.1f}; {s['events_neg']:.1f}")
            old = pct(s["cover95"]) if kind == "eff-n" and s.get("cover95") is not None else "–"
            emit(head + f"| {pp(s['bias'], 2)} | {use['reportable']:,} | {pct(use['cover95'])} "
                 f"| {pct(use['half_width95'])} | {sup} | {ev} | {s['zero_variance']:,} | {old} |")
    emit()

    def span(key):
        lo = min(r["counts"][key]["min"] for r in data.values())
        hi = max(r["counts"][key]["max"] for r in data.values())
        return f"{lo:.0f}" if lo == hi else f"{lo:.0f} to {hi:.0f}"

    emit(f"All {len(data)} scenarios, every replication: labelled answers {span('labelled')}, second labels "
         f"{span('second_labels')}, challenge set {span('h60')}, API reference subset {span('api_ref')}, "
         f"unfilled quota {span('unfilled')}, answers with no chance of selection {span('uncovered_answers')}. "
         "Values in percentage points.")
    emit()
    emit("- **Interval.** `eff-n`: the approximate interval on the effective number of answers (Section 9.5). `ratio`: the "
         "cluster ratio interval of Section 8.")
    emit("- **Replications with an interval.** The class holds at least 20 labelled answers. For a ratio interval "
         "the estimated variance is also above zero. Bias and coverage are computed over these replications.")
    emit("- **Events.** For a rate: labelled answers of the class with the property and without it. For a change: "
         "labelled answers of the class that gain a flag in context and that lose one. For a difference between "
         "authors and controls the sign is that of the difference.")
    emit("- **Zero variance.** Replications with at least 20 labelled answers in the class in which the estimated "
         "variance of the ratio is zero.")
    emit("- **Last column.** The coverage of the cluster ratio interval for the same rate. This interval is not "
         "reported. It has no width when no event, or nothing but events, is observed.")
    emit()


def pilot_power(name="sim_v23_pilot_rs1.json"):
    """The table of Section 8.4 over the pilot planning grid (run (f) of Appendix A.4): each value is the range
    over the grid points of R-S1 rows computed by sim_v23_registered.py --grid pilot_rs1. Printed only when that
    result file exists."""
    if not (OUT / name).exists():
        return
    data = load(name)
    rows = {r["name"]: r for r in data["rows"]}
    points = sorted({n.split("|")[0] for n in rows})

    def rng(row, f, d=1):
        v = [f(rows[f"{p}|{row}"]["summary"]) for p in points if f"{p}|{row}" in rows]
        v = [x for x in v if x is not None]
        if not v:
            return "n/a"
        lo, hi = pct(min(v), d), pct(max(v), d)
        return lo if lo == hi else f"{lo} to {hi}"

    reps = sorted({r["reps"] for r in rows.values()})
    emit(f"### Section 8.4 over the pilot planning grid (run (f); {', '.join(f'{x:,}' for x in reps)} replications "
         "per row)")
    emit()
    emit("| Property | Range over the grid |")
    emit("|---|---|")
    emit(f"| Family-wise error of P1 and P2, no effect | {rng('null', lambda s: s['registered']['any'])} |")
    emit(f"| Error of P3 at β_S = −7 points | {rng('bound', lambda s: s['p3_reject'])} |")
    cover = " / ".join(rng("null", lambda s, k=k: s[k]["cover95"]) for k in ("th", "io", "iw", "be"))
    emit(f"| Coverage of the 95% intervals of θ_S / ι_S / ι_W / β_S, no effect | {cover} |")
    emit(f"| Power of P1 for θ_S = −5 points | {rng('theta', lambda s: s['registered']['holm_theta'])} |")
    emit(f"| Power of P2 for ι_S = −5 points | {rng('iota', lambda s: s['registered']['holm_iota'])} |")
    emit(f"| Power of P3 at β_S = 0 | {rng('null', lambda s: s['p3_reject'])} |")
    half = " / ".join(rng("null", lambda s, k=k: s[k]["half_width95"]) for k in ("th", "io", "be"))
    emit(f"| Half-width of the 95% interval: θ_S / ι_S / β_S (points) | {half} |")
    emit()
    marked = sorted({n.split("|")[0] for n, r in rows.items() if r["scenario"].get("target_not_reproduced")})
    emit("Grid points: " + ", ".join(points) + ". Rates in percent. "
         + ("Target not reproduced (analysis/pilot_planning_v23.py lists the cases): " + ", ".join(marked) + "."
            if marked else "Every pilot target was reproduced."))
    emit()
    emit(boundary(rows.values()))
    emit()


def summary():
    """The figures that Sections 8.3 and 8.4 quote, from the rows of R-S1 (the same numbers as table A.1)."""
    rows = {r["name"]: r for r in load("sim_v23_rs1.json")["rows"]}
    cases = list(dict.fromkeys(n.split("|")[0] for n in rows))

    def rng(vals, d=1):
        vals = [v for v in vals if v is not None]
        return f"{pct(min(vals), d)}% to {pct(max(vals), d)}%"

    z = stats.t.ppf(0.99, APPROX_DF)
    for c in ("baseline", "low_failure"):
        se = rows[f"{c}|null"]["summary"]["be"]["mean_se"]
        cells = {m: [pct(stats.norm.cdf((m + b) / se - z), 0) for b in bs]
                 for m, bs in ((0.03, (0, -0.01)), (0.05, (0, -0.01, -0.02)), (0.07, (0, -0.01, -0.02, -0.03)))}
        print(f"8.3 approximate power, {c} (standard error of beta {pct(se, 2)} points): {cells}")
    nulls = [rows[f"{c}|null"]["summary"] for c in cases]
    print("8.4 family-wise error, null:", rng(s["registered"]["any"] for s in nulls))
    print("8.4 error of P3 at beta = -7:", rng(rows[f"{c}|bound"]["summary"]["p3_reject"] for c in cases))
    print("8.4 coverage, null rows:", rng(s[k]["cover95"] for s in nulls for k in ("th", "io", "iw", "be")))
    print("8.4 coverage, all rows:", rng(r["summary"][k]["cover95"] for r in rows.values() for k in ("th", "io", "iw", "be")))
    print("8.4 power of P1, theta = -5:", rng(rows[f"{c}|theta"]["summary"]["registered"]["holm_theta"] for c in cases))
    print("8.4 power of P2, iota = -5:", rng(rows[f"{c}|iota"]["summary"]["registered"]["holm_iota"] for c in cases))
    for k in ("th", "io", "be"):
        v = [s[k]["half_width95"] for s in nulls]
        print(f"8.4 half-width {k}: {pct(min(v))} to {pct(max(v))} points")


if __name__ == "__main__":
    if "--summary" in sys.argv:
        sys.stdout.reconfigure(encoding="utf-8")
        summary()
        sys.exit(0)
    rs1()
    rs2()
    rs3()
    pilot_power()
    text = "\n".join(LINES)
    sys.stdout.reconfigure(encoding="utf-8")
    print(text)
    if "--write" in sys.argv:
        (OUT / "tables_v23.md").write_text(text + "\n", encoding="utf-8", newline="\n")
