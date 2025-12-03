import pytest

from src.inputTypes import employee, instace, shiftType
from src.LNS.slice_instance import Slice_instance
from src.solution import Solution


class Test_slice_instance_assigned:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.lokal_shift_types = shiftType.ShiftType()
        self.lokal_employee = employee.Employee()
        instance = instace.Instance.create(
            number_of_days=9,
            shift_typs=[self.lokal_shift_types],
            emplyees=[self.lokal_employee],
        )
        solution = Solution(instance)
        for day in range(9):
            if (day >= 1 and day <= 2) or (day >= 6 and day <= 7):
                solution.set_var(
                    day, self.lokal_shift_types.uid, self.lokal_employee.uid, 1
                )
            else:
                solution.set_var(
                    day, self.lokal_shift_types.uid, self.lokal_employee.uid, 0
                )

        self.slice_instance = Slice_instance(solution, start=3, end=5)

    def test_count_assigned_shifts_start(self):
        assert (
            self.slice_instance.count_assigned_shifts_start(self.lokal_employee.uid)
            == 2
        )

    def test_count_assigned_shifts_end(self):
        assert (
            self.slice_instance.count_assigned_shifts_end(self.lokal_employee.uid) == 2
        )


class Test_slice_instance_not_assigned:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.lokal_shift_types = shiftType.ShiftType()
        self.lokal_employee = employee.Employee()
        instance = instace.Instance.create(
            number_of_days=9,
            shift_typs=[self.lokal_shift_types],
            emplyees=[self.lokal_employee],
        )
        solution = Solution(instance)
        for day in range(9):
            if (day >= 1 and day <= 2) or (day >= 6 and day <= 7):
                solution.set_var(
                    day, self.lokal_shift_types.uid, self.lokal_employee.uid, 0
                )
            else:
                solution.set_var(
                    day, self.lokal_shift_types.uid, self.lokal_employee.uid, 1
                )

        self.slice_instance = Slice_instance(solution, start=3, end=5)

    def test_count_not_assigned_shifts_start(self):
        assert (
            self.slice_instance.count_not_assigned_shifts_start(self.lokal_employee.uid)
            == 2
        )

    def test_count_not_assigned_shifts_end(self):
        assert (
            self.slice_instance.count_not_assigned_shifts_end(self.lokal_employee.uid)
            == 2
        )
