import logging
import time

from ortools.sat.python import cp_model

from .. import solution, solver
from ..inputTypes import instace


class StopAfterMinTimeAndFirstSolution(cp_model.CpSolverSolutionCallback):
    def __init__(self, min_runtime_sec):
        super().__init__()
        self.min_runtime_sec = min_runtime_sec
        self.start = time.time()
        self.solution_found_after_min_time = False

    def on_solution_callback(self):
        now = time.time()
        if now - self.start >= self.min_runtime_sec:
            # Sobald die Mindestzeit erreicht ist und eine Lösung existiert → Solver stoppen
            print("Stopping: min time reached and a solution is available.")
            self.StopSearch()


class LNS:
    MIN_SMALL_SEARCH_TIME: float = 2.0  # sec

    def __init__(
        self,
        sol_or_instance: solution.Solution | instace.Instance,
        disabled_constraints=None,
        percent_search_time_first_solution: float = 0.1,
        timeout_seconds: float = 180,
        small_runtime_base: float = 0.01,  # * number_of_days * (number_of_shift_types + number_of_employees)
        start_search_window_size: int = 7,
        search_window_size_min: int = 3,
        window_increase_factor: float = 1.3,
        window_decrease_factor: float = 0.7,
        strong_improvement_threshold: float = 0.01,
        logger=logging.getLogger(__name__),
        log_level: int = logging.DEBUG,
    ):
        self.logger = logger
        self.logger.setLevel(log_level)

        # get first Solution
        assert percent_search_time_first_solution < 1.0, (
            "search_time_first_solution must be < 1.0"
        )
        assert percent_search_time_first_solution > 0.0, (
            "search_time_first_solution must be > 0.0"
        )
        self.old_solution, create_time_first_solution = (
            self.__parse_solution_or_instance(
                sol_or_instance,
                timeout_seconds * percent_search_time_first_solution,
                timeout_seconds,
            )
        )
        self.NUMBER_OF_SHIFT_TYPES = len(self.old_solution.instance.shift_types)
        self.NUMBER_OF_EMPLOYEES = len(self.old_solution.instance.employees)

        # window change size parameters
        self.window_increase_factor = window_increase_factor
        self.window_decrease_factor = window_decrease_factor
        self.strong_improvement_threshold = strong_improvement_threshold

        self.MIN_DAY: int = 0
        self.start_day: int = self.MIN_DAY
        self.MAX_DAY: int = self.old_solution.instance.number_of_days - 1
        self.end_day: int = self.MAX_DAY
        self.start_search_window_size: int = start_search_window_size
        self.search_window_size_min = search_window_size_min

        # time parameters
        self.timeout_seconds: float = timeout_seconds
        self.small_runtime_milliseconds_base: float = small_runtime_base
        self.timeout_seconds: float = max(
            0.0, timeout_seconds - create_time_first_solution
        )

        # disabled constraints
        self.disabled_constraints = (
            disabled_constraints
            if disabled_constraints is not None
            else self.old_solution.disabled_constraints
        )

        # logging info
        self.logger.info(
            f"LNS initialized with search_window_size={self.start_search_window_size}, "
            f"timeout_seconds={self.timeout_seconds}, small_runtime_seconds_base={self.small_runtime_milliseconds_base}"
        )
        self.logger.debug(
            f"Initial solution objective value: {self.old_solution.objective_value}"
        )

    @staticmethod
    def __parse_solution_or_instance(
        sol_or_instance: solution.Solution | instace.Instance,
        min_runtime_sec: float,
        timeout_seconds: float,
    ) -> tuple[solution.Solution, float]:
        if isinstance(sol_or_instance, solution.Solution):
            return sol_or_instance, 0.0
        elif isinstance(sol_or_instance, instace.Instance):
            start_time = time.time()
            vars = solver.shift_vars.Shift_vars(sol_or_instance)
            solv = solver.Solver(sol_or_instance, vars)
            callback = StopAfterMinTimeAndFirstSolution(min_runtime_sec)
            initial_solution = solv.solve(
                log_search_progress=False,
                max_time_in_seconds=timeout_seconds,
                callback=callback,
            )
            assert (
                initial_solution.solve_status == cp_model.OPTIMAL
                or initial_solution.solve_status == cp_model.FEASIBLE
            )
            return initial_solution, time.time() - start_time
        else:
            raise ValueError("Input must be a Solution or an Instance")

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

    def update_search_window(self, improvement: float):
        """
        Passt die Größe des Suchfensters basierend auf der Verbesserung an.
        Verschiebt start_day und end_day unter Beachtung der min/max Grenzen.

        Args:
            improvement: Die Verbesserung des Objective-Werts (positiv wenn besser)
        """

        def __calculate_new_window_size():
            old_window_size = self.end_day - self.start_day
            new_window_size = old_window_size

            if improvement > 0:
                # Starke Verbesserung? -> Fenster verkleinern
                relative_improvement = (
                    improvement / self.old_solution.objective_value
                    if self.old_solution.objective_value > 0
                    else 0
                )

                if relative_improvement >= self.strong_improvement_threshold:
                    new_window_size = max(
                        self.search_window_size_min,
                        int(old_window_size * self.window_decrease_factor),
                    )
                    self.logger.debug(
                        f"Strong improvement ({relative_improvement:.2%}): "
                        f"Decreasing window size from {old_window_size} to {new_window_size}"
                    )
            else:
                # Keine Verbesserung -> Fenster vergrößern
                new_window_size = min(
                    self.MAX_DAY, int(old_window_size * self.window_increase_factor)
                )
                self.logger.debug(
                    f"No improvement: Increasing window size from {old_window_size} to {new_window_size}"
                )
            return new_window_size

        import random

        new_window_size = __calculate_new_window_size()

        # Fenster verschieben/anpassen
        max_possible_window = self.MAX_DAY - self.MIN_DAY
        new_window_size = min(new_window_size, max_possible_window)

        current_window_size = self.end_day - self.start_day
        if new_window_size < current_window_size:
            # Fenster verkleinern
            reduction = current_window_size - new_window_size
            shift_start = random.randint(0, reduction)
            self.start_day += shift_start
            self.end_day = self.start_day + new_window_size
        elif new_window_size > current_window_size:
            # Fenster vergrößern
            increase = new_window_size - current_window_size
            shift_start = random.randint(0, increase)
            self.start_day = max(
                self.MIN_DAY, self.start_day - (increase - shift_start)
            )
            self.end_day = min(self.MAX_DAY, self.start_day + new_window_size)
        # else: Fenster bleibt gleich groß

        assert self.end_day - self.start_day >= self.search_window_size_min
        assert self.start_day >= self.MIN_DAY
        assert self.end_day <= self.MAX_DAY

    def solve(self) -> solution.Solution:
        self.logger.info("Starting LNS solve process")
        start_time = time.time()
        iteration = 0
        improvements = 0

        while time.time() - start_time < self.timeout_seconds:
            assert self.end_day > self.start_day
            iteration += 1
            elapsed_time = time.time() - start_time
            small_max_solve_time = max(
                self.MIN_SMALL_SEARCH_TIME,
                self.small_runtime_milliseconds_base
                * (self.end_day - self.start_day)
                * (self.NUMBER_OF_SHIFT_TYPES + self.NUMBER_OF_EMPLOYEES),
            )
            self.logger.debug(
                f"Iteration {iteration}({elapsed_time:.2f}): Solving with small max solve time: {small_max_solve_time:.2f}s "
                f"for window days {self.start_day} to {self.end_day}"
            )

            solv = solver.Solver(
                self.old_solution.instance,
                solver.shift_vars.Shift_vars(self.old_solution.instance),
            )

            self.fix_outside_window(self.start_day, self.end_day, solv)

            solv = solv.solve(
                log_search_progress=False,
                disabled_constraints=self.disabled_constraints,
                max_time_in_seconds=small_max_solve_time,
            )

            if not (
                solv.solve_status == cp_model.OPTIMAL
                or solv.solve_status == cp_model.FEASIBLE
            ):
                self.logger.debug(
                    f"Iteration {iteration}: No feasible solution found (status: {solv.solve_status})"
                )

                continue

            self.logger.debug(
                f"Iteration {iteration}: Found solution with objective {solv.objective_value}"
            )

            improvement = 0
            if solv.objective_value < self.old_solution.objective_value:
                improvements += 1
                improvement = self.old_solution.objective_value - solv.objective_value
                self.logger.info(
                    f"Iteration {iteration}: Found improvement! "
                    f"Old objective: {self.old_solution.objective_value}, "
                    f"New objective: {solv.objective_value}, "
                    f"Improvement: {improvement}"
                )
                self.old_solution = solv
            else:
                self.logger.debug(
                    f"Iteration {iteration}: No improvement (current best: {self.old_solution.objective_value})"
                )

            self.update_search_window(improvement)
            print("-" * 80)

        total_time = time.time() - start_time
        self.logger.info(
            f"LNS completed: {iteration} iterations, {improvements} improvements, "
            f"total time: {total_time:.2f}s, final objective: {self.old_solution.objective_value}"
        )

        assert (
            self.old_solution.solve_status == cp_model.OPTIMAL
            or self.old_solution.solve_status == cp_model.FEASIBLE
        )
        return self.old_solution
