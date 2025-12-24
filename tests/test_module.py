from cpsat_utils.testing import AssertModelFeasible, AssertModelInfeasible
from ortools.sat.python import cp_model

from src import shift_vars
from src.inputTypes import employee, instace, shiftType
from src.LNS.module import max_weekend_days as max_weekend_days_lns
from src.module import (
    cover_requirements,
    days_off,
    max_Cons_Shifts,
    max_weekend_days,
    minimum_consecutive_days_off,
    minimum_consecutive_shifts,
    minMaxWorkTime,
    shift_assignment_single_day_validation,
    shift_rotation_constraint,
    days_off_new,
    max_Cons_shifts_new,
    minimum_consecutove_days_off_new,
    minimum_consecutive_shifts_new,
)


# Employee gets two shifts (different types) on a single day - should be infeasible
def test_single_day_validation():
    with AssertModelInfeasible() as model:
        lokal_shift_types = [shiftType.ShiftType() for _ in range(2)]
        lokal_employee = employee.Employee()
        instance = instace.Instance.create(
            number_of_days=1,
            shift_typs=lokal_shift_types,
            emplyees=[lokal_employee],
        )
        vars = shift_vars.Shift_vars(instance, model)
        shift_assignment_single_day_validation.Single_day_validation().build(
            instance, vars
        )
        for type_uid in lokal_shift_types:
            model.Add(vars.vars[(0, type_uid.uid, lokal_employee.uid)] == 1)


# Employee gets two shifts (different types) on consecutive days where the first shift type blocks the second - should be infeasible
def test_shift_rotation():
    with AssertModelInfeasible() as model:
        lokal_shift_types = [shiftType.ShiftType() for _ in range(2)]
        # set second shift type to be blocked after first
        lokal_shift_types[0].blocked_shifts_after.add(lokal_shift_types[1].uid)
        lokal_employee = employee.Employee()
        instance = instace.Instance.create(
            number_of_days=2,
            shift_typs=lokal_shift_types,
            emplyees=[lokal_employee],
        )
        vars = shift_vars.Shift_vars(instance, model)
        shift_rotation_constraint.Shift_rotation_constraint().build(instance, vars)

        model.Add(vars.vars[(0, lokal_shift_types[0].uid, lokal_employee.uid)] == 1)
        model.Add(vars.vars[(1, lokal_shift_types[1].uid, lokal_employee.uid)] == 1)


def test_max_cons_shifts():
    with AssertModelInfeasible() as model:
        lokal_shift_type = shiftType.ShiftType()
        lokal_employee = employee.Employee(max_number_consecutive_shifts=1)
        instance = instace.Instance.create(
            number_of_days=2,
            shift_typs=[lokal_shift_type],
            emplyees=[lokal_employee],
        )
        vars = shift_vars.Shift_vars(instance, model)
        max_Cons_shifts_new.Max_Cons_Shifts_Automaton().build(instance, vars)
        model.Add(vars.vars[(0, lokal_shift_type.uid, lokal_employee.uid)] == 1)
        model.Add(vars.vars[(1, lokal_shift_type.uid, lokal_employee.uid)] == 1)


# Employee works not enough minutes- should be infeasible
def test_min_max_worktime_below():
    with AssertModelInfeasible() as model:
        lokal_shift_type = shiftType.ShiftType()
        lokal_shift_type.length = 60
        lokal_employee = employee.Employee()
        lokal_employee.min_minutes_assigned = 120
        instance = instace.Instance.create(
            number_of_days=1,
            shift_typs=[lokal_shift_type],
            emplyees=[lokal_employee],
        )
        vars = shift_vars.Shift_vars(instance, model)
        minMaxWorkTime.MinMaxWorkTime().build(instance, vars)


# Employee works to many minutes- should be infeasible
def test_min_max_worktime_above():
    with AssertModelInfeasible() as model:
        lokal_shift_type = shiftType.ShiftType()
        lokal_shift_type.length = 120
        lokal_employee = employee.Employee()
        lokal_employee.max_minutes_assigned = 60
        instance = instace.Instance.create(
            number_of_days=1,
            shift_typs=[lokal_shift_type],
            emplyees=[lokal_employee],
        )
        vars = shift_vars.Shift_vars(instance, model)
        minMaxWorkTime.MinMaxWorkTime().build(instance, vars)
        model.Add(vars.vars[(0, lokal_shift_type.uid, lokal_employee.uid)] == 1)


# Employee works exact minutes- should be feasible
def test_min_max_worktime_exact():
    with AssertModelFeasible() as model:
        lokal_shift_type = shiftType.ShiftType()
        lokal_shift_type.length = 120
        lokal_employee = employee.Employee()
        lokal_employee.min_minutes_assigned = 60
        lokal_employee.max_minutes_assigned = 160
        instance = instace.Instance.create(
            number_of_days=1,
            shift_typs=[lokal_shift_type],
            emplyees=[lokal_employee],
        )
        vars = shift_vars.Shift_vars(instance, model)
        minMaxWorkTime.MinMaxWorkTime().build(instance, vars)
        model.Add(vars.vars[(0, lokal_shift_type.uid, lokal_employee.uid)] == 1)


def test_minimum_consecutive_shifts():
    # Min_Cons_Shifts
    with AssertModelFeasible() as model:
        lokal_shift_type_list = [shiftType.ShiftType()]
        lokal_employee = employee.Employee()
        lokal_employee.min_number_consecutive_shifts = 4
        instance = instace.Instance.create(
            number_of_days=5,
            shift_typs=lokal_shift_type_list,
            emplyees=[lokal_employee],
        )
        vars = shift_vars.Shift_vars(instance, model)
        minimum_consecutive_shifts.Minimum_consecutive_shifts().build(instance, vars)
        status = cp_model.CpSolver().Solve(vars.model)

    with AssertModelInfeasible() as model:
        lokal_shift_type_list = [shiftType.ShiftType()]
        lokal_employee = employee.Employee()
        lokal_employee.min_number_consecutive_shifts = 4
        instance = instace.Instance.create(
            number_of_days=5,
            shift_typs=lokal_shift_type_list,
            emplyees=[lokal_employee],
        )
        vars = shift_vars.Shift_vars(instance, model)
        minimum_consecutive_shifts.Minimum_consecutive_shifts().build(instance, vars)
        vars.model.add(
            vars.vars[(0, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(1, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(2, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        status = cp_model.CpSolver().Solve(vars.model)

    with AssertModelInfeasible() as model:
        lokal_shift_type_list = [shiftType.ShiftType()]
        lokal_employee = employee.Employee()
        lokal_employee.min_number_consecutive_shifts = 4
        instance = instace.Instance.create(
            number_of_days=5,
            shift_typs=lokal_shift_type_list,
            emplyees=[lokal_employee],
        )
        vars = shift_vars.Shift_vars(instance, model)
        minimum_consecutive_shifts.Minimum_consecutive_shifts().build(instance, vars)
        vars.model.add(
            vars.vars[(0, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(1, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(2, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(3, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(4, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        status = cp_model.CpSolver().Solve(vars.model)

    with AssertModelInfeasible() as model:
        lokal_shift_type_list = [shiftType.ShiftType()]
        lokal_employee = employee.Employee()
        lokal_employee.min_number_consecutive_shifts = 4
        instance = instace.Instance.create(
            number_of_days=5,
            shift_typs=lokal_shift_type_list,
            emplyees=[lokal_employee],
        )
        vars = shift_vars.Shift_vars(instance, model)
        minimum_consecutive_shifts.Minimum_consecutive_shifts().build(instance, vars)
        vars.model.add(
            vars.vars[(0, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(1, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(2, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(3, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(4, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        status = cp_model.CpSolver().Solve(vars.model)

    with AssertModelFeasible() as model:
        lokal_shift_type_list = [shiftType.ShiftType()]
        lokal_employee = employee.Employee()
        lokal_employee.min_number_consecutive_shifts = 4
        instance = instace.Instance.create(
            number_of_days=5,
            shift_typs=lokal_shift_type_list,
            emplyees=[lokal_employee],
        )
        vars = shift_vars.Shift_vars(instance, model)
        minimum_consecutive_shifts.Minimum_consecutive_shifts().build(instance, vars)
        vars.model.add(
            vars.vars[(0, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(1, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(2, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(3, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(4, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        status = cp_model.CpSolver().Solve(vars.model)

    
    
    # Min_Cons_Shifts_Alternative
    with AssertModelFeasible() as model:
        lokal_shift_type_list = [shiftType.ShiftType()]
        lokal_employee = employee.Employee()
        lokal_employee.min_number_consecutive_shifts = 4
        instance = instace.Instance.create(
            number_of_days=5,
            shift_typs=lokal_shift_type_list,
            emplyees=[lokal_employee],
        )
        vars = shift_vars.Shift_vars(instance, model)
        minimum_consecutive_shifts_new.Min_Cons_Shifts_Alternative().build(instance, vars)
        status = cp_model.CpSolver().Solve(vars.model)

    with AssertModelInfeasible() as model:
        lokal_shift_type_list = [shiftType.ShiftType()]
        lokal_employee = employee.Employee()
        lokal_employee.min_number_consecutive_shifts = 4
        instance = instace.Instance.create(
            number_of_days=5,
            shift_typs=lokal_shift_type_list,
            emplyees=[lokal_employee],
        )
        vars = shift_vars.Shift_vars(instance, model)
        minimum_consecutive_shifts_new.Min_Cons_Shifts_Alternative().build(instance, vars)
        vars.model.add(
            vars.vars[(0, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(1, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(2, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        status = cp_model.CpSolver().Solve(vars.model)

    with AssertModelInfeasible() as model:
        lokal_shift_type_list = [shiftType.ShiftType()]
        lokal_employee = employee.Employee()
        lokal_employee.min_number_consecutive_shifts = 4
        instance = instace.Instance.create(
            number_of_days=5,
            shift_typs=lokal_shift_type_list,
            emplyees=[lokal_employee],
        )
        vars = shift_vars.Shift_vars(instance, model)
        minimum_consecutive_shifts_new.Min_Cons_Shifts_Alternative().build(instance, vars)
        vars.model.add(
            vars.vars[(0, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(1, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(2, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(3, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(4, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        status = cp_model.CpSolver().Solve(vars.model)

    with AssertModelInfeasible() as model:
        lokal_shift_type_list = [shiftType.ShiftType()]
        lokal_employee = employee.Employee()
        lokal_employee.min_number_consecutive_shifts = 4
        instance = instace.Instance.create(
            number_of_days=5,
            shift_typs=lokal_shift_type_list,
            emplyees=[lokal_employee],
        )
        vars = shift_vars.Shift_vars(instance, model)
        minimum_consecutive_shifts_new.Min_Cons_Shifts_Alternative().build(instance, vars)
        vars.model.add(
            vars.vars[(0, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(1, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(2, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(3, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(4, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        status = cp_model.CpSolver().Solve(vars.model)

    with AssertModelFeasible() as model:
        lokal_shift_type_list = [shiftType.ShiftType()]
        lokal_employee = employee.Employee()
        lokal_employee.min_number_consecutive_shifts = 4
        instance = instace.Instance.create(
            number_of_days=5,
            shift_typs=lokal_shift_type_list,
            emplyees=[lokal_employee],
        )
        vars = shift_vars.Shift_vars(instance, model)
        minimum_consecutive_shifts_new.Min_Cons_Shifts_Alternative().build(instance, vars)
        vars.model.add(
            vars.vars[(0, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(1, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(2, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(3, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(4, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        status = cp_model.CpSolver().Solve(vars.model)




    # Min_Cons_Shifts_Alternative_exact
    with AssertModelFeasible() as model:
        lokal_shift_type_list = [shiftType.ShiftType()]
        lokal_employee = employee.Employee()
        lokal_employee.min_number_consecutive_shifts = 4
        instance = instace.Instance.create(
            number_of_days=5,
            shift_typs=lokal_shift_type_list,
            emplyees=[lokal_employee],
        )
        vars = shift_vars.Shift_vars(instance, model)
        minimum_consecutive_shifts_new.Min_Cons_Shifts_Alternative_exact().build(instance, vars)
        status = cp_model.CpSolver().Solve(vars.model)

    with AssertModelInfeasible() as model:
        lokal_shift_type_list = [shiftType.ShiftType()]
        lokal_employee = employee.Employee()
        lokal_employee.min_number_consecutive_shifts = 4
        instance = instace.Instance.create(
            number_of_days=5,
            shift_typs=lokal_shift_type_list,
            emplyees=[lokal_employee],
        )
        vars = shift_vars.Shift_vars(instance, model)
        minimum_consecutive_shifts_new.Min_Cons_Shifts_Alternative_exact().build(instance, vars)
        vars.model.add(
            vars.vars[(0, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(1, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(2, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        status = cp_model.CpSolver().Solve(vars.model)


    with AssertModelInfeasible() as model:
        lokal_shift_type_list = [shiftType.ShiftType()]
        lokal_employee = employee.Employee()
        lokal_employee.min_number_consecutive_shifts = 4
        instance = instace.Instance.create(
            number_of_days=5,
            shift_typs=lokal_shift_type_list,
            emplyees=[lokal_employee],
        )
        vars = shift_vars.Shift_vars(instance, model)
        minimum_consecutive_shifts_new.Min_Cons_Shifts_Alternative_exact().build(instance, vars)
        vars.model.add(
            vars.vars[(0, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(1, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(2, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(3, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(4, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        status = cp_model.CpSolver().Solve(vars.model)

    with AssertModelInfeasible() as model:
        lokal_shift_type_list = [shiftType.ShiftType()]
        lokal_employee = employee.Employee()
        lokal_employee.min_number_consecutive_shifts = 4
        instance = instace.Instance.create(
            number_of_days=5,
            shift_typs=lokal_shift_type_list,
            emplyees=[lokal_employee],
        )
        vars = shift_vars.Shift_vars(instance, model)
        minimum_consecutive_shifts_new.Min_Cons_Shifts_Alternative_exact().build(instance, vars)
        vars.model.add(
            vars.vars[(0, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(1, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(2, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(3, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(4, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        status = cp_model.CpSolver().Solve(vars.model)

    with AssertModelFeasible() as model:
        lokal_shift_type_list = [shiftType.ShiftType()]
        lokal_employee = employee.Employee()
        lokal_employee.min_number_consecutive_shifts = 4
        instance = instace.Instance.create(
            number_of_days=5,
            shift_typs=lokal_shift_type_list,
            emplyees=[lokal_employee],
        )
        vars = shift_vars.Shift_vars(instance, model)
        minimum_consecutive_shifts_new.Min_Cons_Shifts_Alternative_exact().build(instance, vars)
        vars.model.add(
            vars.vars[(0, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(1, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(2, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(3, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(4, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        status = cp_model.CpSolver().Solve(vars.model)





# Min_Cons_Shifts_Alternative_exact_Enforce_If
    with AssertModelFeasible() as model:
        lokal_shift_type_list = [shiftType.ShiftType()]
        lokal_employee = employee.Employee()
        lokal_employee.min_number_consecutive_shifts = 4
        instance = instace.Instance.create(
            number_of_days=5,
            shift_typs=lokal_shift_type_list,
            emplyees=[lokal_employee],
        )
        vars = shift_vars.Shift_vars(instance, model)
        minimum_consecutive_shifts_new.Min_Cons_Shifts_Alternative_exact_Enforce_If().build(instance, vars)
        status = cp_model.CpSolver().Solve(vars.model)

    with AssertModelInfeasible() as model:
        lokal_shift_type_list = [shiftType.ShiftType()]
        lokal_employee = employee.Employee()
        lokal_employee.min_number_consecutive_shifts = 4
        instance = instace.Instance.create(
            number_of_days=5,
            shift_typs=lokal_shift_type_list,
            emplyees=[lokal_employee],
        )
        vars = shift_vars.Shift_vars(instance, model)
        minimum_consecutive_shifts_new.Min_Cons_Shifts_Alternative_exact_Enforce_If().build(instance, vars)
        vars.model.add(
            vars.vars[(0, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(1, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(2, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        status = cp_model.CpSolver().Solve(vars.model)


    with AssertModelInfeasible() as model:
        lokal_shift_type_list = [shiftType.ShiftType()]
        lokal_employee = employee.Employee()
        lokal_employee.min_number_consecutive_shifts = 4
        instance = instace.Instance.create(
            number_of_days=5,
            shift_typs=lokal_shift_type_list,
            emplyees=[lokal_employee],
        )
        vars = shift_vars.Shift_vars(instance, model)
        minimum_consecutive_shifts_new.Min_Cons_Shifts_Alternative_exact_Enforce_If().build(instance, vars)
        vars.model.add(
            vars.vars[(0, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(1, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(2, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(3, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(4, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        status = cp_model.CpSolver().Solve(vars.model)

    with AssertModelInfeasible() as model:
        lokal_shift_type_list = [shiftType.ShiftType()]
        lokal_employee = employee.Employee()
        lokal_employee.min_number_consecutive_shifts = 4
        instance = instace.Instance.create(
            number_of_days=5,
            shift_typs=lokal_shift_type_list,
            emplyees=[lokal_employee],
        )
        vars = shift_vars.Shift_vars(instance, model)
        minimum_consecutive_shifts_new.Min_Cons_Shifts_Alternative_exact_Enforce_If().build(instance, vars)
        vars.model.add(
            vars.vars[(0, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(1, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(2, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(3, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(4, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        status = cp_model.CpSolver().Solve(vars.model)

    with AssertModelFeasible() as model:
        lokal_shift_type_list = [shiftType.ShiftType()]
        lokal_employee = employee.Employee()
        lokal_employee.min_number_consecutive_shifts = 4
        instance = instace.Instance.create(
            number_of_days=5,
            shift_typs=lokal_shift_type_list,
            emplyees=[lokal_employee],
        )
        vars = shift_vars.Shift_vars(instance, model)
        minimum_consecutive_shifts_new.Min_Cons_Shifts_Alternative_exact_Enforce_If().build(instance, vars)
        vars.model.add(
            vars.vars[(0, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(1, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(2, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(3, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(4, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        status = cp_model.CpSolver().Solve(vars.model)




    # Min_Cons_Shifts_Alternative_Enforce_If
    with AssertModelFeasible() as model:
        lokal_shift_type_list = [shiftType.ShiftType()]
        lokal_employee = employee.Employee()
        lokal_employee.min_number_consecutive_shifts = 4
        instance = instace.Instance.create(
            number_of_days=5,
            shift_typs=lokal_shift_type_list,
            emplyees=[lokal_employee],
        )
        vars = shift_vars.Shift_vars(instance, model)
        minimum_consecutive_shifts_new.Min_Cons_Shifts_Alternative_Enforce_If().build(instance, vars)
        status = cp_model.CpSolver().Solve(vars.model)

    with AssertModelInfeasible() as model:
        lokal_shift_type_list = [shiftType.ShiftType()]
        lokal_employee = employee.Employee()
        lokal_employee.min_number_consecutive_shifts = 4
        instance = instace.Instance.create(
            number_of_days=5,
            shift_typs=lokal_shift_type_list,
            emplyees=[lokal_employee],
        )
        vars = shift_vars.Shift_vars(instance, model)
        minimum_consecutive_shifts_new.Min_Cons_Shifts_Alternative_Enforce_If().build(instance, vars)
        vars.model.add(
            vars.vars[(0, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(1, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(2, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        status = cp_model.CpSolver().Solve(vars.model)

    with AssertModelInfeasible() as model:
        lokal_shift_type_list = [shiftType.ShiftType()]
        lokal_employee = employee.Employee()
        lokal_employee.min_number_consecutive_shifts = 4
        instance = instace.Instance.create(
            number_of_days=5,
            shift_typs=lokal_shift_type_list,
            emplyees=[lokal_employee],
        )
        vars = shift_vars.Shift_vars(instance, model)
        minimum_consecutive_shifts_new.Min_Cons_Shifts_Alternative_Enforce_If().build(instance, vars)
        vars.model.add(
            vars.vars[(0, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(1, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(2, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(3, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(4, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        status = cp_model.CpSolver().Solve(vars.model)


    with AssertModelInfeasible() as model:
        lokal_shift_type_list = [shiftType.ShiftType()]
        lokal_employee = employee.Employee()
        lokal_employee.min_number_consecutive_shifts = 4
        instance = instace.Instance.create(
            number_of_days=5,
            shift_typs=lokal_shift_type_list,
            emplyees=[lokal_employee],
        )
        vars = shift_vars.Shift_vars(instance, model)
        minimum_consecutive_shifts_new.Min_Cons_Shifts_Alternative_Enforce_If().build(instance, vars)
        vars.model.add(
            vars.vars[(0, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(1, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(2, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(3, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(4, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        status = cp_model.CpSolver().Solve(vars.model)

    with AssertModelFeasible() as model:
        lokal_shift_type_list = [shiftType.ShiftType()]
        lokal_employee = employee.Employee()
        lokal_employee.min_number_consecutive_shifts = 4
        instance = instace.Instance.create(
            number_of_days=5,
            shift_typs=lokal_shift_type_list,
            emplyees=[lokal_employee],
        )
        vars = shift_vars.Shift_vars(instance, model)
        minimum_consecutive_shifts_new.Min_Cons_Shifts_Alternative_Enforce_If().build(instance, vars)
        vars.model.add(
            vars.vars[(0, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(1, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(2, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(3, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(4, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        status = cp_model.CpSolver().Solve(vars.model)

    with AssertModelInfeasible() as model:
        lokal_shift_type_list = [shiftType.ShiftType()]
        lokal_employee = employee.Employee()
        lokal_employee.min_number_consecutive_shifts = 4
        instance = instace.Instance.create(
            number_of_days=5,
            shift_typs=lokal_shift_type_list,
            emplyees=[lokal_employee],
        )
        vars = shift_vars.Shift_vars(instance, model)
        minimum_consecutive_shifts_new.Min_Cons_Shifts_Automaton().build(instance, vars)
        vars.model.add(
            vars.vars[(0, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(1, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(2, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        status = cp_model.CpSolver().Solve(vars.model)
        assert status == cp_model.INFEASIBLE

    with AssertModelInfeasible() as model:
        lokal_shift_type_list = [shiftType.ShiftType()]
        lokal_employee = employee.Employee()
        lokal_employee.min_number_consecutive_shifts = 4
        instance = instace.Instance.create(
            number_of_days=5,
            shift_typs=lokal_shift_type_list,
            emplyees=[lokal_employee],
        )
        vars = shift_vars.Shift_vars(instance, model)
        minimum_consecutive_shifts_new.Min_Cons_Shifts_Automaton().build(instance, vars)
        vars.model.add(
            vars.vars[(0, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(1, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(2, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(3, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(4, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        status = cp_model.CpSolver().Solve(vars.model)
        assert status == cp_model.INFEASIBLE


def test_minimum_consecutive_days_off():
    # Min_Cons_Days_Off
    with AssertModelFeasible() as model:
        lokal_shift_type_list = [shiftType.ShiftType()]
        lokal_employee = employee.Employee()
        lokal_employee.min_number_consecutive_days_off = 4
        instance = instace.Instance.create(
            number_of_days=5,
            shift_typs=lokal_shift_type_list,
            emplyees=[lokal_employee],
        )
        vars = shift_vars.Shift_vars(instance, model)
        minimum_consecutive_days_off.Minimum_consecutive_days_off().build(instance, vars)
        status = cp_model.CpSolver().Solve(vars.model)

    with AssertModelInfeasible() as model:
        lokal_shift_type_list = [shiftType.ShiftType()]
        lokal_employee = employee.Employee()
        lokal_employee.min_number_consecutive_days_off = 4
        instance = instace.Instance.create(
            number_of_days=5,
            shift_typs=lokal_shift_type_list,
            emplyees=[lokal_employee],
        )
        vars = shift_vars.Shift_vars(instance, model)
        minimum_consecutive_days_off.Minimum_consecutive_days_off().build(instance, vars)
        vars.model.add(
            vars.vars[(0, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(1, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(2, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        status = cp_model.CpSolver().Solve(vars.model)

    with AssertModelInfeasible() as model:
        lokal_shift_type_list = [shiftType.ShiftType()]
        lokal_employee = employee.Employee()
        lokal_employee.min_number_consecutive_days_off = 4
        instance = instace.Instance.create(
            number_of_days=5,
            shift_typs=lokal_shift_type_list,
            emplyees=[lokal_employee],
        )
        vars = shift_vars.Shift_vars(instance, model)
        minimum_consecutive_days_off.Minimum_consecutive_days_off().build(instance, vars)
        vars.model.add(
            vars.vars[(0, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(1, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(2, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(3, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(4, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        status = cp_model.CpSolver().Solve(vars.model)

    with AssertModelInfeasible() as model:
        lokal_shift_type_list = [shiftType.ShiftType()]
        lokal_employee = employee.Employee()
        lokal_employee.min_number_consecutive_days_off = 4
        instance = instace.Instance.create(
            number_of_days=5,
            shift_typs=lokal_shift_type_list,
            emplyees=[lokal_employee],
        )
        vars = shift_vars.Shift_vars(instance, model)
        minimum_consecutive_days_off.Minimum_consecutive_days_off().build(instance, vars)
        vars.model.add(
            vars.vars[(0, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(1, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(2, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(3, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(4, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        status = cp_model.CpSolver().Solve(vars.model)

    with AssertModelFeasible() as model:
        lokal_shift_type_list = [shiftType.ShiftType()]
        lokal_employee = employee.Employee()
        lokal_employee.min_number_consecutive_days_off = 4
        instance = instace.Instance.create(
            number_of_days=5,
            shift_typs=lokal_shift_type_list,
            emplyees=[lokal_employee],
        )
        vars = shift_vars.Shift_vars(instance, model)
        minimum_consecutive_days_off.Minimum_consecutive_days_off().build(instance, vars)
        vars.model.add(
            vars.vars[(0, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(1, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(2, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(3, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(4, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        status = cp_model.CpSolver().Solve(vars.model)


    
    
    # Min_Cons_Days_Off_Alternative
    with AssertModelFeasible() as model:
        lokal_shift_type_list = [shiftType.ShiftType()]
        lokal_employee = employee.Employee()
        lokal_employee.min_number_consecutive_days_off = 4
        instance = instace.Instance.create(
            number_of_days=5,
            shift_typs=lokal_shift_type_list,
            emplyees=[lokal_employee],
        )
        vars = shift_vars.Shift_vars(instance, model)
        minimum_consecutove_days_off_new.Min_Cons_Days_Off_Alternative().build(instance, vars)
        status = cp_model.CpSolver().Solve(vars.model)

    with AssertModelInfeasible() as model:
        lokal_shift_type_list = [shiftType.ShiftType()]
        lokal_employee = employee.Employee()
        lokal_employee.min_number_consecutive_days_off = 4
        instance = instace.Instance.create(
            number_of_days=5,
            shift_typs=lokal_shift_type_list,
            emplyees=[lokal_employee],
        )
        vars = shift_vars.Shift_vars(instance, model)
        minimum_consecutove_days_off_new.Min_Cons_Days_Off_Alternative().build(instance, vars)
        vars.model.add(
            vars.vars[(0, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(1, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(2, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        status = cp_model.CpSolver().Solve(vars.model)

    with AssertModelInfeasible() as model:
        lokal_shift_type_list = [shiftType.ShiftType()]
        lokal_employee = employee.Employee()
        lokal_employee.min_number_consecutive_days_off = 4
        instance = instace.Instance.create(
            number_of_days=5,
            shift_typs=lokal_shift_type_list,
            emplyees=[lokal_employee],
        )
        vars = shift_vars.Shift_vars(instance, model)
        minimum_consecutove_days_off_new.Min_Cons_Days_Off_Alternative().build(instance, vars)
        vars.model.add(
            vars.vars[(0, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(1, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(2, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(3, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(4, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        status = cp_model.CpSolver().Solve(vars.model)

    with AssertModelInfeasible() as model:
        lokal_shift_type_list = [shiftType.ShiftType()]
        lokal_employee = employee.Employee()
        lokal_employee.min_number_consecutive_days_off = 4
        instance = instace.Instance.create(
            number_of_days=5,
            shift_typs=lokal_shift_type_list,
            emplyees=[lokal_employee],
        )
        vars = shift_vars.Shift_vars(instance, model)
        minimum_consecutove_days_off_new.Min_Cons_Days_Off_Alternative().build(instance, vars)
        vars.model.add(
            vars.vars[(0, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(1, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(2, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(3, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(4, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        status = cp_model.CpSolver().Solve(vars.model)

    with AssertModelFeasible() as model:
        lokal_shift_type_list = [shiftType.ShiftType()]
        lokal_employee = employee.Employee()
        lokal_employee.min_number_consecutive_days_off = 4
        instance = instace.Instance.create(
            number_of_days=5,
            shift_typs=lokal_shift_type_list,
            emplyees=[lokal_employee],
        )
        vars = shift_vars.Shift_vars(instance, model)
        minimum_consecutove_days_off_new.Min_Cons_Days_Off_Alternative().build(instance, vars)
        vars.model.add(
            vars.vars[(0, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(1, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(2, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(3, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(4, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        status = cp_model.CpSolver().Solve(vars.model)




    # Min_Cons_Shifts_Alternative_exact
    with AssertModelFeasible() as model:
        lokal_shift_type_list = [shiftType.ShiftType()]
        lokal_employee = employee.Employee()
        lokal_employee.min_number_consecutive_days_off = 4
        instance = instace.Instance.create(
            number_of_days=5,
            shift_typs=lokal_shift_type_list,
            emplyees=[lokal_employee],
        )
        vars = shift_vars.Shift_vars(instance, model)
        minimum_consecutove_days_off_new.Min_Cons_Days_Off_Alternative_exact().build(instance, vars)
        status = cp_model.CpSolver().Solve(vars.model)

    with AssertModelInfeasible() as model:
        lokal_shift_type_list = [shiftType.ShiftType()]
        lokal_employee = employee.Employee()
        lokal_employee.min_number_consecutive_days_off = 4
        instance = instace.Instance.create(
            number_of_days=5,
            shift_typs=lokal_shift_type_list,
            emplyees=[lokal_employee],
        )
        vars = shift_vars.Shift_vars(instance, model)
        minimum_consecutove_days_off_new.Min_Cons_Days_Off_Alternative_exact().build(instance, vars)
        vars.model.add(
            vars.vars[(0, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(1, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(2, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        status = cp_model.CpSolver().Solve(vars.model)


    with AssertModelInfeasible() as model:
        lokal_shift_type_list = [shiftType.ShiftType()]
        lokal_employee = employee.Employee()
        lokal_employee.min_number_consecutive_days_off = 4
        instance = instace.Instance.create(
            number_of_days=5,
            shift_typs=lokal_shift_type_list,
            emplyees=[lokal_employee],
        )
        vars = shift_vars.Shift_vars(instance, model)
        minimum_consecutove_days_off_new.Min_Cons_Days_Off_Alternative_exact().build(instance, vars)
        vars.model.add(
            vars.vars[(0, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(1, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(2, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(3, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(4, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        status = cp_model.CpSolver().Solve(vars.model)

    with AssertModelInfeasible() as model:
        lokal_shift_type_list = [shiftType.ShiftType()]
        lokal_employee = employee.Employee()
        lokal_employee.min_number_consecutive_days_off = 4
        instance = instace.Instance.create(
            number_of_days=5,
            shift_typs=lokal_shift_type_list,
            emplyees=[lokal_employee],
        )
        vars = shift_vars.Shift_vars(instance, model)
        minimum_consecutove_days_off_new.Min_Cons_Days_Off_Alternative_exact().build(instance, vars)
        vars.model.add(
            vars.vars[(0, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(1, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(2, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(3, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(4, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        status = cp_model.CpSolver().Solve(vars.model)

    with AssertModelFeasible() as model:
        lokal_shift_type_list = [shiftType.ShiftType()]
        lokal_employee = employee.Employee()
        lokal_employee.min_number_consecutive_days_off = 4
        instance = instace.Instance.create(
            number_of_days=5,
            shift_typs=lokal_shift_type_list,
            emplyees=[lokal_employee],
        )
        vars = shift_vars.Shift_vars(instance, model)
        minimum_consecutove_days_off_new.Min_Cons_Days_Off_Alternative_exact().build(instance, vars)
        vars.model.add(
            vars.vars[(0, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(1, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(2, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(3, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(4, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        status = cp_model.CpSolver().Solve(vars.model)





# Min_Cons_Days_Off_Alternative_exact_Enforce_If
    with AssertModelFeasible() as model:
        lokal_shift_type_list = [shiftType.ShiftType()]
        lokal_employee = employee.Employee()
        lokal_employee.min_number_consecutive_days_off = 4
        instance = instace.Instance.create(
            number_of_days=5,
            shift_typs=lokal_shift_type_list,
            emplyees=[lokal_employee],
        )
        vars = shift_vars.Shift_vars(instance, model)
        minimum_consecutove_days_off_new.Min_Cons_Days_Off_Alternative_exact_Enforce_If().build(instance, vars)
        status = cp_model.CpSolver().Solve(vars.model)

    with AssertModelInfeasible() as model:
        lokal_shift_type_list = [shiftType.ShiftType()]
        lokal_employee = employee.Employee()
        lokal_employee.min_number_consecutive_days_off = 4
        instance = instace.Instance.create(
            number_of_days=5,
            shift_typs=lokal_shift_type_list,
            emplyees=[lokal_employee],
        )
        vars = shift_vars.Shift_vars(instance, model)
        minimum_consecutove_days_off_new.Min_Cons_Days_Off_Alternative_exact_Enforce_If().build(instance, vars)
        vars.model.add(
            vars.vars[(0, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(1, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(2, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        status = cp_model.CpSolver().Solve(vars.model)


    with AssertModelInfeasible() as model:
        lokal_shift_type_list = [shiftType.ShiftType()]
        lokal_employee = employee.Employee()
        lokal_employee.min_number_consecutive_days_off = 4
        instance = instace.Instance.create(
            number_of_days=5,
            shift_typs=lokal_shift_type_list,
            emplyees=[lokal_employee],
        )
        vars = shift_vars.Shift_vars(instance, model)
        minimum_consecutove_days_off_new.Min_Cons_Days_Off_Alternative_exact_Enforce_If().build(instance, vars)
        vars.model.add(
            vars.vars[(0, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(1, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(2, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(3, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(4, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        status = cp_model.CpSolver().Solve(vars.model)

    with AssertModelInfeasible() as model:
        lokal_shift_type_list = [shiftType.ShiftType()]
        lokal_employee = employee.Employee()
        lokal_employee.min_number_consecutive_days_off = 4
        instance = instace.Instance.create(
            number_of_days=5,
            shift_typs=lokal_shift_type_list,
            emplyees=[lokal_employee],
        )
        vars = shift_vars.Shift_vars(instance, model)
        minimum_consecutove_days_off_new.Min_Cons_Days_Off_Alternative_exact_Enforce_If().build(instance, vars)
        vars.model.add(
            vars.vars[(0, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(1, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(2, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(3, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(4, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        status = cp_model.CpSolver().Solve(vars.model)

    with AssertModelFeasible() as model:
        lokal_shift_type_list = [shiftType.ShiftType()]
        lokal_employee = employee.Employee()
        lokal_employee.min_number_consecutive_days_off = 4
        instance = instace.Instance.create(
            number_of_days=5,
            shift_typs=lokal_shift_type_list,
            emplyees=[lokal_employee],
        )
        vars = shift_vars.Shift_vars(instance, model)
        minimum_consecutove_days_off_new.Min_Cons_Days_Off_Alternative_exact_Enforce_If().build(instance, vars)
        vars.model.add(
            vars.vars[(0, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(1, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(2, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(3, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(4, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        status = cp_model.CpSolver().Solve(vars.model)




    # Min_Cons_Days_Off_Alternative_Enforce_If
    with AssertModelFeasible() as model:
        lokal_shift_type_list = [shiftType.ShiftType()]
        lokal_employee = employee.Employee()
        lokal_employee.min_number_consecutive_days_off = 4
        instance = instace.Instance.create(
            number_of_days=5,
            shift_typs=lokal_shift_type_list,
            emplyees=[lokal_employee],
        )
        vars = shift_vars.Shift_vars(instance, model)
        minimum_consecutove_days_off_new.Min_Cons_Days_Off_Alternative_Enforce_If().build(instance, vars)
        status = cp_model.CpSolver().Solve(vars.model)

    with AssertModelInfeasible() as model:
        lokal_shift_type_list = [shiftType.ShiftType()]
        lokal_employee = employee.Employee()
        lokal_employee.min_number_consecutive_days_off = 4
        instance = instace.Instance.create(
            number_of_days=5,
            shift_typs=lokal_shift_type_list,
            emplyees=[lokal_employee],
        )
        vars = shift_vars.Shift_vars(instance, model)
        minimum_consecutove_days_off_new.Min_Cons_Days_Off_Alternative_Enforce_If().build(instance, vars)
        vars.model.add(
            vars.vars[(0, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(1, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(2, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        status = cp_model.CpSolver().Solve(vars.model)

    with AssertModelInfeasible() as model:
        lokal_shift_type_list = [shiftType.ShiftType()]
        lokal_employee = employee.Employee()
        lokal_employee.min_number_consecutive_days_off = 4
        instance = instace.Instance.create(
            number_of_days=5,
            shift_typs=lokal_shift_type_list,
            emplyees=[lokal_employee],
        )
        vars = shift_vars.Shift_vars(instance, model)
        minimum_consecutove_days_off_new.Min_Cons_Days_Off_Alternative_Enforce_If().build(instance, vars)
        vars.model.add(
            vars.vars[(0, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(1, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(2, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(3, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(4, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        status = cp_model.CpSolver().Solve(vars.model)


    with AssertModelInfeasible() as model:
        lokal_shift_type_list = [shiftType.ShiftType()]
        lokal_employee = employee.Employee()
        lokal_employee.min_number_consecutive_days_off = 4
        instance = instace.Instance.create(
            number_of_days=5,
            shift_typs=lokal_shift_type_list,
            emplyees=[lokal_employee],
        )
        vars = shift_vars.Shift_vars(instance, model)
        minimum_consecutove_days_off_new.Min_Cons_Days_Off_Alternative_Enforce_If().build(instance, vars)
        vars.model.add(
            vars.vars[(0, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(1, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(2, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(3, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(4, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        status = cp_model.CpSolver().Solve(vars.model)

    with AssertModelFeasible() as model:
        lokal_shift_type_list = [shiftType.ShiftType()]
        lokal_employee = employee.Employee()
        lokal_employee.min_number_consecutive_days_off = 4
        instance = instace.Instance.create(
            number_of_days=5,
            shift_typs=lokal_shift_type_list,
            emplyees=[lokal_employee],
        )
        vars = shift_vars.Shift_vars(instance, model)
        minimum_consecutove_days_off_new.Min_Cons_Days_Off_Alternative_Enforce_If().build(instance, vars)
        vars.model.add(
            vars.vars[(0, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(1, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(2, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(3, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(4, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        status = cp_model.CpSolver().Solve(vars.model)



    with AssertModelInfeasible() as model:
        lokal_shift_type_list = [shiftType.ShiftType()]
        lokal_employee = employee.Employee()
        lokal_employee.min_number_consecutive_days_off = 3
        instance = instace.Instance.create(
            number_of_days=5,
            shift_typs=lokal_shift_type_list,
            emplyees=[lokal_employee],
        )
        vars = shift_vars.Shift_vars(instance, model)
        minimum_consecutove_days_off_new.Minimum_consecutive_days_off_new().build(
            instance, vars
        )
        status = cp_model.CpSolver().Solve(vars.model)
        assert status == cp_model.OPTIMAL or status == cp_model.FEASIBLE
        vars.model.add(
            vars.vars[(0, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(1, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(2, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        status = cp_model.CpSolver().Solve(vars.model)
        assert status == cp_model.INFEASIBLE

    with AssertModelInfeasible() as model:
        lokal_shift_type_list = [shiftType.ShiftType()]
        lokal_employee = employee.Employee()
        lokal_employee.min_number_consecutive_days_off = 3
        instance = instace.Instance.create(
            number_of_days=5,
            shift_typs=lokal_shift_type_list,
            emplyees=[lokal_employee],
        )
        vars = shift_vars.Shift_vars(instance, model)
        minimum_consecutove_days_off_new.Minimum_consecutive_days_off_new().build(
            instance, vars
        )
        status = cp_model.CpSolver().Solve(vars.model)
        assert status == cp_model.OPTIMAL or status == cp_model.FEASIBLE
        vars.model.add(
            vars.vars[(0, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        vars.model.add(
            vars.vars[(1, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(2, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 0
        )
        vars.model.add(
            vars.vars[(3, lokal_shift_type_list[0].uid, lokal_employee.uid)] == 1
        )
        status = cp_model.CpSolver().Solve(vars.model)
        assert status == cp_model.INFEASIBLE


def test_days_off():
    with AssertModelInfeasible() as model:
        lokal_shift_type = shiftType.ShiftType()
        lokal_employee = employee.Employee(blocked_shifts={0})
        instance = instace.Instance.create(
            number_of_days=1,
            shift_typs=[lokal_shift_type],
            emplyees=[lokal_employee],
        )
        vars = shift_vars.Shift_vars(instance, model)
        days_off_new.Days_off_new().build(instance, vars)

        model.Add(vars.vars[(0, lokal_shift_type.uid, lokal_employee.uid)] == 1)


def test_cover_requirements():
    with AssertModelInfeasible() as model:
        lokal_shift_types = [shiftType.ShiftType()]
        lokal_employee = employee.Employee()

        # lokal_shift = shift.Shift()
        # lokal_shift.preffert_number_employees = 3
        # <-- Typ-Hinweis + leeres Dict
        # shifts: dict[int, dict[shiftType.TypeUid, shift.Shift]] = {}
        # shifts[0] = {}  # inneres Dict initialisieren
        # shifts[0][lokal_shift_types[0].uid] = lokal_shift
        instance = instace.Instance.create(
            number_of_days=1,
            shift_typs=lokal_shift_types,
            emplyees=[lokal_employee],
            cover_requirements={(0, lokal_shift_types[0].uid): (3, 1, 1)},
        )

        vars = shift_vars.Shift_vars(instance, model)
        cover_requirements.Cover_requirements().build(instance, vars)
        for type_uid in lokal_shift_types:
            model.Add(vars.vars[(0, type_uid.uid, lokal_employee.uid)] == 1)
            model.Add(vars.below_prefferd_vars[(0, type_uid.uid)] == 1)


# nicht vollumfassend
def test_max_weekends_1():
    with AssertModelInfeasible() as model:
        lokal_shift_type = shiftType.ShiftType()
        lokal_employee = employee.Employee(max_number_weekends=0)
        instance = instace.Instance.create(
            number_of_days=7,
            shift_typs=[lokal_shift_type],
            emplyees=[lokal_employee],
            weekend_days={6},
        )
        vars = shift_vars.Shift_vars(instance, model)
        max_weekend_days.Max_weekend_days().build(instance, vars)
        # test if an employee can work one weekend, which shouldnt be possible

        model.Add(vars.vars[(6, lokal_shift_type.uid, lokal_employee.uid)] == 1)


# nicht vollumfassend
def test_max_weekends_2():
    lokal_shift_type = shiftType.ShiftType()
    lokal_employee = employee.Employee(max_number_weekends=1)
    instance = instace.Instance.create(
        number_of_days=7,
        shift_typs=[lokal_shift_type],
        emplyees=[lokal_employee],
    )
    vars = shift_vars.Shift_vars(instance)
    max_weekend_days.Max_weekend_days().build(instance, vars)
    # test if weekend_var is correctly set to 1 when employee works on weekend

    vars.model.Add(vars.vars[(6, lokal_shift_type.uid, lokal_employee.uid)] == 1)

    solver = cp_model.CpSolver()
    status = solver.Solve(vars.model)
    assert status == cp_model.OPTIMAL or status == cp_model.FEASIBLE
    x = solver.Value(vars.weekend_vars[(6, lokal_employee.uid)])
    assert x == 1


# nicht vollumfassend
def test_max_weekends_lns_1():
    lokal_shift_type = shiftType.ShiftType()
    lokal_employee = employee.Employee(max_number_weekends=1)
    instance = instace.Instance.create(
        number_of_days=4,
        shift_typs=[lokal_shift_type],
        emplyees=[lokal_employee],
        weekend_days={0},
    )
    vars = shift_vars.Shift_vars(instance)
    max_weekend_days_lns.Max_weekend_days(start_day=13).build(instance, vars)
    # test if weekend_var is correctly set to 1 when employee works on weekend

    vars.model.Add(vars.vars[(0, lokal_shift_type.uid, lokal_employee.uid)] == 1)

    solver = cp_model.CpSolver()
    status = solver.Solve(vars.model)
    assert status == cp_model.OPTIMAL or status == cp_model.FEASIBLE
    x = solver.Value(vars.weekend_vars[(0, lokal_employee.uid)])
    assert x == 1
