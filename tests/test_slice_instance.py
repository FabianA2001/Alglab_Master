from src.inputTypes import employee, instace, shiftType
from src.LNS.slice_instance import Slice_instance
from src.solution import Solution


def test_count_assigned_shifts_start():
    lokal_shift_types = shiftType.ShiftType()
    lokal_employee = employee.Employee()
    instance = instace.Instance.create(
        number_of_days=7,
        shift_typs=[lokal_shift_types],
        emplyees=[lokal_employee],
    )
    solution = Solution(instance)
    for day in range(7):
        if day >= 1 and day <= 2:
            solution.set_var(day, lokal_shift_types.uid, lokal_employee.uid, 1)
        else:
            solution.set_var(day, lokal_shift_types.uid, lokal_employee.uid, 0)

    si = Slice_instance(solution, start=3, end=5)
    assert si.count_assigned_shifts_start(lokal_employee.uid) == 2
