import logging
import time

from ortools.sat.python import cp_model

from .. import solution, solver
from ..inputTypes import instace

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class LNS:
    def __init__(
        self,
        sol_or_instance: solution.Solution | instace.Instance,
        timeout_seconds: float = 180,
        small_runtime_seconds: int = 20,
        search_window_size: int = 7,
    ):
        self.search_window_size: int = search_window_size  # days
        self.timeout_seconds: float = timeout_seconds
        self.small_runtime_seconds: int = small_runtime_seconds

        self.old_solution, create_time_first_solution = (
            self.__parse_solution_or_instance(sol_or_instance, timeout_seconds)
        )
        self.timeout_seconds: float = max(
            0.0, timeout_seconds - create_time_first_solution
        )

        logger.info(
            f"LNS initialized with search_window_size={self.search_window_size}, "
            f"timeout_seconds={self.timeout_seconds}, small_runtime_seconds={self.small_runtime_seconds}"
        )
        logger.debug(
            f"Initial solution objective value: {self.old_solution.objective_value}"
        )

    @staticmethod
    def __parse_solution_or_instance(
        sol_or_instance: solution.Solution | instace.Instance,
        timeout_seconds: float,
    ) -> tuple[solution.Solution, float]:
        if isinstance(sol_or_instance, solution.Solution):
            return sol_or_instance, 0.0
        elif isinstance(sol_or_instance, instace.Instance):
            start_time = time.time()
            vars = solver.shift_vars.Shift_vars(sol_or_instance)
            solv = solver.Solver(sol_or_instance, vars)
            initial_solution = solv.solve(
                log_search_progress=False,
                max_time_in_seconds=timeout_seconds,
                stop_after_first_solution=True,
            )
            assert (
                initial_solution.solve_status == cp_model.OPTIMAL
                or initial_solution.solve_status == cp_model.FEASIBLE
            )
            return initial_solution, time.time() - start_time
        else:
            raise ValueError("Input must be a Solution or an Instance")

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
        start_time = time.time()
        iteration = 0
        improvements = 0

        while time.time() - start_time < self.timeout_seconds:
            iteration += 1
            elapsed_time = time.time() - start_time
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

        total_time = time.time() - start_time
        logger.info(
            f"LNS completed: {iteration} iterations, {improvements} improvements, "
            f"total time: {total_time:.2f}s, final objective: {self.old_solution.objective_value}"
        )

        assert (
            self.old_solution.solve_status == cp_model.OPTIMAL
            or self.old_solution.solve_status == cp_model.FEASIBLE
        )
        return self.old_solution
