import hashlib
from typing import List, Tuple, Dict
from src.solution import Solution


def hash_string(s: str) -> int:
    """Erstellt einen konsistenten Hash-Wert für einen gegebenen String."""
    return int(hashlib.md5(s.encode()).hexdigest(), 16)


def compare_solutions(
    solution_a: Solution, solution_b: Solution, *, include_details: bool = True
) -> dict:
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

    def _build_assignments(solution: Solution) -> tuple[dict, int, dict]:
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


def compare_multiple_solutions(
    solutions: List[Solution], *, threshold: float = 2.0, include_details: bool = True
) -> dict:
    """
    Vergleicht mehrere Solutions derselben Instanz und findet "stabile"
    Lösungsbereiche, d.h. Assignments (day, shift_uid, emp_uid), die in
    mindestens `threshold` Anteil der Lösungen gleich (assigned==1) sind.

    Args:
        solutions: Liste von Solution-Objekten (müssen dieselbe Instanz repräsentieren)
        threshold: Bruchteil der Lösungen (0..1), ab dem eine Zuweisung als "stabil" gilt.
                   Default 1.0 (in allen Lösungen vorhanden).
        include_details: Falls True, werden detaillierte Counts/Fractions zurückgegeben.

    Rückgabe (Beispiel):
    {
      'num_solutions': 5,
      'threshold': 1.0,
      'stable_assignments_count': 12,
      'stable_assignments': {(0,774): [3,4], ...}, # pro (day,shift) Liste von emp_uids
      'stable_details': {(day,shift,emp): {'count':3,'fraction':0.6}, ...},
      'stable_employee_ranges': {emp_uid: {shift_uid:[(start,end), ...]}},
      'per_day_summary': {day: {'stable_triples': 5, 'stable_shifts': 2}}
    }

    Hinweis: Die Funktion erwartet, dass alle Solutions dieselbe Instanz-Struktur
    (Anzahl Tage, Shift-Types, Employee-IDs) besitzen. Es wird anhand der ersten
    Solution validiert.
    """

    if not solutions:
        return {
            "num_solutions": 0,
            "threshold": threshold,
            "stable_assignments_count": 0,
            "stable_assignments": {},
        }

    # Grundvalidierung: alle Solutions sollten zur selben Instanz gehören
    base_inst = solutions[0].instance
    num_solutions = len(solutions)

    for s in solutions[1:]:
        if (
            s.instance.number_of_days != base_inst.number_of_days
            or s.instance.name != base_inst.name
        ):
            raise ValueError(
                "Alle Solutions müssen dieselbe Instanz (gleiches Instance.name und number_of_days) haben"
            )

    # Zähle für jedes Tripel (day, shift_uid, emp_uid) wie oft assigned==1
    counts: Dict[Tuple[int, int, int], int] = {}

    # Wir gehen über alle möglichen (day, shift_uid, emp_uid) basierend auf der Instanz
    days = list(range(base_inst.number_of_days))
    employee_ids = list(base_inst.employees.keys())

    for sol in solutions:
        # jeweils vorhandene vars nutzen (falls key fehlt -> 0)
        for day in days:
            day_shifts = base_inst.shifts.get(day, {})
            for shift_uid in day_shifts.keys():
                for emp_uid in employee_ids:
                    if sol.vars.get((day, shift_uid, emp_uid), 0) == 1:
                        counts[(day, shift_uid, emp_uid)] = (
                            counts.get((day, shift_uid, emp_uid), 0) + 1
                        )

    # Grenze: minimaler Count, basierend auf threshold
    min_count = int(round(threshold))

    stable_triples = {k: v for k, v in counts.items() if v >= min_count}

    # organize by (day, shift) -> list of employees
    stable_by_shift: Dict[Tuple[int, int], List[int]] = {}
    stable_details: Dict[Tuple[int, int, int], Dict[str, float]] = {}
    per_day_summary: Dict[int, Dict[str, int]] = {
        d: {"stable_triples": 0, "stable_shifts": 0} for d in days
    }

    # helper to track which shifts have at least one stable assignment that day
    shifts_with_stable_on_day: Dict[int, set] = {d: set() for d in days}

    for (day, shift_uid, emp_uid), cnt in stable_triples.items():
        stable_by_shift.setdefault((day, shift_uid), []).append(emp_uid)
        frac = cnt / num_solutions
        if include_details:
            stable_details[(day, shift_uid, emp_uid)] = {"count": cnt, "fraction": frac}
        per_day_summary[day]["stable_triples"] += 1
        shifts_with_stable_on_day[day].add(shift_uid)

    for d in days:
        per_day_summary[d]["stable_shifts"] = len(shifts_with_stable_on_day[d])

    # build consecutive-day ranges per employee per shift for which the triple was stable
    stable_employee_ranges: Dict[int, Dict[int, List[Tuple[int, int]]]] = {}

    # For each (emp, shift) collect days where stable
    emp_shift_days: Dict[Tuple[int, int], List[int]] = {}
    for (day, shift_uid, emp_uid), cnt in stable_triples.items():
        emp_shift_days.setdefault((emp_uid, shift_uid), []).append(day)

    for (emp_uid, shift_uid), day_list in emp_shift_days.items():
        day_list_sorted = sorted(day_list)
        ranges: List[Tuple[int, int]] = []
        if not day_list_sorted:
            stable_employee_ranges.setdefault(emp_uid, {})[shift_uid] = []
            continue
        start = day_list_sorted[0]
        prev = start
        for d in day_list_sorted[1:]:
            if d == prev + 1:
                prev = d
                continue
            # gap -> close previous range
            ranges.append((start, prev))
            start = d
            prev = d
        # close last range
        ranges.append((start, prev))

        stable_employee_ranges.setdefault(emp_uid, {})[shift_uid] = ranges

    result = {
        "num_solutions": num_solutions,
        "threshold": threshold,
        "min_count": min_count,
        "stable_assignments_count": len(stable_triples),
        "stable_assignments": stable_by_shift,
        "stable_details": stable_details if include_details else {},
        "stable_employee_ranges": stable_employee_ranges,
        "per_day_summary": per_day_summary,
    }

    return result
