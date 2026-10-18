#!/bin/bash
set -euo pipefail
OUT=$1
VTUNE=/share/intel/oneapi-2023.1/vtune/2023.1.0/bin64/vtune
for name in pp2048 tg128_d2048; do
    case_dir="$OUT/$name"
    for ((i=0;i<1200;i++)); do
        [[ -s "$case_dir/threads.csv" ]] && break
        sleep 5
    done
    "$VTUNE" -report hotspots -r "$case_dir/vtune" -group-by cpuid -format csv -csv-delimiter comma -limit 80 -report-output "$case_dir/cpus.csv"
    "$VTUNE" -report hotspots -r "$case_dir/vtune" -group-by function,callstack -format csv -csv-delimiter comma -limit 40 -report-output "$case_dir/callstacks.csv"
done
date -Is > "$OUT/extra_reports.ready"
