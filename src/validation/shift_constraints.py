"""Shift and worktime related constraint validation functions."""

from typing import TYPE_CHECKING, List, Tuple

if TYPE_CHECKING:
    from ..solution import Solution


def check_lim_shifts_type_constraint(sol: "Solution") -> Tuple[bool, List[str]]:
    """Prüft ob die Limited Shifts per Type Constraint erfüllt ist."""
    violations = []
    for employee_uid in sol.instance.employees:
        emp_name = sol.instance.employees[employee_uid].name
        for type_uid in sol.instance.shift_types:
            assigned_shifts = []
            for day in range(sol.instance.number_of_days):
                assigned_shifts.append(sol.vars[(day, type_uid, employee_uid)])

            total = sum(assigned_shifts)
            max_allowed = sol.instance.employees[employee_uid].max_numbers_of_shifts[
                type_uid
            ]

            if total > max_allowed:
                shift_name = sol.instance.shift_types[type_uid].name
                violations.append(
                    f"Mitarbeiter {emp_name} hat {total} Schichten vom Typ {shift_name} (Max: {max_allowed})"
                )

    return len(violations) == 0, violations


def check_max_cons_shifts_constraint(sol: "Solution") -> Tuple[bool, List[str]]:
    """Prüft ob die Max Consecutive Shifts Constraint erfüllt ist."""
    violations = []
    for employee_uid in sol.instance.employees:
        emp_name = sol.instance.employees[employee_uid].name
        max_cons = sol.instance.employees[employee_uid].max_number_consecutive_shifts

        for day in range(sol.instance.number_of_days - max_cons):
            assigned_shifts = []
            for type_uid in sol.instance.shifts[day]:
                for i in range(max_cons + 1):
                    assigned_shifts.append(sol.vars[(day + i, type_uid, employee_uid)])

            total = sum(assigned_shifts)
            if total > max_cons:
                violations.append(
                    f"Mitarbeiter {emp_name} hat {total} aufeinanderfolgende Schichten ab Tag {day} (Max: {max_cons})"
                )

    return len(violations) == 0, violations


def check_min_cons_shifts_constraint(sol: "Solution") -> Tuple[bool, List[str]]:
    """Prüft ob die Min Consecutive Shifts Constraint erfüllt ist."""
    violations = []
    for employee_uid in sol.instance.employees:
        emp_name = sol.instance.employees[employee_uid].name
        min_shifts = sol.instance.employees[employee_uid].min_number_consecutive_shifts

        for day_s in range(min_shifts - 1):
            for day_d in range(sol.instance.number_of_days - (day_s + 1) - 1):
                assigned_shifts = []
                assigned_shifts_inner_interval = []
                assigned_shifts_interval_end = []

                for type_uid in sol.instance.shift_types:
                    assigned_shifts.append(sol.vars[(day_d, type_uid, employee_uid)])

                    for day_j in range(day_d + 1, day_d + day_s + 1 + 1):
                        assigned_shifts_inner_interval.append(
                            sol.vars[(day_j, type_uid, employee_uid)]
                        )

                    assigned_shifts_interval_end.append(
                        sol.vars[(day_d + day_s + 1 + 1, type_uid, employee_uid)]
                    )

                result = (
                    sum(assigned_shifts)
                    + day_s
                    + 1
                    - sum(assigned_shifts_inner_interval)
                    + sum(assigned_shifts_interval_end)
                )

                if result <= 0:
                    violations.append(
                        f"Mitarbeiter {emp_name} hat nicht genug aufeinanderfolgende Schichten ab Tag {day_d}"
                    )

    return len(violations) == 0, violations


def check_min_max_worktime_constraint(sol: "Solution") -> Tuple[bool, List[str]]:
    """Prüft ob die Min/Max Worktime Constraint erfüllt ist."""
    violations = []
    for employee_uid in sol.instance.employees:
        emp_name = sol.instance.employees[employee_uid].name
        assigned_minutes = 0

        for day in range(sol.instance.number_of_days):
            for type_uid in sol.instance.shifts[day]:
                assigned_minutes += (
                    sol.vars[(day, type_uid, employee_uid)]
                    * sol.instance.shift_types[type_uid].length
                )

        min_minutes = sol.instance.employees[employee_uid].min_minutes_assigned
        max_minutes = sol.instance.employees[employee_uid].max_minutes_assigned

        if assigned_minutes > max_minutes:
            violations.append(
                f"Mitarbeiter {emp_name} hat {assigned_minutes} Minuten (Max: {max_minutes})"
            )

        if assigned_minutes < min_minutes:
            violations.append(
                f"Mitarbeiter {emp_name} hat {assigned_minutes} Minuten (Min: {min_minutes})"
            )

    return len(violations) == 0, violations
