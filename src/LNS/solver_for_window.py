from ortools.sat.python import cp_model

from .. import solver
from ..inputTypes import employee
from ..solution import Solution


class Solver_for_window(solver.Solver):
    def solve_window(
        self,
        log_search_progress: bool = True,
        max_time_in_seconds: float = 60.0,
        stop_after_first_solution: bool = False,
        callback: cp_model.CpSolverSolutionCallback | None = None,
        **solver_params,
    ) -> Solution:
        # TODO : add support for disabling constraints in the windowed solver
        return super().solve(
            log_search_progress=log_search_progress,
            max_time_in_seconds=max_time_in_seconds,
            stop_after_first_solution=stop_after_first_solution,
            callback=callback,
            **solver_params,
        )

    def add_start_maximum_consecutive_shifts_constraints(
        self, employee_uid: employee.EmployeeUid, max_consecutive_shifts: int
    ):
        if max_consecutive_shifts <= 0:
            return
        # prefix_active[i] = 1, wenn bis i-1 alle TRUE sind
        prefix_active = [
            self.vars.model.NewBoolVar(f"prefix_active_{i}_for_{employee_uid}")
            for i in range(max_consecutive_shifts)
        ]
        prefix_true = [
            self.vars.model.NewBoolVar(f"prefix_true_{i}")
            for i in range(max_consecutive_shifts)
        ]
        for i in range(max_consecutive_shifts):
            day = i
            # prefix_true[i] = 1, wenn an Tag i der Mitarbeiter einen Dienst hat
            shift_vars = [
                self.vars.vars[(day, shift_type_uid, employee_uid)]
                for shift_type_uid in self.instance.shift_types
            ]
            self.vars.model.AddMaxEquality(prefix_true[i], shift_vars)

            if i == 0:
                # prefix_active[0] = 1
                self.vars.model.Add(prefix_active[0] == 1)
            else:
                # prefix_active[i] = prefix_active[i-1] AND prefix_true[i-1]
                self.vars.model.AddBoolAnd(
                    [prefix_active[i - 1], prefix_true[i - 1]]
                ).OnlyEnforceIf(prefix_active[i])
                self.vars.model.AddBoolOr(
                    [prefix_active[i - 1].Not(), prefix_true[i - 1].Not()]
                ).OnlyEnforceIf(prefix_active[i].Not())

    def add_end_maximum_consecutive_shifts_constraints(
        self, employee_uid: employee.EmployeeUid, max_consecutive_shifts: int
    ):
        if max_consecutive_shifts <= 0:
            return
        # suffix_active[i] = 1, wenn von i+1 bis Ende alle TRUE sind
        suffix_active = [
            self.vars.model.NewBoolVar(f"suffix_active_{i}_for_{employee_uid}")
            for i in range(max_consecutive_shifts)
        ]
        suffix_true = [
            self.vars.model.NewBoolVar(f"suffix_true_{i}")
            for i in range(max_consecutive_shifts)
        ]
        for i in range(max_consecutive_shifts):
            day = self.instance.number_of_days - max_consecutive_shifts + i
            # suffix_true[i] = 1, wenn an Tag day der Mitarbeiter einen Dienst hat
            shift_vars = [
                self.vars.vars[(day, shift_type_uid, employee_uid)]
                for shift_type_uid in self.instance.shift_types
            ]
            self.vars.model.AddMaxEquality(suffix_true[i], shift_vars)

            if i == max_consecutive_shifts - 1:
                # suffix_active[last] = 1
                self.vars.model.Add(suffix_active[i] == 1)
            else:
                # suffix_active[i] = suffix_active[i+1] AND suffix_true[i+1]
                self.vars.model.AddBoolAnd(
                    [suffix_active[i + 1], suffix_true[i + 1]]
                ).OnlyEnforceIf(suffix_active[i])
                self.vars.model.AddBoolOr(
                    [suffix_active[i + 1].Not(), suffix_true[i + 1].Not()]
                ).OnlyEnforceIf(suffix_active[i].Not())

    def add_start_minimum_consecutive_shifts_constraints(
        self, employee_uid: employee.EmployeeUid, min_consecutive_shifts: int
    ):
        if min_consecutive_shifts <= 0:
            return
        # Prüft, ob am Anfang des Fensters die Mindestanzahl aufeinanderfolgender Schichten eingehalten wird
        # Wenn eine Schicht am Anfang startet, müssen mindestens min_consecutive_shifts Schichten folgen
        for start_day in range(min_consecutive_shifts):
            # has_shift[i] = 1, wenn an Tag i der Mitarbeiter einen Dienst hat
            has_shift = [
                self.vars.model.NewBoolVar(
                    f"start_min_cons_has_shift_{start_day}_{i}_for_{employee_uid}"
                )
                for i in range(min_consecutive_shifts)
            ]

            for i in range(min_consecutive_shifts):
                day = start_day + i
                if day >= self.instance.number_of_days:
                    break
                shift_vars = [
                    self.vars.vars[(day, shift_type_uid, employee_uid)]
                    for shift_type_uid in self.instance.shift_types
                ]
                self.vars.model.AddMaxEquality(has_shift[i], shift_vars)

            # Wenn start_day eine Schicht hat und start_day-1 keine Schicht hat (oder start_day=0),
            # dann müssen die nächsten min_consecutive_shifts Tage alle Schichten haben
            if start_day == 0:
                # Wenn Tag 0 eine Schicht hat, müssen die nächsten min_consecutive_shifts-1 Tage auch Schichten haben
                for i in range(
                    1,
                    min(
                        min_consecutive_shifts, self.instance.number_of_days - start_day
                    ),
                ):
                    self.vars.model.Add(has_shift[i] == 1).OnlyEnforceIf(has_shift[0])
            else:
                # Prüfe ob vorheriger Tag keine Schicht hat
                prev_shift_vars = [
                    self.vars.vars[(start_day - 1, shift_type_uid, employee_uid)]
                    for shift_type_uid in self.instance.shift_types
                ]
                has_prev_shift = self.vars.model.NewBoolVar(
                    f"start_min_cons_has_prev_{start_day}_for_{employee_uid}"
                )
                self.vars.model.AddMaxEquality(has_prev_shift, prev_shift_vars)

                # Wenn start_day Schicht hat UND start_day-1 keine hat, dann Mindestanzahl erzwingen
                starts_here = self.vars.model.NewBoolVar(
                    f"start_min_cons_starts_{start_day}_for_{employee_uid}"
                )
                self.vars.model.AddBoolAnd(
                    [has_shift[0], has_prev_shift.Not()]
                ).OnlyEnforceIf(starts_here)
                self.vars.model.AddBoolOr(
                    [has_shift[0].Not(), has_prev_shift]
                ).OnlyEnforceIf(starts_here.Not())

                for i in range(
                    1,
                    min(
                        min_consecutive_shifts, self.instance.number_of_days - start_day
                    ),
                ):
                    self.vars.model.Add(has_shift[i] == 1).OnlyEnforceIf(starts_here)

    def add_end_minimum_consecutive_shifts_constraints(
        self, employee_uid: employee.EmployeeUid, min_consecutive_shifts: int
    ):
        if min_consecutive_shifts <= 0:
            return
        # Prüft, ob am Ende des Fensters die Mindestanzahl aufeinanderfolgender Schichten eingehalten wird
        # Wenn eine Schicht am Ende endet, müssen mindestens min_consecutive_shifts Schichten davor sein
        for end_day in range(
            self.instance.number_of_days - min_consecutive_shifts,
            self.instance.number_of_days,
        ):
            # has_shift[i] = 1, wenn an Tag (end_day - min_consecutive_shifts + 1 + i) der Mitarbeiter einen Dienst hat
            has_shift = [
                self.vars.model.NewBoolVar(
                    f"end_min_cons_has_shift_{end_day}_{i}_for_{employee_uid}"
                )
                for i in range(min_consecutive_shifts)
            ]

            for i in range(min_consecutive_shifts):
                day = end_day - min_consecutive_shifts + 1 + i
                if day < 0:
                    continue
                shift_vars = [
                    self.vars.vars[(day, shift_type_uid, employee_uid)]
                    for shift_type_uid in self.instance.shift_types
                ]
                self.vars.model.AddMaxEquality(has_shift[i], shift_vars)

            # Wenn end_day eine Schicht hat und end_day+1 keine Schicht hat (oder end_day=last),
            # dann müssen die vorherigen min_consecutive_shifts Tage alle Schichten haben
            if end_day == self.instance.number_of_days - 1:
                # Wenn letzter Tag eine Schicht hat, müssen die vorherigen min_consecutive_shifts-1 Tage auch Schichten haben
                for i in range(
                    max(
                        0,
                        min_consecutive_shifts
                        - (self.instance.number_of_days - end_day),
                    )
                ):
                    if end_day - min_consecutive_shifts + 1 + i >= 0:
                        self.vars.model.Add(has_shift[i] == 1).OnlyEnforceIf(
                            has_shift[-1]
                        )
            else:
                # Prüfe ob nächster Tag keine Schicht hat
                next_shift_vars = [
                    self.vars.vars[(end_day + 1, shift_type_uid, employee_uid)]
                    for shift_type_uid in self.instance.shift_types
                ]
                has_next_shift = self.vars.model.NewBoolVar(
                    f"end_min_cons_has_next_{end_day}_for_{employee_uid}"
                )
                self.vars.model.AddMaxEquality(has_next_shift, next_shift_vars)

                # Wenn end_day Schicht hat UND end_day+1 keine hat, dann Mindestanzahl erzwingen
                ends_here = self.vars.model.NewBoolVar(
                    f"end_min_cons_ends_{end_day}_for_{employee_uid}"
                )
                self.vars.model.AddBoolAnd(
                    [has_shift[-1], has_next_shift.Not()]
                ).OnlyEnforceIf(ends_here)
                self.vars.model.AddBoolOr(
                    [has_shift[-1].Not(), has_next_shift]
                ).OnlyEnforceIf(ends_here.Not())

                for i in range(max(0, min_consecutive_shifts - 1)):
                    if end_day - min_consecutive_shifts + 1 + i >= 0:
                        self.vars.model.Add(has_shift[i] == 1).OnlyEnforceIf(ends_here)

    def add_start_minimum_consecutive_days_off_constraints(
        self, employee_uid: employee.EmployeeUid, min_consecutive_days_off: int
    ):
        if min_consecutive_days_off <= 0:
            return
        # Prüft, ob am Anfang des Fensters die Mindestanzahl aufeinanderfolgender freier Tage eingehalten wird
        # Wenn eine freie Tag-Sequenz am Anfang startet, müssen mindestens min_consecutive_days_off Tage frei sein
        for start_day in range(min_consecutive_days_off):
            # has_day_off[i] = 1, wenn an Tag i der Mitarbeiter keinen Dienst hat
            has_day_off = [
                self.vars.model.NewBoolVar(
                    f"start_min_days_off_has_day_off_{start_day}_{i}_for_{employee_uid}"
                )
                for i in range(min_consecutive_days_off)
            ]

            for i in range(min_consecutive_days_off):
                day = start_day + i
                if day >= self.instance.number_of_days:
                    break
                shift_vars = [
                    self.vars.vars[(day, shift_type_uid, employee_uid)]
                    for shift_type_uid in self.instance.shift_types
                ]
                has_shift = self.vars.model.NewBoolVar(
                    f"start_min_days_off_has_shift_{start_day}_{i}_for_{employee_uid}"
                )
                self.vars.model.AddMaxEquality(has_shift, shift_vars)
                # has_day_off[i] = NOT has_shift
                self.vars.model.Add(has_day_off[i] == 1 - has_shift)

            # Wenn start_day ein freier Tag ist und start_day-1 eine Schicht hat (oder start_day=0),
            # dann müssen die nächsten min_consecutive_days_off Tage alle frei sein
            if start_day == 0:
                # Wenn Tag 0 frei ist, müssen die nächsten min_consecutive_days_off-1 Tage auch frei sein
                for i in range(
                    1,
                    min(
                        min_consecutive_days_off,
                        self.instance.number_of_days - start_day,
                    ),
                ):
                    self.vars.model.Add(has_day_off[i] == 1).OnlyEnforceIf(
                        has_day_off[0]
                    )
            else:
                # Prüfe ob vorheriger Tag eine Schicht hat
                prev_shift_vars = [
                    self.vars.vars[(start_day - 1, shift_type_uid, employee_uid)]
                    for shift_type_uid in self.instance.shift_types
                ]
                has_prev_shift = self.vars.model.NewBoolVar(
                    f"start_min_days_off_has_prev_{start_day}_for_{employee_uid}"
                )
                self.vars.model.AddMaxEquality(has_prev_shift, prev_shift_vars)

                # Wenn start_day frei ist UND start_day-1 eine Schicht hat, dann Mindestanzahl erzwingen
                starts_here = self.vars.model.NewBoolVar(
                    f"start_min_days_off_starts_{start_day}_for_{employee_uid}"
                )
                self.vars.model.AddBoolAnd(
                    [has_day_off[0], has_prev_shift]
                ).OnlyEnforceIf(starts_here)
                self.vars.model.AddBoolOr(
                    [has_day_off[0].Not(), has_prev_shift.Not()]
                ).OnlyEnforceIf(starts_here.Not())

                for i in range(
                    1,
                    min(
                        min_consecutive_days_off,
                        self.instance.number_of_days - start_day,
                    ),
                ):
                    self.vars.model.Add(has_day_off[i] == 1).OnlyEnforceIf(starts_here)

    def add_end_minimum_consecutive_days_off_constraints(
        self, employee_uid: employee.EmployeeUid, min_consecutive_days_off: int
    ):
        if min_consecutive_days_off <= 0:
            return
        # Prüft, ob am Ende des Fensters die Mindestanzahl aufeinanderfolgender freier Tage eingehalten wird
        # Wenn eine freie Tag-Sequenz am Ende endet, müssen mindestens min_consecutive_days_off Tage frei gewesen sein
        for end_day in range(
            self.instance.number_of_days - min_consecutive_days_off,
            self.instance.number_of_days,
        ):
            # has_day_off[i] = 1, wenn an Tag (end_day - min_consecutive_days_off + 1 + i) der Mitarbeiter keinen Dienst hat
            has_day_off = [
                self.vars.model.NewBoolVar(
                    f"end_min_days_off_has_day_off_{end_day}_{i}_for_{employee_uid}"
                )
                for i in range(min_consecutive_days_off)
            ]

            for i in range(min_consecutive_days_off):
                day = end_day - min_consecutive_days_off + 1 + i
                if day < 0:
                    continue
                shift_vars = [
                    self.vars.vars[(day, shift_type_uid, employee_uid)]
                    for shift_type_uid in self.instance.shift_types
                ]
                has_shift = self.vars.model.NewBoolVar(
                    f"end_min_days_off_has_shift_{end_day}_{i}_for_{employee_uid}"
                )
                self.vars.model.AddMaxEquality(has_shift, shift_vars)
                # has_day_off[i] = NOT has_shift
                self.vars.model.Add(has_day_off[i] == 1 - has_shift)

            # Wenn end_day ein freier Tag ist und end_day+1 eine Schicht hat (oder end_day=last),
            # dann müssen die vorherigen min_consecutive_days_off Tage alle frei gewesen sein
            if end_day == self.instance.number_of_days - 1:
                # Wenn letzter Tag frei ist, müssen die vorherigen min_consecutive_days_off-1 Tage auch frei sein
                for i in range(
                    max(
                        0,
                        min_consecutive_days_off
                        - (self.instance.number_of_days - end_day),
                    )
                ):
                    if end_day - min_consecutive_days_off + 1 + i >= 0:
                        self.vars.model.Add(has_day_off[i] == 1).OnlyEnforceIf(
                            has_day_off[-1]
                        )
            else:
                # Prüfe ob nächster Tag eine Schicht hat
                next_shift_vars = [
                    self.vars.vars[(end_day + 1, shift_type_uid, employee_uid)]
                    for shift_type_uid in self.instance.shift_types
                ]
                has_next_shift = self.vars.model.NewBoolVar(
                    f"end_min_days_off_has_next_{end_day}_for_{employee_uid}"
                )
                self.vars.model.AddMaxEquality(has_next_shift, next_shift_vars)

                # Wenn end_day frei ist UND end_day+1 eine Schicht hat, dann Mindestanzahl erzwingen
                ends_here = self.vars.model.NewBoolVar(
                    f"end_min_days_off_ends_{end_day}_for_{employee_uid}"
                )
                self.vars.model.AddBoolAnd(
                    [has_day_off[-1], has_next_shift]
                ).OnlyEnforceIf(ends_here)
                self.vars.model.AddBoolOr(
                    [has_day_off[-1].Not(), has_next_shift.Not()]
                ).OnlyEnforceIf(ends_here.Not())

                for i in range(max(0, min_consecutive_days_off - 1)):
                    if end_day - min_consecutive_days_off + 1 + i >= 0:
                        self.vars.model.Add(has_day_off[i] == 1).OnlyEnforceIf(
                            ends_here
                        )
