"""Weekend and days-off related constraint validation functions."""

from typing import TYPE_CHECKING, List, Tuple

if TYPE_CHECKING:
    from ..solution import Solution


def check_max_weekend_days_constraint(sol: "Solution") -> Tuple[bool, List[str]]:
    """Prüft ob die Max Weekend Days Constraint erfüllt ist."""
    violations = []
    for employee_uid in sol.instance.employees:
        emp_name = sol.instance.employees[employee_uid].name
        assigned_weekends = []

        for weekend in range(round(sol.instance.number_of_days / 7)):
            assigned_shifts = []
            for type_uid in sol.instance.shifts[weekend]:
                assigned_shifts.append(
                    sol.vars[((7 * (weekend + 1) - 1 - 1), type_uid, employee_uid)]
                )
                assigned_shifts.append(
                    sol.vars[((7 * (weekend + 1) - 1), type_uid, employee_uid)]
                )

            weekend_var = sol.weekend_vars[(weekend, employee_uid)]

            if weekend_var > sum(assigned_shifts):
                violations.append(
                    f"Mitarbeiter {emp_name}, Wochenende {weekend}: Weekend-Variable fehlerhaft"
                )

            if sum(assigned_shifts) > 2 * weekend_var:
                violations.append(
                    f"Mitarbeiter {emp_name}, Wochenende {weekend}: Zu viele Schichten"
                )

            assigned_weekends.append(weekend_var)

        total_weekends = sum(assigned_weekends)
        max_weekends = sol.instance.employees[employee_uid].max_number_weekends

        if total_weekends > max_weekends:
            violations.append(
                f"Mitarbeiter {emp_name} hat {total_weekends} Wochenenden (Max: {max_weekends})"
            )

    return len(violations) == 0, violations


def check_min_cons_days_constraint(sol: "Solution") -> Tuple[bool, List[str]]:
    """Prüft ob die Min Consecutive Days Off Constraint erfüllt ist."""
    violations = []
    for employee_uid in sol.instance.employees:
        emp_name = sol.instance.employees[employee_uid].name
        min_days_off = sol.instance.employees[
            employee_uid
        ].min_number_consecutive_days_off

        for day_s in range(min_days_off - 1):
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
                    1
                    - sum(assigned_shifts)
                    + sum(assigned_shifts_inner_interval)
                    + 1
                    - sum(assigned_shifts_interval_end)
                )

                if result <= 0:
                    violations.append(
                        f"Mitarbeiter {emp_name} hat nicht genug aufeinanderfolgende freie Tage ab Tag {day_d}"
                    )

    return len(violations) == 0, violations
