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

from pathlib import Path
from src.parseData import parseTXT
from src.shift_vars import Shift_vars

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
        self.hint_solution = Solution(instance=instance)


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
                #         self.solution.store_solution_vars(solution, employee_uid)
                # else:
                self.solution.store_solution_vars(solution, employee_uid)
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
            solution2 = solver_2.warm_start_generalized(hint_solution=self.solution.model_copy(deep=True), max_time_in_seconds=soft_max_time_in_seconds, objective_function=solver_2.objective_value_new).model_copy(deep=True)
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
        solution1 = solver_1.warm_start_generalized(hint_solution=self.solution.model_copy(deep=True)).model_copy(deep=True)
        solution1.to_json_file(self.instance.name + "start")

        end_time = time.time()
        execution_time = end_time - start_time
        print(f"Execution time 1: {execution_time:.6f} seconds")

        solver_2 = Solver(self.instance, shift_vars.Shift_vars(self.instance))
        solution2 = solver_2.warm_start_generalized(hint_solution=self.solution).model_copy(deep=True)
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
        self.solution.store_solution_vars(solution, employee_uid)
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
            self.solution.store_solution_vars(solution, employee_uid)

    # def store_employee_solution(self, solution: Solution, employee_uid: employee.EmployeeUid) -> None:
    #     """Stores the solution in the given Solution instance."""
    #     for day in range(self.instance.number_of_days):
    #         for type_uid in self.instance.shifts[day]:
    #             if (day, type_uid, employee_uid) in self.solution.vars.keys():
    #                 if solution.vars[(day, type_uid, employee_uid)] != self.solution.vars[(day, type_uid, employee_uid)]:
    #                     print(f"something bad happened:{(day, type_uid, employee_uid)} {solution.vars[(day, type_uid, employee_uid)]} - {self.solution.vars[(day, type_uid, employee_uid)]}")
    #             self.solution.set_var(day, type_uid, employee_uid, solution.vars[(day, type_uid, employee_uid)])

    #     for weekend in range(round(self.instance.number_of_days / 7)):
    #         self.solution.set_weekend_var(weekend, employee_uid, solution.weekend_vars[(weekend, employee_uid)])
        
    # def store_solution_work_vars(self, solution: Solution, employee_uid: employee.EmployeeUid):
    #     for day in range(self.instance.number_of_days):
    #         if (day, employee_uid) in self.solution.work_vars.keys():
    #             if solution.work_vars[(day, employee_uid)] != self.solution.work_vars[(day, employee_uid)]:
    #                 print(f"something bad happened:{(day, employee_uid)} {solution.work_vars[(day, employee_uid)]} - {self.solution.work_vars[(day, employee_uid)]}")
    #         self.solution.set_work_vars(day, employee_uid, solution.work_vars[(day, employee_uid)])
    

    def solve_instance_one_shift(self):
        # Create one shift instance and solve it
        instance = self.instance.instance_to_one_shift_type()
        start_time = time.time()
        solver = Solver(instance, shift_vars.Shift_vars(instance))
        solution = solver.solve_callback_with_solution(log_search_progress=False, max_time_in_seconds=120, objective_function=solver.objective_value_new, stop_after_first_solution=True,disabled_constraints=[SolverConstraints.shift_assignment_single_day_validation, SolverConstraints.shift_rotation_constraint, SolverConstraints.limited_shifts_per_type_validation])
        end_time = time.time()
        print(end_time - start_time)
        solution.solve_time = end_time - start_time
        #TODO remove
        solution.to_json_file(instance.name)
        greedy_solution_name = instance.name
        for employee_uid, employee_ in self.instance.employees.items():
            self.solution.store_solution_work_vars(solution=solution, employee_uid=employee_uid)
        

        # See if any employee does not have a solution with the given work days and repair their shifts if so.
        employee_uids = []
        count_ = 0
        invalid_employees = []
        for employee_uid in self.instance.employees:
            count_ = count_ + 1
            print(count_)
            employee_uids.append(employee_uid)            
            solution_temp = self.solve_employee_sub_(employee_uid, self.instance.name, greedy_solution_name, 450)
            self.hint_solution.store_solution_vars(solution=solution_temp, employee_uid=employee_uid)
            self.hint_solution.store_solution_work_vars(solution=solution_temp, employee_uid=employee_uid)
            if solution_temp.solve_status not in [cp_model.INFEASIBLE]:
                if solution_temp.solve_status in [cp_model.UNKNOWN]:
                    invalid_employees.append(employee_uid)
                    for day in range(self.instance.number_of_days):
                            self.solution.work_vars.pop((day, employee_uid))
            else:
                print(f"Error solving for employee {employee_uid}: ")
            
            self.solution.copy_solution(solution=solution_temp)
        end_time = time.time()
        print(end_time - start_time)
        self.solution.solve_time = end_time - start_time
        self.solution.to_json_file(self.instance.name + "methodxx")

        
        #
        solver = Solver(self.instance, shift_vars.Shift_vars(self.instance))
        self.solution = solver.warm_start_generalized(hard_constraint_solution=self.solution, hint_solution=self.hint_solution, max_time_in_seconds=999, objective_function=solver.objective_value_new, stop_after_first_solution=True)
        end_time = time.time()
        print(end_time - start_time)
        self.solution.solve_time = end_time - start_time
        self.solution.to_json_file(self.instance.name + "methodex")


        solver = Solver(self.instance, shift_vars.Shift_vars(self.instance))
        self.solution = solver.warm_start_generalized(hint_solution=self.solution, max_time_in_seconds=999, objective_function=solver.objective_value_new, stop_after_first_solution=True)
        end_time = time.time()
        print(end_time - start_time)
        self.solution.solve_time = end_time - start_time
        self.solution.to_json_file(self.instance.name + "methodex_till120")


    #TODO workm start and generlized should have two solutions one is for hint another for hard constraints
    def solve_instance_one_shift_original(self):
        solution_copy=self.solution.model_copy(deep=True)
        for i in range(50):
            self.solution=solution_copy.model_copy(deep=True)
            instance_copy = self.instance.model_copy(deep=True)
            instance = instance_copy.instance_to_one_shift_type()
            instance.name = instance.name + "one_shift"
            start_time = time.time()
            solver_1 = Solver(instance, shift_vars.Shift_vars(instance))
            solution = solver_1.solve_callback_with_solution(log_search_progress=False, max_time_in_seconds=60, stop_after_first_solution=True, objective_function=solver_1.objective_value_new, disabled_constraints=[SolverConstraints.shift_assignment_single_day_validation, SolverConstraints.shift_rotation_constraint, SolverConstraints.limited_shifts_per_type_validation]).model_copy(deep=True)
            end_time = time.time()
            print(end_time - start_time)
            solution.solve_time = end_time - start_time
            solution.to_json_file(instance.name)
            greedy_solution_name = instance.name+""
            for employee_uid, employee_ in instance_copy.employees.items():
                self.solution.store_solution_work_vars(solution=solution, employee_uid=employee_uid)

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
            invalid_employees = []
            for employee_uid in instance_copy.employees:
                count_ = count_ + 1
                print(count_)
                employee_uids.append(employee_uid)
                end_time = time.time()
                execution_time = end_time - start_time
                
                solution_temp = self.solve_employee_sub(employee_uid, instance_copy.name, greedy_solution_name, 450)

                # Call the subprocess
                # result = subprocess.run(
                #     ['py', 'subprocess_employee_work_var.py', str(employee_uid), str(self.instance.name), str(450), str(greedy_solution_name)],
                #     capture_output=True, text=True
                # )
                # print(result.stdout)
                # Handle return code and output from subprocess
                self.solution.store_solution_vars(solution=solution_temp, employee_uid=employee_uid)
                if not (solution_temp.solve_status in [cp_model.INFEASIBLE]):
                    # if incrementally:
                    #     for employee_uid in employee_uids:
                    #         self.solution.store_solution_vars(solution, employee_uid)
                    # else:
                    if solution_temp.solve_status in [cp_model.UNKNOWN]:
                        invalid_employees.append(employee_uid)
                        for day in range(self.instance.number_of_days):
                            self.solution.work_vars.pop((day, employee_uid))
                else:
                    print(f"Error solving for employee {employee_uid}: ")
            #     if len(employee_uids) > 1:
            #         Solution.delete_json_solution(str(employee_uids[-2]))
            # Solution.delete_json_solution(str(employee_uids[-1]))

            print(f"invalid_employees: {invalid_employees}")
            # TODO maybe if there is less than 5 employee just make them free and then solve the full instance at once with the valid remaining work_var
            # for unvalid_employee in invalid_employees:
            #     count_ = count_ + 1
            #     print(count_)
            #     employee_uids.append(unvalid_employee)
            #     end_time = time.time()
            #     execution_time = end_time - start_time
                
            #     solution_temp = self.solve_employee_sub(unvalid_employee, instance_copy.name, greedy_solution_name, 450)

            #     # Call the subprocess
            #     # result = subprocess.run(
            #     #     ['py', 'subprocess_employee_work_var.py', str(unvalid_employee), str(self.instance.name), str(450), str(greedy_solution_name)],
            #     #     capture_output=True, text=True
            #     # )
            #     # print(result.stdout)
            #     # Handle return code and output from subprocess
            #     if not (solution_temp.solve_status in [cp_model.INFEASIBLE]):
            #         #solution = Solution.from_json_file(str(unvalid_employee))
            #         # if incrementally:
            #         #     for employee_uid in employee_uids:
            #         #         self.solution.store_solution_vars(solution, employee_uid)
            #         # else:
            #         self.solution.store_solution_vars(solution=solution_temp, employee_uid=unvalid_employee)
            #         for day in range(instance_copy.number_of_days):
            #             self.solution.work_vars.pop((day, unvalid_employee))
            #     else:
            #         print(f"Error solving for employee x {unvalid_employee}: ")
            #     if len(employee_uids) > 1:
            #         Solution.delete_json_solution(str(employee_uids[-2]))
            # Solution.delete_json_solution(str(employee_uids[-1]))


            solver_1 = Solver(instance_copy, shift_vars.Shift_vars(instance_copy))
            self.solution = solver_1.warm_start_generalized(hard_constraint_solution=self.solution.model_copy(deep=True), max_time_in_seconds=60, stop_after_first_solution=True, objective_function=solver_1.objective_value_new).model_copy(deep=True)
            end_time = time.time()
            print(end_time - start_time)
            self.solution.solve_time = end_time - start_time
            self.solution.to_json_file(instance_copy.name + "methodex")



            del solver_1

            solver_1 = Solver(instance_copy, shift_vars.Shift_vars(instance_copy))
            self.solution = solver_1.warm_start_generalized(hint_solution=self.solution.model_copy(deep=True), max_time_in_seconds=60, stop_after_first_solution=True, objective_function=solver_1.objective_value_new).model_copy(deep=True)
            end_time = time.time()
            print(end_time - start_time)
            self.solution.solve_time = end_time - start_time
            self.solution.to_json_file(instance_copy.name + "methodex_till60")








    def solve_instance_one_shift_(self):
        for i in range(50):
            instance = self.instance.instance_to_one_shift_type()
            start_time = time.time()
            solver = Solver(instance, shift_vars.Shift_vars(instance))
            solution = solver.solve_callback_with_solution(log_search_progress=False, max_time_in_seconds=120, objective_function=solver.objective_value_new, disabled_constraints=[SolverConstraints.shift_assignment_single_day_validation, SolverConstraints.shift_rotation_constraint, SolverConstraints.limited_shifts_per_type_validation])
            end_time = time.time()
            print(end_time - start_time)
            solution.solve_time = end_time - start_time
            #TODO remove
            solution.to_json_file(instance.name)
            greedy_solution_name = instance.name
            for employee_uid, employee_ in self.instance.employees.items():
                print()
                #self.solution.store_solution_work_vars(solution=solution, employee_uid=employee_uid)

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
            invalid_employees = []
            for employee_uid in self.instance.employees:
                count_ = count_ + 1
                print(count_)
                employee_uids.append(employee_uid)
                end_time = time.time()
                execution_time = end_time - start_time
                
                solution_temp = self.solve_employee_sub_(employee_uid, self.instance.name, greedy_solution_name, 450)

                # Call the subprocess
                # result = subprocess.run(
                #     ['py', 'subprocess_employee_work_var.py', str(employee_uid), str(self.instance.name), str(450), str(greedy_solution_name)],
                #     capture_output=True, text=True
                # )
                # print(result.stdout)
                # Handle return code and output from subprocess
                if not (solution_temp.solve_status in [cp_model.INFEASIBLE]):
                    # if incrementally:
                    #     for employee_uid in employee_uids:
                    #         self.solution.store_solution_vars(solution, employee_uid)
                    # else:
                    if solution_temp.solve_status in [cp_model.UNKNOWN]:
                        invalid_employees.append(employee_uid)
                else:
                    print(f"Error solving for employee {employee_uid}: ")
            #     if len(employee_uids) > 1:
            #         Solution.delete_json_solution(str(employee_uids[-2]))
            # Solution.delete_json_solution(str(employee_uids[-1]))

            print(f"invalid_employees: {invalid_employees}")
            # TODO maybe if there is less than 5 employee just make them free and then solve the full instance at once with the valid remaining work_var
            for unvalid_employee in invalid_employees:
                count_ = count_ + 1
                print(count_)
                employee_uids.append(unvalid_employee)
                end_time = time.time()
                execution_time = end_time - start_time
                
                solution_temp = self.solve_employee_sub_(unvalid_employee, self.instance.name, greedy_solution_name, 450)

                # Call the subprocess
                # result = subprocess.run(
                #     ['py', 'subprocess_employee_work_var.py', str(unvalid_employee), str(self.instance.name), str(450), str(greedy_solution_name)],
                #     capture_output=True, text=True
                # )
                # print(result.stdout)
                # Handle return code and output from subprocess
                if not (solution_temp.solve_status in [cp_model.INFEASIBLE]):
                    #solution = Solution.from_json_file(str(unvalid_employee))
                    # if incrementally:
                    #     for employee_uid in employee_uids:
                    #         self.solution.store_solution_vars(solution, employee_uid)
                    # else:
                    self.solution.store_solution_vars(solution=solution_temp, employee_uid=unvalid_employee)
                    for day in range(self.instance.number_of_days):
                        self.solution.work_vars.pop((day, unvalid_employee))
                else:
                    print(f"Error solving for employee x {unvalid_employee}: ")
            #     if len(employee_uids) > 1:
            #         Solution.delete_json_solution(str(employee_uids[-2]))
            # Solution.delete_json_solution(str(employee_uids[-1]))


            solver_1 = Solver(self.instance, shift_vars.Shift_vars(self.instance))
            self.solution = solver_1.warm_start_generalized(hard_constraint_solution=self.solution.model_copy(deep=True), max_time_in_seconds=120, objective_function=solver_1.objective_value_new).model_copy(deep=True)
            end_time = time.time()
            print(end_time - start_time)
            self.solution.solve_time = end_time - start_time
            self.solution.to_json_file(self.instance.name + "methodex")



            del solver_1

            solver_1 = Solver(self.instance, shift_vars.Shift_vars(self.instance))
            self.solution = solver_1.warm_start_generalized(hint_solution=self.solution.model_copy(deep=True), max_time_in_seconds=120, objective_function=solver_1.objective_value_new).model_copy(deep=True)
            end_time = time.time()
            print(end_time - start_time)
            self.solution.solve_time = end_time - start_time
            self.solution.to_json_file(self.instance.name + "methodex_till450")











    def solve_employee_sub_(self, employee_uid, instance_data, solution_name, soft_max_time_in_seconds:int=60):
        start_time=time.time()
        
        instance = self.instance.model_copy()
        instance.employees = {int(employee_uid): instance.employees[int(employee_uid)]}
        
        solution_one_shift_type = self.solution

        # Create your ShiftVars and Solver as before
        solver = Solver(instance, Shift_vars(instance))
        stop_after_first_solution = True
        if soft_max_time_in_seconds <= 8:
            soft_max_time_in_seconds = 450
            stop_after_first_solution = True

        solution = solver.warm_start_generalized(hard_constraint_solution=solution_one_shift_type,
            disabled_constraints=[SolverConstraints.cover_requirements],
            objective_function=solver.objective_value_new,
            log_search_progress=False,
            max_time_in_seconds=soft_max_time_in_seconds,
            stop_after_first_solution=stop_after_first_solution
        )

        solve_normally = False
        if solution.solve_status in [cp_model.UNKNOWN, cp_model.INFEASIBLE]:
            solve_normally = True
        
        if solve_normally:
            #TODO you should create new solvers for the others files and functions
            solver_x = Solver(instance, Shift_vars(instance))
            solution1 = solver_x.solve_callback_with_solution(
                objective_function=solver_x.objective_value_only_wishes,
                log_search_progress=False,
                max_time_in_seconds=450,
                stop_after_first_solution=True
            )
            #TODO Unknown to check if an employee was bad (should find a better way in the feature)
            solution1.solve_status = cp_model.UNKNOWN
            print(f"solution of {cp_model.UNKNOWN}")
            end_time=time.time()
            print(end_time - start_time)
            print(solution1.solve_status)
            return solution1
        end_time=time.time()
        print(end_time - start_time)
        return solution






    
    #TODO test which is faster for first solution handling each employee on there own or first one shift type  and then one employee
    def solve_employee_sub(self, employee_uid, instance_data, solution_name, soft_max_time_in_seconds:int=60):
        # Load instance from passed data
        start_time=time.time()
        DATA_DIR = (
            Path(__file__).resolve().parent.parent / "data" / "instance_raw"
        )
        instance_data = instance_data + ".txt"
        path = DATA_DIR / instance_data
        instance = parseTXT.parse_txt(path)
        instance.employees = {int(employee_uid): instance.employees[int(employee_uid)]}
        
        solution_one_shift_type = self.solution

        # Create your ShiftVars and Solver as before
        solver_ = Solver(instance, Shift_vars(instance))
        stop_after_first_solution = True
        if soft_max_time_in_seconds <= 8:
            soft_max_time_in_seconds = 450
            stop_after_first_solution = True

        solution = solver_.test_solution_validity(solution=solution_one_shift_type,
            disabled_constraints=[SolverConstraints.cover_requirements],
            objective_function=solver_.objective_value_new,
            log_search_progress=False,
            max_time_in_seconds=soft_max_time_in_seconds,
            stop_after_first_solution=False
        )

        solve_normally = False
        if solution.solve_status in [cp_model.UNKNOWN, cp_model.INFEASIBLE]:
            solve_normally = True
        end_time=time.time()
        if solve_normally:
            del solution
            del solver_
            instance1 = parseTXT.parse_txt(path)
            instance1.employees = {int(employee_uid): instance1.employees[int(employee_uid)]}
            #TODO you should create new solvers for the others files and functions
            solver_x = Solver(instance1, Shift_vars(instance1))
            solution1 = solver_x.solve_callback_with_solution(
                objective_function=solver_x.objective_value_only_wishes,
                log_search_progress=False,
                max_time_in_seconds=450,
                stop_after_first_solution=True
            )
            #TODO Unknown to check if an employee was bad (should find a better way in the feature)
            solution1.solve_status = cp_model.UNKNOWN
            end_time=time.time()
            print(end_time - start_time)
            print(solution1.solve_status)
            return solution1
        print(end_time - start_time)
        return solution