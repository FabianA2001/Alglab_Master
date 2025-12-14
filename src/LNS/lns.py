import logging
import random
import time

from ortools.sat.python import cp_model

from .. import solution, solver
from ..inputTypes import instace
from . import slice_instance


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


# TODO disabled_constraints erlauben
class LNS:
    MIN_SMALL_SEARCH_TIME: float = 2.0  # sec

    def __init__(
        self,
        sol_or_instance: solution.Solution | instace.Instance,
        percent_search_time_first_solution: float = 0.1,
        timeout_seconds: float = 180,
        small_runtime_base: float = 0.01,  # * number_of_days * (number_of_shift_types + number_of_employees)
        ####################
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
        self.MAX_DAY: int = self.old_solution.instance.number_of_days - 1
        self.start_search_window_size: int = start_search_window_size
        self.search_window_size_min = search_window_size_min
        self.start_day: int = random.randint(
            self.MIN_DAY,
            max(
                self.MIN_DAY,
                self.MAX_DAY - self.start_search_window_size,
            ),
        )
        self.end_day: int = self.start_day + self.start_search_window_size

        # time parameters
        self.timeout_seconds: float = timeout_seconds
        self.small_runtime_milliseconds_base: float = small_runtime_base
        self.timeout_seconds: float = max(
            0.0, timeout_seconds - create_time_first_solution
        )
        self.disabled_for_window = []
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
                    self.MAX_DAY,
                    round(old_window_size * self.window_increase_factor),
                )
                self.logger.debug(
                    f"No improvement: Increasing window size from {old_window_size} to {new_window_size}"
                )
            return new_window_size

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

    def merge_solutions(self, new_solution: solution.Solution) -> solution.Solution:
        """
        Integriert die neue Lösung aus dem Suchfenster in die alte Gesamtlösung.

        Args:
            new_solution: Die neue Lösung aus dem Suchfenster

        Returns:
            Eine neue Solution-Instanz mit den integrierten Änderungen
        """
        # Erstelle eine Kopie der alten Lösung
        import copy

        updated_solution = copy.deepcopy(self.old_solution)

        updated_solution.disabled_constraints = new_solution.disabled_constraints

        # Iteriere über alle Tage im erweiterten Fenster
        for window_day in range(self.end_day - self.start_day + 1):
            original_day = self.start_day + window_day

            # Kopiere alle Shift-Zuweisungen für diesen Tag
            for shift_type_uid in updated_solution.instance.shift_types:
                for emp_uid in updated_solution.instance.employees:
                    # Hole den Wert aus der neuen Lösung
                    new_value = new_solution.vars[(window_day, shift_type_uid, emp_uid)]
                    # Setze den Wert in der kopierten Lösung
                    updated_solution.set_var(
                        original_day, shift_type_uid, emp_uid, new_value
                    )
            # Kopiere Weekend-Variablen falls der Tag ein Wochenendtag ist
            if original_day in updated_solution.instance.weekend_days:
                for emp_uid in updated_solution.instance.employees:
                    new_weekend_value = new_solution.weekend_vars.get(
                        (window_day, emp_uid), 0
                    )
                    updated_solution.set_weekend_var(
                        original_day, emp_uid, new_weekend_value
                    )

            # Kopiere above/below preferred Variablen
            for shift_type_uid in updated_solution.instance.shift_types:
                new_above = new_solution.above_prefferd_vars.get(
                    (window_day, shift_type_uid), 0
                )
                new_below = new_solution.below_prefferd_vars.get(
                    (window_day, shift_type_uid), 0
                )
                updated_solution.set_above_prefferd_var(
                    original_day, shift_type_uid, new_above
                )
                updated_solution.set_below_prefferd_var(
                    original_day, shift_type_uid, new_below
                )

        # Berechne den neuen objective value der gesamten Lösung
        objective_value = self._calculate_objective_value(updated_solution)
        updated_solution.set_objective_value(objective_value)
        updated_solution.disabled_constraints = self.disabled_for_window

        return updated_solution

    def _calculate_objective_value(self, sol: solution.Solution) -> float:
        """
        Berechnet den objective value einer Lösung basierend auf den Zuweisungen.
        """
        objective_value = 0.0

        # Penalty für Mitarbeiter-Zuweisungen
        for employee_uid in sol.instance.employees:
            for day in range(sol.instance.number_of_days):
                for type_uid in sol.instance.shifts[day]:
                    is_assigned = sol.vars.get((day, type_uid, employee_uid), 0)

                    # Penalty wenn NICHT zugewiesen (aber gewünscht)
                    objective_value += sol.instance.get_shift(
                        day=day, type_uid=type_uid
                    ).penalty_assigned_day_employee.get(employee_uid, 0) * (
                        1 - is_assigned
                    )

                    # Penalty wenn zugewiesen (aber nicht gewünscht)
                    objective_value += (
                        sol.instance.get_shift(
                            day=day, type_uid=type_uid
                        ).penalty_not_assigned_day_employee.get(employee_uid, 0)
                        * is_assigned
                    )

        # Penalty für above/below preferred
        for day in range(sol.instance.number_of_days):
            for type_uid in sol.instance.shifts[day]:
                below = sol.below_prefferd_vars.get((day, type_uid), 0)
                above = sol.above_prefferd_vars.get((day, type_uid), 0)

                objective_value += (
                    below * sol.instance.shifts[day][type_uid].weight_below_preferred
                )
                objective_value += (
                    above * sol.instance.shifts[day][type_uid].weight_above_preferred
                )

        return objective_value

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

            solvr = slice_instance.Slice_instance(
                sol=self.old_solution,
                start=self.start_day,
                end=self.end_day,
            ).get_solver()

            sol = solvr.solve_window(
                log_search_progress=False,
                max_time_in_seconds=small_max_solve_time,
            )

            if not (
                sol.solve_status == cp_model.OPTIMAL
                or sol.solve_status == cp_model.FEASIBLE
            ):
                self.logger.debug(
                    f"Iteration {iteration}: No feasible solution found (status: {sol.solve_status})"
                )
                self.old_solution.to_json_file(
                    f"error_lns_infeasible_start_{self.start_day}_end_{self.end_day}.json"
                )
                continue
            old_sol_debugg = sol.model_copy()
            sol = self.merge_solutions(sol)
            if not sol.checkt_constraints[0]:
                self.old_solution.to_json_file(
                    f"error_lns_merge_old_start_{self.start_day}_end_{self.end_day}.json"
                )
                old_sol_debugg.to_json_file(
                    f"error_lns_merge_bevor_start_{self.start_day}_end_{self.end_day}.json"
                )
                sol.to_json_file(
                    f"error_lns_merge_after_start_{self.start_day}_end_{self.end_day}.json"
                )
                continue

            self.logger.debug(
                f"Iteration {iteration}: Found solution with objective {sol.objective_value}"
            )

            improvement = 0
            if sol.objective_value < self.old_solution.objective_value:
                improvements += 1
                improvement = self.old_solution.objective_value - sol.objective_value
                self.logger.info(
                    f"Iteration {iteration}: Found improvement! "
                    f"Old objective: {self.old_solution.objective_value}, "
                    f"New objective: {sol.objective_value}, "
                    f"Improvement: {improvement}"
                )
                self.old_solution = sol
            else:
                self.logger.debug(
                    f"Iteration {iteration}: No improvement (current best: {self.old_solution.objective_value})"
                )

            self.update_search_window(improvement)

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
