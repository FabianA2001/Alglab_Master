import hashlib
import string


def hash_string(s: str) -> int:
    """Erstellt einen konsistenten Hash-Wert für einen gegebenen String."""
    return int(hashlib.md5(s.encode()).hexdigest(), 16)


def compare_solutions(
    path_a: str, path_b: str, *, include_details: bool = True
) -> dict:
    """
    Vergleicht zwei Solution-JSON-Dateien und liefert zusammenfassende Informationen
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
        path_a: Pfad zur ersten Solution-Datei (ältere Version)
        path_b: Pfad zur zweiten Solution-Datei (neuere Version)
        include_details: Falls True, werden pro-Employee-Details und per-day counts
                         mitgeliefert. Sonst nur summary counts.
    """
    import json
    from pathlib import Path

    def _load(path: str) -> dict:
        p = Path(path)
        with p.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _build_assignments(data: dict) -> tuple[dict, int, dict]:
        """Gibt zurück: assignments(emp_uid -> {day: shift_uid}), number_of_days, employee_names"""
        vars_map = data.get("vars", {})
        assignments: dict[int, dict[int, int]] = {}
        # keys may be strings like 'day,shift_uid,employee_uid' or already tuples
        for k, v in vars_map.items():
            if not v:
                continue
            if isinstance(k, str):
                parts = k.split(",")
            else:
                # likely a list/tuple from deserialized pydantic
                parts = list(k)
            if len(parts) != 3:
                continue
            try:
                day = int(parts[0])
                shift_uid = int(parts[1])
                emp_uid = int(parts[2])
            except Exception:
                continue
            if v == 1:
                assignments.setdefault(emp_uid, {})[day] = shift_uid

        num_days = data.get("instance", {}).get("number_of_days")
        # employee names mapping
        emp_names = {}
        for k, info in data.get("instance", {}).get("employees", {}).items():
            try:
                uid = int(k)
            except Exception:
                uid = int(info.get("uid")) if info.get("uid") is not None else k
            emp_names[uid] = info.get("name")

        return assignments, num_days or 0, emp_names

    a = _load(path_a)
    b = _load(path_b)

    assign_a, days_a, names_a = _build_assignments(a)
    assign_b, days_b, names_b = _build_assignments(b)

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
    #     result = {}
    #     result["per_employee_changes"] = per_employee_changes
    #     result["per_day_changes"] = per_day_changes

    return result
