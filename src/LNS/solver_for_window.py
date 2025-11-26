from ortools.sat.python import cp_model

from .. import shift_vars, solver
from ..inputTypes import employee, instace
from ..module.shift_assignment_module import ShiftAssignmentModule
from ..module.solverConstraints import SolverConstraints
from ..solution import Solution


class Solver_for_window(solver.Solver):
    def __init__(
        self,
        instance: instace.Instance,
        vars: shift_vars.Shift_vars,
        disabled_constraints: list[SolverConstraints] = [],
        add_module_constraints: list[ShiftAssignmentModule] = [],
    ):
        # HACK Weekend raus
        super().__init__(
            instance,
            vars,
            disabled_constraints
            + [
                SolverConstraints.max_Cons_Shifts,
                SolverConstraints.max_weekend_days,
                SolverConstraints.minimum_consecutive_days_off,
                SolverConstraints.minimum_consecutive_shifts,
            ],
            add_module_constraints,
        )

    def solve_window(
        self,
        log_search_progress: bool = True,
        max_time_in_seconds: float = 60.0,
        stop_after_first_solution: bool = False,
        callback: cp_model.CpSolverSolutionCallback | None = None,
    ) -> Solution:
        return super().solve(
            log_search_progress=log_search_progress,
            max_time_in_seconds=max_time_in_seconds,
            stop_after_first_solution=stop_after_first_solution,
            callback=callback,
        )

    def add_start_maximum_consecutive_shifts_constraints(
        self, employee_uid: employee.EmployeeUid, max_consecutive_shifts: int
    ):
        if max_consecutive_shifts <= 0:
            return
        # all_previus_aktive[i] = 1, wenn bis i-1 alle TRUE sind
        all_previus_aktive = [
            self.vars.model.NewBoolVar(f"prefix_active_{i}_for_{employee_uid}")
            for i in range(max_consecutive_shifts)
        ]
        # is_assigend[i] = 1, wenn an Tag i der Mitarbeiter einen Dienst hat
        is_assigend = [
            self.vars.model.NewBoolVar(f"prefix_true_{i}")
            for i in range(max_consecutive_shifts)
        ]
        for i in range(max_consecutive_shifts):
            shift_vars = [
                self.vars.vars[(i, shift_type_uid, employee_uid)]
                for shift_type_uid in self.instance.shift_types
            ]
            self.vars.model.AddMaxEquality(is_assigend[i], shift_vars)

            if i == 0:
                # all_previus_aktive[0] = 1
                self.vars.model.Add(all_previus_aktive[0] == 1)
            else:
                # all_previus_aktive[i] = all_previus_aktive[i-1] AND is_assigend[i-1]
                self.vars.model.AddBoolAnd(
                    [all_previus_aktive[i - 1], is_assigend[i - 1]]
                ).OnlyEnforceIf(all_previus_aktive[i])
                self.vars.model.AddBoolOr(
                    [all_previus_aktive[i - 1].Not(), is_assigend[i - 1].Not()]
                ).OnlyEnforceIf(all_previus_aktive[i].Not())

        # Wenn alle ersten max_consecutive_shifts Tage eine Schicht haben,
        # dann darf Tag max_consecutive_shifts keine Schicht haben
        if max_consecutive_shifts < self.instance.number_of_days:
            next_day_shift_vars = [
                self.vars.vars[(max_consecutive_shifts, shift_type_uid, employee_uid)]
                for shift_type_uid in self.instance.shift_types
            ]
            next_day_has_shift = self.vars.model.NewBoolVar(
                f"next_day_has_shift_after_max_cons_{employee_uid}"
            )
            self.vars.model.AddMaxEquality(next_day_has_shift, next_day_shift_vars)

            # Wenn all_previus_aktive[last] UND is_assigend[last] beide 1 sind,
            # dann müssen alle ersten max_consecutive_shifts Tage Schichten haben
            # In diesem Fall darf next_day_has_shift nicht 1 sein
            self.vars.model.AddBoolOr(
                [
                    all_previus_aktive[-1].Not(),
                    is_assigend[-1].Not(),
                    next_day_has_shift.Not(),
                ]
            )

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

        # Wenn alle letzten max_consecutive_shifts Tage eine Schicht haben,
        # dann darf der Tag vor dem ersten dieser Tage keine Schicht haben
        if max_consecutive_shifts < self.instance.number_of_days:
            prev_day = self.instance.number_of_days - max_consecutive_shifts - 1
            prev_day_shift_vars = [
                self.vars.vars[(prev_day, shift_type_uid, employee_uid)]
                for shift_type_uid in self.instance.shift_types
            ]
            prev_day_has_shift = self.vars.model.NewBoolVar(
                f"prev_day_has_shift_before_max_cons_{employee_uid}"
            )
            self.vars.model.AddMaxEquality(prev_day_has_shift, prev_day_shift_vars)

            # Wenn suffix_active[0] UND suffix_true[0] beide 1 sind,
            # dann müssen alle letzten max_consecutive_shifts Tage Schichten haben
            # In diesem Fall darf prev_day_has_shift nicht 1 sein
            self.vars.model.AddBoolOr(
                [
                    suffix_active[0].Not(),
                    suffix_true[0].Not(),
                    prev_day_has_shift.Not(),
                ]
            )

    def add_start_minimum_consecutive_shifts_constraints(
        self, employee_uid: employee.EmployeeUid, min_consecutive_shifts: int
    ):
        for day in range(min_consecutive_shifts):
            shifts_vars = []
            for shift_type_uid in self.instance.shift_types:
                shifts_vars.append(
                    self.vars.get_var(day + 1, shift_type_uid, employee_uid)
                )
            self.vars.model.Add(sum(shifts_vars) == 1)

    def add_end_minimum_consecutive_shifts_constraints(
        self, employee_uid: employee.EmployeeUid, min_consecutive_shifts: int
    ):
        last_modifibarbe_day = self.instance.number_of_days - 2
        assert min_consecutive_shifts <= last_modifibarbe_day
        for day in range(min_consecutive_shifts):
            shifts_vars = []
            for shift_type_uid in self.instance.shift_types:
                shifts_vars.append(
                    self.vars.get_var(
                        last_modifibarbe_day - day, shift_type_uid, employee_uid
                    )
                )
            self.vars.model.Add(sum(shifts_vars) == 1)

    def add_start_minimum_consecutive_days_off_constraints(
        self, employee_uid: employee.EmployeeUid, min_consecutive_days_off: int
    ):
        for day in range(min_consecutive_days_off):
            shifts_vars = []
            for shift_type_uid in self.instance.shift_types:
                shifts_vars.append(
                    self.vars.get_var(day + 1, shift_type_uid, employee_uid)
                )
            self.vars.model.Add(sum(shifts_vars) == 0)

    def add_end_minimum_consecutive_days_off_constraints(
        self, employee_uid: employee.EmployeeUid, min_consecutive_days_off: int
    ):
        last_modifibarbe_day = self.instance.number_of_days - 2
        assert min_consecutive_days_off <= last_modifibarbe_day
        for day in range(min_consecutive_days_off):
            shifts_vars = []
            for shift_type_uid in self.instance.shift_types:
                shifts_vars.append(
                    self.vars.get_var(
                        last_modifibarbe_day - day, shift_type_uid, employee_uid
                    )
                )
            self.vars.model.Add(sum(shifts_vars) == 0)

    def block_employee_on_day(self, employee_uid: employee.EmployeeUid, day: int):
        for shift_type_uid in self.instance.shift_types:
            self.vars.model.Add(
                self.vars.get_var(day, shift_type_uid, employee_uid) == 0
            )
