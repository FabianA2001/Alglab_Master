from ortools.sat.python import cp_model

from .. import shift_vars
from ..inputTypes import instace
from .shift_assignment_module import ShiftAssignmentModule


class Max_Cons_Shifts(ShiftAssignmentModule):
    def build(
        self,
        instance: instace.Instance,
        vars: shift_vars.Shift_vars,
    ) -> cp_model.LinearExprT:
        for employee_uid in instance.employees:
            for day in range(
                instance.number_of_days
                - instance.employees[employee_uid].max_number_consecutive_shifts
            ):
                assigned_shifts = []
                for type_uid in instance.shifts[day]:
                    for i in range(
                        instance.employees[employee_uid].max_number_consecutive_shifts
                        + 1
                    ):
                        assigned_shifts.append(
                            vars.vars[(day + i, type_uid, employee_uid)]
                        )

                vars.model.Add(
                    sum(assigned_shifts)
                    <= instance.employees[employee_uid].max_number_consecutive_shifts
                )
        return 0
