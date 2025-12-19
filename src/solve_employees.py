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

import json

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
        instance_name=""+self.instance.name
        for employee_uid in self.instance.employees:
            # Convert tuple keys to string keys
            vars_str_keys = {f"{key[0]}_{key[1]}_{key[2]}": value for key, value in self.solution.vars.items()}

            # Serialize to JSON
            vars_json = json.dumps(vars_str_keys)
            count_ += 1
            print(count_)
            employee_uids.append(employee_uid)
            end_time = time.time()
            execution_time = end_time - start_time
            soft_max_time_in_seconds_employee = soft_max_time_in_seconds - int(execution_time)
            if (len(self.instance.employees)-len(employee_uids)) != 0:
                soft_max_time_in_seconds_employee = int(soft_max_time_in_seconds_employee/(len(self.instance.employees)-len(employee_uids)))
            if incrementally:
                result = subprocess.run(
                    ['python3', 'subprocess_employees.py', ','.join(map(str, employee_uids)), str(self.instance.name), str(soft_max_time_in_seconds_employee)],
                    input=vars_json,  # Pass vars_json through stdin
                    capture_output=True,
                    text=True
                )
                print(result.stdout)
            else:
                # Call the subprocess
                result = subprocess.run(
                    ['python3', 'subprocess_employee.py', str(employee_uid), str(self.instance.name), str(soft_max_time_in_seconds_employee)],
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
        self.solution.to_json_file(self.instance.name + "start")

        end_time = time.time()
        execution_time = end_time - start_time
        print(f"Execution time 1: {execution_time:.6f} seconds")

        soft_max_time_in_seconds = soft_max_time_in_seconds - int(execution_time)
        if soft_max_time_in_seconds < 0:
            soft_max_time_in_seconds = 30
        self.instance.name = instance_name
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
        
    def store_solution_work_vars(self, solution: Solution, employee_uid: employee.EmployeeUid):
        for day in range(self.instance.number_of_days):
            if (day, employee_uid) in self.solution.work_vars.keys():
                if solution.work_vars[(day, employee_uid)] != self.solution.work_vars[(day, employee_uid)]:
                    print(f"something bad happened:{(day, employee_uid)} {solution.work_vars[(day, employee_uid)]} - {self.solution.work_vars[(day, employee_uid)]}")
            self.solution.set_work_vars(day, employee_uid, solution.work_vars[(day, employee_uid)])
    
    def solve_instance_one_shift(self):
        instance = self.instance.instance_to_one_shift_type()
        instance.name = instance.name + "one_shift"
        start_time = time.time()
        solver_1 = Solver(instance, shift_vars.Shift_vars(instance))
        solution = solver_1.solve_callback_with_solution(log_search_progress=False, max_time_in_seconds=30, objective_function=solver_1.objective_value_new, disabled_constraints=[SolverConstraints.shift_assignment_single_day_validation, SolverConstraints.shift_rotation_constraint, SolverConstraints.limited_shifts_per_type_validation]).model_copy(deep=True)
        end_time = time.time()
        print(end_time - start_time)
        solution.solve_time = end_time - start_time
        solution.to_json_file(instance.name)
        greedy_solution_name = instance.name+""
        for employee_uid, employee_ in self.instance.employees.items():
            self.store_solution_work_vars(solution=solution, employee_uid=employee_uid)

        del solver_1
        del instance
        del solution
        #TODO maybe readd this because maybe it doesnt take too long to find that somthing is unvalid also find a way to use the informatino found in the single employee solution that are valid
        #TODO it is most likely possible to remove the other two methods incremantly and single employee with this method, should be faster, considering that we are solving one thing at a time
        #TODO instead of using timers only, use instead callbacks
        # solver_1 = Solver(self.instance, shift_vars.Shift_vars(self.instance))
        # self.solution = solver_1.test_solution_validity(solution=self.solution.model_copy(deep=True), max_time_in_seconds=450, objective_function=solver_1.objective_value_new).model_copy(deep=True)
        # end_time = time.time()
        # print(end_time - start_time)
        # self.solution.solve_time = end_time - start_time
        # self.solution.to_json_file(self.instance.name + "methodex")
        #solve one employee at a time and if an employee is not solvable then do simple greedy without work_vars

        employee_uids = []
        count_ = 0
        unvalid_employees = []
        for employee_uid in self.instance.employees:
            count_ = count_ + 1
            print(count_)
            employee_uids.append(employee_uid)
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Call the subprocess
            result = subprocess.run(
                ['py', 'subprocess_employee_work_var.py', str(employee_uid), str(self.instance.name), str(450), str(greedy_solution_name)],
                capture_output=True, text=True
            )
            print(result.stdout)
            # Handle return code and output from subprocess
            if result.returncode == 0:
                solution = Solution.from_json_file(str(employee_uid))
                # if incrementally:
                #     for employee_uid in employee_uids:
                #         self.store_employee_solution(solution, employee_uid)
                # else:
                if solution.solve_status in [cp_model.UNKNOWN]:
                    unvalid_employees.append(employee_uid)
            else:
                print(f"Error solving for employee {employee_uid}: {result.stderr}")
            if len(employee_uids) > 1:
                Solution.delete_json_solution(str(employee_uids[-2]))
        Solution.delete_json_solution(str(employee_uids[-1]))

        print(f"unvalid_employees: {unvalid_employees}")
        # TODO maybe if there is less than 5 employee just make them free and then solve the full instance at once with the valid remaining work_var
        for unvalid_employee in unvalid_employees:
            count_ = count_ + 1
            print(count_)
            employee_uids.append(unvalid_employee)
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Call the subprocess
            result = subprocess.run(
                ['py', 'subprocess_employee_work_var.py', str(unvalid_employee), str(self.instance.name), str(450), str(greedy_solution_name)],
                capture_output=True, text=True
            )
            print(result.stdout)
            # Handle return code and output from subprocess
            if result.returncode == 0:
                solution = Solution.from_json_file(str(unvalid_employee))
                # if incrementally:
                #     for employee_uid in employee_uids:
                #         self.store_employee_solution(solution, employee_uid)
                # else:
                self.store_employee_solution(solution=solution, employee_uid=unvalid_employee)
                for day in range(self.instance.number_of_days):
                    self.solution.work_vars.pop((day, unvalid_employee))
            else:
                print(f"Error solving for employee {unvalid_employee}: {result.stderr}")
            if len(employee_uids) > 1:
                Solution.delete_json_solution(str(employee_uids[-2]))
        Solution.delete_json_solution(str(employee_uids[-1]))


        solver_1 = Solver(self.instance, shift_vars.Shift_vars(self.instance))
        self.solution = solver_1.test_solution_validity(solution=self.solution.model_copy(deep=True), max_time_in_seconds=400, objective_function=solver_1.objective_value_new).model_copy(deep=True)
        end_time = time.time()
        print(end_time - start_time)
        self.solution.solve_time = end_time - start_time
        self.solution.to_json_file(self.instance.name + "methodex")



        del solver_1

        solver_1 = Solver(self.instance, shift_vars.Shift_vars(self.instance))
        self.solution = solver_1.warm_start_generalized(solution=self.solution.model_copy(deep=True), max_time_in_seconds=400, objective_function=solver_1.objective_value_new).model_copy(deep=True)
        end_time = time.time()
        print(end_time - start_time)
        self.solution.solve_time = end_time - start_time
        self.solution.to_json_file(self.instance.name + "methodex_till450")