from ortools.sat.python import cp_model

from .. import shift_vars, solver
from ..inputTypes import employee, instace
from ..module.shift_assignment_module import ShiftAssignmentModule
from ..module.solverConstraints import SolverConstraints
from ..solution import Solution
from .config_for_employee import Config_for_employee


class Vars_for_employee:
    """Stores all constraint variables for one employee in the window"""

    # Start maximum consecutive shifts
    all_previus_aktive_start: list[cp_model.BoolVarT]
    next_day_has_shift_start: cp_model.BoolVarT | None

    # End maximum consecutive shifts
    all_next_aktive_end: list[cp_model.BoolVarT]
    prev_day_has_shift_end: cp_model.BoolVarT | None

    def __init__(self):
        self.all_previus_aktive_start = []
        self.next_day_has_shift_start = None
        self.all_next_aktive_end = []
        self.prev_day_has_shift_end = None


class Solver_for_window(solver.Solver):
    def __init__(
        self,
        instance: instace.Instance,
        vars: shift_vars.Shift_vars,
        config: dict[employee.EmployeeUid, Config_for_employee],
        disabled_constraints: list[SolverConstraints] = [],
        add_module_constraints: list[ShiftAssignmentModule] = [],
    ):
        super().__init__(
            instance,
            vars,
            disabled_constraints
            + [
                # SolverConstraints.max_Cons_Shifts,
                SolverConstraints.max_weekend_days,
                # SolverConstraints.minimum_consecutive_days_off,
                # SolverConstraints.minimum_consecutive_shifts,
                # SolverConstraints.cover_requirements,
                # SolverConstraints.days_off,
                # SolverConstraints.cover_requirements,
                # SolverConstraints.limited_shifts_per_type_validation,
                # SolverConstraints.minMaxWorkTime,
            ],
            add_module_constraints,
        )

        self.config = config
        # Create all constraint variables for each employee
        self.vars_per_employee: dict[employee.EmployeeUid, Vars_for_employee] = {}
        for employee_uid, emp_config in self.config.items():
            emp_vars = Vars_for_employee()
            self.vars_per_employee[employee_uid] = emp_vars

            # Create start maximum consecutive shifts variables
            if emp_config.max_consecutive_shifts_start > 0:
                max_cons = emp_config.max_consecutive_shifts_start
                emp_vars.all_previus_aktive_start = [
                    self.vars.model.NewBoolVar(f"prefix_active_{i}_for_{employee_uid}")
                    for i in range(max_cons)
                ]
                if max_cons < self.instance.number_of_days:
                    emp_vars.next_day_has_shift_start = self.vars.model.NewBoolVar(
                        f"next_day_has_shift_after_max_cons_{employee_uid}"
                    )

            # Create end maximum consecutive shifts variables
            if emp_config.max_consecutive_shifts_end > 0:
                max_cons = emp_config.max_consecutive_shifts_end
                emp_vars.all_next_aktive_end = [
                    self.vars.model.NewBoolVar(f"suffix_active_{i}_for_{employee_uid}")
                    for i in range(max_cons)
                ]
                if max_cons < self.instance.number_of_days:
                    emp_vars.prev_day_has_shift_end = self.vars.model.NewBoolVar(
                        f"prev_day_has_shift_before_max_cons_{employee_uid}"
                    )

    def solve_window(
        self,
        log_search_progress: bool = True,
        max_time_in_seconds: float = 60.0,
        stop_after_first_solution: bool = False,
        callback: cp_model.CpSolverSolutionCallback | None = None,
    ) -> Solution:
        return super().solve_with_early_stop(
            log_search_progress=log_search_progress,
            max_time_in_seconds=max_time_in_seconds,
            stop_after_first_solution=stop_after_first_solution,
        )

    def solve_window_min_changes(
        self,
        solution: Solution,
        hint_solution: Solution | None = None,
        log_search_progress: bool = True,
        max_time_in_seconds: float = 60.0,
        stop_after_first_solution: bool = False,
        callback: cp_model.CpSolverSolutionCallback | None = None,
    ) -> Solution:
        print("Solving window with minimal changes...")
        return super().solve_min_changes(
            solution=solution,
            log_search_progress=log_search_progress,
            max_time_in_seconds=max_time_in_seconds,
        )
        # return super().solve_with_early_stop(
        #     log_search_progress=log_search_progress,
        #     max_time_in_seconds=max_time_in_seconds,
        #     stop_after_first_solution=stop_after_first_solution,
        # )

    def add_start_maximum_consecutive_shifts_constraints(
        self, employee_uid: employee.EmployeeUid
    ):
        max_consecutive_shifts = self.config[employee_uid].max_consecutive_shifts_start
        if max_consecutive_shifts <= 0:
            return

        # Get the pre-created variables for this employee
        emp_vars = self.vars_per_employee[employee_uid]
        all_previus_aktive = emp_vars.all_previus_aktive_start

        for i in range(max_consecutive_shifts):
            if i >= self.instance.number_of_days:
                break
            # Use work_vars instead of creating redundant is_assigend variables
            is_assigend = self.vars.get_work_vars(i, employee_uid)

            if i == 0:
                # all_previus_aktive[0] = 1
                self.vars.model.Add(all_previus_aktive[0] == 1)
            else:
                # all_previus_aktive[i] = all_previus_aktive[i-1] AND is_assigend[i-1]
                is_assigend_prev = self.vars.get_work_vars(i - 1, employee_uid)
                self.vars.model.AddBoolAnd(
                    [all_previus_aktive[i - 1], is_assigend_prev]
                ).OnlyEnforceIf(all_previus_aktive[i])
                self.vars.model.AddBoolOr(
                    [all_previus_aktive[i - 1].Not(), is_assigend_prev.Not()]
                ).OnlyEnforceIf(all_previus_aktive[i].Not())

        # Wenn alle ersten max_consecutive_shifts Tage eine Schicht haben,
        # dann darf Tag max_consecutive_shifts keine Schicht haben
        if max_consecutive_shifts < self.instance.number_of_days:
            next_day_has_shift = emp_vars.next_day_has_shift_start
            assert next_day_has_shift is not None, (
                "next_day_has_shift_start should be created in __init__"
            )
            next_day_shift_vars = [
                self.vars.vars[(max_consecutive_shifts, shift_type_uid, employee_uid)]
                for shift_type_uid in self.instance.shift_types
            ]
            self.vars.model.AddMaxEquality(next_day_has_shift, next_day_shift_vars)

            # Wenn all_previus_aktive[last] UND is_assigend[last] beide 1 sind,
            # dann müssen alle ersten max_consecutive_shifts Tage Schichten haben
            # In diesem Fall darf next_day_has_shift nicht 1 sein
            is_assigend_last = self.vars.get_work_vars(
                max_consecutive_shifts - 1, employee_uid
            )
            self.vars.model.AddBoolOr(
                [
                    all_previus_aktive[-1].Not(),
                    is_assigend_last.Not(),
                    next_day_has_shift.Not(),
                ]
            )

    def add_end_maximum_consecutive_shifts_constraints(
        self, employee_uid: employee.EmployeeUid
    ):
        max_consecutive_shifts = self.config[employee_uid].max_consecutive_shifts_end
        if max_consecutive_shifts <= 0:
            return

        # Get the pre-created variables for this employee
        emp_vars = self.vars_per_employee[employee_uid]
        suffix_active = emp_vars.all_next_aktive_end

        for i in range(max_consecutive_shifts):
            day = self.instance.number_of_days - max_consecutive_shifts + i
            if day < 0 or day >= self.instance.number_of_days:
                break

            if i == max_consecutive_shifts - 1:
                # suffix_active[last] = 1
                self.vars.model.Add(suffix_active[i] == 1)
            else:
                # suffix_active[i] = suffix_active[i+1] AND suffix_true[i+1]
                day_next = self.instance.number_of_days - max_consecutive_shifts + i + 1
                suffix_true_next = self.vars.get_work_vars(day_next, employee_uid)
                self.vars.model.AddBoolAnd(
                    [suffix_active[i + 1], suffix_true_next]
                ).OnlyEnforceIf(suffix_active[i])
                self.vars.model.AddBoolOr(
                    [suffix_active[i + 1].Not(), suffix_true_next.Not()]
                ).OnlyEnforceIf(suffix_active[i].Not())

        # Wenn alle letzten max_consecutive_shifts Tage eine Schicht haben,
        # dann darf der Tag vor dem ersten dieser Tage keine Schicht haben
        if max_consecutive_shifts < self.instance.number_of_days:
            prev_day = self.instance.number_of_days - max_consecutive_shifts - 1
            prev_day_has_shift = emp_vars.prev_day_has_shift_end
            assert prev_day_has_shift is not None, (
                "prev_day_has_shift_end should be created in __init__"
            )
            prev_day_shift_vars = [
                self.vars.vars[(prev_day, shift_type_uid, employee_uid)]
                for shift_type_uid in self.instance.shift_types
            ]
            self.vars.model.AddMaxEquality(prev_day_has_shift, prev_day_shift_vars)

            # Wenn suffix_active[0] UND suffix_true[0] beide 1 sind,
            # dann müssen alle letzten max_consecutive_shifts Tage Schichten haben
            # In diesem Fall darf prev_day_has_shift nicht 1 sein
            suffix_true_first = self.vars.get_work_vars(
                self.instance.number_of_days - max_consecutive_shifts, employee_uid
            )
            self.vars.model.AddBoolOr(
                [
                    suffix_active[0].Not(),
                    suffix_true_first.Not(),
                    prev_day_has_shift.Not(),
                ]
            )

    def add_custom_maximum_consecutive_shifts_constraints(
        self, employee_uid: employee.EmployeeUid
    ):
        emp_config = self.config.get(employee_uid)
        if emp_config is None:
            return
        emp_max_start = emp_config.max_consecutive_shifts_start
        emp_max_end = emp_config.max_consecutive_shifts_end

        window_size = (
            self.instance.employees[employee_uid].max_number_consecutive_shifts + 1
        )

        emp_vars = self.vars_per_employee.get(employee_uid)

        # iterate over possible window starts (as before)
        for day in range(
            self.instance.number_of_days
            - self.instance.employees[employee_uid].max_number_consecutive_shifts
        ):
            window_start = day
            window_end = day + window_size - 1

            # Use work_vars for each day in the window
            assigned_shifts = [
                self.vars.get_work_vars(day + i, employee_uid)
                for i in range(window_size)
            ]

            # Check if we need to conditionally apply this constraint based on
            # all_previus_aktive_start or all_next_aktive_end
            apply_constraint_conditions = []

            # Skip if window_start is in the start range AND all_previus_aktive_start is active for that day
            if window_start < emp_max_start and emp_vars is not None:
                if len(emp_vars.all_previus_aktive_start) > window_start:
                    # Only apply constraint if all_previus_aktive_start[window_start] is NOT active
                    apply_constraint_conditions.append(
                        emp_vars.all_previus_aktive_start[window_start].Not()
                    )

            # Skip if window_end is in the end range AND all_next_aktive_end is active for that day
            if (
                window_end >= self.instance.number_of_days - emp_max_end
                and emp_vars is not None
            ):
                # Map window_end to the index in all_next_aktive_end
                # all_next_aktive_end[i] corresponds to day (number_of_days - emp_max_end + i)
                end_index = window_end - (self.instance.number_of_days - emp_max_end)
                if 0 <= end_index < len(emp_vars.all_next_aktive_end):
                    # Only apply constraint if all_next_aktive_end is NOT active for that day
                    apply_constraint_conditions.append(
                        emp_vars.all_next_aktive_end[end_index].Not()
                    )

            # Apply the constraint conditionally
            if apply_constraint_conditions:
                # Create a helper variable for the constraint
                constraint_var = self.vars.model.NewBoolVar(
                    f"constraint_active_day_{day}_emp_{employee_uid}"
                )
                # constraint is active if ALL apply_constraint_conditions are true
                self.vars.model.AddBoolAnd(apply_constraint_conditions).OnlyEnforceIf(
                    constraint_var
                )
                # Apply the max consecutive shifts constraint only when constraint_var is true
                self.vars.model.Add(
                    sum(assigned_shifts)
                    <= self.instance.employees[
                        employee_uid
                    ].max_number_consecutive_shifts
                ).OnlyEnforceIf(constraint_var)
            else:
                # No conditions, apply constraint unconditionally
                self.vars.model.Add(
                    sum(assigned_shifts)
                    <= self.instance.employees[
                        employee_uid
                    ].max_number_consecutive_shifts
                )

    def add_start_minimum_consecutive_shifts_constraints(
        self, employee_uid: employee.EmployeeUid
    ):
        min_consecutive_shifts = self.config[employee_uid].min_consecutive_shifts_start
        if min_consecutive_shifts > 0:
            for day in range(min_consecutive_shifts):
                # Use work_vars instead of iterating over all shift types
                self.vars.model.Add(self.vars.get_work_vars(day, employee_uid) == 1)
        if min_consecutive_shifts == -1:
            nedded_min_consecutive_shifts = self.instance.employees[
                employee_uid
            ].min_number_consecutive_shifts
            if nedded_min_consecutive_shifts <= 1:
                return
            shifts_vars_previus_and_current_day = []
            for day in range(nedded_min_consecutive_shifts - 1):
                # Use work_vars instead of creating redundant variables
                shifts_vars_previus_and_current_day.append(
                    self.vars.get_work_vars(day, employee_uid)
                )

                next_day_has_shift = self.vars.get_work_vars(day + 1, employee_uid)

                self.vars.model.Add(
                    sum(shifts_vars_previus_and_current_day) == 0
                ).OnlyEnforceIf(next_day_has_shift.Not())

    def add_end_minimum_consecutive_shifts_constraints(
        self, employee_uid: employee.EmployeeUid
    ):
        min_consecutive_shifts = self.config[employee_uid].min_consecutive_shifts_end
        last_day = self.instance.number_of_days - 1
        if min_consecutive_shifts > 0:
            assert min_consecutive_shifts <= last_day
            for day in range(min_consecutive_shifts):
                # Use work_vars instead of iterating over all shift types
                self.vars.model.Add(
                    self.vars.get_work_vars(last_day - day, employee_uid) == 1
                )
        elif min_consecutive_shifts == -1:
            nedded_min_consecutive_shifts = self.instance.employees[
                employee_uid
            ].min_number_consecutive_shifts
            if nedded_min_consecutive_shifts <= 1:
                return
            shifts_vars_next_and_current_day = []
            for day in range(
                last_day, last_day - nedded_min_consecutive_shifts + 1, -1
            ):
                # Use work_vars instead of creating redundant variables
                shifts_vars_next_and_current_day.append(
                    self.vars.get_work_vars(day, employee_uid)
                )

                prev_day_has_shift = self.vars.get_work_vars(day - 1, employee_uid)

                self.vars.model.Add(
                    sum(shifts_vars_next_and_current_day) == 0
                ).OnlyEnforceIf(prev_day_has_shift.Not())

    def add_start_minimum_consecutive_days_off_constraints(
        self, employee_uid: employee.EmployeeUid
    ):
        min_consecutive_days_off = self.config[
            employee_uid
        ].min_consecutive_days_off_start
        if min_consecutive_days_off == -1 or min_consecutive_days_off == -3:
            return
        if min_consecutive_days_off == -2:
            min_consecutive_days_off = self.instance.employees[
                employee_uid
            ].min_number_consecutive_days_off

        for day in range(min_consecutive_days_off):
            # Use work_vars instead of iterating over all shift types
            self.vars.model.Add(self.vars.get_work_vars(day, employee_uid) == 0)

    def add_end_minimum_consecutive_days_off_constraints(
        self, employee_uid: employee.EmployeeUid
    ):
        min_consecutive_days_off = self.config[
            employee_uid
        ].min_consecutive_days_off_end
        if min_consecutive_days_off == -1 or min_consecutive_days_off == -3:
            return
        if min_consecutive_days_off == -2:
            min_consecutive_days_off = self.instance.employees[
                employee_uid
            ].min_number_consecutive_days_off

        last_modifibarbe_day = self.instance.number_of_days - 1
        assert min_consecutive_days_off <= last_modifibarbe_day
        for day in range(min_consecutive_days_off):
            # Use work_vars instead of iterating over all shift types
            self.vars.model.Add(
                self.vars.get_work_vars(last_modifibarbe_day - day, employee_uid) == 0
            )

    def block_employee_on_day(self, employee_uid: employee.EmployeeUid, day: int):
        self.vars.model.Add(self.vars.get_work_vars(day, employee_uid) == 0)
