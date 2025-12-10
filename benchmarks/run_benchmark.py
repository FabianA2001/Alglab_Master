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
import subprocess
import sys


STATUS_MAP: dict[int, str] = {
    cp_model.OPTIMAL: "OPTIMAL",
    cp_model.FEASIBLE: "FEASIBLE",
    cp_model.INFEASIBLE: "INFEASIBLE",
    cp_model.UNKNOWN: "UNKNOWN",
    cp_model.MODEL_INVALID: "MODEL_INVALID",
}


def find_txt_instances(data_folder: Path, start_number: int = 10) -> list[Path]:
    def natural_sort_key(path: Path):
        import re

        parts = re.split(r"(\d+)", path.name)
        return [int(part) if part.isdigit() else part for part in parts]

    files = sorted(data_folder.iterdir(), key=natural_sort_key)
    txt_files = [f for f in files if f.suffix == ".txt"]

    # Filtere Instances die kleiner als start_number sind
    filtered_files = []
    for f in txt_files:
        import re

        match = re.search(r"\d+", f.stem)
        if match:
            num = int(match.group())
            if num >= start_number:
                filtered_files.append(f)

    return filtered_files


def run_benchmark(
    instance_dir: Path,
    output_dir: Path,
    timeout: float = 60.0,
    save_solutions: bool = False,
    limit: int | None = None,
    out_name: str | None = None,
    single_instance: Path | None = None,
    start_number: int = 10,
):
    output_dir.mkdir(parents=True, exist_ok=True)
    results = []

    instance_files = find_txt_instances(instance_dir, start_number=start_number)
    if single_instance is not None:
        instance_files = [single_instance]
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
            sol = solver.solve_with_early_stop(
                max_time_in_seconds=timeout, log_search_progress=False, automaton=False
            )
            # sol = solver.warm_start_greedy(
            #     max_time_in_seconds=timeout, instance=instance
            # )
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
                sols_dir = output_dir / "solutions"
                sols_dir.mkdir(parents=True, exist_ok=True)
                out_path = sols_dir / f"{inst_file.stem}.json"
                # solver's to_json_file may accept a path string
                sol.to_json_file(str(out_path))
                result["solution_file"] = str(out_path)
            except Exception as e:
                result["solution_file_error"] = str(e)

        results.append(result)

    # Write JSON/CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # If caller provided a base output name, allow '{timestamp}' formatting.
    if out_name:
        formatted = out_name.format(timestamp=timestamp)
        out_path = Path(formatted)
        # ensure .json suffix if none provided
        if out_path.suffix == "":
            out_path = out_path.with_suffix(".json")
        json_path = output_dir / out_path.name
        csv_path = output_dir / out_path.with_suffix(".csv").name
    else:
        json_path = output_dir / f"results_{timestamp}.json"
        csv_path = output_dir / f"results_{timestamp}.csv"

    with open(json_path, "w") as jf:
        json.dump(results, jf, indent=2)
    # Optionally write CSV (disabled by default). Use --csv to enable.
    write_csv = getattr(run_benchmark, "write_csv", False)
    if write_csv:
        # csv_path already computed above if out_name was present
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
    parser.add_argument(
        "--out-name",
        "-n",
        type=str,
        default=None,
        help="Base filename for JSON/CSV outputs. Use '{timestamp}' to include timestamp. Example: myrun_{timestamp}.json",
    )
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--save-solutions", action="store_true")
    parser.add_argument(
        "--limit", type=int, default=None, help="Limit to first N instances"
    )
    parser.add_argument(
        "--start-instance",
        type=int,
        default=10,
        help="Start from instance number (default: 10)",
    )
    parser.add_argument(
        "--csv", action="store_true", help="Also write CSV (disabled by default)"
    )
    parser.add_argument(
        "--isolate",
        action="store_true",
        help="Run each instance in a separate Python process (isolated).",
    )
    parser.add_argument(
        "--single-instance",
        type=Path,
        default=None,
        help=argparse.SUPPRESS,
    )
    args = parser.parse_args()

    # Control CSV writing via a flag; JSON is written by default.
    run_benchmark.write_csv = args.csv

    # If isolate mode requested, spawn a fresh Python process for each instance.
    if args.isolate and args.single_instance is None:
        instances = find_txt_instances(args.data_dir, start_number=args.start_instance)
        if args.limit is not None:
            instances = instances[: args.limit]
        for inst in instances:
            cmd = [
                sys.executable,
                "-m",
                "benchmarks.run_benchmark",
                "--single-instance",
                str(inst),
                "--output",
                str(args.output),
                "--timeout",
                str(args.timeout),
            ]
            if args.out_name:
                cmd += ["--out-name", args.out_name]
            if args.csv:
                cmd.append("--csv")
            if args.save_solutions:
                cmd.append("--save-solutions")
            print(f"Launching isolated process: {' '.join(cmd)}")
            try:
                subprocess.run(cmd, check=True)
            except subprocess.CalledProcessError as e:
                print(f"Instance {inst} failed with return code {e.returncode}")
        return

    # If called as single-instance (internal), only process that file
    if args.single_instance is not None:
        run_benchmark(
            args.data_dir,
            args.output,
            timeout=args.timeout,
            save_solutions=args.save_solutions,
            limit=args.limit,
            out_name=args.out_name,
            single_instance=args.single_instance,
            start_number=args.start_instance,
        )
        return

    # Default: run multiple instances in-process
    run_benchmark(
        args.data_dir,
        args.output,
        timeout=args.timeout,
        save_solutions=args.save_solutions,
        limit=args.limit,
        out_name=args.out_name,
        start_number=args.start_instance,
    )


if __name__ == "__main__":
    main()
