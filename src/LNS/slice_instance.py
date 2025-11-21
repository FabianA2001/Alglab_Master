from .. import solution, solver
from ..inputTypes import instace


def creat_solver_with_window_instance(
    sol: solution.Solution, start: int, min_day: int, end: int, max_day: int
) -> solver.Solver:
    slicer = slice_instance(
        sol=sol, start=start, min_day=min_day, end=end, max_day=max_day
    )
    window_instance = slicer.get_sliced_instance()
    solvr = solver.Solver(
        window_instance, solver.shift_vars.Shift_vars(window_instance)
    )
    slicer.fix_first_and_last_day(solvr)
    return solvr


class slice_instance:
    def __init__(
        self, sol: solution.Solution, start: int, min_day: int, end: int, max_day: int
    ):
        self.sol = sol
        self.inst: instace.Instance = sol.instance
        self.start_day = start
        self.min_day = min_day
        self.end_day = end
        self.max_day = max_day
        self.window_instance = self.create_window_instance()

    def get_sliced_instance(self) -> instace.Instance:
        return self.window_instance

    def fix_first_and_last_day(self, solver_instance: solver.Solver):
        """Fixiert die Zuweisungen des ersten und letzten Tages des erweiterten Fensters mit den Werten der gegebenen Lösung."""

        # Fixiere den ersten und letzten Tag des erweiterten Fensters
        extended_start = max(self.min_day, self.start_day - 1)
        extended_end = min(self.max_day, self.end_day + 1)

        # Fixiere den ersten Tag (extended_start)
        for shift_type_uid in solver_instance.instance.shift_types:
            for emp_id in solver_instance.instance.employees:
                assigned = self.sol.is_employee_assigned(
                    extended_start, shift_type_uid, emp_id
                )
                # Tag 0 in der window_instance entspricht extended_start in der alten Instanz
                var = solver_instance.vars.vars[(0, shift_type_uid, emp_id)]
                if assigned:
                    solver_instance.vars.model.Add(var == 1)
                else:
                    solver_instance.vars.model.Add(var == 0)

        # Fixiere den letzten Tag (extended_end)
        last_day_in_window = extended_end - extended_start
        for shift_type_uid in solver_instance.instance.shift_types:
            for emp_id in solver_instance.instance.employees:
                assigned = self.sol.is_employee_assigned(
                    extended_end, shift_type_uid, emp_id
                )
                var = solver_instance.vars.vars[
                    (last_day_in_window, shift_type_uid, emp_id)
                ]
                if assigned:
                    solver_instance.vars.model.Add(var == 1)
                else:
                    solver_instance.vars.model.Add(var == 0)

    def create_window_instance(self) -> instace.Instance:
        """Erstellt eine Instanz, die das aktuelle Suchfenster plus einen Tag davor und danach umfasst."""
        old_instance = self.sol.instance

        # Erweitere Fenster um einen Tag vor und nach (falls möglich)
        extended_start = max(self.min_day, self.start_day - 1)
        extended_end = min(self.max_day, self.end_day + 1)
        days_in_window = extended_end - extended_start + 1

        # Kopiere employees (Referenz auf dieselben Employee-Objekte)
        employees = old_instance.employees.copy()

        # Kopiere shift_types (Referenz auf dieselben ShiftType-Objekte)
        shift_types = old_instance.shift_types.copy()

        # Erstelle neue shifts für das erweiterte Fenster
        from collections import defaultdict

        shifts = defaultdict(dict)
        for day_offset in range(days_in_window):
            old_day = extended_start + day_offset
            for shift_type_uid in old_instance.shift_types:
                # Kopiere den Shift vom alten Tag
                shifts[day_offset][shift_type_uid] = old_instance.get_shift(
                    old_day, shift_type_uid
                )

        # Berechne neue weekend_days (angepasst an neuen day-Index)
        weekend_days = set()
        for old_weekend_day in old_instance.weekend_days:
            if extended_start <= old_weekend_day <= extended_end:
                new_day = old_weekend_day - extended_start
                weekend_days.add(new_day)

        # Erstelle neue Instanz mit __init__
        window_instance = instace.Instance(
            name=f"{old_instance.name}_window_{extended_start}_{extended_end}",
            employees=employees,
            number_of_days=days_in_window,
            weekend_days=weekend_days,
            shifts=shifts,
            shift_types=shift_types,
        )

        return window_instance
