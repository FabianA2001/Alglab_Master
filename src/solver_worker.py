#!/usr/bin/env python3
"""
Worker module for solving sub-instances in separate processes.

This module is used by warm_start_half_instance to solve quarters in isolated processes
to prevent CP-SAT performance degradation from repeated solving.

Usage (called by subprocess):
    python -m src.solver_worker --instance <pkl_file> --output <pkl_file> --timeout <seconds> [--hints <pkl_file>]
"""

import argparse
import pickle
import sys

from ortools.sat.python import cp_model

from src.shift_vars import Shift_vars
from src.solver import Solver


def main():
    parser = argparse.ArgumentParser(
        description="Solve a sub-instance in an isolated process"
    )
    parser.add_argument(
        "--instance", type=str, required=True, help="Path to pickled Instance"
    )
    parser.add_argument(
        "--output", type=str, required=True, help="Path to save pickled Solution"
    )
    parser.add_argument(
        "--timeout", type=float, default=60.0, help="Timeout in seconds"
    )
    parser.add_argument(
        "--hints",
        type=str,
        default=None,
        help="Path to pickled hints data (quarter_solutions, quarter_instances)",
    )

    args = parser.parse_args()

    try:
        # Load the instance from pickle
        with open(args.instance, "rb") as f:
            instance = pickle.load(f)

        # Create variables and solver
        vars_obj = Shift_vars(instance)
        solver = Solver(instance, vars_obj)

        # If hints are provided, add them to the model
        if args.hints:
            try:
                with open(args.hints, "rb") as f:
                    quarter_solutions, quarter_instances = pickle.load(f)

                # Add hints from each quarter solution
                for sol, sub_inst in zip(quarter_solutions, quarter_instances):
                    if sol is None or sol.solve_status not in [
                        cp_model.OPTIMAL,
                        cp_model.FEASIBLE,
                    ]:
                        continue

                    for day in range(instance.number_of_days):
                        for type_uid in instance.shifts[day]:
                            for emp_uid in sub_inst.employees:
                                key = (day, type_uid, emp_uid)
                                if key in sol.vars:
                                    value = sol.vars[key] == 1
                                    try:
                                        vars_obj.model.AddHint(
                                            vars_obj.get_var(day, type_uid, emp_uid),
                                            value,
                                        )
                                    except Exception:
                                        pass  # Silently skip hints that fail
            except Exception as e:
                print(f"Warning: Failed to load/apply hints: {e}", file=sys.stderr)

        # Solve the instance
        solution = solver.solve(
            max_time_in_seconds=args.timeout,
            stop_after_first_solution=True,
            log_search_progress=False,
        )

        # Save the solution to pickle
        with open(args.output, "wb") as f:
            pickle.dump(solution, f)

        sys.exit(0)

    except Exception as e:
        print(f"Error in solver_worker: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
