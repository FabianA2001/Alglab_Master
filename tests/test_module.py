from cpsat_utils.testing import AssertModelInfeasible

from src import shift_vars
from src.inputTypes import employee, instace, shiftType
from src.module import shift_assignment_single_day_validation, shift_rotation_constraint


def test_single_day_validation():
    with AssertModelInfeasible() as model:
        lokal_shift_types = [shiftType.ShiftType() for _ in range(2)]
        lokal_employee = employee.Employee()
        instance = instace.Instance(
            number_of_days=1,
            shift_typs=lokal_shift_types,
            emplyees=[lokal_employee],
        )
        vars = shift_vars.Shift_vars(instance, model)
        shift_assignment_single_day_validation.Single_day_validation().build(
            instance, vars
        )
        for type_uid in lokal_shift_types:
            model.Add(vars.vars[(0, type_uid.uid, lokal_employee.uid)] == 1)


def test_shift_rotation():
    with AssertModelInfeasible() as model:
        lokal_shift_types = [shiftType.ShiftType() for _ in range(2)]
        # set second shift type to be blocked after first
        lokal_shift_types[0].blocked_shifts_after.add(lokal_shift_types[1].uid)
        lokal_employee = employee.Employee()
        instance = instace.Instance(
            number_of_days=2,
            shift_typs=lokal_shift_types,
            emplyees=[lokal_employee],
        )
        vars = shift_vars.Shift_vars(instance, model)
        shift_rotation_constraint.Shift_rotation_constraint().build(instance, vars)

        model.Add(vars.vars[(0, lokal_shift_types[0].uid, lokal_employee.uid)] == 1)
        model.Add(vars.vars[(1, lokal_shift_types[1].uid, lokal_employee.uid)] == 1)
