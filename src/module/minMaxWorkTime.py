from ortools.sat.python import cp_model

from .. import shift_vars
from ..inputTypes import instace
from .shift_assignment_module import ShiftAssignmentModule


class MinMaxWorkTime(ShiftAssignmentModule):
    def build(
        self,
        instance: instace.Instance,
        vars: shift_vars.Shift_vars,
    ) -> cp_model.LinearExprT:
        for employee_uid in instance.employees:
            assigned_minutes = 0
            for day in range(instance.number_of_days):
                for type_uid in instance.shifts[day]:
                    assigned_minutes += (vars.vars[(day, type_uid, employee_uid)]
                                         )*instance.shift_types[type_uid].length

            vars.model.Add(
                assigned_minutes <= instance.employees[employee_uid].max_minutes_assigned)
            vars.model.Add(
                assigned_minutes >= instance.employees[employee_uid].min_minutes_assigned)

        return 0
