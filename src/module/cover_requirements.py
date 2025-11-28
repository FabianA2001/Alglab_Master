from ortools.sat.python import cp_model

from .. import shift_vars
from ..inputTypes import instace
from .shift_assignment_module import ShiftAssignmentModule
from ortools.sat.python import cp_model

# Die benutzten vars stimmen nicht mit den vorraussetzungen überein


class Cover_requirements(ShiftAssignmentModule):
    def build(
        self,
        instance: instace.Instance,
        vars: shift_vars.Shift_vars,
    ) -> cp_model.LinearExprT:
        for day in range(instance.number_of_days):
            for type_uid in instance.shifts[day]:
                assigned_shifts = []
                for employee_uid in instance.employees:
                    assigned_shifts.append(vars.vars[(day, type_uid, employee_uid)])

                vars.model.Add(
                    (
                        sum(assigned_shifts)
                        - vars.above_prefferd_vars[(day, type_uid)]
                        + vars.below_prefferd_vars[(day, type_uid)]
                    )
                    == instance.shifts[day][type_uid].preffert_number_employees
                )
                vars.model.Add(
                    3
                    * (
                        sum(assigned_shifts)
                        + vars.below_threshold_vars[(day, type_uid)]
                    )
                    >= 2 * instance.shifts[day][type_uid].preffert_number_employees
                )
        return 0
