from ortools.sat.python import cp_model

from .. import shift_vars
from ..inputTypes import instace
from .shift_assignment_module import ShiftAssignmentModule


class Minimum_consecutive_days_off(ShiftAssignmentModule):
    def build(
        self,
        instance: instace.Instance,
        vars: shift_vars.Shift_vars,
    ) -> cp_model.LinearExprT:
        for employee_uid in instance.employees:
            #TODO min_number_consecutive_shifts should have the default value of 2?
            # because 1 or less mean that an employee is not allowed to have any shifts.
            for day_s in range(instance.employees[employee_uid].min_number_consecutive_days_off -1 -1):
                assigned_shifts = []
                assigned_shift_j_limited_days = []
                assigned_shift_s_limited_days = []
                for day_d in range(instance.number_of_days - (day_s + 1) -1):
                    for type_uid in instance.shift_types:
                        assigned_shifts.append(vars.vars[(day_d, type_uid, employee_uid)])
                        for day_j in range(day_d + 1, day_d + day_s):
                            assigned_shift_j_limited_days.append(vars.vars[(day_j, type_uid, employee_uid)])
                        assigned_shift_s_limited_days.append(vars.vars[(day_d + day_s + 1, type_uid, employee_uid)])
                    
                    vars.model.add(1 - (sum(assigned_shifts)) + sum(assigned_shift_j_limited_days ) 
                                   + 1 - (sum(assigned_shift_s_limited_days)) > 0)
        return 0
