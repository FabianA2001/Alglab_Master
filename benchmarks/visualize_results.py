#!/usr/bin/env python3
"""
Visualize benchmark results as graphs.

Reads JSON benchmark result files and creates plots showing solve times.

Usage:
    python -m benchmarks.visualize_results --input benchmarks/results_first/results_20251203_210153.json
    python -m benchmarks.visualize_results --input benchmarks/results_first/ --all  # All files in folder
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import numpy as np


def load_results(file_path: Path) -> list[dict]:
    """Load benchmark results from JSON file."""
    with open(file_path, "r") as f:
        return json.load(f)


def plot_solve_times(
    results: list[dict],
    title: str = "Solve Times by Instance",
    output_path: Optional[Path] = None,
):
    """Plot solve times for all instances."""
    instances = [r["name"] for r in results]
    times = [r["solve_time"] if r["solve_time"] is not None else 0 for r in results]
    statuses = [r["status"] for r in results]

    # Create color map based on status
    color_map = {
        "OPTIMAL": "#2ecc71",  # Green
        "FEASIBLE": "#3498db",  # Blue
        "INFEASIBLE": "#e74c3c",  # Red
        "UNKNOWN": "#f39c12",  # Orange
        "PARSE_ERROR": "#95a5a6",  # Gray
        "SOLVER_ERROR": "#c0392b",  # Dark Red
    }
    colors = [color_map.get(status, "#95a5a6") for status in statuses]

    fig, ax = plt.subplots(figsize=(14, 6))
    bars = ax.bar(
        range(len(instances)), times, color=colors, edgecolor="black", linewidth=0.5
    )

    ax.set_xlabel("Instance", fontsize=12, fontweight="bold")
    ax.set_ylabel("Solve Time (seconds)", fontsize=12, fontweight="bold")
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xticks(range(len(instances)))
    ax.set_xticklabels(instances, rotation=45, ha="right")

    # Add value labels on bars
    for i, (bar, time) in enumerate(zip(bars, times)):
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            height,
            f"{time:.2f}s",
            ha="center",
            va="bottom",
            fontsize=8,
        )

    # Add legend
    from matplotlib.patches import Patch

    legend_elements = [
        Patch(facecolor=color_map["OPTIMAL"], edgecolor="black", label="OPTIMAL"),
        Patch(facecolor=color_map["FEASIBLE"], edgecolor="black", label="FEASIBLE"),
        Patch(facecolor=color_map["INFEASIBLE"], edgecolor="black", label="INFEASIBLE"),
        Patch(facecolor=color_map["UNKNOWN"], edgecolor="black", label="UNKNOWN"),
        Patch(
            facecolor=color_map["PARSE_ERROR"], edgecolor="black", label="PARSE_ERROR"
        ),
        Patch(
            facecolor=color_map["SOLVER_ERROR"], edgecolor="black", label="SOLVER_ERROR"
        ),
    ]
    ax.legend(handles=legend_elements, loc="upper left", fontsize=10)

    plt.tight_layout()

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        print(f"✓ Graph saved to {output_path}")
    else:
        plt.show()

    plt.close()


def plot_solve_times_cumulative(
    results: list[dict],
    title: str = "Cumulative Solve Time",
    output_path: Optional[Path] = None,
):
    """Plot cumulative solve times."""
    instances = [r["name"] for r in results]
    times = [r["solve_time"] if r["solve_time"] is not None else 0 for r in results]

    cumulative_times = np.cumsum(times)

    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(
        range(len(instances)),
        cumulative_times,
        marker="o",
        linestyle="-",
        linewidth=2,
        markersize=6,
        color="#3498db",
    )
    ax.fill_between(range(len(instances)), cumulative_times, alpha=0.3, color="#3498db")

    ax.set_xlabel("Instance", fontsize=12, fontweight="bold")
    ax.set_ylabel("Cumulative Time (seconds)", fontsize=12, fontweight="bold")
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xticks(range(len(instances)))
    ax.set_xticklabels(instances, rotation=45, ha="right")
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        print(f"✓ Graph saved to {output_path}")
    else:
        plt.show()

    plt.close()


def plot_compare_instances(
    results_list: list[list[dict]],
    labels: list[str],
    title: str = "Compare Solve Times",
    output_dir: Optional[Path] = None,
    show: bool = False,
):
    """For each instance, plot solve times from multiple result sets side-by-side.

    results_list: list where each element is the loaded results (list of dicts) for one run.
    labels: labels for the runs (used in legend and filenames).
    """
    # Build a mapping: instance_name -> list of times per run (None if missing)
    instance_names = set()
    for res in results_list:
        instance_names.update([r["name"] for r in res])
    instance_names = sorted(instance_names)

    # For quick lookup, create dicts for each run
    lookups = []
    for res in results_list:
        d = {r["name"]: r for r in res}
        lookups.append(d)

    # Create output dir
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)

    for inst in instance_names:
        times = []
        statuses = []
        for d in lookups:
            entry = d.get(inst)
            if entry is None:
                times.append(None)
                statuses.append(None)
            else:
                times.append(entry.get("solve_time"))
                statuses.append(entry.get("status"))

        # Plot bars for this instance
        fig, ax = plt.subplots(figsize=(8, 4))
        x = np.arange(len(labels))
        bar_colors = []
        for s in statuses:
            if s is None:
                bar_colors.append("#95a5a6")
            elif s == "OPTIMAL":
                bar_colors.append("#2ecc71")
            elif s == "FEASIBLE":
                bar_colors.append("#3498db")
            elif s == "INFEASIBLE":
                bar_colors.append("#e74c3c")
            else:
                bar_colors.append("#f39c12")

        # Replace None with 0 for height, but mark them specially
        heights = [t if t is not None else 0 for t in times]
        bars = ax.bar(x, heights, color=bar_colors, edgecolor="black")

        # Annotate missing entries
        for idx, t in enumerate(times):
            if t is None:
                ax.text(
                    x[idx],
                    0,
                    "missing",
                    ha="center",
                    va="bottom",
                    fontsize=9,
                    color="#2c3e50",
                )
            else:
                ax.text(x[idx], t, f"{t:.2f}s", ha="center", va="bottom", fontsize=9)

        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=45, ha="right")
        ax.set_ylabel("Solve Time (seconds)")
        ax.set_title(f"{title} - {inst}")

        plt.tight_layout()

        if output_dir:
            safe_label = inst.replace("/", "_")
            out_path = output_dir / f"compare_{safe_label}.png"
            plt.savefig(out_path, dpi=300, bbox_inches="tight")
            print(f"✓ Saved comparison for {inst} -> {out_path}")
        else:
            plt.show()

        plt.close()


def plot_grouped_compare(
    results_list: list[list[dict]],
    labels: list[str],
    title: str = "Grouped Compare Solve Times",
    output_path: Optional[Path] = None,
    show: bool = False,
):
    """Create a single grouped bar plot: for each instance, show one bar per run.

    - results_list: list of loaded results (one list per run)
    - labels: run labels
    """
    # Collect union of instance names in stable order
    instance_names = set()
    for res in results_list:
        instance_names.update([r["name"] for r in res])
    instance_names = sorted(instance_names)

    # Build lookup dicts and aligned time arrays
    lookups = [{r["name"]: r for r in res} for res in results_list]
    n_runs = len(results_list)
    n_inst = len(instance_names)

    times = np.full((n_runs, n_inst), np.nan)
    for i, d in enumerate(lookups):
        for j, inst in enumerate(instance_names):
            entry = d.get(inst)
            if entry is not None and entry.get("solve_time") is not None:
                times[i, j] = entry.get("solve_time")

    # Plot grouped bars
    fig, ax = plt.subplots(figsize=(max(10, n_inst * 0.6), 6))
    x = np.arange(n_inst)
    total_width = 0.8
    if n_runs > 0:
        bar_width = total_width / n_runs
    else:
        bar_width = total_width

    # Choose colors (cycle if needed)
    base_colors = ["#2ecc71", "#3498db", "#e74c3c", "#9b59b6", "#f39c12"]
    colors = [base_colors[i % len(base_colors)] for i in range(n_runs)]

    for i in range(n_runs):
        offsets = x - (total_width - bar_width) / 2 + i * bar_width
        ax.bar(
            offsets,
            times[i],
            width=bar_width,
            label=labels[i],
            color=colors[i],
            edgecolor="black",
        )

        # Annotate
        for j in range(n_inst):
            val = times[i, j]
            if not np.isnan(val):
                ax.text(
                    offsets[j], val, f"{val:.1f}", ha="center", va="bottom", fontsize=8
                )

    ax.set_xticks(x)
    ax.set_xticklabels(instance_names, rotation=45, ha="right")
    ax.set_ylabel("Solve Time (seconds)")
    ax.set_title(title)
    ax.legend()
    ax.grid(axis="y", alpha=0.3)

    plt.tight_layout()

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        print(f"✓ Grouped comparison saved to {output_path}")
    else:
        plt.show()

    plt.close()


def main():
    repo_root = Path(__file__).resolve().parent.parent
    default_output = repo_root / "benchmarks" / "graphs"

    parser = argparse.ArgumentParser(
        description="Visualize benchmark results as graphs."
    )
    parser.add_argument(
        "--input",
        type=Path,
        help="Input JSON file or folder with JSON files",
    )
    parser.add_argument(
        "--inputs",
        nargs="+",
        type=Path,
        help="Multiple JSON files to compare (use instead of --input)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Process all files in folder (use with --input folder)",
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Compare multiple result files per instance (use with --inputs or --input folder + --all)",
    )
    parser.add_argument(
        "--grouped",
        action="store_true",
        help="Create a single grouped-bar plot comparing runs across instances",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=default_output,
        help="Output folder for graphs",
    )
    parser.add_argument(
        "--show", action="store_true", help="Show plots instead of saving"
    )
    args = parser.parse_args()

    # Determine input sources
    if not args.input and not args.inputs:
        print("Please specify --input (JSON file or folder) or --inputs <files>")
        return

    input_path = args.input

    # If multiple inputs provided explicitly, use them
    if args.inputs:
        files_to_process = args.inputs
    else:
        files_to_process = None

    # Single file processing
    if (
        input_path
        and input_path.is_file()
        and input_path.suffix == ".json"
        and not args.inputs
    ):
        # Single file
        print(f"Loading {input_path.name}...")
        results = load_results(input_path)

        base_name = input_path.stem

        if args.show:
            print(f"\nDisplaying graphs for {base_name}...")
            plot_solve_times(results, title=f"Solve Times - {base_name}")
            plot_solve_times_cumulative(
                results, title=f"Cumulative Solve Time - {base_name}"
            )
        else:
            output_dir = args.output / base_name
            output_dir.mkdir(parents=True, exist_ok=True)
            print(f"\nSaving graphs to {output_dir}...")
            plot_solve_times(
                results,
                title=f"Solve Times - {base_name}",
                output_path=output_dir / "01_solve_times.png",
            )
            plot_solve_times_cumulative(
                results,
                title=f"Cumulative Solve Time - {base_name}",
                output_path=output_dir / "02_cumulative.png",
            )
            # Optionally also create a single grouped plot
            if getattr(args, "grouped", False):
                out_file = output_dir / "grouped_compare.png"
                # wrap single results into list to match API
                plot_grouped_compare(
                    [results],
                    [base_name],
                    title="Grouped Compare",
                    output_path=out_file,
                    show=args.show,
                )

    else:
        # Either process all files in a folder, or do a compare across multiple files
        if files_to_process is None:
            if input_path and input_path.is_dir() and args.all:
                json_files = sorted(input_path.glob("*.json"))
                files_to_process = json_files
            else:
                print(
                    "Invalid input: specify a JSON file, use --inputs, or use --all with a folder"
                )
                return

        # If only one file provided in files_to_process, treat as single-file behavior
        if len(files_to_process) == 1 and not args.compare:
            json_file = files_to_process[0]
            print(f"\nProcessing {json_file.name}...")
            results = load_results(json_file)
            base_name = json_file.stem
            if args.show:
                plot_solve_times(results, title=f"Solve Times - {base_name}")
                plot_solve_times_cumulative(
                    results, title=f"Cumulative Solve Time - {base_name}"
                )
            else:
                output_dir = args.output / base_name
                output_dir.mkdir(parents=True, exist_ok=True)
                plot_solve_times(
                    results,
                    title=f"Solve Times - {base_name}",
                    output_path=output_dir / "01_solve_times.png",
                )
                plot_solve_times_cumulative(
                    results,
                    title=f"Cumulative Solve Time - {base_name}",
                    output_path=output_dir / "02_cumulative.png",
                )

        else:
            # Compare mode across multiple files
            files = list(files_to_process)
            print(f"Comparing {len(files)} files...")
            results_list = [load_results(f) for f in files]
            labels = [f.stem for f in files]

            # Build output directory name from labels. If too long, shorten
            joined = "_vs_".join(labels)
            if len(joined) > 80:
                import hashlib

                h = hashlib.sha1(joined.encode()).hexdigest()[:8]
                joined = joined[:40] + "_" + h

            out_dir = args.output / f"compare_{joined}"
            out_dir.mkdir(parents=True, exist_ok=True)

            plot_compare_instances(
                results_list,
                labels,
                title="Compare Solve Times",
                output_dir=out_dir,
                show=args.show,
            )
            if getattr(args, "grouped", False):
                out_file = out_dir / "grouped_compare.png"
                plot_grouped_compare(
                    results_list,
                    labels,
                    title="Grouped Compare",
                    output_path=out_file,
                    show=args.show,
                )


if __name__ == "__main__":
    main()
