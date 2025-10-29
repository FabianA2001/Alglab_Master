from ortools.sat.python import cp_model

from .. import shift_vars
from ..inputTypes import instace
from .shift_assignment_module import ShiftAssignmentModule


class Single_day_validation(ShiftAssignmentModule):
    def build(
        self,
        instance: instace.Instance,
        vars: shift_vars.Shift_vars,
    ) -> cp_model.LinearExprT:
        for employee_uid in instance.employees:
            for day in range(instance.number_of_days):
                assigned_shifts = []
                for type_uid in instance.shifts[day]:
                    assigned_shifts.append(vars.vars[(day, type_uid, employee_uid)])
                # Ensure that at most one shift is assigned to the employee on this day
                vars.model.AddAtMostOne(assigned_shifts)
        return 0
