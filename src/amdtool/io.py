"""Reading extracted CSVs.

`load_extracted` is copied verbatim from python/seep_detect.py, including its
de-duplication key, so every analysis that reads extraction files through
amdtool sees exactly the rows the committed reports were computed from.
"""

import csv
import os

_TEXT_COLUMNS = ("region", "sensor", "tier", "pid", "name", "site_type", "season")


def load_extracted(paths):
    """Load extracted CSVs, DEDUPED on (sensor, radius, tier, pid).

    The C3b amendment was extracted in a separate pass that also re-extracted
    the targets (a control tier is meaningless without something to compare it
    to), so target rows appear in two files. Without deduping they would be
    counted twice, inflating n+ and every statistic built on it.

    Load extracted CSVs, DEDUPED on (sensor, radius, tier, region, pid,
    k_bare, clay_bare).
    """
    rows = []
    seen = set()
    for p in paths:
        if not os.path.isfile(p):
            continue
        with open(p, encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                # k_bare/clay_bare MUST be in the key. Without them the B2b
                # sweep's 8 grid points - same pid, same tier, same radius,
                # different thresholds - collapse onto the first one, and the
                # verdict gets computed from 1/8 of the data. Observed
                # 2026-08-16: reported FAILURE off a single grid point before
                # the CSV was checked against the analysis output.
                key = (r.get("sensor"), r.get("radius"), r.get("tier"),
                       r.get("region"), r.get("pid"),
                       r.get("k_bare"), r.get("clay_bare"))
                if key in seen:
                    continue
                seen.add(key)
                for k, v in list(r.items()):
                    if k in _TEXT_COLUMNS:
                        continue
                    r[k] = float(v) if v not in ("", None, "None") else float("nan")
                rows.append(r)
    return rows
