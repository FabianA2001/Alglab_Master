from collections import defaultdict

from .. import solution, solver
from ..inputTypes import employee, instace
from . import solver_for_window
from .module.max_weekend_days import Max_weekend_days
from .module.minimum_consecutive_shifts import Minimum_consecutive_shifts


class Slice_instance:
    def __init__(self, sol: solution.Solution, start: int, end: int):
        self.sol = sol
        self.inst: instace.Instance = sol.instance
        self.start_day = start
        self.end_day = end

        self.window_instance = self.create_window_instance()

        self.config = defaultdict(solver_for_window.Config_for_employee)
        for emp_uid, emp in self.window_instance.employees.items():
            (
                self.config[emp_uid].max_consecutive_shifts_start,
                self.config[emp_uid].max_consecutive_shifts_end,
            ) = self.calulate_maximum_consecutive_shifts_config(emp_uid, emp)

            (
                self.config[emp_uid].min_consecutive_shifts_start,
                self.config[emp_uid].min_consecutive_shifts_end,
            ) = self.calulate_minimum_consecutive_shifts_config(emp_uid, emp)

            (
                self.config[emp_uid].min_consecutive_days_off_start,
                self.config[emp_uid].min_consecutive_days_off_end,
            ) = self.calulate_minimum_consecutive_days_off_config(emp_uid, emp)

        self.solvr = solver_for_window.Solver_for_window(
            self.window_instance,
            solver.shift_vars.Shift_vars(self.window_instance),
            self.config,
            add_module_constraints=[
                Minimum_consecutive_shifts(self.config),
                Max_weekend_days(self.start_day),
            ],
        )

        self.fix_first_and_last_day()

        # TODO rework to also use modules
        self.update_maximum_consecutive_shifts()
        self.update_minimum_consecutive_shifts()
        self.update_minimum_consecutive_days_off()

    def get_solver(self) -> solver_for_window.Solver_for_window:
        return self.solvr

    def fix_first_and_last_day(self):
        """Fixiert die Zuweisungen des ersten und letzten Tages des erweiterten Fensters mit den Werten der gegebenen Lösung."""

        if self.start_day != 0:
            # Fixiere den ersten Tag
            for shift_type_uid in self.solvr.instance.shift_types:
                for emp_id in self.solvr.instance.employees:
                    assigned = self.sol.is_employee_assigned(
                        self.start_day, shift_type_uid, emp_id
                    )
                    # Tag 0 in der window_instance entspricht extended_start in der alten Instanz
                    var = self.solvr.vars.vars[(0, shift_type_uid, emp_id)]
                    if assigned:
                        self.solvr.vars.model.Add(var == 1)
                    else:
                        self.solvr.vars.model.Add(var == 0)

        if self.end_day != self.inst.number_of_days - 1:
            last_day_in_window = self.solvr.instance.number_of_days - 1
            for shift_type_uid in self.solvr.instance.shift_types:
                for emp_id in self.solvr.instance.employees:
                    assigned = self.sol.is_employee_assigned(
                        self.end_day, shift_type_uid, emp_id
                    )
                    var = self.solvr.vars.vars[
                        (last_day_in_window, shift_type_uid, emp_id)
                    ]
                    if assigned:
                        self.solvr.vars.model.Add(var == 1)
                    else:
                        self.solvr.vars.model.Add(var == 0)

    def create_window_instance(self) -> instace.Instance:
        """Erstellt eine Instanz, die das aktuelle Suchfenster umfasst."""
        old_instance = self.sol.instance

        days_in_window = self.end_day - self.start_day + 1

        # edit employees
        employees = {}
        for uid, emp in old_instance.employees.items():
            emp_with_shifts = self.edit_max_numbers_of_shifts_for_emploeey(uid, emp)
            emp_with_work_time = self.edit_work_time_for_emploeey(uid, emp_with_shifts)
            emp_with_max_weekends = self.edit_max_weekends_for_employee(
                uid, emp_with_work_time
            )
            employees[uid] = self.edit_blocked_shifts_for_employee(
                uid, emp_with_max_weekends, self.start_day, self.end_day
            )

        # Kopiere shift_types (Referenz auf dieselben ShiftType-Objekte)
        shift_types = old_instance.shift_types.copy()

        # Erstelle neue shifts für das Fenster
        from collections import defaultdict

        shifts = defaultdict(dict)
        for day_offset in range(days_in_window):
            old_day = self.start_day + day_offset
            for shift_type_uid in old_instance.shift_types:
                # Kopiere den Shift vom alten Tag
                shifts[day_offset][shift_type_uid] = old_instance.get_shift(
                    old_day, shift_type_uid
                )

        # Berechne neue weekend_days (angepasst an neuen day-Index)
        weekend_days = set()
        for old_weekend_day in old_instance.weekend_days:
            if self.start_day <= old_weekend_day <= self.end_day:
                new_day = old_weekend_day - self.start_day
                weekend_days.add(new_day)

        # Erstelle neue Instanz mit __init__
        window_instance = instace.Instance(
            name=f"{old_instance.name}_window_{self.start_day}_{self.end_day}",
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

        # Iteriere durch alle Tage außerhalb des Windows
        for day in range(self.inst.number_of_days):
            if day < self.start_day or day > self.end_day:
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

        # Zähle Arbeitszeit (in Minuten) außerhalb des Windows UND an fixierten Tagen
        minutes_outside = 0

        # Iteriere durch alle Tage außerhalb des Windows
        for day in range(self.inst.number_of_days):
            if day < self.start_day or day > self.end_day:
                # Tag liegt außerhalb des Windows
                for shift_type_uid in self.inst.shift_types:
                    if self.sol.is_employee_assigned(day, shift_type_uid, uid):
                        # Hole die Länge des Shift-Typs
                        shift_type = self.inst.shift_types[shift_type_uid]
                        minutes_outside += shift_type.length

        # Passe max_minutes_assigned an
        assert old_emp.max_minutes_assigned >= minutes_outside, (
            f"Employee {uid} has more minutes assigned outside+fixed ({minutes_outside}) "
            f"than their maximum allowed ({old_emp.max_minutes_assigned})."
        )
        new_emp.max_minutes_assigned = max(
            0, old_emp.max_minutes_assigned - minutes_outside
        )

        # Passe auch min_minutes_assigned an
        new_emp.min_minutes_assigned = max(
            0, old_emp.min_minutes_assigned - minutes_outside
        )

        return new_emp

    def edit_blocked_shifts_for_employee(
        self,
        uid: employee.EmployeeUid,
        old_emp: employee.Employee,
        start: int,
        end: int,
    ) -> employee.Employee:
        """Adjust blocked_shifts days to the window's coordinate system."""
        new_emp = old_emp.model_copy()

        # Convert blocked_shifts from original instance days to window days
        new_blocked_shifts = set()
        for old_day in old_emp.blocked_shifts:
            # Only include blocked days that fall within the extended window
            if start <= old_day <= end:
                # Convert to window coordinate system (0-based)
                new_day = old_day - start

                new_blocked_shifts.add(new_day)

        new_emp.blocked_shifts = new_blocked_shifts
        return new_emp

    def edit_max_weekends_for_employee(
        self,
        uid: employee.EmployeeUid,
        old_emp: employee.Employee,
    ) -> employee.Employee:
        new_emp = old_emp.model_copy()
        for day in self.inst.weekend_days:
            if day < self.start_day or day > self.end_day:
                if self.sol.is_employee_assigned_ad_weekend(day, uid):
                    new_emp.max_number_weekends -= 1

        # TODO check if self.start_day == 1 needs special treatment
        if self.start_day > 0 and self.start_day in self.inst.weekend_days:
            assigned = []
            for shift_type_uid in self.inst.shift_types:
                if self.sol.is_employee_assigned(
                    self.start_day - 1, shift_type_uid, uid
                ) and not self.sol.is_employee_assigned(
                    self.start_day, shift_type_uid, uid
                ):
                    assigned.append(1)
                else:
                    assigned.append(0)
            if max(assigned):
                new_emp.max_number_weekends -= 1
        return new_emp

    def calulate_maximum_consecutive_shifts_config(
        self,
        emp_uid: employee.EmployeeUid,
        emp: employee.Employee,
    ) -> tuple[int, int]:
        """Erstellt eine Konfigurations-Dictionary für maximale aufeinanderfolgende Schichten pro Mitarbeiter."""
        current_consecutive_shifts = self.count_assigned_shifts_start(emp_uid)
        if current_consecutive_shifts < 0:
            current_consecutive_shifts = -current_consecutive_shifts

        assert emp.max_number_consecutive_shifts >= current_consecutive_shifts, (
            f"Employee {emp_uid} has {current_consecutive_shifts} consecutive shifts "
            f"before the window, which exceeds their maximum allowed "
            f"({emp.max_number_consecutive_shifts})."
        )
        start_vorbidden_days = (
            emp.max_number_consecutive_shifts - current_consecutive_shifts
        )
        current_consecutive_shifts = self.count_assigned_shifts_end(emp_uid)

        if current_consecutive_shifts < 0:
            current_consecutive_shifts = -current_consecutive_shifts

        assert emp.max_number_consecutive_shifts >= current_consecutive_shifts, (
            f"Employee {emp_uid} has {current_consecutive_shifts} consecutive shifts "
            f"after the window, which exceeds their maximum allowed "
            f"({emp.max_number_consecutive_shifts})."
        )
        end_vorbidden_days = (
            emp.max_number_consecutive_shifts - current_consecutive_shifts
        )
        assert start_vorbidden_days >= 0
        assert end_vorbidden_days >= 0
        return (start_vorbidden_days, end_vorbidden_days)

    def update_maximum_consecutive_shifts(self):
        """Aktualisiert die max_number_consecutive_shifts für alle Mitarbeiter basierend auf den Zuweisungen außerhalb des Fensters."""
        for emp_uid, emp in self.window_instance.employees.items():
            start_vorbidden_days = self.config[emp_uid].max_consecutive_shifts_start
            if start_vorbidden_days == 0:
                # Employee has reached max consecutive shifts before window
                # We need to block the first modifiable day in the window
                self.solvr.block_employee_on_day(emp_uid, 0)
            else:
                self.solvr.add_start_maximum_consecutive_shifts_constraints(emp_uid)

            end_vorbidden_days = self.config[emp_uid].max_consecutive_shifts_end
            if end_vorbidden_days == 0:
                # Employee has reached max consecutive shifts after window
                # We need to block the last modifiable day in the window
                last_day = self.solvr.instance.number_of_days - 1
                self.solvr.block_employee_on_day(emp_uid, last_day)
            else:
                # Still have room for more consecutive shifts, add constraint
                self.solvr.add_end_maximum_consecutive_shifts_constraints(emp_uid)

            self.solvr.add_custom_maximum_consecutive_shifts_constraints(emp_uid)

    def update_minimum_consecutive_shifts(self):
        """Aktualisiert die minimum consecutive shifts Constraints basierend auf self.config."""
        for emp_uid, emp in self.window_instance.employees.items():
            self.solvr.add_start_minimum_consecutive_shifts_constraints(emp_uid)
            self.solvr.add_end_minimum_consecutive_shifts_constraints(emp_uid)

    def update_minimum_consecutive_days_off(self):
        """Aktualisiert die minimum consecutive days-off Constraints basierend auf self.config."""
        for emp_uid, emp in self.window_instance.employees.items():
            self.solvr.add_start_minimum_consecutive_days_off_constraints(emp_uid)

            self.solvr.add_end_minimum_consecutive_days_off_constraints(emp_uid)

    def calulate_minimum_consecutive_shifts_config(
        self,
        emp_uid: employee.EmployeeUid,
        emp: employee.Employee,
    ) -> tuple[int, int]:
        """Calculate minimum consecutive shifts config for an employee.

        start_needed: how many more consecutive assigned days are required at the
        start of the window to satisfy the employee's min_number_consecutive_shifts.

        >= 0: assigned days needed
        == -1: start - 1 is not assigned
        == -2: no previus shifts, no restriction

        end_needed: same for the end of the window.
        """
        start_consecutive = self.count_assigned_shifts_start(emp_uid)
        # print(
        #     f"Employee {emp.name} has {start_consecutive} consecutive shifts before the window. Und benötigt {emp.min_number_consecutive_shifts}."
        # )
        if start_consecutive == 0:
            start_needed = -1
        elif start_consecutive < 0:
            start_needed = -2
        else:
            start_needed = max(0, emp.min_number_consecutive_shifts - start_consecutive)

        end_consecutive = self.count_assigned_shifts_end(emp_uid)
        if end_consecutive == 0:
            end_needed = -1
        elif end_consecutive < 0:
            end_needed = -2
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

        >= 0 free days needed
        == -1 no previus shifts, no restriction
        == -2 last shift start_day-1 => start_day ist first free day
        == -3 shifts at start_day

        end_needed: same for the end of the window.
        """
        if self.start_day != 0:
            start_free = self.count_not_assigned_shifts_start(emp_uid)
            if start_free < 0:
                start_needed = -1
            elif start_free == 0:
                shifts = []
                for shift_type_uid in self.inst.shift_types:
                    if self.sol.is_employee_assigned(
                        self.start_day, shift_type_uid, emp_uid
                    ):
                        shifts.append(1)
                    else:
                        shifts.append(0)
                if max(shifts):
                    start_needed = -3
                else:
                    start_needed = -2
            else:
                start_needed = max(0, emp.min_number_consecutive_days_off - start_free)
        else:
            start_needed = 0

        if self.end_day != self.inst.number_of_days - 1:
            end_free = self.count_not_assigned_shifts_end(emp_uid)
            if end_free < 0:
                end_needed = -1
            elif end_free == 0:
                shifts = []
                for shift_type_uid in self.inst.shift_types:
                    if self.sol.is_employee_assigned(
                        self.end_day, shift_type_uid, emp_uid
                    ):
                        shifts.append(1)
                    else:
                        shifts.append(0)
                if max(shifts):
                    end_needed = -3
                else:
                    end_needed = -2
            else:
                end_needed = max(0, emp.min_number_consecutive_days_off - end_free)
        else:
            end_needed = 0

        return (start_needed, end_needed)

    def count_assigned_shifts_start(self, emp_uid: employee.EmployeeUid) -> int:
        current_consecutive_shifts = 0
        if self.start_day < 1:
            return -1
        for day in range(self.start_day - 1, -1, -1):
            assigneds = []
            for shift_type_uid in self.inst.shift_types:
                assigneds.append(
                    self.sol.is_employee_assigned(day, shift_type_uid, emp_uid)
                )  # None bedeutet beliebiger Shift-Typ
            if max(assigneds):
                current_consecutive_shifts += 1
            else:
                return current_consecutive_shifts

        assert current_consecutive_shifts > 0
        return -current_consecutive_shifts

    def count_not_assigned_shifts_start(self, emp_uid: employee.EmployeeUid) -> int:
        current_free_consecutive_shifts = 0
        if self.start_day < 1:
            return current_free_consecutive_shifts
        for day in range(self.start_day - 1, -1, -1):
            not_assigneds = []
            for shift_type_uid in self.inst.shift_types:
                not_assigneds.append(
                    self.sol.is_employee_assigned(day, shift_type_uid, emp_uid)
                )  # None bedeutet beliebiger Shift-Typ
            if max(not_assigneds):
                return current_free_consecutive_shifts
            else:
                current_free_consecutive_shifts += 1

        assert current_free_consecutive_shifts > 0
        return -current_free_consecutive_shifts

    def count_assigned_shifts_end(self, emp_uid: employee.EmployeeUid) -> int:
        current_consecutive_shifts = 0
        if self.inst.number_of_days - 2 < self.end_day:
            return -1
        for day in range(self.end_day + 1, self.sol.instance.number_of_days):
            assigneds = []
            for shift_type_uid in self.inst.shift_types:
                assigneds.append(
                    self.sol.is_employee_assigned(day, shift_type_uid, emp_uid)
                )  # None bedeutet beliebiger Shift-Typ
            if max(assigneds):
                current_consecutive_shifts += 1
            else:
                return current_consecutive_shifts

        assert current_consecutive_shifts > 0
        return -current_consecutive_shifts

    def count_not_assigned_shifts_end(self, emp_uid: employee.EmployeeUid) -> int:
        current_free_consecutive_shifts = 0
        if self.inst.number_of_days - 2 < self.end_day:
            return current_free_consecutive_shifts
        for day in range(self.end_day + 1, self.sol.instance.number_of_days):
            assigneds = []
            for shift_type_uid in self.inst.shift_types:
                assigneds.append(
                    self.sol.is_employee_assigned(day, shift_type_uid, emp_uid)
                )  # None bedeutet beliebiger Shift-Typ
            if max(assigneds):
                return current_free_consecutive_shifts
            else:
                current_free_consecutive_shifts += 1

        assert current_free_consecutive_shifts > 0
        return -current_free_consecutive_shifts
