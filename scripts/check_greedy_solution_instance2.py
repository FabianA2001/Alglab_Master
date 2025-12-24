from pathlib import Path
from src.parseData import parseTXT
from src.greedy_scheduler import SequentialGreedyScheduler
from src.solution import Solution

# Parse Instance2
data_path = (
    Path(__file__).resolve().parent.parent / "data" / "instance_raw" / "Instance2.txt"
)
instance = parseTXT.parse_txt(data_path)

# Run improved greedy scheduler
scheduler = SequentialGreedyScheduler(instance)
assignment = (
    scheduler.get_assignment_matrix()
)  # dict[(day, type_uid, employee_uid)] = 1/0

# Erzeuge Solution-Objekt aus Greedy-Lösung und setze ALLE Variablen (auch 0)
sol = Solution(instance)
for day in range(instance.number_of_days):
    for type_uid in instance.shift_types:
        for emp_uid in instance.employees:
            val = assignment.get((day, type_uid, emp_uid), 0)
            sol.set_var(day, type_uid, emp_uid, val)

# Setze above/below preferred für jede Schicht
for day in range(instance.number_of_days):
    for type_uid in instance.shift_types:
        shift = instance.get_shift(day, type_uid)
        assigned = sum(
            sol.vars[(day, type_uid, emp_uid)] for emp_uid in instance.employees
        )
        below = max(0, shift.preffert_number_employees - assigned)
        above = max(0, assigned - shift.preffert_number_employees)
        sol.set_below_prefferd_var(day, type_uid, below)
        sol.set_above_prefferd_var(day, type_uid, above)

# Setze weekend_vars für alle (weekend, employee_uid) auf 0, falls nicht belegt
num_weekends = (instance.number_of_days + 6) // 7
for weekend in range(num_weekends):
    for emp_uid in instance.employees:
        if (weekend, emp_uid) not in sol.weekend_vars:
            sol.set_weekend_var(weekend, emp_uid, 0)

# Checke alle Constraints
ok, details = sol.checkt_constraints
print(f"All hard constraints satisfied: {ok}")
for cname, (valid, violations) in details.items():
    if not valid:
        print(f"Constraint violated: {cname}")
        for v in violations:
            print(f"  {v}")

# Zeige das Objective (falls gesetzt)
print(f"Objective value (if set): {getattr(sol, 'objective_value', None)}")

# Tabellarische Ausgabe der Greedy-Lösung
print("\nGreedy-Lösung (Tag | Schicht | Mitarbeiter):")
type_uid_to_name = {t.uid: t.name for t in instance.shift_types.values()}
emp_uid_to_name = {e.uid: e.name for e in instance.employees.values()}

header = "Tag | " + " | ".join(type_uid_to_name.values())
print(header)
print("-" * (6 + 20 * len(type_uid_to_name)))
for day in range(instance.number_of_days):
    row = []
    for t_uid in instance.shift_types:
        emps = [
            emp_uid_to_name[e]
            for e in instance.employees
            if sol.vars[(day, t_uid, e)] == 1
        ]
        row.append(",".join(emps) if emps else "-")
    print(f"{day:2d}  | " + " | ".join(row))
