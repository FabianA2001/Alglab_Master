import pytest
from cpsat_utils.testing import AssertModelInfeasible

from src.inputTypes import employee, instace, shiftType
from src.LNS.solver_for_window import Config_for_employee, Solver_for_window
from src.shift_vars import Shift_vars


def test_add_start_maximum_consecutive_shifts_constraints():
    lokal_shift_types = [shiftType.ShiftType() for _ in range(1)]
    lokal_employee = employee.Employee()
    instance = instace.Instance.create(
        number_of_days=4,
        shift_typs=lokal_shift_types,
        emplyees=[lokal_employee],
    )
    config = {lokal_employee.uid: Config_for_employee()}
    config[lokal_employee.uid].max_consecutive_shifts_start = 2

    with AssertModelInfeasible() as model:
        solv = Solver_for_window(
            instance,
            Shift_vars(instance, model=model),
            config=config,
        )
        solv.add_start_maximum_consecutive_shifts_constraints(lokal_employee.uid, 2)
        for day in range(3):
            model.Add(
                solv.vars.get_var(day, lokal_shift_types[0].uid, lokal_employee.uid)
                == 1
            )


def test_add_end_maximum_consecutive_shifts_constraints():
    lokal_shift_types = [shiftType.ShiftType() for _ in range(1)]
    lokal_employee = employee.Employee()
    instance = instace.Instance.create(
        number_of_days=4,
        shift_typs=lokal_shift_types,
        emplyees=[lokal_employee],
    )
    config = {lokal_employee.uid: Config_for_employee()}
    config[lokal_employee.uid].max_consecutive_shifts_end = 2

    with AssertModelInfeasible() as model:
        solv = Solver_for_window(
            instance,
            Shift_vars(instance, model=model),
            config=config,
        )
        solv.add_end_maximum_consecutive_shifts_constraints(lokal_employee.uid, 2)
        # Erzwinge Schichten an den letzten 3 Tagen (Tage 1, 2, 3)
        for day in range(1, 4):
            model.Add(
                solv.vars.get_var(day, lokal_shift_types[0].uid, lokal_employee.uid)
                == 1
            )


@pytest.mark.parametrize(
    "min_consecutive,day0_value,day1_value",
    [
        (2, 0, 0),
        (2, 1, 0),
    ],
)
def test_add_start_minimum_consecutive_shifts_constraints(
    min_consecutive, day0_value, day1_value
):
    lokal_shift_types = [shiftType.ShiftType() for _ in range(1)]
    lokal_employee = employee.Employee()
    instance = instace.Instance.create(
        number_of_days=5,
        shift_typs=lokal_shift_types,
        emplyees=[lokal_employee],
    )
    config = {lokal_employee.uid: Config_for_employee()}
    config[lokal_employee.uid].min_consecutive_shifts_start = min_consecutive

    with AssertModelInfeasible() as model:
        solv = Solver_for_window(
            instance,
            Shift_vars(instance, model=model),
            config=config,
        )
        solv.add_start_minimum_consecutive_shifts_constraints(
            lokal_employee.uid, min_consecutive
        )
        # Erzwinge Schichten gemäß Parametern
        model.Add(
            solv.vars.get_var(0, lokal_shift_types[0].uid, lokal_employee.uid)
            == day0_value
        )
        model.Add(
            solv.vars.get_var(1, lokal_shift_types[0].uid, lokal_employee.uid)
            == day1_value
        )


@pytest.mark.parametrize(
    "min_consecutive,day3_value,day4_value",
    [
        (2, 0, 0),
        (2, 0, 1),
    ],
)
def test_add_end_minimum_consecutive_shifts_constraints(
    min_consecutive, day3_value, day4_value
):
    lokal_shift_types = [shiftType.ShiftType() for _ in range(1)]
    lokal_employee = employee.Employee()
    instance = instace.Instance.create(
        number_of_days=5,
        shift_typs=lokal_shift_types,
        emplyees=[lokal_employee],
    )
    config = {lokal_employee.uid: Config_for_employee()}
    config[lokal_employee.uid].min_consecutive_shifts_end = min_consecutive

    with AssertModelInfeasible() as model:
        solv = Solver_for_window(
            instance,
            Shift_vars(instance, model=model),
            config=config,
        )
        solv.add_end_minimum_consecutive_shifts_constraints(
            lokal_employee.uid, min_consecutive
        )
        # Erzwinge Schichten gemäß Parametern
        model.Add(
            solv.vars.get_var(3, lokal_shift_types[0].uid, lokal_employee.uid)
            == day3_value
        )
        model.Add(
            solv.vars.get_var(4, lokal_shift_types[0].uid, lokal_employee.uid)
            == day4_value
        )


@pytest.mark.parametrize(
    "min_consecutive,day0_value,day1_value",
    [
        (2, 1, 1),
        (2, 1, 0),
    ],
)
def test_add_start_minimum_consecutive_days_off_constraints(
    min_consecutive, day0_value, day1_value
):
    lokal_shift_types = [shiftType.ShiftType() for _ in range(1)]
    lokal_employee = employee.Employee()
    instance = instace.Instance.create(
        number_of_days=5,
        shift_typs=lokal_shift_types,
        emplyees=[lokal_employee],
    )
    config = {lokal_employee.uid: Config_for_employee()}
    config[lokal_employee.uid].min_consecutive_days_off_start = min_consecutive

    with AssertModelInfeasible() as model:
        solv = Solver_for_window(
            instance,
            Shift_vars(instance, model=model),
            config=config,
        )
        solv.add_start_minimum_consecutive_days_off_constraints(
            lokal_employee.uid, min_consecutive
        )
        # Erzwinge Schichten gemäß Parametern
        model.Add(
            solv.vars.get_var(1, lokal_shift_types[0].uid, lokal_employee.uid)
            == day0_value
        )
        model.Add(
            solv.vars.get_var(2, lokal_shift_types[0].uid, lokal_employee.uid)
            == day1_value
        )


@pytest.mark.parametrize(
    "min_consecutive,day3_value,day4_value",
    [
        (2, 0, 1),
        (2, 1, 0),
    ],
)
def test_add_end_minimum_consecutive_days_off_constraints(
    min_consecutive, day3_value, day4_value
):
    lokal_shift_types = [shiftType.ShiftType() for _ in range(1)]
    lokal_employee = employee.Employee()
    instance = instace.Instance.create(
        number_of_days=5,
        shift_typs=lokal_shift_types,
        emplyees=[lokal_employee],
    )
    config = {lokal_employee.uid: Config_for_employee()}
    config[lokal_employee.uid].min_consecutive_days_off_end = min_consecutive

    with AssertModelInfeasible() as model:
        solv = Solver_for_window(
            instance,
            Shift_vars(instance, model=model),
            config=config,
        )
        solv.add_end_minimum_consecutive_days_off_constraints(
            lokal_employee.uid, min_consecutive
        )
        # Erzwinge Schichten gemäß Parametern
        model.Add(
            solv.vars.get_var(3, lokal_shift_types[0].uid, lokal_employee.uid)
            == day3_value
        )
        model.Add(
            solv.vars.get_var(4, lokal_shift_types[0].uid, lokal_employee.uid)
            == day4_value
        )
