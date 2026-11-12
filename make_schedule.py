"""Export the weekly plan used in "Visible Delay, Invisible Cost" to schedule.csv.

There is no random generator and no seed. The plan is read row for row from an
airline timetable export and written out unchanged except for column selection
and ordering.

    python make_schedule.py --verify     # check the shipped CSV (stdlib only)
    python make_schedule.py --rebuild    # re-export from the source workbook

--verify needs nothing beyond the standard library. --rebuild needs the source
workbook (set AEROTOWER_XLSX) and pandas + openpyxl.
"""

import argparse
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "schedule.csv")
MANIFEST = os.path.join(HERE, "manifest.json")
SRC = os.environ.get("AEROTOWER_XLSX", "")
SHEET = "Sheet1"
FMT = "%d/%m/%Y %H:%M:%S"
FIELDS = ["flight_id", "rotation_id", "seq_in_rotation", "origin", "dest",
          "sched_dep", "sched_arr", "ac_type", "block_min", "turn_min"]


def build():
    import pandas as pd

    if not SRC or not os.path.exists(SRC):
        raise SystemExit(
            "rebuild needs the source workbook: set AEROTOWER_XLSX to the .xlsx path.\n"
            "To check the shipped CSV instead, run: python make_schedule.py --verify"
        )
    df = pd.read_excel(SRC, sheet_name=SHEET, header=1)
    d = pd.DataFrame({
        "flight_id": df["FLIGHT_ID"].astype("int64"),
        "rotation_id": df["AC_LINK_LINE"].astype(str).str.strip(),
        "origin": df["DEPARTURE_AIRPORT"].astype(str).str.strip(),
        "dest": df["ARRIVAL_AIRPORT"].astype(str).str.strip(),
        "ac_type": df["AC_TYPE"].astype(str).str.strip(),
        "dep": pd.to_datetime(df["STD"], format=FMT, errors="raise"),
        "arr": pd.to_datetime(df["STA"], format=FMT, errors="raise"),
    })
    d = d.sort_values(["rotation_id", "dep", "flight_id"], kind="mergesort").reset_index(drop=True)
    d["seq_in_rotation"] = d.groupby("rotation_id").cumcount()
    d["block_min"] = ((d["arr"] - d["dep"]).dt.total_seconds() / 60).round().astype(int)
    prev_arr = d.groupby("rotation_id")["arr"].shift(1)
    turn = (d["dep"] - prev_arr).dt.total_seconds() / 60
    d["turn_min"] = turn.round().astype("Int64")
    d["sched_dep"] = d["dep"].dt.strftime("%Y-%m-%d %H:%M")
    d["sched_arr"] = d["arr"].dt.strftime("%Y-%m-%d %H:%M")
    return d[FIELDS]


def stats_of(df, digest):
    import pandas as pd  # noqa: F401  (only for quantile)

    turns = df["turn_min"].dropna()
    return {
        "rows": int(len(df)),
        "rotations": int(df["rotation_id"].nunique()),
        "airports": int(len(set(df["origin"]) | set(df["dest"]))),
        "ac_types": sorted(df["ac_type"].unique().tolist()),
        "consecutive_pairs": int(len(turns)),
        "turn_p5": float(turns.quantile(0.05)),
        "turn_median": float(turns.quantile(0.50)),
        "turn_p90": float(turns.quantile(0.90)),
        "sha256": digest,
        "seed": None,
        "source": "weekly airline timetable export, not redistributed",
    }


def verify():
    import csv

    if not os.path.exists(MANIFEST) or not os.path.exists(OUT):
        print("need both schedule.csv and manifest.json", file=sys.stderr)
        return 2
    ref = json.load(open(MANIFEST, encoding="utf-8"))
    raw = open(OUT, "rb").read()
    digest = hashlib.sha256(raw).hexdigest()
    rows = list(csv.DictReader(open(OUT, encoding="utf-8")))
    turns = [float(r["turn_min"]) for r in rows if r["turn_min"]]
    turns.sort()

    def q(p):
        return turns[int(p * (len(turns) - 1))]

    checks = {
        "rows": ref["rows"] == len(rows),
        "rotations": ref["rotations"] == len({r["rotation_id"] for r in rows}),
        "airports": ref["airports"] == len({r["origin"] for r in rows} | {r["dest"] for r in rows}),
        "ac_types": ref["ac_types"] == sorted({r["ac_type"] for r in rows}),
        "consecutive_pairs": ref["consecutive_pairs"] == len(turns),
        "turn_p5": abs(ref["turn_p5"] - q(0.05)) < 1e-9,
        "turn_median": abs(ref["turn_median"] - q(0.50)) < 1e-9,
        "turn_p90": abs(ref["turn_p90"] - q(0.90)) < 1e-9,
        "sha256": ref["sha256"] == digest,
    }
    print("VERIFY", json.dumps(checks))
    return 0 if all(checks.values()) else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true", help="check the shipped CSV (stdlib only)")
    ap.add_argument("--rebuild", action="store_true", help="re-export from AEROTOWER_XLSX")
    args = ap.parse_args()

    if args.verify:
        return verify()
    if not args.rebuild:
        ap.print_help()
        return 2

    df = build()
    text = df.to_csv(index=False, lineterminator="\n")
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    stats = stats_of(df, digest)
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    with open(OUT, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)
    json.dump(stats, open(MANIFEST, "w", encoding="utf-8"), indent=2)
    print("wrote", OUT, "and", MANIFEST)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
