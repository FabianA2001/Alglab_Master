Benchmark runner
================

This folder contains a small benchmark script to run the solver on all `.txt` instances in `data/instance_raw`.

Usage:

    python -m benchmarks.run_benchmark --timeout 60 --output benchmarks/results --save-solutions

Output:
 - JSON and CSV files with per-instance results (status, solve_time, objective_value, timestamp)

Notes:
 - The script uses `src.parseData.parseTXT` to load instances. Instances in other formats are not currently supported by the benchmark script.
