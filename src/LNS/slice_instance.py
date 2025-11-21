from .. import solution, solver
from ..inputTypes import employee, instace


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
        self.extended_start = max(self.min_day, self.start_day - 1)
        self.extended_end = min(self.max_day, self.end_day + 1)

        self.window_instance = self.create_window_instance()

    def get_sliced_instance(self) -> instace.Instance:
        return self.window_instance

    def fix_first_and_last_day(self, solver_instance: solver.Solver):
        """Fixiert die Zuweisungen des ersten und letzten Tages des erweiterten Fensters mit den Werten der gegebenen Lösung."""

        # Fixiere den ersten Tag (extended_start)
        for shift_type_uid in solver_instance.instance.shift_types:
            for emp_id in solver_instance.instance.employees:
                assigned = self.sol.is_employee_assigned(
                    self.extended_start, shift_type_uid, emp_id
                )
                # Tag 0 in der window_instance entspricht extended_start in der alten Instanz
                var = solver_instance.vars.vars[(0, shift_type_uid, emp_id)]
                if assigned:
                    solver_instance.vars.model.Add(var == 1)
                else:
                    solver_instance.vars.model.Add(var == 0)

        # Fixiere den letzten Tag (extended_end)
        last_day_in_window = self.extended_end - self.extended_start
        for shift_type_uid in solver_instance.instance.shift_types:
            for emp_id in solver_instance.instance.employees:
                assigned = self.sol.is_employee_assigned(
                    self.extended_end, shift_type_uid, emp_id
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

        # edit employees
        employees = {}
        for uid, emp in old_instance.employees.items():
            emp_with_shifts = self.edit_max_numbers_of_shifts_for_emploeey(uid, emp)
            employees[uid] = self.edit_work_time_for_emploeey(uid, emp_with_shifts)

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

    def edit_max_numbers_of_shifts_for_emploeey(
        self, uid: employee.EmployeeUid, old_emp: employee.Employee
    ) -> employee.Employee:
        new_emp = old_emp.model_copy()

        # Zähle Shifts außerhalb des Windows für jeden Shift-Typ
        shifts_outside_window = {
            shift_type_uid: 0 for shift_type_uid in self.inst.shift_types
        }

        # Iteriere durch alle Tage außerhalb des erweiterten Windows
        for day in range(self.inst.number_of_days):
            if day < self.extended_start or day > self.extended_end:
                # Tag liegt außerhalb des Windows
                for shift_type_uid in self.inst.shift_types:
                    if self.sol.is_employee_assigned(day, shift_type_uid, uid):
                        shifts_outside_window[shift_type_uid] += 1

        # Passe max_numbers_of_shifts für jeden Shift-Typ an
        new_max_numbers_of_shifts = {}
        for shift_type_uid, max_shifts in old_emp.max_numbers_of_shifts.items():
            # Reduziere das Maximum um die bereits außerhalb zugewiesenen Shifts
            shifts_used_outside = shifts_outside_window.get(shift_type_uid, 0)
            assert max_shifts >= shifts_used_outside, (
                f"Employee {uid} has more shifts assigned outside the window ({shifts_used_outside}) "
                f"than their maximum allowed ({max_shifts}) for shift type {shift_type_uid}."
            )
            new_max = max(0, max_shifts - shifts_used_outside)
            new_max_numbers_of_shifts[shift_type_uid] = new_max

        new_emp.max_numbers_of_shifts = new_max_numbers_of_shifts
        return new_emp

    def edit_work_time_for_emploeey(
        self, uid: employee.EmployeeUid, old_emp: employee.Employee
    ) -> employee.Employee:
        new_emp = old_emp.model_copy()

        # Zähle Arbeitszeit (in Minuten) außerhalb des Windows
        minutes_outside_window = 0

        # Iteriere durch alle Tage außerhalb des erweiterten Windows
        for day in range(self.inst.number_of_days):
            if day < self.extended_start or day > self.extended_end:
                # Tag liegt außerhalb des Windows
                for shift_type_uid in self.inst.shift_types:
                    if self.sol.is_employee_assigned(day, shift_type_uid, uid):
                        # Hole die Länge des Shift-Typs
                        shift_type = self.inst.shift_types[shift_type_uid]
                        minutes_outside_window += shift_type.length

        # Passe max_minutes_assigned an
        assert old_emp.max_minutes_assigned >= minutes_outside_window, (
            f"Employee {uid} has more minutes assigned outside the window ({minutes_outside_window}) "
            f"than their maximum allowed ({old_emp.max_minutes_assigned})."
        )
        new_emp.max_minutes_assigned = max(
            0, old_emp.max_minutes_assigned - minutes_outside_window
        )

        # Passe auch min_minutes_assigned an
        new_emp.min_minutes_assigned = max(
            0, old_emp.min_minutes_assigned - minutes_outside_window
        )

        return new_emp
