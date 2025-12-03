#!/usr/bin/env python3
"""
Simple benchmark runner for instances in data/instance_raw.

Iterates all `.txt` instance files, runs the solver for each, records:
 - instance name / filename
 - solver status (OPTIMAL / FEASIBLE / INFEASIBLE / UNKNOWN / MODEL_INVALID)
 - solve_time (seconds)
 - objective_value (if available)
 - timestamp

Outputs a JSON and CSV file into the output folder (default: `benchmarks/results`).

Usage:
    python -m benchmarks.run_benchmark --timeout 60 --output benchmarks/results --save-solutions

"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
import time

from src.parseData import parseTXT
from src.shift_vars import Shift_vars
from src.solver import Solver
from ortools.sat.python import cp_model


STATUS_MAP: dict[int, str] = {
    cp_model.OPTIMAL: "OPTIMAL",
    cp_model.FEASIBLE: "FEASIBLE",
    cp_model.INFEASIBLE: "INFEASIBLE",
    cp_model.UNKNOWN: "UNKNOWN",
    cp_model.MODEL_INVALID: "MODEL_INVALID",
}


def find_txt_instances(data_folder: Path) -> list[Path]:
    def natural_sort_key(path: Path):
        import re

        parts = re.split(r"(\d+)", path.name)
        return [int(part) if part.isdigit() else part for part in parts]

    files = sorted(data_folder.iterdir(), key=natural_sort_key)
    return [f for f in files if f.suffix == ".txt"]


def run_benchmark(
    instance_dir: Path,
    output_dir: Path,
    timeout: float = 60.0,
    save_solutions: bool = False,
    limit: int | None = None,
):
    output_dir.mkdir(parents=True, exist_ok=True)
    results = []

    instance_files = find_txt_instances(instance_dir)
    if limit is not None:
        instance_files = instance_files[:limit]
    for inst_file in instance_files:
        print(f"Running instance: {inst_file.name}")
        try:
            instance = parseTXT.parse_txt(inst_file)
        except Exception as e:
            print(f"Failed to parse {inst_file.name}: {e}")
            results.append(
                {
                    "file": str(inst_file),
                    "name": inst_file.stem,
                    "status": "PARSE_ERROR",
                    "solve_time": None,
                    "objective_value": None,
                    "timestamp": datetime.now().isoformat(),
                    "error": str(e),
                }
            )
            continue

        vars = Shift_vars(instance)
        solver = Solver(instance, vars)

        start = time.time()
        try:
            # sol = solver.solve(
            #     max_time_in_seconds=timeout, log_search_progress=False, automaton=False
            # )
            sol = solver.warm_start_greedy(
                max_time_in_seconds=timeout, instance=instance
            )
            # HIER
            # sol = solver.warm_start_greedy2(
            #     max_time_in_seconds=timeout, instance=instance
            # )
        except Exception as e:
            elapsed = time.time() - start
            print(f"Solver error on {inst_file.name}: {e}")
            results.append(
                {
                    "file": str(inst_file),
                    "name": inst_file.stem,
                    "status": "SOLVER_ERROR",
                    "solve_time": elapsed,
                    "objective_value": None,
                    "timestamp": datetime.now().isoformat(),
                    "error": str(e),
                }
            )
            continue

        elapsed = (
            solver.solve_time
            if hasattr(solver, "solve_time")
            else (time.time() - start)
        )

        if sol.solve_status in STATUS_MAP:
            status_readable = STATUS_MAP[sol.solve_status]
        else:
            status_readable = str(sol.solve_status)

        result = {
            "file": str(inst_file),
            "name": inst_file.stem,
            "status": status_readable,
            "is_success": sol.solve_status in [cp_model.OPTIMAL, cp_model.FEASIBLE],
            "solve_time": elapsed,
            "objective_value": getattr(sol, "objective_value", None),
            "timestamp": datetime.now().isoformat(),
        }

        # Optionally save the solution
        if save_solutions and sol.solve_status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            try:
                out_name = f"{inst_file.stem}.json"
                sol.to_json_file(out_name)
                result["solution_file"] = out_name
            except Exception as e:
                result["solution_file_error"] = str(e)

        results.append(result)

    # Write JSON
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = output_dir / f"results_{timestamp}.json"
    with open(json_path, "w") as jf:
        json.dump(results, jf, indent=2)
    # Optionally write CSV (disabled by default). Use --csv to enable.
    write_csv = getattr(run_benchmark, "write_csv", False)
    if write_csv:
        csv_path = output_dir / f"results_{timestamp}.csv"
        with open(csv_path, "w", newline="") as cf:
            writer = csv.writer(cf)
            header = [
                "file",
                "name",
                "status",
                "is_success",
                "solve_time",
                "objective_value",
                "timestamp",
            ]
            writer.writerow(header)
            for r in results:
                writer.writerow(
                    [
                        r.get("file"),
                        r.get("name"),
                        r.get("status"),
                        r.get("is_success"),
                        r.get("solve_time"),
                        r.get("objective_value"),
                        r.get("timestamp"),
                    ]
                )
        print(f"Wrote results to {json_path} and {csv_path}")
    else:
        print(f"Wrote results to {json_path}")


def main():
    repo_root = Path(__file__).resolve().parent.parent
    default_data = repo_root / "data" / "instance_raw"
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=default_data)
    parser.add_argument("--output", type=Path, default=Path("benchmarks/results"))
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--save-solutions", action="store_true")
    parser.add_argument(
        "--limit", type=int, default=None, help="Limit to first N instances"
    )
    parser.add_argument(
        "--csv", action="store_true", help="Also write CSV (disabled by default)"
    )
    args = parser.parse_args()

    # Control CSV writing via a flag; JSON is written by default.
    run_benchmark.write_csv = args.csv

    run_benchmark(
        args.data_dir,
        args.output,
        timeout=args.timeout,
        save_solutions=args.save_solutions,
        limit=args.limit,
    )


if __name__ == "__main__":
    main()
