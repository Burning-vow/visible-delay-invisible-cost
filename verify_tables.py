#!/usr/bin/env python3
"""Check every aggregate the paper reports against the per-scenario tables.

Standard library only. `scenarios.csv` is the output of the metering and search
pipeline; this script does not re-simulate anything. It lets a reader recompute the
five medians in Fig. 3, the minute totals in Section VI-A and the flight counts of
Section VI-A without running the engine.

    python verify_tables.py

Exits non-zero if any check fails.
"""
import csv
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RATES = ["unmetered", "1.00x", "0.75x", "0.60x", "0.45x"]
PAPER_MEDIAN = {"unmetered": 1.35, "1.00x": 1.50, "0.75x": 1.79, "0.60x": 1.96, "0.45x": 2.22}

fails = []


def check(name, got, want, tol, fmt="%.4f"):
    ok = abs(got - want) <= tol
    print(("PASS " if ok else "FAIL ") + name.ljust(34) + fmt % got + "  (paper " + fmt % want + ")")
    if not ok:
        fails.append(name)


rows = list(csv.DictReader(open(os.path.join(HERE, "scenarios.csv"), encoding="utf-8")))
check("scenario rows", len(rows), 100, 0, "%d")

by_rate = {r: [] for r in RATES}
for row in rows:
    by_rate[row["rate"]].append(row)

# the ratio column must be T / L, so a corrupted table cannot pass
for row in rows:
    want = float(row["T"]) / float(row["L"])
    if abs(want - float(row["ratio"])) > 2e-6:
        fails.append("ratio column at %s %s %s" % (row["airport"], row["day"], row["rate"]))
print("PASS ratio column equals T/L on all %d rows" % len(rows))

print("\n-- five medians (Section VI-B, Fig. 3)")
for rate in RATES:
    vals = [float(r["ratio"]) for r in by_rate[rate]]
    check("median %-9s" % rate, statistics.median(vals), PAPER_MEDIAN[rate], 0.006)

print("\n-- minute ledger (Section VI-A, two headline rates)")
head = [r for r in rows if r["rate"] in ("0.60x", "0.45x")]
sum_t = sum(float(r["T"]) for r in head)
sum_l = sum(float(r["L"]) for r in head)
check("sum T (minutes)", sum_t, 82723, 1.0, "%.1f")
check("sum L (minutes)", sum_l, 38740, 0.5, "%.1f")
check("remainder", sum_t - sum_l, 43983, 1.0, "%.1f")
check("share outside (per cent)", 100 * (sum_t - sum_l) / sum_t, 53.2, 0.06, "%.2f")

print("\n-- flight counts")
check("affected scenario-flights", sum(int(r["n_affected"]) for r in head), 2113, 0, "%d")
check("mean in-window flights", sum(int(r["n_window"]) for r in head) / len(head), 24.7, 0.05, "%.2f")

print()
if fails:
    print("FAILED: %d check(s): %s" % (len(fails), ", ".join(fails)))
    sys.exit(1)
print("ALL CHECKS PASSED")
