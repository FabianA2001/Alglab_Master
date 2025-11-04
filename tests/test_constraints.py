import pytest

from src.solution import Solution


@pytest.fixture
def solution():
    """Lädt die zuletzt berechnete Solution aus dem Solver-Ausgabeordner."""
    return Solution.from_json_file("Instance2")


def test_cover_requirements_constraint(solution: Solution):
    for day in range(solution.instance.number_of_days):
        for type_uid in solution.instance.shifts[day]:
            assigned_shifts = []
            for employee_uid in solution.instance.employees:
                assigned_shifts.append(solution.vars[(day, type_uid, employee_uid)])

            assert (
                sum(assigned_shifts)
                - solution.above_prefferd_vars[(day, type_uid)]
                + solution.below_prefferd_vars[(day, type_uid)]
                == solution.instance.shifts[day][type_uid].preffert_number_employees
            )


def test_days_off_constraint(solution: Solution):
    for employee_uid in solution.instance.employees:
        assigned_shifts = []
        for day in solution.instance.employees[employee_uid].blocked_shifts:
            for type_uid in solution.instance.shifts[day]:
                assigned_shifts.append(solution.vars[(day, type_uid, employee_uid)])

        assert sum(assigned_shifts) == 0


def test_lim_shifts_type_constraint(solution: Solution):
    for employee_uid in solution.instance.employees:
        for type_uid in solution.instance.shift_types:
            assigned_shifts = []
            for day in range(solution.instance.number_of_days):
                assigned_shifts.append(solution.vars[(day, type_uid, employee_uid)])
            assert (
                sum(assigned_shifts)
                <= solution.instance.employees[employee_uid].max_numbers_of_shifts[
                    type_uid
                ]
            )


def test_max_cons_shifts_constraint(solution: Solution):
    for employee_uid in solution.instance.employees:
        for day in range(
            solution.instance.number_of_days
            - solution.instance.employees[employee_uid].max_number_consecutive_shifts
        ):
            assigned_shifts = []
            for type_uid in solution.instance.shifts[day]:
                for i in range(
                    solution.instance.employees[
                        employee_uid
                    ].max_number_consecutive_shifts
                    + 1
                ):
                    assigned_shifts.append(
                        solution.vars[(day + i, type_uid, employee_uid)]
                    )

            assert (
                sum(assigned_shifts)
                <= solution.instance.employees[
                    employee_uid
                ].max_number_consecutive_shifts
            )


def test_max_weekend_days_constraint(solution: Solution):
    for employee_uid in solution.instance.employees:
        assigned_weekends = []
        for weekend in range(round(solution.instance.number_of_days / 7)):
            assigned_shifts = []
            for type_uid in solution.instance.shifts[weekend]:
                assigned_shifts.append(
                    # + 1 because of for range start with 0, - 1 because are weekends days are on 5 and 6
                    # not 6 and 7
                    solution.vars[((7 * (weekend + 1) - 1 - 1), type_uid, employee_uid)]
                )
                assigned_shifts.append(
                    solution.vars[((7 * (weekend + 1) - 1), type_uid, employee_uid)]
                )

            assert solution.weekend_vars[(weekend, employee_uid)] <= sum(
                assigned_shifts
            )
            assert (
                # x
                sum(assigned_shifts)
                <= 2 * (solution.weekend_vars[(weekend, employee_uid)])
            )
            assigned_weekends.append(solution.weekend_vars[(weekend, employee_uid)])
        assert (
            sum(assigned_weekends)
            <= solution.instance.employees[employee_uid].max_number_weekends
        )


def test_min_cons_days_constraint(solution: Solution):
    for employee_uid in solution.instance.employees:
        # TODO is a constraint with 1 consecutive working day meaningful?
        for day_s in range(
            solution.instance.employees[employee_uid].min_number_consecutive_days_off
            - 1
        ):
            for day_d in range(solution.instance.number_of_days - (day_s + 1) - 1):
                assigned_shifts = []
                assigned_shifts_inner_interval = []
                assigned_shifts_interval_end = []
                for type_uid in solution.instance.shift_types:
                    assigned_shifts.append(
                        solution.vars[(day_d, type_uid, employee_uid)]
                    )
                    # Because range end range is exclusive, the end range should have + 1
                    # Because day_s start with 0, another +1 should be added
                    for day_j in range(day_d + 1, day_d + day_s + 1 + 1):
                        assigned_shifts_inner_interval.append(
                            solution.vars[(day_j, type_uid, employee_uid)]
                        )
                    assigned_shifts_interval_end.append(
                        solution.vars[(day_d + day_s + 1 + 1, type_uid, employee_uid)]
                    )
                assert (
                    1
                    - (sum(assigned_shifts))
                    + sum(assigned_shifts_inner_interval)
                    + 1
                    - (sum(assigned_shifts_interval_end))
                    > 0
                )


def test_min_cons_shifts_constraint(solution: Solution):
    for employee_uid in solution.instance.employees:
        for day_s in range(
            solution.instance.employees[employee_uid].min_number_consecutive_shifts - 1
        ):
            for day_d in range(solution.instance.number_of_days - (day_s + 1) - 1):
                assigned_shifts = []
                assigned_shifts_inner_interval = []
                assigned_shifts_interval_end = []
                for type_uid in solution.instance.shift_types:
                    assigned_shifts.append(
                        solution.vars[(day_d, type_uid, employee_uid)]
                    )
                    # Because range end range is exclusive, the end range should have + 1
                    # Because day_s start with 0, another +1 should be added
                    for day_j in range(day_d + 1, day_d + day_s + 1 + 1):
                        assigned_shifts_inner_interval.append(
                            solution.vars[(day_j, type_uid, employee_uid)]
                        )
                    assigned_shifts_interval_end.append(
                        solution.vars[(day_d + day_s + 1 + 1, type_uid, employee_uid)]
                    )
                # Even though our indecies start with 0, day_s should still have the start value of 1
                assert (
                    sum(assigned_shifts)
                    + day_s
                    + 1
                    - (sum(assigned_shifts_inner_interval))
                    + sum(assigned_shifts_interval_end)
                    > 0
                )


def test_min_max_worktime_constraint(solution: Solution):
    for employee_uid in solution.instance.employees:
        assigned_minutes = 0
        for day in range(solution.instance.number_of_days):
            for type_uid in solution.instance.shifts[day]:
                assigned_minutes += (
                    (solution.vars[(day, type_uid, employee_uid)])
                    * solution.instance.shift_types[type_uid].length
                )

        assert (
            assigned_minutes
            <= solution.instance.employees[employee_uid].max_minutes_assigned
        )
        assert (
            assigned_minutes
            >= solution.instance.employees[employee_uid].min_minutes_assigned
        )


def test_single_day_constraint(solution: Solution):
    for employee_uid in solution.instance.employees:
        for day in range(solution.instance.number_of_days):
            assigned_shifts = []
            for type_uid in solution.instance.shifts[day]:
                assigned_shifts.append(solution.vars[(day, type_uid, employee_uid)])
            # Ensure that at most one shift is assigned to the employee on this day
            assert sum(assigned_shifts) <= 1


def test_shift_rotation_constraint(solution: Solution):
    for employee_uid in solution.instance.employees:
        for day in range(solution.instance.number_of_days - 1):
            # assigned_shifts = []
            for type_uid in solution.instance.shifts[day]:
                # assigned_shifts.append(vars.vars[(day, type_uid, employee_uid)])
                for btype_uid in solution.instance.shift_types[
                    type_uid
                ].blocked_shifts_after:
                    # incorrect because more shift combination are being denied
                    # assigned_shifts.append(
                    #     vars.vars[(day + 1, btype_uid, employee_uid)]
                    # )
                    assert (
                        solution.vars[(day, type_uid, employee_uid)]
                        + solution.vars[(day + 1, btype_uid, employee_uid)]
                        <= 1
                    )
