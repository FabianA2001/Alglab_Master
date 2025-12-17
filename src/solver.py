from datetime import datetime

from ortools.sat.python import cp_model

from typing import Callable

from . import shift_vars
from .callback_early_stop import Callback_Early_Stop
from .solverCallback.callback_three_best_solutions import Callback_Top_Solutions
from .inputTypes import instace
from .module import (
    assign_employee_day_shift,
    ban_employee_day_shift,
    cover_requirements,
    days_off_new,
    limited_shifts_per_type_validation,
    max_Cons_shifts_new,
    max_weekend_days,
    minimum_consecutive_shifts_new,
    minimum_consecutove_days_off_new,
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
        callback: cp_model.CpSolverSolutionCallback | None = None,
        **solver_params,
    ) -> Solution:
        self.set_constraints(disabled_constraints=disabled_constraints)
        solver = cp_model.CpSolver()
        solver.parameters.log_search_progress = log_search_progress
        solver.parameters.max_time_in_seconds = max_time_in_seconds

        if stop_after_first_solution:
            solver.parameters.stop_after_first_solution = True

        for key, value in solver_params.items():
            setattr(solver.parameters, key, value)

        self.vars.model.Minimize(self.objective_value_new())
        self.start_solve_time = datetime.now()
        if callback is not None:
            status = solver.SolveWithSolutionCallback(self.vars.model, callback)
        else:
            status = solver.Solve(self.vars.model)

        self.solve_time = (datetime.now() - self.start_solve_time).total_seconds()
        return self.handle_results(status, solver, disabled_constraints)

    def solve_with_early_stop(
        self,
        log_search_progress: bool = True,
        max_time_in_seconds: float = 60.0,
        disabled_constraints: list[SolverConstraints] = [],
        **solver_params,
    ):
        callback = Callback_Early_Stop(self.instance, self.vars)
        return self.solve(
            log_search_progress,
            max_time_in_seconds,
            disabled_constraints,
            callback=callback,
        )

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

    def solve_callback_with_solution(
        self,
        log_search_progress: bool = True,
        max_time_in_seconds: float = 60.0,
        disabled_constraints: list[SolverConstraints] = [],
        stop_after_first_solution: bool = False,
        callback: cp_model.CpSolverSolutionCallback | None = None,
        objective_function: Callable[[], cp_model.ObjLinearExprT] | None = None,  # Accept a callable
        **solver_params,
    ) -> Solution:

        self.set_constraints(disabled_constraints=disabled_constraints)
        solver = cp_model.CpSolver()
        solver.parameters.log_search_progress = log_search_progress
        solver.parameters.max_time_in_seconds = max_time_in_seconds

        if stop_after_first_solution:
            solver.parameters.stop_after_first_solution = True

        for key, value in solver_params.items():
            setattr(solver.parameters, key, value)

        # Set the objective function; use objective_value_new as the default if none is provided
        if objective_function is None:
            objective_function = self.objective_value_new  # Default to objective_value_new

        self.vars.model.Minimize(objective_function())  # Call the objective function
        
        self.start_solve_time = datetime.now()
        if callback is not None:
            status = solver.SolveWithSolutionCallback(self.vars.model, callback)
        else:
            status = solver.Solve(self.vars.model)

        self.solve_time = (datetime.now() - self.start_solve_time).total_seconds()
        return self.handle_results(status, solver, disabled_constraints, callback)
    
    def handle_results(
        self,
        status,
        solver: cp_model.CpSolver,
        disabled_constraints: list[SolverConstraints] = [],
        callback: cp_model.CpSolverSolutionCallback | None = None,
    ) -> Solution:
        """Handles the different results returned by the solver and returns a solution."""
        
        # Check for the best solution stored in the callback
        #TODO instead of looking which class it is make it so that a parameter is given or each callback class should have a parameter that say if it should continue or stop at first good enough solution
        if isinstance(callback, Callback_Top_Solutions):
            if callback.best_solution is not None:
                return callback.best_solution  # Return the best solution if it exists
        
        solution = Solution(self.instance)  # Create a new Solution instance
        solution.solve_status = status
        
        if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            self.store_solution(solver, solution)  # Store the current solution values
            solution.objective_value = solver.ObjectiveValue()
            solution.instance = self.instance
            solution.disabled_constraints = disabled_constraints
            solution.solve_time = self.solve_time
            solution.timestamp = datetime.now()
            return solution  # Return the populated solution

        elif status == cp_model.INFEASIBLE:
            self.process_infeasible_solution()
            return solution

        elif status == cp_model.UNKNOWN:
            self.process_unknown_status()
            return solution

        elif status == cp_model.MODEL_INVALID:
            self.process_invalid_model()
            return solution

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

    def warm_start_generalized(
        self,
        solution: Solution,
        disabled_constraints: list[SolverConstraints] = [],
        max_time_in_seconds: float = 60.0,
        objective_function: Callable[[], cp_model.ObjLinearExprT] | None = None,
        log_search_progress: bool = False,
        stop_after_first_solution: bool = False,
        callback: cp_model.CpSolverSolutionCallback | None = None,
    ) -> Solution:
        """Warm starts the solver with a given solution."""
        for day in range(self.instance.number_of_days):
            for type_uid in self.instance.shifts[day]:
                for employee_uid in self.instance.employees:
                    var_value = solution.vars[(day, type_uid, employee_uid)] == 1
                    self.vars.model.AddHint(
                        self.vars.get_var(day, type_uid, employee_uid), var_value
                    )
        return self.solve_callback_with_solution(
            disabled_constraints=disabled_constraints,
            max_time_in_seconds=max_time_in_seconds,
            log_search_progress=log_search_progress,
            objective_function=objective_function,
            stop_after_first_solution=stop_after_first_solution,
            callback=callback
        )
    
    #TODO maybe remove
    def test_solution_validity(
        self,
        solution: Solution,
        disabled_constraints: list[SolverConstraints] = [],
        max_time_in_seconds: float = 60.0,
        objective_function: Callable[[], cp_model.ObjLinearExprT] | None = None,
        log_search_progress: bool = False,
        stop_after_first_solution: bool = False,
        callback: cp_model.CpSolverSolutionCallback | None = None,
    ) -> Solution:
        """Warm starts the solver with a given solution."""
        employee_uid_ = None
        for day in range(self.instance.number_of_days):
            for type_uid in self.instance.shifts[day]:
                for employee_uid in self.instance.employees:
                    if (day, type_uid, employee_uid) in solution.vars:
                        var_value = solution.vars[(day, type_uid, employee_uid)] == 1
                        self.vars.model.AddHint(
                            self.vars.get_var(day, type_uid, employee_uid), var_value
                        )
                        self.vars.model.add(self.vars.get_var(day, type_uid, employee_uid) == var_value)
                    elif employee_uid_ != employee_uid:
                        employee_uid_ = employee_uid
                        print(f"{employee_uid}")
        return self.solve_callback_with_solution(
            disabled_constraints=disabled_constraints,
            max_time_in_seconds=max_time_in_seconds,
            log_search_progress=log_search_progress,
            objective_function=objective_function,
            stop_after_first_solution=stop_after_first_solution,
            callback=callback
        )
    
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
        return self.solve_min_changes(
            solution=solution,
            disabled_constraints=disabled_constraints,
            max_time_in_seconds=max_time_in_seconds,
        )

    def objective_value_weight_changes(
        self,
        solution: Solution,
        changes_weight: int = 10,
    ):
        """Calculates the objective value weight based on changes from a given solution."""
        objective_value = 0
        for day in range(self.instance.number_of_days):
            for type_uid in self.instance.shifts[day]:
                for employee_uid in self.instance.employees:
                    current_var = self.vars.vars[(day, type_uid, employee_uid)]
                    previous_var_value = solution.vars.get(
                        (day, type_uid, employee_uid), 0
                    )
                    changed = self.vars.model.NewBoolVar(
                        f"changed_{day}_{type_uid}_{employee_uid}"
                    )

                    self.vars.model.Add(
                        current_var != previous_var_value
                    ).OnlyEnforceIf(changed)
                    self.vars.model.Add(
                        current_var == previous_var_value
                    ).OnlyEnforceIf(changed.Not())
                    # If the assignment has changed, add the change weight

                    objective_value += changes_weight * changed
        return objective_value + self.objective_value_new()

    def solve_min_changes(
        self,
        solution: Solution,
        log_search_progress: bool = True,
        max_time_in_seconds: float = 60.0,
        disabled_constraints: list[SolverConstraints] = [],
        **solver_params,
    ) -> Solution:
        self.set_constraints(disabled_constraints=disabled_constraints)
        solver = cp_model.CpSolver()
        solver.parameters.log_search_progress = log_search_progress
        solver.parameters.max_time_in_seconds = max_time_in_seconds

        for key, value in solver_params.items():
            setattr(solver.parameters, key, value)

        self.vars.model.Minimize(self.objective_value_weight_changes(solution=solution))
        self.start_solve_time = datetime.now()
        # status = solver.Solve(self.vars.model)
        ##mit Callback
        callback = Callback_Early_Stop(self.instance, self.vars)
        status = solver.SolveWithSolutionCallback(self.vars.model, callback)
        ###
        self.solve_time = (datetime.now() - self.start_solve_time).total_seconds()
        return self.handle_results(status, solver, disabled_constraints)

    def set_constraints(
        self,
        log_search_progress: bool = True,
        max_time_in_seconds: float = 60.0,
        disabled_constraints: list[SolverConstraints] = [],
        **solver_params,
    ):
        if SolverConstraints.days_off not in disabled_constraints:
            days_off_new.Days_off_new().build(self.instance, self.vars)
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
            max_Cons_shifts_new.Max_Cons_Shifts_new().build(
                self.instance, self.vars
            )
        if SolverConstraints.max_weekend_days not in disabled_constraints:
            max_weekend_days.Max_weekend_days().build(self.instance, self.vars)
        if SolverConstraints.minimum_consecutive_days_off not in disabled_constraints:
            minimum_consecutove_days_off_new.Minimum_consecutive_days_off_new().build(
                self.instance, self.vars
            )
        if SolverConstraints.minimum_consecutive_shifts not in disabled_constraints:
            minimum_consecutive_shifts_new.Minimum_consecutive_shifts_new().build(
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
        if SolverConstraints.assign_employee_day_shift not in disabled_constraints:
            assign_employee_day_shift.Assign_employee_day_shift().build(
                self.instance, self.vars
            )
        if SolverConstraints.ban_employee_day_shift not in disabled_constraints:
            ban_employee_day_shift.Ban_employee_day_shift().build(
                self.instance, self.vars
            )

    def objective_value_new(self):
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
                    self.vars.below_threshold_vars[(day, type_uid)]
                    * self.instance.shifts[day][type_uid].weight_below_preferred
                    * 2
                )

                # objective_value += (
                #     self.vars.above_prefferd_vars[(day, type_uid)]
                #     * self.instance.shifts[day][type_uid].weight_above_preferred
                # )
        return objective_value
    
    def objective_value_only_wishes(self) -> cp_model.ObjLinearExprT:
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

                # objective_value += (
                #     self.vars.above_prefferd_vars[(day, type_uid)]
                #     * self.instance.shifts[day][type_uid].weight_above_preferred
                # )
        return objective_value
