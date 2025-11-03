from ortools.sat.python import cp_model

from .. import shift_vars
from ..inputTypes import instace
from .shift_assignment_module import ShiftAssignmentModule


class Shift_rotation_constraint(ShiftAssignmentModule):
    def build(
        self, instance: instace.Instance, vars: shift_vars.Shift_vars
    ) -> cp_model.LinearExprT:
        for employee_uid in instance.employees:
            for day in range(instance.number_of_days - 1):
                # assigned_shifts = []
                for type_uid in instance.shifts[day]:
                    # assigned_shifts.append(vars.vars[(day, type_uid, employee_uid)])
                    for btype_uid in instance.shift_types[
                        type_uid
                    ].blocked_shifts_after:
                        # incorrect because more shift combination are being denied
                        # assigned_shifts.append(
                        #     vars.vars[(day + 1, btype_uid, employee_uid)]
                        # )
                        vars.model.AddAtMostOne(
                            vars.vars[(day, type_uid, employee_uid)],
                            vars.vars[(day + 1, btype_uid, employee_uid)],
                        )

        return 0
