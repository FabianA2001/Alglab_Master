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
            #TODO is a constraint with 1 consecutive working day meaningful?
            for day_s in range(instance.employees[employee_uid].min_number_consecutive_days_off -1):
                assigned_shifts = []
                assigned_shifts_inner_interval = []
                assigned_shifts_interval_end = []
                for day_d in range(instance.number_of_days - (day_s + 1)):
                    for type_uid in instance.shift_types:
                        assigned_shifts.append(vars.vars[(day_d, type_uid, employee_uid)])
                        for day_j in range(day_d + 1, day_d + day_s + 1):
                            assigned_shifts_inner_interval.append(vars.vars[(day_j, type_uid, employee_uid)])
                        assigned_shifts_interval_end.append(vars.vars[(day_d + day_s + 1, type_uid, employee_uid)])
                    
                    vars.model.add(1 - (sum(assigned_shifts)) + sum(assigned_shifts_inner_interval) 
                                   + 1 - (sum(assigned_shifts_interval_end)) > 0)
        return 0
