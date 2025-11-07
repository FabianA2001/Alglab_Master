from ortools.sat.python import cp_model

from .. import shift_vars
from ..inputTypes import instace
from .shift_assignment_module import ShiftAssignmentModule


class Days_off(ShiftAssignmentModule):
    def build(
        self,
        instance: instace.Instance,
        vars: shift_vars.Shift_vars,
    ) -> cp_model.LinearExprT:
        for employee_uid in instance.employees:
            assigned_shifts = []
            for day in instance.employees[employee_uid].blocked_shifts:
                for type_uid in instance.shifts[day]:
                    assigned_shifts.append(vars.vars[(day, type_uid, employee_uid)])

            vars.model.Add(sum(assigned_shifts) == 0)
        return 0
