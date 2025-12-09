Benchmark runner
================

This folder contains a small benchmark script to run the solver on all `.txt` instances in `data/instance_raw`.

Usage:

    python -m benchmarks.run_benchmark --timeout 60 --output benchmarks/results --save-solutions

Output:
 - JSON and CSV files with per-instance results (status, solve_time, objective_value, timestamp)

Notes:
 - The script uses `src.parseData.parseTXT` to load instances. Instances in other formats are not currently supported by the benchmark script.

Options and examples
--------------------

The benchmark runner supports a few additional command-line options to control output naming and saved solutions:

- `--output <PATH>`: target folder for the generated result files (default: `benchmarks/results`).
- `--out-name, -n <NAME>`: base filename for the JSON/CSV outputs. You can include the placeholder `{timestamp}` which will be replaced by a timestamp (format: `YYYYmmdd_HHMMSS`). If no extension is provided, `.json` will be appended to the output name.
- `--csv`: write an additional CSV file with the same base name as the JSON output.
- `--save-solutions`: save solution files for instances where a solution was found. Solution files are written to `OUTPUT_DIR/solutions/<InstanceName>.json`.
- `--limit N`: only process the first N instances (handy for quick tests).

Examples:

- Default behavior (JSON written to automatic results filename):

```
python -m benchmarks.run_benchmark --output benchmarks/results
```

- Custom output name with timestamp and CSV:

```
python -m benchmarks.run_benchmark --output benchmarks/results -n myrun_{timestamp}.json --csv
```

- Save solutions and run only first 5 instances:

```
python -m benchmarks.run_benchmark --output benchmarks/results --save-solutions --limit 5
```

Isolation mode
--------------

If you observe solver state leaks, memory growth, or other instability when running many instances in the same process, you can run each instance in a fresh Python interpreter using the `--isolate` flag. In this mode the main script spawns a separate Python process for every instance and calls itself with an internal `--single-instance <PATH>` flag. This guarantees a clean interpreter state per run.

Notes about the flags:

- `--isolate`: run each instance in a separate Python process. Useful when native solver bindings keep state or leak memory.
- `--single-instance <PATH>`: internal flag used by the isolate implementation; you don't need to call it manually. It's hidden from normal help output.

Example (isolated runs, CSV + save solutions):

```
python -m benchmarks.run_benchmark --output benchmarks/results --isolate -n myrun_{timestamp}.json --csv --save-solutions
```

Performance note: isolated mode is slower due to interpreter startup overhead, but it is the safest option when runs interfere with each other.
