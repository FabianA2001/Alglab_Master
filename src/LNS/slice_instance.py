from collections import defaultdict

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
        self.extended_start = (
            self.start_day - 1 if self.start_day > self.min_day else -1
        )
        self.extended_end = self.end_day + 1 if self.end_day < self.max_day else -1

        self.window_instance = self.create_window_instance()

        config = defaultdict(solver_for_window.Config_for_employee)
        for emp_uid, emp in self.window_instance.employees.items():
            (
                config[emp_uid].max_consecutive_shifts_start,
                config[emp_uid].max_consecutive_shifts_end,
            ) = self.calulate_maximum_consecutive_shifts_config(emp_uid, emp)

            (
                config[emp_uid].min_consecutive_shifts_start,
                config[emp_uid].min_consecutive_shifts_end,
            ) = self.calulate_minimum_consecutive_shifts_config(emp_uid, emp)

            (
                config[emp_uid].min_consecutive_days_off_start,
                config[emp_uid].min_consecutive_days_off_end,
            ) = self.calulate_minimum_consecutive_days_off_config(emp_uid, emp)
        self.config = config

        self.solvr = solver_for_window.Solver_for_window(
            self.window_instance,
            solver.shift_vars.Shift_vars(self.window_instance),
            config,
            # add_module_constraints=[
            #     LNS_Max_Cons_Shifts(maximum_consecutive_shifts_config)
            # ],
        )
        self.fix_first_and_last_day(self.solvr)

        # TODO rework to also use modules
        self.update_maximum_consecutive_shifts()
        self.update_minimum_consecutive_shifts()
        self.update_minimum_consecutive_days_off()

    def get_solver(self) -> solver_for_window.Solver_for_window:
        return self.solvr

    def fix_first_and_last_day(self, solver_instance: solver.Solver):
        """Fixiert die Zuweisungen des ersten und letzten Tages des erweiterten Fensters mit den Werten der gegebenen Lösung."""

        if self.extended_start != -1:
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

        if self.extended_end != -1:
            # Calculate the actual window boundaries independent of extended_start
            window_start = max(self.min_day, self.start_day - 1)
            last_day_in_window = self.extended_end - window_start
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
        window_start = max(self.min_day, self.start_day - 1)
        window_end = min(self.max_day, self.end_day + 1)
        days_in_window = window_end - window_start + 1

        # edit employees
        employees = {}
        for uid, emp in old_instance.employees.items():
            emp_with_shifts = self.edit_max_numbers_of_shifts_for_emploeey(uid, emp)
            emp_with_work_time = self.edit_work_time_for_emploeey(uid, emp_with_shifts)
            employees[uid] = self.edit_blocked_shifts_for_employee(
                uid, emp_with_work_time, window_start, window_end
            )

        # Kopiere shift_types (Referenz auf dieselben ShiftType-Objekte)
        shift_types = old_instance.shift_types.copy()

        # Erstelle neue shifts für das erweiterte Fenster
        from collections import defaultdict

        shifts = defaultdict(dict)
        for day_offset in range(days_in_window):
            old_day = window_start + day_offset
            for shift_type_uid in old_instance.shift_types:
                # Kopiere den Shift vom alten Tag
                shifts[day_offset][shift_type_uid] = old_instance.get_shift(
                    old_day, shift_type_uid
                )

        # Berechne neue weekend_days (angepasst an neuen day-Index)
        weekend_days = set()
        for old_weekend_day in old_instance.weekend_days:
            if window_start <= old_weekend_day <= window_end:
                new_day = old_weekend_day - window_start
                weekend_days.add(new_day)

        # Erstelle neue Instanz mit __init__
        window_instance = instace.Instance(
            name=f"{old_instance.name}_window_{window_start}_{window_end}",
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

        # Berechne die tatsächlichen Fenstergrenzen (wie in create_window_instance)
        window_start = max(self.min_day, self.start_day - 1)
        window_end = min(self.max_day, self.end_day + 1)

        # Iteriere durch alle Tage außerhalb des erweiterten Windows
        for day in range(self.inst.number_of_days):
            if day < window_start or day > window_end:
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

        # Berechne die tatsächlichen Fenstergrenzen (wie in create_window_instance)
        window_start = max(self.min_day, self.start_day - 1)
        window_end = min(self.max_day, self.end_day + 1)

        # Iteriere durch alle Tage außerhalb des erweiterten Windows
        for day in range(self.inst.number_of_days):
            if day < window_start or day > window_end:
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

    def calulate_maximum_consecutive_shifts_config(
        self,
        emp_uid: employee.EmployeeUid,
        emp: employee.Employee,
    ) -> tuple[int, int]:
        """Erstellt eine Konfigurations-Dictionary für maximale aufeinanderfolgende Schichten pro Mitarbeiter."""
        current_consecutive_shifts = self.count_assigned_shifts_start(emp_uid)
        start_vorbidden_days = (
            max(0, emp.max_number_consecutive_shifts - current_consecutive_shifts)
            if current_consecutive_shifts != 0
            else 0
        )
        current_consecutive_shifts = self.count_assigned_shifts_end(emp_uid)

        assert emp.max_number_consecutive_shifts >= current_consecutive_shifts, (
            f"Employee {emp_uid} has {current_consecutive_shifts} consecutive shifts "
            f"after the window, which exceeds their maximum allowed "
            f"({emp.max_number_consecutive_shifts})."
        )
        end_vorbidden_days = (
            (emp.max_number_consecutive_shifts - current_consecutive_shifts)
            if current_consecutive_shifts != 0
            else 0
        )
        return (start_vorbidden_days, end_vorbidden_days)

    def update_maximum_consecutive_shifts(self):
        """Aktualisiert die max_number_consecutive_shifts für alle Mitarbeiter basierend auf den Zuweisungen außerhalb des Fensters."""
        for emp_uid, emp in self.window_instance.employees.items():
            end_vorbidden_days = self.config[emp_uid].max_consecutive_shifts_end

            self.solvr.add_start_maximum_consecutive_shifts_constraints(emp_uid)
            if end_vorbidden_days == 0:
                # Employee has reached max consecutive shifts after window
                # We need to block the last modifiable day in the window
                if self.extended_end != -1:
                    # Last modifiable day is before the fixed extended_end day
                    last_modifiable_day = self.solvr.instance.number_of_days - 2
                    self.solvr.block_employee_on_day(emp_uid, last_modifiable_day)
            else:
                # Still have room for more consecutive shifts, add constraint
                self.solvr.add_end_maximum_consecutive_shifts_constraints(emp_uid)

    def update_minimum_consecutive_shifts(self):
        """Aktualisiert die minimum consecutive shifts Constraints basierend auf self.config."""
        for emp_uid, emp in self.window_instance.employees.items():
            start_needed = self.config[emp_uid].min_consecutive_shifts_start
            end_needed = self.config[emp_uid].min_consecutive_shifts_end

            if start_needed > 0:
                self.solvr.add_start_minimum_consecutive_shifts_constraints(emp_uid)

            if end_needed > 0:
                self.solvr.add_end_minimum_consecutive_shifts_constraints(emp_uid)

    def update_minimum_consecutive_days_off(self):
        """Aktualisiert die minimum consecutive days-off Constraints basierend auf self.config."""
        for emp_uid, emp in self.window_instance.employees.items():
            start_needed = self.config[emp_uid].min_consecutive_days_off_start
            end_needed = self.config[emp_uid].min_consecutive_days_off_end

            if start_needed > 0:
                self.solvr.add_start_minimum_consecutive_days_off_constraints(emp_uid)

            if end_needed > 0:
                self.solvr.add_end_minimum_consecutive_days_off_constraints(emp_uid)

    def calulate_minimum_consecutive_shifts_config(
        self,
        emp_uid: employee.EmployeeUid,
        emp: employee.Employee,
    ) -> tuple[int, int]:
        """Calculate minimum consecutive shifts config for an employee.

        start_needed: how many more consecutive assigned days are required at the
        start of the window to satisfy the employee's min_number_consecutive_shifts.

        end_needed: same for the end of the window.
        """
        start_consecutive = self.count_assigned_shifts_start(emp_uid)
        if start_consecutive == 0:
            start_needed = 0
        else:
            start_needed = max(0, emp.min_number_consecutive_shifts - start_consecutive)

        end_consecutive = self.count_assigned_shifts_end(emp_uid)
        if end_consecutive == 0:
            end_needed = 0
        else:
            end_needed = max(0, emp.min_number_consecutive_shifts - end_consecutive)

        return (start_needed, end_needed)

    def calulate_minimum_consecutive_days_off_config(
        self,
        emp_uid: employee.EmployeeUid,
        emp: employee.Employee,
    ) -> tuple[int, int]:
        """Calculate minimum consecutive days-off config for an employee.

        start_needed: how many more consecutive days-off are required at the start of the window
        to satisfy min_number_consecutive_days_off.

        end_needed: same for the end of the window.
        """
        start_free = self.count_not_assigned_shifts_start(emp_uid)
        if start_free == 0:
            start_needed = 0
        else:
            start_needed = max(0, emp.min_number_consecutive_days_off - start_free)

        end_free = self.count_not_assigned_shifts_end(emp_uid)
        if end_free == 0:
            end_needed = 0
        else:
            end_needed = max(0, emp.min_number_consecutive_days_off - end_free)

        return (start_needed, end_needed)

    def count_assigned_shifts_start(self, emp_uid: employee.EmployeeUid) -> int:
        current_consecutive_shifts = 0
        for day in range(self.start_day - 1, self.min_day - 1, -1):
            assigneds = []
            for shift_type_uid in self.inst.shift_types:
                assigneds.append(
                    self.sol.is_employee_assigned(day, shift_type_uid, emp_uid)
                )  # None bedeutet beliebiger Shift-Typ
            if max(assigneds):
                current_consecutive_shifts += 1
            else:
                break  # Stoppe, wenn ein freier Tag gefunden wird
        return current_consecutive_shifts

    def count_not_assigned_shifts_start(self, emp_uid: employee.EmployeeUid) -> int:
        current_free_consecutive_shifts = 0
        for day in range(self.start_day - 1, self.min_day - 1, -1):
            not_assigneds = []
            for shift_type_uid in self.inst.shift_types:
                not_assigneds.append(
                    self.sol.is_employee_assigned(day, shift_type_uid, emp_uid)
                )  # None bedeutet beliebiger Shift-Typ
            if max(not_assigneds):
                break
            else:
                current_free_consecutive_shifts += 1

        return current_free_consecutive_shifts

    def count_assigned_shifts_end(self, emp_uid: employee.EmployeeUid) -> int:
        current_consecutive_shifts = 0
        for day in range(self.end_day + 1, self.max_day + 1):
            assigneds = []
            for shift_type_uid in self.inst.shift_types:
                assigneds.append(
                    self.sol.is_employee_assigned(day, shift_type_uid, emp_uid)
                )  # None bedeutet beliebiger Shift-Typ
            if max(assigneds):
                current_consecutive_shifts += 1
            else:
                break  # Stoppe, wenn ein freier Tag gefunden wird
        return current_consecutive_shifts

    def count_not_assigned_shifts_end(self, emp_uid: employee.EmployeeUid) -> int:
        current_free_consecutive_shifts = 0
        for day in range(self.end_day + 1, self.max_day + 1):
            assigneds = []
            for shift_type_uid in self.inst.shift_types:
                assigneds.append(
                    self.sol.is_employee_assigned(day, shift_type_uid, emp_uid)
                )  # None bedeutet beliebiger Shift-Typ
            if max(assigneds):
                break
            else:
                current_free_consecutive_shifts += 1
        return current_free_consecutive_shifts
