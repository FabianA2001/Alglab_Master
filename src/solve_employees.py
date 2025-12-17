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

import subprocess

#TODO Write automatic solution creator for both
# Similarly to all this check for a not valid solution, which employees are causing the invalidity
# at timer and also test to see the difference to subprocess
class solve_employee():
    def __init__(self, instance: instace.Instance):
        self.instance = instance
        self.instance_copy = instance
        self.solve_time = 0
        self.solution = Solution(instance=instance)


    def solve_all_employees_subprocess(self, incrementally: bool = False, soft_max_time_in_seconds: int = 30*60, optimize_till_max_time: bool = False) -> Solution:
        count_ = 0
        start_time = time.time()
        employee_uids = []
        for employee_uid in self.instance.employees:
            count_ += 1
            print(count_)
            employee_uids.append(employee_uid)
            if incrementally:
                result = subprocess.run(
                    ['python3', 'subprocess_employees.py', ','.join(map(str, employee_uids)), str(self.instance.name)],
    capture_output=True, text=True
                )
                print(result.stdout)
            else:
                # Call the subprocess
                result = subprocess.run(
                    ['python3', 'subprocess_employee.py', str(employee_uid), str(self.instance.name)],
                    capture_output=True, text=True
                )
            
            # Handle return code and output from subprocess
            if result.returncode == 0:
                solution = Solution.from_json_file(str(employee_uid))
                # if incrementally:
                #     for employee_uid in employee_uids:
                #         self.store_employee_solution(solution, employee_uid)
                # else:
                self.store_employee_solution(solution, employee_uid)
            else:
                print(f"Error solving for employee {employee_uid}: {result.stderr}")
            if len(employee_uids) > 1:
                Solution.delete_json_solution(str(employee_uids[-2]))
        Solution.delete_json_solution(str(employee_uids[-1]))

        solver_1 = Solver(self.instance, shift_vars.Shift_vars(self.instance))
        self.solution = solver_1.test_solution_validity(solution=self.solution.model_copy(deep=True), max_time_in_seconds=30, objective_function=solver_1.objective_value_new).model_copy(deep=True)
        end_time = time.time()
        self.solution.solve_time = end_time - start_time
        #self.solution.to_json_file(self.instance.name + "start")

        end_time = time.time()
        execution_time = end_time - start_time
        print(f"Execution time 1: {execution_time:.6f} seconds")

        soft_max_time_in_seconds = soft_max_time_in_seconds - int(execution_time)
        if soft_max_time_in_seconds < 0:
            soft_max_time_in_seconds = 30
        
        if optimize_till_max_time:
            solver_2 = Solver(self.instance, shift_vars.Shift_vars(self.instance))
            solution2 = solver_2.warm_start_generalized(solution=self.solution.model_copy(deep=True), max_time_in_seconds=soft_max_time_in_seconds, objective_function=solver_2.objective_value_new).model_copy(deep=True)
            end_time = time.time()
            solution2.solve_time = end_time - start_time
            #solution2.to_json_file(self.instance.name + "end")

            end_time = time.time()
            execution_time = end_time - start_time
            print(f"Execution time 2: {execution_time:.6f} seconds")
            return solution2
            

        return self.solution


    def solve_all_employees(self, incrementally: bool = False):
        count_= 0
        start_time = time.time()
        employee_uids = []
        for employee_uid in self.instance.employees:
            count_= count_+1
            print(count_)
            employee_uids.append(employee_uid)
            if incrementally:
                self.solve_employees_incrementally(employee_uids=employee_uids)
            else:
                self.solve_employee(employee_uid=employee_uid)
            



        solver_1 = Solver(self.instance, shift_vars.Shift_vars(self.instance))
        solution1 = solver_1.warm_start_generalized(solution=self.solution.model_copy(deep=True)).model_copy(deep=True)
        solution1.to_json_file(self.instance.name + "start")

        end_time = time.time()
        execution_time = end_time - start_time
        print(f"Execution time 1: {execution_time:.6f} seconds")

        solver_2 = Solver(self.instance, shift_vars.Shift_vars(self.instance))
        solution2 = solver_2.warm_start_generalized(solution=self.solution).model_copy(deep=True)
        solution2.to_json_file(self.instance.name + "end")

        end_time = time.time()
        execution_time = end_time - start_time
        print(f"Execution time 2: {execution_time:.6f} seconds")

    def solve_employee(self, employee_uid: employee.EmployeeUid):
        self.instance_copy = self.instance.model_copy(deep=True)
        self.instance_copy.employees = {employee_uid: self.instance_copy.employees[employee_uid]}
        solver_ = Solver(self.instance_copy, shift_vars.Shift_vars(self.instance_copy))
        # also implement something to consider the previously set employees shifts
        solution = solver_.solve_callback_with_solution(disabled_constraints=[SolverConstraints.cover_requirements], objective_function=solver_.objective_value_only_wishes, log_search_progress=False, max_time_in_seconds=450)
        self.store_employee_solution(solution, employee_uid)
        print(employee_uid)

    def solve_employees_incrementally(self, employee_uids: list[employee.EmployeeUid]):
        self.instance_copy = self.instance.model_copy(deep=True)
        employee_copy = self.instance_copy.employees.copy()
        self.instance_copy.employees.clear()
        for employee_uid in employee_uids:
            self.instance_copy.employees[employee_uid] = employee_copy[employee_uid]
        solver_ = Solver(self.instance_copy, shift_vars.Shift_vars(self.instance_copy))
        # also implement something to consider the previously set employees shifts
        solution = solver_.test_solution_validity(objective_function=solver_.objective_value_new, solution=self.solution, log_search_progress=False, max_time_in_seconds=450)
        for employee_uid in employee_uids:
            self.store_employee_solution(solution, employee_uid)

    def store_employee_solution(self, solution: Solution, employee_uid: employee.EmployeeUid) -> None:
        """Stores the solution in the given Solution instance."""
        for day in range(self.instance.number_of_days):
            for type_uid in self.instance.shifts[day]:
                if (day, type_uid, employee_uid) in self.solution.vars.keys():
                    if solution.vars[(day, type_uid, employee_uid)] != self.solution.vars[(day, type_uid, employee_uid)]:
                        print(f"something bad happened:{(day, type_uid, employee_uid)} {solution.vars[(day, type_uid, employee_uid)]} - {self.solution.vars[(day, type_uid, employee_uid)]}")
                self.solution.set_var(day, type_uid, employee_uid, solution.vars[(day, type_uid, employee_uid)])
                

        for weekend in range(round(self.instance.number_of_days / 7)):
            self.solution.set_weekend_var(weekend, employee_uid, solution.weekend_vars[(weekend, employee_uid)])
    
