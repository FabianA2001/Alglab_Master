from unittest.mock import patch

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

        # Mock the solver and window instance creation to speed up tests
        with patch.object(
            Slice_instance, "__init__", lambda self, sol, start, end: None
        ):
            self.slice_instance = Slice_instance(solution, start=3, end=5)
            # Manually set only the attributes needed for counting methods
            self.slice_instance.sol = solution
            self.slice_instance.inst = instance
            self.slice_instance.start_day = 3
            self.slice_instance.end_day = 5

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

        # Mock the solver and window instance creation to speed up tests
        with patch.object(
            Slice_instance, "__init__", lambda self, sol, start, end: None
        ):
            self.slice_instance = Slice_instance(solution, start=3, end=5)
            # Manually set only the attributes needed for counting methods
            self.slice_instance.sol = solution
            self.slice_instance.inst = instance
            self.slice_instance.start_day = 3
            self.slice_instance.end_day = 5

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


class Test_slice_instance_count_days_off:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.lokal_shift_types = shiftType.ShiftType()
        self.lokal_employee = employee.Employee()
        self.instance = instace.Instance.create(
            number_of_days=9,
            shift_typs=[self.lokal_shift_types],
            emplyees=[self.lokal_employee],
        )
        self.solution = Solution(self.instance)

    def get_slice_instance(self, start: int = 3, end: int = 5):
        # Mock the solver and window instance creation to speed up tests
        with patch.object(
            Slice_instance, "__init__", lambda self, sol, start, end: None
        ):
            self.slice_instance = Slice_instance(self.solution, start=start, end=end)
            # Manually set only the attributes needed for counting methods
            self.slice_instance.sol = self.solution
            self.slice_instance.inst = self.instance
            self.slice_instance.start_day = start
            self.slice_instance.end_day = end
        return self.slice_instance

    def test_count_days_off_1(self):
        self.lokal_employee.min_number_consecutive_days_off = 3
        for day in range(9):
            self.solution.set_var(
                day, self.lokal_shift_types.uid, self.lokal_employee.uid, 0
            )

        count_start, count_end = self.get_slice_instance(
            start=3, end=6
        ).calulate_minimum_consecutive_days_off_config(
            self.lokal_employee.uid, self.lokal_employee
        )
        assert count_start == -1
        assert count_end == -1

    def test_count_days_off_2(self):
        self.lokal_employee.min_number_consecutive_days_off = 2
        for day in range(9):
            if day in [0, 1, 8]:
                self.solution.set_var(
                    day, self.lokal_shift_types.uid, self.lokal_employee.uid, 1
                )
            else:
                self.solution.set_var(
                    day, self.lokal_shift_types.uid, self.lokal_employee.uid, 0
                )

        count_start, count_end = self.get_slice_instance(
            start=3, end=6
        ).calulate_minimum_consecutive_days_off_config(
            self.lokal_employee.uid, self.lokal_employee
        )
        assert count_start == 1
        assert count_end == 1

    def test_count_days_off_3(self):
        self.lokal_employee.min_number_consecutive_days_off = 2
        for day in range(9):
            if day in [0, 1, 2, 7, 8]:
                self.solution.set_var(
                    day, self.lokal_shift_types.uid, self.lokal_employee.uid, 1
                )
            else:
                self.solution.set_var(
                    day, self.lokal_shift_types.uid, self.lokal_employee.uid, 0
                )

        si = self.get_slice_instance(start=3, end=6)
        assert si.count_not_assigned_shifts_start(self.lokal_employee.uid) == 0, (
            "error in count not assined shifts start"
        )

        count_start, count_end = si.calulate_minimum_consecutive_days_off_config(
            self.lokal_employee.uid, self.lokal_employee
        )
        assert count_start == -2, "start"
        assert count_end == -2, "end"

    def test_count_days_off_4(self):
        self.lokal_employee.min_number_consecutive_days_off = 2
        for day in range(9):
            if day in [0, 8]:
                self.solution.set_var(
                    day, self.lokal_shift_types.uid, self.lokal_employee.uid, 1
                )
            else:
                self.solution.set_var(
                    day, self.lokal_shift_types.uid, self.lokal_employee.uid, 0
                )

        si = self.get_slice_instance(start=3, end=5)
        assert si.count_not_assigned_shifts_start(self.lokal_employee.uid) == 2, (
            "error in count not assined shifts start"
        )

        count_start, count_end = si.calulate_minimum_consecutive_days_off_config(
            self.lokal_employee.uid, self.lokal_employee
        )
        assert count_start == 0, "start"
        assert count_end == 0, "end"


class Test_slice_instance_min_days:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.lokal_shift_types = shiftType.ShiftType()
        self.lokal_employee = employee.Employee()
        self.instance = instace.Instance.create(
            number_of_days=10,
            shift_typs=[self.lokal_shift_types],
            emplyees=[self.lokal_employee],
        )
        self.solution = Solution(self.instance)

    def get_slice_instance(self, start: int = 3, end: int = 5):
        # Mock the solver and window instance creation to speed up tests
        with patch.object(
            Slice_instance, "__init__", lambda self, sol, start, end: None
        ):
            self.slice_instance = Slice_instance(self.solution, start=start, end=end)
            # Manually set only the attributes needed for counting methods
            self.slice_instance.sol = self.solution
            self.slice_instance.inst = self.instance
            self.slice_instance.start_day = start
            self.slice_instance.end_day = end
        return self.slice_instance

    def test_count_min_days_1(self):
        self.lokal_employee.min_number_consecutive_shifts = 3
        for day in range(10):
            if day in [1, 2, 7, 8]:
                self.solution.set_var(
                    day, self.lokal_shift_types.uid, self.lokal_employee.uid, 1
                )
            else:
                self.solution.set_var(
                    day, self.lokal_shift_types.uid, self.lokal_employee.uid, 0
                )

        count_start, count_end = self.get_slice_instance(
            start=3, end=6
        ).calulate_minimum_consecutive_shifts_config(
            self.lokal_employee.uid, self.lokal_employee
        )
        assert count_start == 1, "start"
        assert count_end == 1, "end"

    def test_count_min_days_2(self):
        self.lokal_employee.min_number_consecutive_shifts = 3
        for day in range(10):
            if day in [1, 2, 3, 6, 7, 8]:
                self.solution.set_var(
                    day, self.lokal_shift_types.uid, self.lokal_employee.uid, 1
                )
            else:
                self.solution.set_var(
                    day, self.lokal_shift_types.uid, self.lokal_employee.uid, 0
                )

        count_start, count_end = self.get_slice_instance(
            start=3, end=6
        ).calulate_minimum_consecutive_shifts_config(
            self.lokal_employee.uid, self.lokal_employee
        )
        assert count_start == 1, "start"
        assert count_end == 1, "end"

    def test_count_min_days_3(self):
        self.lokal_employee.min_number_consecutive_shifts = 3
        for day in range(10):
            if day in []:
                self.solution.set_var(
                    day, self.lokal_shift_types.uid, self.lokal_employee.uid, 1
                )
            else:
                self.solution.set_var(
                    day, self.lokal_shift_types.uid, self.lokal_employee.uid, 0
                )

        count_start, count_end = self.get_slice_instance(
            start=3, end=6
        ).calulate_minimum_consecutive_shifts_config(
            self.lokal_employee.uid, self.lokal_employee
        )
        assert count_start == -1, "start"
        assert count_end == -1, "end"

    def test_count_min_days_4(self):
        self.lokal_employee.min_number_consecutive_shifts = 3
        for day in range(10):
            if day in [0, 1, 2, 6, 7, 8]:
                self.solution.set_var(
                    day, self.lokal_shift_types.uid, self.lokal_employee.uid, 1
                )
            else:
                self.solution.set_var(
                    day, self.lokal_shift_types.uid, self.lokal_employee.uid, 0
                )

        # ACHTUNG: ende verschoben
        count_start, count_end = self.get_slice_instance(
            start=3, end=5
        ).calulate_minimum_consecutive_shifts_config(
            self.lokal_employee.uid, self.lokal_employee
        )
        assert count_start == -2, "start"
        assert count_end == 0, "end"


class Test_slice_instance_max_days:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.lokal_shift_types = shiftType.ShiftType()
        self.lokal_employee = employee.Employee()
        self.instance = instace.Instance.create(
            number_of_days=9,
            shift_typs=[self.lokal_shift_types],
            emplyees=[self.lokal_employee],
        )
        self.solution = Solution(self.instance)

    def get_slice_instance(self, start: int = 3, end: int = 5):
        # Mock the solver and window instance creation to speed up tests
        with patch.object(
            Slice_instance, "__init__", lambda self, sol, start, end: None
        ):
            self.slice_instance = Slice_instance(self.solution, start=start, end=end)
            # Manually set only the attributes needed for counting methods
            self.slice_instance.sol = self.solution
            self.slice_instance.inst = self.instance
            self.slice_instance.start_day = start
            self.slice_instance.end_day = end
        return self.slice_instance

    def test_count_max_days_1(self):
        self.lokal_employee.max_number_consecutive_shifts = 3
        for day in range(9):
            if day in []:
                self.solution.set_var(
                    day, self.lokal_shift_types.uid, self.lokal_employee.uid, 1
                )
            else:
                self.solution.set_var(
                    day, self.lokal_shift_types.uid, self.lokal_employee.uid, 0
                )

        count_start, count_end = self.get_slice_instance(
            start=3, end=6
        ).calulate_minimum_consecutive_shifts_config(
            self.lokal_employee.uid, self.lokal_employee
        )
        assert count_start == -1, "start"
        assert count_end == -1, "end"

    def test_count_max_days_2(self):
        self.lokal_employee.max_number_consecutive_shifts = 3
        for day in range(9):
            if day in [0, 1, 2, 6, 7, 8]:
                self.solution.set_var(
                    day, self.lokal_shift_types.uid, self.lokal_employee.uid, 1
                )
            else:
                self.solution.set_var(
                    day, self.lokal_shift_types.uid, self.lokal_employee.uid, 0
                )

        count_start, count_end = self.get_slice_instance(
            start=3, end=5
        ).calulate_maximum_consecutive_shifts_config(
            self.lokal_employee.uid, self.lokal_employee
        )
        assert count_start == 0, "start"
        assert count_end == 0, "end"

    def test_count_max_days_3(self):
        self.lokal_employee.max_number_consecutive_shifts = 3
        for day in range(9):
            if day in [2, 7]:
                self.solution.set_var(
                    day, self.lokal_shift_types.uid, self.lokal_employee.uid, 1
                )
            else:
                self.solution.set_var(
                    day, self.lokal_shift_types.uid, self.lokal_employee.uid, 0
                )

        count_start, count_end = self.get_slice_instance(
            start=3, end=6
        ).calulate_maximum_consecutive_shifts_config(
            self.lokal_employee.uid, self.lokal_employee
        )
        assert count_start == 2, "start"
        assert count_end == 2, "end"

    def test_count_max_days_4(self):
        self.lokal_employee.max_number_consecutive_shifts = 4
        for day in range(9):
            if day in [5, 6, 7, 8]:
                self.solution.set_var(
                    day, self.lokal_shift_types.uid, self.lokal_employee.uid, 1
                )
            else:
                self.solution.set_var(
                    day, self.lokal_shift_types.uid, self.lokal_employee.uid, 0
                )

        count_start, count_end = self.get_slice_instance(
            start=3, end=7
        ).calulate_maximum_consecutive_shifts_config(
            self.lokal_employee.uid, self.lokal_employee
        )
        assert count_end == 3

    def test_count_max_days_5(self):
        self.lokal_employee.max_number_consecutive_shifts = 4
        for day in range(9):
            if day in [8]:
                self.solution.set_var(
                    day, self.lokal_shift_types.uid, self.lokal_employee.uid, 1
                )
            else:
                self.solution.set_var(
                    day, self.lokal_shift_types.uid, self.lokal_employee.uid, 0
                )

        count_start, count_end = self.get_slice_instance(
            start=3, end=7
        ).calulate_maximum_consecutive_shifts_config(
            self.lokal_employee.uid, self.lokal_employee
        )
        assert count_end == 3

    def test_count_max_days_6(self):
        self.lokal_employee.max_number_consecutive_shifts = 4
        for day in range(9):
            if day in [7, 8]:
                self.solution.set_var(
                    day, self.lokal_shift_types.uid, self.lokal_employee.uid, 1
                )
            else:
                self.solution.set_var(
                    day, self.lokal_shift_types.uid, self.lokal_employee.uid, 0
                )

        count_start, count_end = self.get_slice_instance(
            start=2, end=6
        ).calulate_maximum_consecutive_shifts_config(
            self.lokal_employee.uid, self.lokal_employee
        )
        assert count_end == 2
