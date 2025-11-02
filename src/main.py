from pathlib import Path

from cpsat_utils.testing import AssertModelFeasible
from ortools.sat.python import cp_model

from .inputTypes import employee, instace, shiftType
from .parseData import parseTXT
from .shift_vars import Shift_vars
from .solution import Solution
from .solver import Solver


def sayHello(name="World") -> str:
    return f"Hello, {name}!"


def get_tes_data() -> instace.Instance:
    test_file = Path.joinpath(
        Path(__file__).resolve().parent.parent, "data", "instance_raw", "Instance1.txt"
    )
    return parseTXT.parse_txt(test_file)


def get_test_constraint_deactivation():
    instance = get_tes_data()
    vars = Shift_vars(instance)
    print("active constraints: \n", vars.active_constraints)
    for key in instance.employees.keys():
        print(f"days_off_{instance.employees[key]}")
        vars.deactivate_constraint(f"days_off_{instance.employees[key].uid}")
    print("\n" * 5)
    print("deactive constraints: \n", vars.active_constraints)
    solution = Solver(instance, Shift_vars(instance)).solve_with_constraints(
        list(vars.active_constraints.values())
    )
    solution.print_all_variables()
    solution.print_all_variables_values()
    print("obj value: ", solution.objective_value)


def get_test_solution_from_model():
    instance = get_tes_data()
    vars = Shift_vars(instance)
    solution = Solver(instance, vars).solve()
    solution.print_all_variables()
    solution.print_all_variables_values()
    print("obj value: ", solution.objective_value)


def t_single_day_validation():
    with AssertModelFeasible() as model:
        lokal_shift_type = shiftType.ShiftType()
        employees = [employee.Employee() for _ in range(2)]
        instance = instace.Instance.create(
            number_of_days=1,
            shift_typs=[lokal_shift_type],
            emplyees=employees,
        )
        instance.get_shift(0, lokal_shift_type.uid).preffert_number_employees = 1

        vars = Shift_vars(instance, model)
        for lokal_employee in employees:
            vars.model.add(
                vars.vars[(0, lokal_shift_type.uid, lokal_employee.uid)] == 1
            )
        solver = cp_model.CpSolver()
        status = solver.Solve(vars.model)

        assert status == cp_model.OPTIMAL or status == cp_model.FEASIBLE
        assert solver.Value(vars.get_above_prefferd_var(0, lokal_shift_type.uid)) == 1


def main() -> None:
    # inst = get_tes_data()
    # x = inst
    # # t_single_day_validation()
    # get_test_constraint_deactivation()
    # get_test_solution_from_model()
    sol = Solution.from_json_file("Instance1")


if __name__ == "__main__":
    main()
