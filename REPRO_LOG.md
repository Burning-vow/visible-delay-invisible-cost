# REPRO_LOG.md — defect V3, reproduced against the engine

Artifact: `reproduce_v3.py` (standard library only). Raw run output: `repro_stdout.txt`.

## Version identification

The AeroTower tree carries no version-control metadata (`git` was not used), so the version is
pinned by content hashes and file dates. The three files the script executes:

| file | SHA-256 | mtime |
|---|---|---|
| `backend/services/simulation_engine.py` | `2b6db8d7865cfcab5087534404528c2565b78be44ca84bee64924f4e46c308e1` | 2026-09-28T14:05:12 |
| `backend/models/flight_state.py` | `39b1985370b515dd73174f4a4982fa58d72cb99525edd7400b4cdfd575975585` | 2026-09-28T14:05:12 |
| `backend/models/flight.py` | `118e24b165998df56ca01de185a0d0b75721ed6868cc22d9accb1da88a0e6175` | 2026-09-28T14:05:12 |

Interpreter: CPython 3.13.5. No third-party packages are imported by the script or by the modules
above.

## Command

```
set AEROTOWER_BACKEND=<path-to>/AeroTower/backend
python reproduce_v3.py
```

## Output (pasted from the run, not typed)

```
assigned_release_delay_min = 75
during day : punctuality_raw = 0.0  delayed_count = 2
end of day : punctuality     = 1.00 (100.0 per cent)  delayed_count = 0
V3 REPRODUCED
```

## What the mechanism is

`sync_to` first clears `delay_minutes` (line 278 of `simulation_engine.py`) and then re-applies the
plan only while `minutes < fs.dep_minutes` (line 285). The punctuality KPI is
`(total - delay_count) / total` (line 591). Once the clock passes a flight's scheduled departure, its
assigned delay stops counting, so the end-of-day indicator can read 100 % on a day that carried
assigned delay.

## Scope

This reproduces V3 only. The engine itself and the source timetable export are not redistributed
here; see `README.md` for what the artifact does and does not ship.
