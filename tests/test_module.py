from cpsat_utils.testing import AssertModelInfeasible

from src import shift_vars
from src.inputTypes import employee, instace, shiftType
from src.module import shift_assignment_single_day_validation


def test_shift_assignment_single_day_validation():
    with AssertModelInfeasible() as model:
        # build a model that is supposed to be feasible
        # if the model is infeasible, the context manager will raise an error
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
