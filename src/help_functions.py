import hashlib
import string


def hash_string(s: str) -> int:
    """Erstellt einen konsistenten Hash-Wert für einen gegebenen String."""
    return int(hashlib.md5(s.encode()).hexdigest(), 16)


def compare_solutions(solution_a, solution_b, *, include_details: bool = True) -> dict:
    """
    Vergleicht zwei Solution-Objekte und liefert zusammenfassende Informationen
    darüber, wie viele Mitarbeitende an wie vielen Tagen andere Schichten hätten.

    Rückgabe (Beispiel):
    {
      'employees_with_changes': 5,
      'total_changed_days': 12,
      'per_employee_changes': {
         1698: {'name': 'A', 'num_changed_days': 3, 'changes': [{'day':0,'from':null,'to':774...}, ...]},
         ...
      },
      'per_day_changes': {0:2,1:1, ...}
    }

    Args:
        solution_a: Solution-Objekt (ältere Version)
        solution_b: Solution-Objekt (neuere Version)
        include_details: Falls True, werden pro-Employee-Details und per-day counts
                         mitgeliefert. Sonst nur summary counts.
    """

    def _build_assignments(solution) -> tuple[dict, int, dict]:
        """Gibt zurück: assignments(emp_uid -> {day: shift_uid}), number_of_days, employee_names"""
        vars_map = solution.vars
        assignments: dict[int, dict[int, int]] = {}
        # vars ist ein dict mit tuple-keys (day, shift_uid, emp_uid) -> value
        for (day, shift_uid, emp_uid), v in vars_map.items():
            if not v:
                continue
            if v == 1:
                assignments.setdefault(emp_uid, {})[day] = shift_uid

        num_days = solution.instance.number_of_days
        # employee names mapping
        emp_names = {}
        for emp_uid, emp_obj in solution.instance.employees.items():
            emp_names[emp_uid] = emp_obj.name

        return assignments, num_days or 0, emp_names

    assign_a, days_a, names_a = _build_assignments(solution_a)
    assign_b, days_b, names_b = _build_assignments(solution_b)

    max_days = max(days_a or 0, days_b or 0)

    # All employees that appear in either solution or instance lists
    employees = (
        set(assign_a.keys())
        | set(assign_b.keys())
        | set(names_a.keys())
        | set(names_b.keys())
    )

    per_employee_changes: dict = {}
    per_day_changes: dict[int, int] = {d: 0 for d in range(max_days)}
    total_changed_days = 0

    for emp in sorted(employees):
        emp_name = names_b.get(emp) or names_a.get(emp)
        changes = []
        num_changed = 0
        for day in range(max_days):
            shift_a = assign_a.get(emp, {}).get(day)
            shift_b = assign_b.get(emp, {}).get(day)
            # normalize None vs missing -> None
            if shift_a != shift_b:
                num_changed += 1
                total_changed_days += 1
                per_day_changes[day] = per_day_changes.get(day, 0) + 1
                if include_details:
                    changes.append({"day": day, "from": shift_a, "to": shift_b})

        if num_changed > 0:
            per_employee_changes[emp] = {
                "name": emp_name,
                "num_changed_days": num_changed,
            }
            if include_details:
                per_employee_changes[emp]["changes"] = changes

    employees_with_changes = len(per_employee_changes)

    result = {
        "employees_with_changes": employees_with_changes,
        "total_changed_days": total_changed_days,
    }
    # if include_details:
    #     result["per_employee_changes"] = per_employee_changes
    #     result["per_day_changes"] = per_day_changes

    return result
