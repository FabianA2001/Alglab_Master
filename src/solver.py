from datetime import datetime

from ortools.sat.python import cp_model

from . import shift_vars
from .inputTypes import instace
from .module import (
    cover_requirements,
    days_off,
    limited_shifts_per_type_validation,
    max_Cons_Shifts,
    max_weekend_days,
    minimum_consecutive_days_off,
    minimum_consecutive_shifts,
    minMaxWorkTime,
    shift_assignment_single_day_validation,
    shift_rotation_constraint,
)
from .module.solverConstraints import SolverConstraints
from .solution import Solution


class Solver:
    def __init__(self, instance: instace.Instance, vars: shift_vars.Shift_vars):
        self.instance = instance
        self.vars = vars
        self.solve_time = 0
        self.start_solve_time: datetime = datetime(2005, 1, 1, 0, 0)

    def solve(
        self,
        log_search_progress: bool = True,
        max_time_in_seconds: float = 60.0,
        disabled_constraints: list[SolverConstraints] = [],
        stop_after_first_solution: bool = False,
        **solver_params,
    ) -> Solution:
        if SolverConstraints.days_off not in disabled_constraints:
            days_off.Days_off().build(self.instance, self.vars)
        if SolverConstraints.cover_requirements not in disabled_constraints:
            cover_requirements.Cover_requirements().build(self.instance, self.vars)
        if (
            SolverConstraints.limited_shifts_per_type_validation
            not in disabled_constraints
        ):
            limited_shifts_per_type_validation.Limited_shifts_per_type_validation().build(
                self.instance, self.vars
            )
        if SolverConstraints.max_Cons_Shifts not in disabled_constraints:
            max_Cons_Shifts.Max_Cons_Shifts().build(self.instance, self.vars)
        if SolverConstraints.max_weekend_days not in disabled_constraints:
            max_weekend_days.Max_weekend_days().build(self.instance, self.vars)
        if SolverConstraints.minimum_consecutive_days_off not in disabled_constraints:
            minimum_consecutive_days_off.Minimum_consecutive_days_off().build(
                self.instance, self.vars
            )
        if SolverConstraints.minimum_consecutive_shifts not in disabled_constraints:
            minimum_consecutive_shifts.Minimum_consecutive_shifts().build(
                self.instance, self.vars
            )
        if SolverConstraints.minMaxWorkTime not in disabled_constraints:
            minMaxWorkTime.MinMaxWorkTime().build(self.instance, self.vars)
        if SolverConstraints.shift_rotation_constraint not in disabled_constraints:
            shift_rotation_constraint.Shift_rotation_constraint().build(
                self.instance, self.vars
            )
        if (
            SolverConstraints.shift_assignment_single_day_validation
            not in disabled_constraints
        ):
            shift_assignment_single_day_validation.Single_day_validation().build(
                self.instance, self.vars
            )
        solver = cp_model.CpSolver()
        solver.parameters.log_search_progress = log_search_progress
        solver.parameters.max_time_in_seconds = max_time_in_seconds

        if stop_after_first_solution:
            solver.parameters.stop_after_first_solution = True

        for key, value in solver_params.items():
            setattr(solver.parameters, key, value)

        self.vars.model.Minimize(self.objevtive_value())
        self.start_solve_time = datetime.now()
        status = solver.Solve(self.vars.model)
        self.solve_time = (datetime.now() - self.start_solve_time).total_seconds()
        return self.handle_results(status, solver, disabled_constraints)

    def objevtive_value(self):
        objective_value = 0
        for employee_uid in self.instance.employees:
            for day in range(self.instance.number_of_days):
                for type_uid in self.instance.shifts[day]:
                    objective_value += self.instance.get_shift(
                        day=day, type_uid=type_uid
                    ).penalty_assigned_day_employee.get(employee_uid, 0) * (
                        1 - self.vars.vars[(day, type_uid, employee_uid)]
                    )
                    objective_value += (
                        self.instance.shifts[day][
                            type_uid
                        ].penalty_not_assigned_day_employee.get(employee_uid, 0)
                        * self.vars.vars[(day, type_uid, employee_uid)]
                    )
        for day in range(self.instance.number_of_days):
            for type_uid in self.instance.shifts[day]:
                objective_value += (
                    self.vars.below_prefferd_vars[(day, type_uid)]
                    * self.instance.shifts[day][type_uid].weight_below_preferred
                )
                objective_value += (
                    self.vars.above_prefferd_vars[(day, type_uid)]
                    * self.instance.shifts[day][type_uid].weight_above_preferred
                )
        return objective_value

    def handle_results(
        self,
        status,
        solver: cp_model.CpSolver,
        disabled_constraints: list[SolverConstraints] = [],
    ) -> Solution:
        """Handles the different results returned by the solver and returns a solution."""
        solution = Solution(self.instance)  # Create a new Solution instance
        if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            self.store_solution(
                solver, solution
            )  # Pass the solution instance to store values
            # if status == cp_model.OPTIMAL:
            #     print("Optimal solution found.")
            # else:
            #     print("Feasible solution found but not optimal.")
            solution.objective_value = solver.ObjectiveValue()
            solution.solve_status = status
            solution.instance = self.instance
            solution.disabled_constraints = disabled_constraints
            solution.solve_time = self.solve_time
            solution.timestamp = datetime.now()
            return solution  # Return the populated solution
        elif status == cp_model.INFEASIBLE:
            self.process_infeasible_solution()
        elif status == cp_model.UNKNOWN:
            self.process_unknown_status()
        elif status == cp_model.MODEL_INVALID:
            self.process_invalid_model()

        return solution  # Return an empty solution for cases where no valid solution was found

    def store_solution(self, solver: cp_model.CpSolver, solution: Solution) -> None:
        """Stores the solution in the given Solution instance."""
        for day in range(self.instance.number_of_days):
            for type_uid in self.instance.shifts[day]:
                for employee_uid in self.instance.employees:
                    var_value = solver.Value(
                        self.vars.get_var(day, type_uid, employee_uid)
                    )
                    solution.set_var(day, type_uid, employee_uid, var_value)

        for weekend in range(round(self.instance.number_of_days / 7)):
            for employee_uid in self.instance.employees:
                weekend_value = solver.Value(
                    self.vars.get_weekend_var(weekend, employee_uid)
                )
                solution.set_weekend_var(weekend, employee_uid, weekend_value)

        # Store above and below preferred vars
        for day in range(self.instance.number_of_days):
            for type_uid in self.instance.shifts[day]:
                above_value = solver.Value(
                    self.vars.get_above_prefferd_var(day, type_uid)
                )
                below_value = solver.Value(
                    self.vars.get_below_prefferd_var(day, type_uid)
                )
                solution.set_above_prefferd_var(day, type_uid, above_value)
                solution.set_below_prefferd_var(day, type_uid, below_value)

    def process_infeasible_solution(self) -> None:
        """Handles the case when no feasible solution exists."""
        print("No feasible solution exists for the provided constraints.")

    def process_unknown_status(self) -> None:
        """Handles the case when the solver stops without finding a solution."""
        print(
            "Solver stopped without finding a solution. Possible reasons may include time limits or resource limits."
        )

    def process_invalid_model(self) -> None:
        """Handles the case when the model is invalid."""
        print("The model provided is invalid and cannot be solved.")
        print("The model provided is invalid and cannot be solved.")

    def warm_start(
        self,
        solution: Solution,
        instance: instace.Instance,
        disabled_constraints: list[SolverConstraints] = [],
        max_time_in_seconds: float = 60.0,
    ) -> Solution:
        """Warm starts the solver with a given solution."""
        self.instance = instance
        for day in range(instance.number_of_days):
            for type_uid in instance.shifts[day]:
                for employee_uid in instance.employees:
                    var_value = solution.vars[(day, type_uid, employee_uid)] == 1
                    self.vars.model.AddHint(
                        self.vars.get_var(day, type_uid, employee_uid), var_value
                    )
        return self.solve(
            disabled_constraints=disabled_constraints,
            max_time_in_seconds=max_time_in_seconds,
        )
