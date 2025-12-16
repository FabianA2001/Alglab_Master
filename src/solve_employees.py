from datetime import datetime

from ortools.sat.python import cp_model
from pydantic import BaseModel, Field, model_validator

from typing import Callable

from . import shift_vars
from .callback_early_stop import Callback_Early_Stop
from .solverCallback.callback_three_best_solutions import Callback_Top_Solutions
from .inputTypes import employee, instace, shift, shiftType
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
from .solver import Solver

import time

class solve_employee():
    def __init__(self, instance: instace.Instance, vars: shift_vars.Shift_vars):
        self.instance = instance
        self.instance_copy = instance
        self.solve_time = 0
        self.solution = Solution(instance=instance)


    def solve_all_employees(self):
        count_= 0
        start_time = time.time()
        for employee_uid in self.instance.employees:
            count_= count_+1
            print(count_)
            self.solve_employee(employee_uid=employee_uid)
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"Execution time: {execution_time:.6f} seconds")

    def solve_employee(self, employee_uid: employee.EmployeeUid):
        self.instance_copy = self.instance.model_copy(deep=True)
        self.instance_copy.employees = {employee_uid: self.instance_copy.employees[employee_uid]}
        solver_ = Solver(self.instance_copy, shift_vars.Shift_vars(self.instance_copy))
        solution = solver_.solve_callback_with_solution(disabled_constraints=[SolverConstraints.cover_requirements], objective_function=solver_.objective_value_only_wishes, log_search_progress=False, stop_after_first_solution=True, max_time_in_seconds=450)
        self.store_employee_solution(solution, employee_uid)
        print(employee_uid)


    def store_employee_solution(self, solution: Solution, employee_uid: employee.EmployeeUid) -> None:
        """Stores the solution in the given Solution instance."""
        for day in range(self.instance.number_of_days):
            for type_uid in self.instance.shifts[day]:
                self.solution.set_var(day, type_uid, employee_uid, solution.vars[(day, type_uid, employee_uid)])

        for weekend in range(round(self.instance.number_of_days / 7)):
            self.solution.set_weekend_var(weekend, employee_uid, solution.weekend_vars[(weekend, employee_uid)])