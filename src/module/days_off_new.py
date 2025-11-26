from ortools.sat.python import cp_model

from .. import shift_vars
from ..inputTypes import instace
from .shift_assignment_module import ShiftAssignmentModule


class Days_off_new(ShiftAssignmentModule):
    def build(
        self,
        instance: instace.Instance,
        vars: shift_vars.Shift_vars,
    ) -> cp_model.LinearExprT:
        for employee_uid in instance.employees:
            for day in instance.employees[employee_uid].blocked_shifts:
                vars.model.Add(vars.work_vars[(day, employee_uid)] == 0)
        return 0
