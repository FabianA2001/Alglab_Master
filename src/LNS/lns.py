import logging
from time import time

from ortools.sat.python import cp_model

from .. import solution, solver

logger = logging.getLogger(__name__)


class LNS:
    def __init__(self, sol: solution.Solution):
        self.search_window_size: int = 3  # days
        self.timeout_seconds: int = 180
        self.small_runtime_seconds: int = 20
        self.old_solution = sol
        logger.info(
            f"LNS initialized with search_window_size={self.search_window_size}, "
            f"timeout_seconds={self.timeout_seconds}, small_runtime_seconds={self.small_runtime_seconds}"
        )
        logger.debug(f"Initial solution objective value: {sol.objective_value}")

    def choose_search_window(self) -> tuple[int, int]:
        """Wählt ein Suchfenster basierend auf der alten Lösung aus."""
        import random

        total_days = self.old_solution.instance.number_of_days
        logger.debug(f"Total days in instance: {total_days}")

        if total_days <= self.search_window_size:
            logger.debug(
                f"Total days ({total_days}) <= search_window_size ({self.search_window_size}), using full range"
            )
            return 0, total_days - 1

        start_day = random.randint(0, total_days - self.search_window_size)
        end_day = start_day + self.search_window_size - 1
        logger.debug(f"Selected search window: days {start_day} to {end_day}")
        return start_day, end_day

    def fix_outside_window(
        self, start_day: int, end_day: int, solver_instance: solver.Solver
    ):
        """Fixiert die Zuweisungen außerhalb des Suchfensters in der Solver-Instanz."""

        for day in range(solver_instance.instance.number_of_days):
            if day < start_day or day > end_day:
                for shift_type_uid in solver_instance.instance.shift_types:
                    for emp_id in solver_instance.instance.employees:
                        assigned = self.old_solution.is_employee_assigned(
                            day, shift_type_uid, emp_id
                        )
                        var = solver_instance.vars.vars[(day, shift_type_uid, emp_id)]
                        if assigned:
                            solver_instance.vars.model.Add(var == 1)
                        else:
                            solver_instance.vars.model.Add(var == 0)

    def solve(self) -> solution.Solution:
        logger.info("Starting LNS solve process")
        start_time = time.now()
        iteration = 0
        improvements = 0

        while time.now() - start_time < self.timeout_seconds:
            iteration += 1
            elapsed_time = time.now() - start_time
            logger.debug(
                f"Iteration {iteration} started (elapsed: {elapsed_time:.2f}s)"
            )

            start_day, end_day = self.choose_search_window()
            assert end_day > start_day

            logger.debug("Creating new solver instance")
            solv = solver.Solver(
                self.old_solution.instance,
                solver.shift_vars.Shift_vars(self.old_solution.instance),
            )

            self.fix_outside_window(start_day, end_day, solv)

            logger.debug(f"Solving with max_time={self.small_runtime_seconds}s")
            solv = solv.solve(
                log_search_progress=False,
                disabled_constraints=self.old_solution.disabled_constraints,
                max_time_in_seconds=self.small_runtime_seconds,
            )

            if not (
                solv.solve_status == cp_model.OPTIMAL
                or solv.solve_status == cp_model.FEASIBLE
            ):
                logger.debug(
                    f"Iteration {iteration}: No feasible solution found (status: {solv.solve_status})"
                )
                continue

            logger.debug(
                f"Iteration {iteration}: Found solution with objective {solv.objective_value}"
            )

            if solv.objective_value < self.old_solution.objective_value:
                improvements += 1
                improvement = self.old_solution.objective_value - solv.objective_value
                logger.info(
                    f"Iteration {iteration}: Found improvement! "
                    f"Old objective: {self.old_solution.objective_value}, "
                    f"New objective: {solv.objective_value}, "
                    f"Improvement: {improvement}"
                )
                self.old_solution = solv
            else:
                logger.debug(
                    f"Iteration {iteration}: No improvement (current best: {self.old_solution.objective_value})"
                )

        total_time = time.now() - start_time
        logger.info(
            f"LNS completed: {iteration} iterations, {improvements} improvements, "
            f"total time: {total_time:.2f}s, final objective: {self.old_solution.objective_value}"
        )

        assert (
            self.old_solution.solve_status == cp_model.OPTIMAL
            or self.old_solution.solve_status == cp_model.FEASIBLE
        )
        return self.old_solution
