# Visible Delay, Invisible Cost — artifact

Companion artifact for *Visible Delay, Invisible Cost: Auditing Cost Attribution in Collaborative
Departure Metering* (submitted to CSCWD 2027).

This repository holds the weekly plan the paper measures on, the script that verifies it, and a
minimal reproducer for defect **V3** — the one that lets the audited system report a perfectly
punctual day.

## What is here

| File | What it is |
|---|---|
| `schedule.csv` | The weekly plan used in the paper: 4,415 flights, 165 rotations, 105 airports, five aircraft types, 30 Nov – 6 Dec 2020. |
| `manifest.json` | Counts and the SHA-256 of `schedule.csv`. |
| `make_schedule.py` | Rebuilds `schedule.csv` from the source export, or verifies the shipped file against the manifest without any third-party package. |
| `reproduce_v3.py` | Runs the audited engine and shows V3: assigned delay stays positive, the end-of-day punctuality indicator reads 100 %. |
| `scenarios.csv` | One row per scenario and release rate: 20 peak blocks × 5 rates. `T` is the created cost in delay-minutes, `L` the cost the system books, `ratio` their quotient, `n_window` and `n_affected` the two flight sets the ledgers cover. |
| `verify_tables.py` | Recomputes the five medians of Fig. 3, the minute totals of Section VI-A and the flight counts from `scenarios.csv`. Standard library only. |
| `repro_stdout.txt` | The raw output of one real run of `reproduce_v3.py`. |
| `REPRO_LOG.md` | Version pinning, engine hashes, and the commands that produced the output. |

## Verified counts

| Quantity | Value |
|---|---|
| Flights | 4,415 |
| Rotations (`AC_LINK_LINE`) | 165 |
| Airports | 105 |
| Aircraft types | A319, A320, A321, A330, A350 |
| Consecutive pairs in a rotation | 4,250 |
| Turn blocks, 5th / 50th / 90th percentile (min) | 45 / 75 / 550 |
| `schedule.csv` SHA-256 | see `manifest.json` |

Verify without installing anything:

```
python make_schedule.py --verify
```

This needs only the standard library. It checks the on-disk hash and the six counts against
`manifest.json`, and exits non-zero on any mismatch.

## Checking the five medians

```
python verify_tables.py
```

Standard library only. It recomputes, from `scenarios.csv`, the five medians plotted in Fig. 3, the
minute totals of Section VI-A and the two flight counts, and exits non-zero on any mismatch. The
table is the output of the metering and search pipeline, so the script checks every aggregate the
paper reports from it; it does not re-simulate the runs.

## Reproducing V3

`reproduce_v3.py` imports the audited engine, which is a research prototype and **is not
redistributed here**. Point it at a copy of the engine backend:

```
set AEROTOWER_BACKEND=<path-to>/AeroTower/backend
python reproduce_v3.py
```

Expected output (recorded in `repro_stdout.txt`):

```
assigned_release_delay_min = 75
during day : punctuality_raw = 0.0  delayed_count = 2
end of day : punctuality     = 1.00 (100.0 per cent)  delayed_count = 0
V3 REPRODUCED
```

The engine files the script executes are pinned by SHA-256 in `REPRO_LOG.md`, so a different build
can be told apart from the one this output came from.

## What is not here

- **The engine.** `AeroTower` is a group prototype; the reproducer is shipped, the system is not.
- **The source timetable export.** `schedule.csv` is derived from it and carries the fields the paper
  uses; aircraft identifiers and carrier codes were dropped. The export itself is not redistributed.
  Rebuilding the CSV from scratch therefore needs that export; verifying the shipped CSV does not.

## Provenance and licence

Planned times come from a weekly airline timetable export; actual times in that export are empty, so
every disruption and every metering rate in the paper is simulated. Code (`make_schedule.py`,
`reproduce_v3.py`) is MIT-licensed. `schedule.csv` and `manifest.json` are released under CC BY 4.0
with the authors' permission; the upstream export is not redistributed.
