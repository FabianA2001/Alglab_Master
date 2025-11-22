from cpsat_utils.testing import AssertModelInfeasible

from src.inputTypes import employee, instace, shiftType
from src.LNS.solver_for_window import Solver_for_window
from src.shift_vars import Shift_vars

# @pytest.fixture
# def mock_instance():
#     lokal_shift_types = [shiftType.ShiftType() for _ in range(1)]
#     lokal_employee = employee.Employee()
#     instance = instace.Instance.create(
#         number_of_days=4,
#         shift_typs=lokal_shift_types,
#         emplyees=[lokal_employee],
#     )

#     return instance


def test_add_start_maximum_consecutive_shifts_constraints():
    lokal_shift_types = [shiftType.ShiftType() for _ in range(1)]
    lokal_employee = employee.Employee()
    instance = instace.Instance.create(
        number_of_days=4,
        shift_typs=lokal_shift_types,
        emplyees=[lokal_employee],
    )

    with AssertModelInfeasible() as model:
        solv = Solver_for_window(
            instance,
            Shift_vars(instance, model=model),
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

    with AssertModelInfeasible() as model:
        solv = Solver_for_window(
            instance,
            Shift_vars(instance, model=model),
        )
        solv.add_end_maximum_consecutive_shifts_constraints(lokal_employee.uid, 2)
        # Erzwinge Schichten an den letzten 3 Tagen (Tage 1, 2, 3)
        for day in range(1, 4):
            model.Add(
                solv.vars.get_var(day, lokal_shift_types[0].uid, lokal_employee.uid)
                == 1
            )


def test_add_start_minimum_consecutive_shifts_constraints():
    lokal_shift_types = [shiftType.ShiftType() for _ in range(1)]
    lokal_employee = employee.Employee()
    instance = instace.Instance.create(
        number_of_days=5,
        shift_typs=lokal_shift_types,
        emplyees=[lokal_employee],
    )

    with AssertModelInfeasible() as model:
        solv = Solver_for_window(
            instance,
            Shift_vars(instance, model=model),
        )
        solv.add_start_minimum_consecutive_shifts_constraints(lokal_employee.uid, 3)
        # Erzwinge eine Schicht an Tag 0, aber keine an Tag 1
        # Das verletzt die Minimum-Constraint (min 3 aufeinanderfolgende)
        model.Add(
            solv.vars.get_var(0, lokal_shift_types[0].uid, lokal_employee.uid) == 1
        )
        model.Add(
            solv.vars.get_var(1, lokal_shift_types[0].uid, lokal_employee.uid) == 0
        )


def test_add_end_minimum_consecutive_shifts_constraints():
    lokal_shift_types = [shiftType.ShiftType() for _ in range(1)]
    lokal_employee = employee.Employee()
    instance = instace.Instance.create(
        number_of_days=5,
        shift_typs=lokal_shift_types,
        emplyees=[lokal_employee],
    )

    with AssertModelInfeasible() as model:
        solv = Solver_for_window(
            instance,
            Shift_vars(instance, model=model),
        )
        solv.add_end_minimum_consecutive_shifts_constraints(lokal_employee.uid, 3)
        # Erzwinge eine Schicht an Tag 4 (letzter Tag), aber keine an Tag 3
        # Das verletzt die Minimum-Constraint (min 3 aufeinanderfolgende am Ende)
        model.Add(
            solv.vars.get_var(4, lokal_shift_types[0].uid, lokal_employee.uid) == 1
        )
        model.Add(
            solv.vars.get_var(3, lokal_shift_types[0].uid, lokal_employee.uid) == 0
        )


def test_add_start_minimum_consecutive_days_off_constraints():
    lokal_shift_types = [shiftType.ShiftType() for _ in range(1)]
    lokal_employee = employee.Employee()
    instance = instace.Instance.create(
        number_of_days=5,
        shift_typs=lokal_shift_types,
        emplyees=[lokal_employee],
    )

    with AssertModelInfeasible() as model:
        solv = Solver_for_window(
            instance,
            Shift_vars(instance, model=model),
        )
        solv.add_start_minimum_consecutive_days_off_constraints(lokal_employee.uid, 3)
        # Erzwinge keinen Dienst an Tag 0 (frei), aber Dienst an Tag 1
        # Das verletzt die Minimum-Constraint (min 3 aufeinanderfolgende freie Tage)
        model.Add(
            solv.vars.get_var(0, lokal_shift_types[0].uid, lokal_employee.uid) == 0
        )
        model.Add(
            solv.vars.get_var(1, lokal_shift_types[0].uid, lokal_employee.uid) == 1
        )


def test_add_end_minimum_consecutive_days_off_constraints():
    lokal_shift_types = [shiftType.ShiftType() for _ in range(1)]
    lokal_employee = employee.Employee()
    instance = instace.Instance.create(
        number_of_days=5,
        shift_typs=lokal_shift_types,
        emplyees=[lokal_employee],
    )

    with AssertModelInfeasible() as model:
        solv = Solver_for_window(
            instance,
            Shift_vars(instance, model=model),
        )
        solv.add_end_minimum_consecutive_days_off_constraints(lokal_employee.uid, 3)
        # Erzwinge keinen Dienst an Tag 4 (letzter Tag frei), aber Dienst an Tag 3
        # Das verletzt die Minimum-Constraint (min 3 aufeinanderfolgende freie Tage am Ende)
        model.Add(
            solv.vars.get_var(4, lokal_shift_types[0].uid, lokal_employee.uid) == 0
        )
        model.Add(
            solv.vars.get_var(3, lokal_shift_types[0].uid, lokal_employee.uid) == 1
        )
