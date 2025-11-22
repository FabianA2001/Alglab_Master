from .. import solution, solver
from ..inputTypes import employee, instace
from . import solver_for_window


class Slice_instance:
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

        self.solvr = solver_for_window.Solver_for_window(
            self.window_instance, solver.shift_vars.Shift_vars(self.window_instance)
        )
        self.fix_first_and_last_day(self.solvr)
        # # TODO rework to also use modules
        self.update_maximum_consecutive_shifts()
        self.update_minimum_consecutive_shifts()
        self.update_minimum_consecutive_days_off()

    def get_solver(self) -> solver_for_window.Solver_for_window:
        return self.solvr

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
            emp_with_work_time = self.edit_work_time_for_emploeey(uid, emp_with_shifts)
            employees[uid] = self.edit_blocked_shifts_for_employee(
                uid, emp_with_work_time, extended_start, extended_end
            )

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

    def edit_blocked_shifts_for_employee(
        self,
        uid: employee.EmployeeUid,
        old_emp: employee.Employee,
        extended_start: int,
        extended_end: int,
    ) -> employee.Employee:
        """Adjust blocked_shifts days to the window's coordinate system."""
        new_emp = old_emp.model_copy()

        # Convert blocked_shifts from original instance days to window days
        new_blocked_shifts = set()
        for old_day in old_emp.blocked_shifts:
            # Only include blocked days that fall within the extended window
            if extended_start <= old_day <= extended_end:
                # Convert to window coordinate system (0-based)
                new_day = old_day - extended_start
                new_blocked_shifts.add(new_day)

        new_emp.blocked_shifts = new_blocked_shifts
        return new_emp

    def update_maximum_consecutive_shifts(self):
        """Aktualisiert die max_number_consecutive_shifts für alle Mitarbeiter basierend auf den Zuweisungen außerhalb des Fensters."""
        for emp_uid, emp in self.window_instance.employees.items():
            # Zähle die assingend tage for den erweiterten Starttag rückwärts
            current_consecutive_shifts = 0
            for day in range(self.extended_start - 1, -1, self.max_day + 1):
                for shift_type_uid in self.inst.shift_types:
                    is_assigned = self.sol.is_employee_assigned(
                        day, shift_type_uid, emp_uid
                    )  # None bedeutet beliebiger Shift-Typ
                    if is_assigned:
                        current_consecutive_shifts += 1
                    else:
                        break  # Stoppe, wenn ein freier Tag gefunden wird
            if current_consecutive_shifts == 0:
                continue

            remaing_forbidden_days = max(
                0, emp.max_number_consecutive_shifts - current_consecutive_shifts
            )
            self.solvr.add_start_maximum_consecutive_shifts_constraints(
                emp_uid, remaing_forbidden_days
            )

        # Zähle die assigned Tage nach dem erweiterten Endtag vorwärts
        for emp_uid, emp in self.window_instance.employees.items():
            current_consecutive_shifts = 0
            for day in range(self.extended_end + 1, self.max_day + 1):
                for shift_type_uid in self.inst.shift_types:
                    is_assigned = self.sol.is_employee_assigned(
                        day, shift_type_uid, emp_uid
                    )
                    if is_assigned:
                        current_consecutive_shifts += 1
                    else:
                        break  # Stoppe, wenn ein freier Tag gefunden wird
            if current_consecutive_shifts == 0:
                continue

            remaing_forbidden_days = max(
                0, emp.max_number_consecutive_shifts - current_consecutive_shifts
            )
            self.solvr.add_end_maximum_consecutive_shifts_constraints(
                emp_uid, remaing_forbidden_days
            )

    def update_minimum_consecutive_shifts(self):
        for emp_uid, emp in self.window_instance.employees.items():
            # Zähle die assingend tage for den erweiterten Starttag rückwärts
            current_consecutive_shifts = 0
            for day in range(self.extended_start - 1, -1, self.max_day + 1):
                for shift_type_uid in self.inst.shift_types:
                    is_assigned = self.sol.is_employee_assigned(
                        day, shift_type_uid, emp_uid
                    )  # None bedeutet beliebiger Shift-Typ
                    if is_assigned:
                        current_consecutive_shifts += 1
                    else:
                        break  # Stoppe, wenn ein freier Tag gefunden wird
            if current_consecutive_shifts == 0:
                continue

            remaing_needet_days = max(
                0, emp.min_number_consecutive_shifts - current_consecutive_shifts
            )
            self.solvr.add_start_minimum_consecutive_shifts_constraints(
                emp_uid, remaing_needet_days
            )

        # Zähle die assigned Tage nach dem erweiterten Endtag vorwärts
        for emp_uid, emp in self.window_instance.employees.items():
            current_consecutive_shifts = 0
            for day in range(self.extended_end + 1, self.max_day + 1):
                for shift_type_uid in self.inst.shift_types:
                    is_assigned = self.sol.is_employee_assigned(
                        day, shift_type_uid, emp_uid
                    )
                    if is_assigned:
                        current_consecutive_shifts += 1
                    else:
                        break  # Stoppe, wenn ein freier Tag gefunden wird
            if current_consecutive_shifts == 0:
                continue

            remaing_needet_days = max(
                0, emp.min_number_consecutive_shifts - current_consecutive_shifts
            )
            self.solvr.add_end_minimum_consecutive_shifts_constraints(
                emp_uid, remaing_needet_days
            )

    def update_minimum_consecutive_days_off(self):
        for emp_uid, emp in self.window_instance.employees.items():
            # Zähle die freien tage for den erweiterten Starttag rückwärts
            current_consecutive_days_off = 0
            for day in range(self.extended_start - 1, -1, self.max_day + 1):
                is_assigned_any_shift = False
                for shift_type_uid in self.inst.shift_types:
                    if self.sol.is_employee_assigned(day, shift_type_uid, emp_uid):
                        is_assigned_any_shift = True
                        break
                if not is_assigned_any_shift:
                    current_consecutive_days_off += 1
                else:
                    break  # Stoppe, wenn ein Arbeitstag gefunden wird
            if current_consecutive_days_off == 0:
                continue

            remaing_needet_days_off = max(
                0, emp.min_number_consecutive_days_off - current_consecutive_days_off
            )
            self.solvr.add_start_minimum_consecutive_days_off_constraints(
                emp_uid, remaing_needet_days_off
            )

        # Zähle die freien Tage nach dem erweiterten Endtag vorwärts
        for emp_uid, emp in self.window_instance.employees.items():
            current_consecutive_days_off = 0
            for day in range(self.extended_end + 1, self.max_day + 1):
                is_assigned_any_shift = False
                for shift_type_uid in self.inst.shift_types:
                    if self.sol.is_employee_assigned(day, shift_type_uid, emp_uid):
                        is_assigned_any_shift = True
                        break
                if not is_assigned_any_shift:
                    current_consecutive_days_off += 1
                else:
                    break  # Stoppe, wenn ein Arbeitstag gefunden wird
            if current_consecutive_days_off == 0:
                continue

            remaing_needet_days_off = max(
                0, emp.min_number_consecutive_days_off - current_consecutive_days_off
            )
            self.solvr.add_end_minimum_consecutive_days_off_constraints(
                emp_uid, remaing_needet_days_off
            )
