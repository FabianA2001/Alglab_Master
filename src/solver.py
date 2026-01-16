import random
from datetime import datetime
from functools import partial
from typing import Callable

from ortools.sat.python import cp_model

from src.greedy_scheduler import SequentialGreedyScheduler, SequentialGreedyScheduler2

from . import shift_vars
from .callback_early_stop import Callback_Early_Stop, Callback_Early_Stop_immediate
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
    minimum_consecutive_days_off,
    minimum_consecutive_shifts,
    minimum_consecutive_shifts_new,
    minimum_consecutove_days_off_new,
    minMaxWorkTime,
    shift_assignment_single_day_validation,
    shift_rotation_constraint,
)
from .module.shift_assignment_module import ShiftAssignmentModule
from .module.solverConstraints import SolverConstraints
from .solution import Solution
from .solverCallback.callback_collect_all_solutions import CollectAllSolutions
from .solverCallback.callback_three_best_solutions import Callback_Top_Solutions


class Solver:
    def __init__(
        self,
        instance: instace.Instance,
        vars: shift_vars.Shift_vars,
        disabled_constraints: list[SolverConstraints] = [],
        add_module_constraints: list[ShiftAssignmentModule] = [],
    ):
        self.instance = instance
        self.vars = vars
        self.solve_time = 0
        self.start_solve_time: datetime = datetime(2005, 1, 1, 0, 0)
        self.disabled_constraints: list[SolverConstraints] = disabled_constraints
        for module in add_module_constraints:
            module.build(self.instance, self.vars)

    def solve(
        self,
        log_search_progress: bool = False,
        max_time_in_seconds: float = 60.0,
        disabled_constraints: list[SolverConstraints] = [],
        stop_after_first_solution: bool = False,
        callback: cp_model.CpSolverSolutionCallback | None = None,
        constraint_set=2,
        automaton: bool = False,
    ) -> Solution:
        objective_function = partial(
            self.objective_value_new,
        )
        return self.solve_callback_with_solution(
            log_search_progress=log_search_progress,
            max_time_in_seconds=max_time_in_seconds,
            disabled_constraints=disabled_constraints,
            stop_after_first_solution=stop_after_first_solution,
            callback=callback,
            constraint_set=constraint_set,
            automaton=automaton,
            objective_function=objective_function,
        )

    def solve_with_early_stop(
        self,
        log_search_progress: bool = False,
        max_time_in_seconds: float = 60.0,
        constraint_set: int = 2,
        stop_after_first_solution: bool = False,
    ):
        callback = Callback_Early_Stop(self.instance, self.vars)
        return self.solve(
            log_search_progress,
            max_time_in_seconds,
            callback=callback,
            constraint_set=constraint_set,
            stop_after_first_solution=stop_after_first_solution,
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
        log_search_progress: bool = False,
        max_time_in_seconds: float = 60.0,
        disabled_constraints: list[SolverConstraints] = [],
        stop_after_first_solution: bool = False,
        callback: cp_model.CpSolverSolutionCallback | None = None,
        objective_function: Callable[[], cp_model.ObjLinearExprT]
        | None = None,  # Accept a callable
        constraint_set=2,
        automaton: bool = False,
    ) -> Solution:
        """
        A function to handle diverse needs, like different objective functions and callbacks

        :param self: Description
        :param log_search_progress: print Solve log?
        :type log_search_progress: bool
        :param max_time_in_seconds: Maximum time the solver is allowed to run
        :type max_time_in_seconds: float
        :param disabled_constraints: Constraints to be disabled
        :type disabled_constraints: list[SolverConstraints]
        :param stop_after_first_solution: Find only the first solution?
        :type stop_after_first_solution: bool
        :param callback: A callback to run after each solution
        :type callback: cp_model.CpSolverSolutionCallback | None
        :param objective_function: The objective function to use
        :type objective_function: Callable[[], cp_model.ObjLinearExprT] | None
        :param constraint_set: Which constraint alternative to use. For more information look to set_constraint function.
        :param automaton: Ignore constraint_set and set the wanted constraint to the Automate variant
        :type automaton: bool
        :return: Description
        :rtype: Solution
        """
        if len(disabled_constraints) > 0:
            self.disabled_constraints = disabled_constraints
        self.set_constraints(constraint_set=constraint_set, automaton=automaton)
        solver = cp_model.CpSolver()
        solver.parameters.random_seed = random.randint(0, 9999999)
        solver.parameters.log_search_progress = log_search_progress
        solver.parameters.max_time_in_seconds = max_time_in_seconds

        if stop_after_first_solution:
            solver.parameters.stop_after_first_solution = True

        # Set the objective function; use objective_value_new as the default if none is provided
        if objective_function is None:
            objective_function = self.objective_value_new

        self.vars.model.Minimize(objective_function())

        self.start_solve_time = datetime.now()
        if callback is not None:
            status = solver.SolveWithSolutionCallback(self.vars.model, callback)
        else:
            status = solver.Solve(self.vars.model)
        self.solve_time = (datetime.now() - self.start_solve_time).total_seconds()
        return self.handle_results(status, solver, callback)

    def handle_results(
        self,
        status,
        solver: cp_model.CpSolver,
        callback: cp_model.CpSolverSolutionCallback | None = None,
    ) -> Solution:
        """Handles the different results returned by the solver and returns a solution."""

        # Check for the best solution stored in the callback
        # TODO instead of looking which class it is make it so that a parameter is given or each callback class should have a parameter that say if it should continue or stop at first good enough solution
        if isinstance(callback, Callback_Top_Solutions):
            if callback.best_solution is not None:
                del solver
                return callback.best_solution  # Return the best solution if it exists
        solution = Solution(self.instance)  # Create a new Solution instance
        solution.solve_status = status
        if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            self.store_solution(solver, solution)  # Store the current solution values
            solution.objective_value = solver.ObjectiveValue()
            solution.instance = self.instance
            solution.disabled_constraints = self.disabled_constraints
            solution.solve_time = self.solve_time
            solution.timestamp = datetime.now()
            del solver
            return solution  # Return the populated solution

        elif status == cp_model.INFEASIBLE:
            self.process_infeasible_solution()
            del solver
            return solution

        elif status == cp_model.UNKNOWN:
            self.process_unknown_status()
            del solver
            return solution

        elif status == cp_model.MODEL_INVALID:
            self.process_invalid_model()
            del solver
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

        for day in range(self.instance.number_of_days):
            for type_uid in self.instance.shifts[day]:
                for employee_uid in self.instance.employees:
                    work_vars_value = solver.Value(
                        self.vars.get_work_vars(day, employee_uid)
                    )
                    solution.set_work_vars(day, employee_uid, work_vars_value)

        for weekend in self.instance.weekend_days:
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
                below_threshold_value = solver.Value(
                    self.vars.get_below_threshold_var(day, type_uid)
                )
                solution.set_above_prefferd_var(day, type_uid, above_value)
                solution.set_below_prefferd_var(day, type_uid, below_value)
                solution.set_below_threshold_var(day, type_uid, below_threshold_value)

        solution.instance.name = (
            solution.instance.name + "_" + f"seed{solver.parameters.random_seed}"
        )

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
        max_time_in_seconds: float = 60.0,
    ) -> Solution:
        """Warm starts the solver with a given solution."""

        # Create a callable for the objective_function
        objective_function = partial(
            self.objective_value_weight_changes,
            solution=solution,
        )
        callback = Callback_Early_Stop(self.instance, self.vars)
        return self.warm_start_generalized(
            hint_solution=solution,
            max_time_in_seconds=max_time_in_seconds,
            objective_function=objective_function,
            callback=callback,
        )

    def warm_start_multi(
        self,
        solution: Solution,
        instance: instace.Instance,
        disabled_constraints: list[SolverConstraints] = [],
        max_time_in_seconds: float = 60.0,
    ) -> list[tuple[int, Solution]]:
        """Warm starts the solver with a given solution."""
        self.instance = instance
        for day in range(instance.number_of_days):
            for type_uid in instance.shifts[day]:
                for employee_uid in instance.employees:
                    var_value = solution.vars[(day, type_uid, employee_uid)] == 1
                    self.vars.model.AddHint(
                        self.vars.get_var(day, type_uid, employee_uid), var_value
                    )
        return self.solve_min_changes_multiple_results(
            solution=solution,
            disabled_constraints=disabled_constraints,
            max_time_in_seconds=max_time_in_seconds,
        )

    def warm_start_generalized(
        self,
        hint_solution: Solution | None = None,
        hard_constraint_solution: Solution | None = None,
        disabled_constraints: list[SolverConstraints] = [],
        max_time_in_seconds: float = 60.0,
        objective_function: Callable[[], cp_model.ObjLinearExprT] | None = None,
        log_search_progress: bool = False,
        stop_after_first_solution: bool = False,
        callback: cp_model.CpSolverSolutionCallback | None = None,
        constraint_set: int = 2,
    ) -> Solution:
        """
        A function that allow to give a solution as hint and another solution as hard constraints (only work_var and var are considered)

        :param self: Description
        :param hint_solution: Solution to add as a hint
        :type hint_solution: Solution | None
        :param hard_constraint_solution: A solution to add its var and work_var as hard constraints
        :type hard_constraint_solution: Solution | None
        :param disabled_constraints: Description
        :type disabled_constraints: list[SolverConstraints]
        :param max_time_in_seconds: Description
        :type max_time_in_seconds: float
        :param objective_function: Description
        :type objective_function: Callable[[], cp_model.ObjLinearExprT] | None
        :param log_search_progress: Description
        :type log_search_progress: bool
        :param stop_after_first_solution: Description
        :type stop_after_first_solution: bool
        :param callback: Description
        :type callback: cp_model.CpSolverSolutionCallback | None
        :return: Description
        :rtype: Solution
        """
        employee_uid_ = None
        if hint_solution is not None:
            """Warm starts the solver with a given solution."""
            for employee_uid in self.instance.employees.keys():
                for day in range(self.instance.number_of_days):
                    for type_uid, _ in self.instance.shifts[day].items():
                        if (day, type_uid, employee_uid) in hint_solution.vars.keys():
                            var_value = (
                                hint_solution.vars[(day, type_uid, employee_uid)] == 1
                            )
                            self.vars.model.AddHint(
                                self.vars.get_var(day, type_uid, employee_uid),
                                var_value,
                            )
                        # elif employee_uid_ != employee_uid:
                        #     employee_uid_ = employee_uid
                        #     print(f"var not found in hint solution solution {employee_uid}")
                    if (day, employee_uid) in hint_solution.work_vars.keys():
                        var_value = hint_solution.work_vars[(day, employee_uid)] == 1
                        self.vars.model.AddHint(
                            self.vars.get_work_vars(day, employee_uid), var_value
                        )
                    # elif employee_uid_ != employee_uid:
                    #     employee_uid_ = employee_uid
                    #     print(f"work var not found in hint solution solution {employee_uid}")

                # for weekend in range(round(self.instance.number_of_days / 7)):
                #     if (weekend, employee_uid) in hint_solution.weekend_vars.keys():
                #         weekend_value = hint_solution.weekend_vars.get((weekend, employee_uid)) == 1  # Assuming 0 means "not on weekend"
                #         self.vars.model.AddHint(self.vars.get_weekend_var(weekend, employee_uid), weekend_value)

            # Adding hints for weekend_vars
                for weekend in range(round(self.instance.number_of_days / 7)):
                    if (weekend, employee_uid) in hint_solution.weekend_vars.keys():
                        var_value = (
                            hint_solution.weekend_vars[(weekend, employee_uid)] == 1
                        )
                        self.vars.model.AddHint(
                            self.vars.get_weekend_var(weekend, employee_uid), var_value
                        )

            # Adding hints for above_prefferd_vars
            for day in range(self.instance.number_of_days):
                for type_uid in self.instance.shifts[day].keys():
                    if (day, type_uid) in hint_solution.above_prefferd_vars.keys():
                        var_value = hint_solution.above_prefferd_vars[(day, type_uid)]
                        self.vars.model.AddHint(
                            self.vars.get_above_prefferd_var(day, type_uid), var_value
                        )
            # Adding hints for below_prefferd_vars
                    if (day, type_uid) in hint_solution.below_prefferd_vars.keys():
                        var_value = hint_solution.below_prefferd_vars[(day, type_uid)]
                        self.vars.model.AddHint(
                            self.vars.get_below_prefferd_var(day, type_uid), var_value
                        )
            # Adding hints for below_threshold_vars
                    if (day, type_uid) in hint_solution.below_threshold_vars.keys():
                        var_value = hint_solution.below_threshold_vars[(day, type_uid)]
                        self.vars.model.AddHint(
                            self.vars.get_below_threshold_var(day, type_uid), var_value
                        )

        if hard_constraint_solution is not None:
            for employee_uid in self.instance.employees.keys():
                for day in range(self.instance.number_of_days):
                    for type_uid, _ in self.instance.shifts[day].items():
                        if (
                            day,
                            type_uid,
                            employee_uid,
                        ) in hard_constraint_solution.vars.keys():
                            var_value = (
                                hard_constraint_solution.vars[
                                    (day, type_uid, employee_uid)
                                ]
                                == 1
                            )
                            if (
                                hint_solution is None
                                or (day, type_uid, employee_uid)
                                not in hint_solution.vars.keys()
                            ):
                                self.vars.model.AddHint(
                                    self.vars.get_var(day, type_uid, employee_uid),
                                    var_value,
                                )
                            self.vars.model.add(
                                self.vars.get_var(day, type_uid, employee_uid)
                                == var_value
                            )
                        # elif employee_uid_ != employee_uid:
                        #     employee_uid_ = employee_uid
                        #     print(f"var not found in hard_constraint solution {employee_uid}")
            for employee_uid, _ in self.instance.employees.items():
                for day in range(self.instance.number_of_days):
                    if (day, employee_uid) in hard_constraint_solution.work_vars.keys():
                        var_value = (
                            hard_constraint_solution.work_vars[(day, employee_uid)] == 1
                        )
                        if (
                            hint_solution is None
                            or (day, employee_uid) not in hint_solution.work_vars.keys()
                        ):
                            self.vars.model.AddHint(
                                self.vars.get_work_vars(day, employee_uid), var_value
                            )
                        self.vars.model.add(
                            self.vars.get_work_vars(day, employee_uid) == var_value
                        )
                    # elif employee_uid_ != employee_uid:
                    #     employee_uid_ = employee_uid
                    #     print(f"work var not found in hard_constraint solution {employee_uid}")

        return self.solve_callback_with_solution(
            disabled_constraints=disabled_constraints,
            max_time_in_seconds=max_time_in_seconds,
            log_search_progress=log_search_progress,
            objective_function=objective_function,
            stop_after_first_solution=stop_after_first_solution,
            callback=callback,
            constraint_set=constraint_set
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
    ) -> Solution:
        self.set_constraints(automaton=False)
        solver = cp_model.CpSolver()
        solver.parameters.log_search_progress = log_search_progress
        solver.parameters.max_time_in_seconds = max_time_in_seconds

        self.vars.model.Minimize(self.objective_value_weight_changes(solution=solution))
        self.start_solve_time = datetime.now()
        # status = solver.Solve(self.vars.model)
        ##mit Callback
        callback = Callback_Early_Stop(self.instance, self.vars)
        status = solver.SolveWithSolutionCallback(self.vars.model, callback)
        ###
        self.solve_time = (datetime.now() - self.start_solve_time).total_seconds()
        return self.handle_results(status, solver)

    def set_constraints(
        self,
        constraint_set=2,
        automaton: bool = False,
    ):
        """
        Docstring for set_constraints

        :param self: Description
        :param log_search_progress: Description
        :type log_search_progress: bool
        :param max_time_in_seconds: Description
        :type max_time_in_seconds: float
        :param disabled_constraints: Description
        :type disabled_constraints: list[SolverConstraints]
        :param constraint_set: Decide which minimal shifts/day off constraint to use:
        0 - original constraint
        1 - New constraint
        2 - Alternative constraint
        3 - Alternative_Enforce_If
        4 - Alternative_exact
        5 - Alternative_exact_Enforce_If
        6 - Automaton
        7 - Alternative_exact_original
        :param automaton: If set to true then Automate implementation of some constraints will be used
        :type automaton: bool
        """
        if automaton:
            constraint_set = 6
        if SolverConstraints.days_off not in self.disabled_constraints:
            days_off_new.Days_off_new().build(self.instance, self.vars)
        if SolverConstraints.cover_requirements not in self.disabled_constraints:
            cover_requirements.Cover_requirements().build(self.instance, self.vars)
        if (
            SolverConstraints.limited_shifts_per_type_validation
            not in self.disabled_constraints
        ):
            limited_shifts_per_type_validation.Limited_shifts_per_type_validation().build(
                self.instance, self.vars
            )
        if SolverConstraints.max_Cons_Shifts not in self.disabled_constraints:
            max_Cons_shifts_new.Max_Cons_Shifts_new().build(self.instance, self.vars)
        if SolverConstraints.max_weekend_days not in self.disabled_constraints:
            max_weekend_days.Max_weekend_days().build(self.instance, self.vars)
        if (
            SolverConstraints.minimum_consecutive_days_off
            not in self.disabled_constraints
            and constraint_set == 0
        ):
            minimum_consecutive_days_off.Minimum_consecutive_days_off().build(
                self.instance, self.vars
            )
            # print("Minimum_consecutive_days_off")
        if (
            SolverConstraints.minimum_consecutive_shifts
            not in self.disabled_constraints
            and constraint_set == 0
        ):
            minimum_consecutive_shifts.Minimum_consecutive_shifts().build(
                self.instance, self.vars
            )
            # print("Minimum_consecutive_shifts")
        if (
            SolverConstraints.minimum_consecutive_days_off
            not in self.disabled_constraints
            and constraint_set == 1
        ):
            minimum_consecutove_days_off_new.Minimum_consecutive_days_off_new().build(
                self.instance, self.vars
            )
            # print("Minimum_consecutive_days_off_new")
        if (
            SolverConstraints.minimum_consecutive_shifts
            not in self.disabled_constraints
            and constraint_set == 1
        ):
            minimum_consecutive_shifts_new.Minimum_consecutive_shifts_new().build(
                self.instance, self.vars
            )
            # print("Minimum_consecutive_shifts_new")
        if (
            SolverConstraints.minimum_consecutive_days_off
            not in self.disabled_constraints
            and constraint_set == 2
        ):
            minimum_consecutove_days_off_new.Min_Cons_Days_Off_Alternative().build(
                self.instance, self.vars
            )
            # print("Min_Cons_Days_Off_Alternative")
        if (
            SolverConstraints.minimum_consecutive_shifts
            not in self.disabled_constraints
            and constraint_set == 2
        ):
            minimum_consecutive_shifts_new.Min_Cons_Shifts_Alternative().build(
                self.instance, self.vars
            )
            # print("Min_Cons_Shifts_Alternative")
        if (
            SolverConstraints.minimum_consecutive_days_off
            not in self.disabled_constraints
            and constraint_set == 3
        ):
            minimum_consecutove_days_off_new.Min_Cons_Days_Off_Alternative_Enforce_If().build(
                self.instance, self.vars
            )
            # print("Min_Cons_Days_Off_Alternative_Enforce_If")
        if (
            SolverConstraints.minimum_consecutive_shifts
            not in self.disabled_constraints
            and constraint_set == 3
        ):
            minimum_consecutive_shifts_new.Min_Cons_Shifts_Alternative_Enforce_If().build(
                self.instance, self.vars
            )
            # print("Min_Cons_Shifts_Alternative_Enforce_If")
        if (
            SolverConstraints.minimum_consecutive_days_off
            not in self.disabled_constraints
            and constraint_set == 4
        ):
            minimum_consecutove_days_off_new.Min_Cons_Days_Off_Alternative_exact().build(
                self.instance, self.vars
            )
            # print("Min_Cons_Days_Off_Alternative_exact")
        if (
            SolverConstraints.minimum_consecutive_shifts
            not in self.disabled_constraints
            and constraint_set == 4
        ):
            minimum_consecutive_shifts_new.Min_Cons_Shifts_Alternative_exact().build(
                self.instance, self.vars
            )
            # print("Min_Cons_Shifts_Alternative_exact")
        if (
            SolverConstraints.minimum_consecutive_days_off
            not in self.disabled_constraints
            and constraint_set == 5
        ):
            minimum_consecutove_days_off_new.Min_Cons_Days_Off_Alternative_exact_Enforce_If().build(
                self.instance, self.vars
            )
            # print("Min_Cons_Days_Off_Alternative_exact_Enforce_If")
        if (
            SolverConstraints.minimum_consecutive_shifts
            not in self.disabled_constraints
            and constraint_set == 5
        ):
            minimum_consecutive_shifts_new.Min_Cons_Shifts_Alternative_exact_Enforce_If().build(
                self.instance, self.vars
            )
            # print("Min_Cons_Shifts_Alternative_exact_Enforce_If")
        if (
            SolverConstraints.minimum_consecutive_days_off
            not in self.disabled_constraints
            and constraint_set == 6
        ):
            minimum_consecutove_days_off_new.Min_Cons_Days_Off_Automaton().build(
                self.instance, self.vars
            )
            # print("Min_Cons_Days_Off_Automaton")
        if (
            SolverConstraints.minimum_consecutive_shifts
            not in self.disabled_constraints
            and constraint_set == 6
        ):
            minimum_consecutive_shifts_new.Min_Cons_Shifts_Automaton().build(
                self.instance, self.vars
            )
            # print("Min_Cons_Shifts_Automaton")
        if (
            SolverConstraints.minimum_consecutive_days_off
            not in self.disabled_constraints
            and constraint_set == 7
        ):
            minimum_consecutove_days_off_new.Min_Cons_Days_Off_Alternative_exact_original().build(
                self.instance, self.vars
            )
            # print("Min_Cons_Days_Off_Alternative_exact_original")
        if (
            SolverConstraints.minimum_consecutive_shifts
            not in self.disabled_constraints
            and constraint_set == 7
        ):
            minimum_consecutive_shifts_new.Min_Cons_Shifts_Alternative_exact_original().build(
                self.instance, self.vars
            )
            # print("Min_Cons_Shifts_Alternative_exact_original")
        if SolverConstraints.minMaxWorkTime not in self.disabled_constraints:
            minMaxWorkTime.MinMaxWorkTime().build(self.instance, self.vars)
        if SolverConstraints.shift_rotation_constraint not in self.disabled_constraints:
            shift_rotation_constraint.Shift_rotation_constraint().build(
                self.instance, self.vars
            )
        if (
            SolverConstraints.shift_assignment_single_day_validation
            not in self.disabled_constraints
        ):
            shift_assignment_single_day_validation.Single_day_validation().build(
                self.instance, self.vars
            )
        if SolverConstraints.assign_employee_day_shift not in self.disabled_constraints:
            assign_employee_day_shift.Assign_employee_day_shift().build(
                self.instance, self.vars
            )
        if SolverConstraints.ban_employee_day_shift not in self.disabled_constraints:
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

                objective_value += self.vars.above_prefferd_vars[(day, type_uid)] * (
                    self.instance.shifts[day][type_uid].weight_above_preferred
                )
                objective_value += (
                    self.vars.below_threshold_vars[(day, type_uid)]
                    * self.instance.shifts[day][type_uid].weight_below_preferred
                    * 2
                )

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

    def warm_start_greedy(
        self,
        # greedy_solution: dict[tuple[int, int], list[int]],
        instance: instace.Instance,
        disabled_constraints: list[SolverConstraints] = [],
        max_time_in_seconds: float = 60.0,
        log_search_progress: bool = False,
    ) -> Solution:
        scheduler = SequentialGreedyScheduler(instance)
        binary_matrix = scheduler.get_assignment_matrix()  # für direkte Verwendung
        """Warm starts the solver with a given greedy solution."""
        self.instance = instance
        for day in range(instance.number_of_days):
            for type_uid in instance.shifts[day]:
                for employee_uid in instance.employees:
                    var_value = binary_matrix[(day, type_uid, employee_uid)] == 1
                    self.vars.model.AddHint(
                        self.vars.get_var(day, type_uid, employee_uid), var_value
                    )
        # return self.solve_with_early_stop(
        #     disabled_constraints=disabled_constraints,
        #     max_time_in_seconds=max_time_in_seconds,
        #     log_search_progress=log_search_progress,
        # )
        return self.solve(
            log_search_progress=log_search_progress,
            max_time_in_seconds=max_time_in_seconds,
            stop_after_first_solution=True,
        )

    def warm_start_greedy2(
        self,
        # greedy_solution: dict[tuple[int, int], list[int]],
        instance: instace.Instance,
        disabled_constraints: list[SolverConstraints] = [],
        max_time_in_seconds: float = 60.0,
        log_search_progress: bool = False,
    ) -> Solution:
        scheduler = SequentialGreedyScheduler2(instance)
        binary_matrix = scheduler.get_assignment_matrix()  # für direkte Verwendung
        """Warm starts the solver with a given greedy solution."""
        self.instance = instance
        for day in range(instance.number_of_days):
            for type_uid in instance.shifts[day]:
                for employee_uid in instance.employees:
                    var_value = binary_matrix[(day, type_uid, employee_uid)] == 1
                    self.vars.model.AddHint(
                        self.vars.get_var(day, type_uid, employee_uid), var_value
                    )
        # return self.solve_with_early_stop(
        #     disabled_constraints=disabled_constraints,
        #     max_time_in_seconds=max_time_in_seconds,
        #     log_search_progress=log_search_progress,
        # )
        return self.solve(
            log_search_progress=log_search_progress,
            max_time_in_seconds=max_time_in_seconds,
            stop_after_first_solution=True,
        )

    def solve_min_changes_multiple_results(
        self,
        solution: Solution,
        log_search_progress: bool = True,
        max_time_in_seconds: float = 60.0,
        disabled_constraints: list[SolverConstraints] = [],
    ) -> list[tuple[int, Solution]]:
        """Run solver minimizing changes weight and collect multiple solutions via a callback.

        Returns a list of Solution objects collected by the callback (may be empty).
        """
        if len(disabled_constraints) > 0:
            self.disabled_constraints = disabled_constraints
        self.set_constraints()
        solver = cp_model.CpSolver()
        solver.parameters.log_search_progress = log_search_progress
        solver.parameters.max_time_in_seconds = max_time_in_seconds

        self.vars.model.Minimize(self.objective_value_weight_changes(solution=solution))
        # record start time for solutions
        self.start_solve_time = datetime.now()

        # Use external callback to collect all intermediate solutions
        callback = CollectAllSolutions(
            self.instance, self.vars, disabled_constraints, self.start_solve_time
        )

        _ = solver.SolveWithSolutionCallback(self.vars.model, callback)

        self.solve_time = (datetime.now() - self.start_solve_time).total_seconds()

        # Now compute number of changes for each collected solution relative to the provided base `solution`.
        def count_changes(sol: Solution, base: Solution) -> int:
            changes = 0
            for day in range(self.instance.number_of_days):
                for type_uid in self.instance.shifts[day]:
                    for emp in self.instance.employees:
                        a = sol.vars.get((day, type_uid, emp), 0)
                        b = base.vars.get((day, type_uid, emp), 0)
                        if a != b:
                            changes += 1
            return changes

        collected = callback.collected

        results: list[tuple[int, Solution]] = []

        for sol in collected:
            changes = count_changes(sol, solution)
            results.append((changes, sol))

        # Nach Anzahl der Änderungen sortieren (aufsteigend)
        # Nach Anzahl der Änderungen sortieren (aufsteigend)
        results_sorted = sorted(results, key=lambda t: t[0])

        if not results_sorted:
            return []

        best_changes = results_sorted[0][0]

        # Schwellenwert bestimmen
        if best_changes < 5:
            max_allowed_changes = 10
        else:
            max_allowed_changes = 2 * best_changes

        # Filtern
        filtered_results = [
            (changes, sol)
            for changes, sol in results_sorted
            if changes <= max_allowed_changes
        ]

        return filtered_results
