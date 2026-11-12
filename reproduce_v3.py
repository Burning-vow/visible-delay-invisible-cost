"""Reproduce defect V3: the live indicator forgets delays at day's end.

Runs against the audited engine itself (standard library only). The engine is a
research prototype and is not redistributed here; point the script at a copy:

    set AEROTOWER_BACKEND=<path-to>/AeroTower/backend
    python reproduce_v3.py

The engine files the script executes are pinned by SHA-256 in REPRO_LOG.md.
"""

import os
import sys
import types

BACKEND = os.environ.get("AEROTOWER_BACKEND", "")
if not BACKEND or not os.path.isdir(BACKEND):
    raise SystemExit(
        "set AEROTOWER_BACKEND to the AeroTower backend directory, e.g.\n"
        "  set AEROTOWER_BACKEND=C:\\path\\to\\AeroTower\\backend\n"
        "The engine is not redistributed with this artifact; reproduce_v3.py has to\n"
        "import it. The recorded output of one run is in repro_stdout.txt."
    )

pkg = types.ModuleType("atb")
pkg.__path__ = [BACKEND]
sys.modules["atb"] = pkg
for sub in ("models", "services"):
    mod = types.ModuleType("atb." + sub)
    mod.__path__ = [os.path.join(BACKEND, sub)]
    sys.modules["atb." + sub] = mod

from atb.models.flight import Flight                          # noqa: E402
from atb.services.simulation_engine import SimulationEngine  # noqa: E402

# Two departures from one airport on 30 Nov 2020; the plan delays both.
flights = [
    Flight(101, "T1", "A320", "C8Y156", "ZUUU", "ZUCK",
           (2020, 11, 30, 8, 0), (2020, 11, 30, 9, 0), 60),
    Flight(102, "T2", "A320", "C8Y156", "ZUUU", "ZUCK",
           (2020, 11, 30, 9, 0), (2020, 11, 30, 10, 0), 60),
]
plan = {101: {"type": "delay", "delay_minutes": 45},
        102: {"type": "delay", "delay_minutes": 30}}
assigned = sum(int(v["delay_minutes"]) for v in plan.values())

engine = SimulationEngine()
engine.load_flights(flights)
DAY = 29 * 1440                        # 2020-11-30 00:00, in engine minutes
engine.sync_to(DAY + 7 * 60, plan)     # 07:00, before either departure
during = dict(engine.kpi)
engine.sync_to(DAY + 23 * 60 + 59, plan)   # 23:59, after both have departed
end = dict(engine.kpi)

print("assigned_release_delay_min =", assigned)
print("during day : punctuality_raw = %.1f  delayed_count = %d"
      % (during["punctuality"], during["delayed_count"]))
print("end of day : punctuality     = %.2f (%.1f per cent)  delayed_count = %d"
      % (end["punctuality"] / 100.0, end["punctuality"], end["delayed_count"]))

assert assigned > 0, "the disruption plan must assign delay"
assert during["delayed_count"] == 2, "both flights are late while the day runs"
assert end["punctuality"] == 100.0, "V3: the end-of-day indicator reads a perfect day"
print("V3 REPRODUCED")
