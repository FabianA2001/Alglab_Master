"""Basic constraint validation functions."""

from typing import TYPE_CHECKING, List, Tuple

if TYPE_CHECKING:
    from ..solution import Solution


def check_cover_requirements_constraint(sol: "Solution") -> Tuple[bool, List[str]]:
    """Prüft ob die Cover Requirements Constraint erfüllt ist."""
    violations = []
    for day in range(sol.instance.number_of_days):
        for type_uid in sol.instance.shifts[day]:
            assigned_shifts = []
            for employee_uid in sol.instance.employees:
                assigned_shifts.append(sol.vars[(day, type_uid, employee_uid)])

            expected = sol.instance.shifts[day][type_uid].preffert_number_employees
            actual = (
                sum(assigned_shifts)
                - sol.above_prefferd_vars[(day, type_uid)]
                + sol.below_prefferd_vars[(day, type_uid)]
            )

            if actual != expected:
                shift_name = sol.instance.shift_types[type_uid].name
                violations.append(
                    f"Tag {day}, Schicht {shift_name}: Erwartet {expected}, tatsächlich {actual}"
                )
                
            if (
                sol.below_threshold_vars[(day, type_uid)]
                < (2 / 3 * sol.instance.shifts[day][type_uid].preffert_number_employees) - sum(assigned_shifts)
            ):
                shift_name = sol.instance.shift_types[type_uid].name
                violations.append(
                    f"Tag {day}, Schicht {shift_name}: Untergrenze nicht erfüllt"
                )

    return len(violations) == 0, violations


def check_days_off_constraint(sol: "Solution") -> Tuple[bool, List[str]]:
    """Prüft ob die Days Off Constraint erfüllt ist."""
    violations = []
    for employee_uid in sol.instance.employees:
        emp_name = sol.instance.employees[employee_uid].name
        for day in sol.instance.employees[employee_uid].blocked_shifts:
            for type_uid in sol.instance.shifts[day]:
                if sol.vars[(day, type_uid, employee_uid)] == 1:
                    shift_name = sol.instance.shift_types[type_uid].name
                    violations.append(
                        f"Mitarbeiter {emp_name} an gesperrtem Tag {day} eingeteilt (Schicht: {shift_name})"
                    )

    return len(violations) == 0, violations


def check_single_day_constraint(sol: "Solution") -> Tuple[bool, List[str]]:
    """Prüft ob die Single Day Constraint erfüllt ist."""
    violations = []
    for employee_uid in sol.instance.employees:
        emp_name = sol.instance.employees[employee_uid].name

        for day in range(sol.instance.number_of_days):
            assigned_shifts = []
            shift_names = []

            for type_uid in sol.instance.shifts[day]:
                if sol.vars[(day, type_uid, employee_uid)] == 1:
                    assigned_shifts.append(sol.vars[(day, type_uid, employee_uid)])
                    shift_names.append(sol.instance.shift_types[type_uid].name)

            if sum(assigned_shifts) > 1:
                violations.append(
                    f"Mitarbeiter {emp_name} an Tag {day} mehrfach eingeteilt: {', '.join(shift_names)}"
                )

    return len(violations) == 0, violations


def check_shift_rotation_constraint(sol: "Solution") -> Tuple[bool, List[str]]:
    """Prüft ob die Shift Rotation Constraint erfüllt ist."""
    violations = []
    for employee_uid in sol.instance.employees:
        emp_name = sol.instance.employees[employee_uid].name

        for day in range(sol.instance.number_of_days - 1):
            for type_uid in sol.instance.shifts[day]:
                if sol.vars[(day, type_uid, employee_uid)] == 1:
                    shift_name = sol.instance.shift_types[type_uid].name

                    for btype_uid in sol.instance.shift_types[
                        type_uid
                    ].blocked_shifts_after:
                        if sol.vars[(day + 1, btype_uid, employee_uid)] == 1:
                            blocked_shift_name = sol.instance.shift_types[
                                btype_uid
                            ].name
                            violations.append(
                                f"Mitarbeiter {emp_name}: {shift_name} an Tag {day} → {blocked_shift_name} an Tag {day + 1} (nicht erlaubt)"
                            )

    return len(violations) == 0, violations
