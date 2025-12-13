from datetime import datetime

from typing import Callable, List
from pydantic import BaseModel, Field, model_validator

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


# employee.blocked_shifts (off days)

class valid_solution_greedy(BaseModel):
    def __init__(self, instance: instace.Instance, vars: shift_vars.Shift_vars):
        self.instance = instance
        self.vars = vars
        self.solution_dict = {}
        self.current_scores = {}

    def get_score_for(self, day: int, EmployeeUid : employee.EmployeeUid, shiftType: shiftType.TypeUid) -> int:
        return self.current_scores[(day, EmployeeUid, shiftType)]
    
    def set_score_for(self, day: int, EmployeeUid : employee.EmployeeUid, shiftType: shiftType.TypeUid, score):
        self.current_scores[(day, EmployeeUid, shiftType)] = score

    def set_solution_dict_for(self, day: int, EmployeeUid : employee.EmployeeUid, shiftType: shiftType.TypeUid, assignment: bool):
        self.solution_dict[(day, EmployeeUid, shiftType)] = assignment
    
    def get_solution_dict_for(self, day: int, EmployeeUid : employee.EmployeeUid, shiftType: shiftType.TypeUid) -> bool:
        return self.solution_dict[(day, EmployeeUid, shiftType)]

    def get_day_min_max_consecutive_shifts_allowed(self, day: int, EmployeeUid : employee.EmployeeUid):
        current_employee = self.instance.employees[EmployeeUid]
        if day in current_employee.blocked_shifts:
            return [-1, -1]

        for current_day in range(day, day+current_employee.min_number_consecutive_shifts):
            if current_day in current_employee.blocked_shifts:
                return [-1, -1]
            
        if day+current_employee.min_number_consecutive_shifts == day+current_employee.max_number_consecutive_shifts:
            return [day+current_employee.min_number_consecutive_shifts, day+current_employee.max_number_consecutive_shifts]
        for current_day in range(day+current_employee.min_number_consecutive_shifts, day+current_employee.max_number_consecutive_shifts):
            if current_day in current_employee.blocked_shifts:
                return [day+current_employee.min_number_consecutive_shifts, day+current_employee.max_number_consecutive_shifts-1]
        print(f'something went wrong: \n day - {day}\nemployee - {self.instance.employees[EmployeeUid].name}')
        exit()

    def get_score_min_max(self, day: int, EmployeeUid : employee.EmployeeUid, min_max_consecutive_shifts: List[int]):
        
        # just assign a shift if it is
        for in min:
            for shiftTypeUID, shift in self.instance.shifts[day].items():
                if EmployeeUid in shift.penalty_assigned_day_employee:

    # fix shifts assignment created in get_score_min_max
    def fix_shifts_assignment(self):



    instance: instace.Instance = Field(
            description="An instance that contains all given variables",
        )