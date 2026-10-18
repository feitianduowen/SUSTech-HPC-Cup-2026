"""Summarize diagnostic CSV timings without treating them as model throughput."""

import argparse
import csv
import json
import statistics
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path", type=Path)
    args = parser.parse_args()
    timings = {}
    correctness = []
    with args.csv_path.open(encoding="utf-8") as stream:
        for row in csv.reader(stream):
            if row and row[0] == "timing" and row[1] in ("resident", "stream"):
                timings.setdefault((row[1], row[3]), []).append(float(row[6]))
            elif row and row[0] == "correctness" and row[1] != "name":
                correctness.append(dict(zip(["name", "cases", "bit_mismatches", "non_finite", "max_abs_vs_baseline", "max_rel_vs_baseline", "rms_vs_baseline", "max_abs_vs_double"], row[1:])))
    results = []
    for (mode, name), values in sorted(timings.items()):
        baseline = timings[(mode, "baseline")]
        median = statistics.median(values)
        results.append({"mode": mode, "name": name, "rounds": len(values), "ns_per_dot_median": median, "ns_per_dot_min": min(values), "ns_per_dot_max": max(values), "speedup_vs_baseline_median": statistics.median(baseline) / median})
    print(json.dumps({"correctness": correctness, "diagnostic_timings": results}, indent=2))


if __name__ == "__main__":
    main()
