import logging
import re
from pathlib import Path

from cpsat_utils.testing import AssertModelFeasible
from ortools.sat.python import cp_model

from src.help_functions import compare_solutions
from src.solution import Solution

from .inputTypes import employee, instace, shiftType
from .LNS import lns
from .parseData import parseTXT
from .shift_vars import Shift_vars
from .solver import Solver

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def try_compare_solutions():
    sol_a = Solution.from_json_file("Instance1")
    sol_b = Solution.from_json_file("Instance2")

    result = compare_solutions(sol_a, sol_b, include_details=True)
    print(f"Mitarbeiter mit Änderungen: {result['employees_with_changes']}")
    print(f"Insgesamt geänderte Tagesschichten: {result['total_changed_days']}")


def sayHello(name="World") -> str:
    return f"Hello, {name}!"


def get_tes_data() -> instace.Instance:
    test_file = Path.joinpath(
        Path(__file__).resolve().parent.parent, "data", "instance_raw", "Instance9.txt"
    )
    # test_file = Path.joinpath(
    #     Path(__file__).resolve().parent.parent, "data", "instance_raw", "Instance13.txt"
    # )
    return parseTXT.parse_txt(test_file)


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


def run_lns_example():
    # old_sol = Solution.from_json_file("Instance9")
    inst = get_tes_data()
    lns_solver = lns.LNS(
        inst,
        timeout_seconds=60,
        start_search_window_size=5,
    )
    improved_solution = lns_solver.solve()
    # improved_solution.print_all_variables_values()
    # print("Objective value before LNS:", old_sol.objective_value)
    print("Objective value after LNS:", improved_solution.objective_value)


def get_all_instancen() -> list[instace.Instance]:
    data_folder = Path.joinpath(
        Path(__file__).resolve().parent.parent, "data", "instance_raw"
    )

    # Hilfsfunktion für numerische Sortierung
    def natural_sort_key(path):
        # Extrahiere Zahlen aus dem Dateinamen für numerische Sortierung
        parts = re.split(r"(\d+)", path.name)
        return [int(part) if part.isdigit() else part for part in parts]

    instances = []
    # Sortiere die Dateien numerisch korrekt
    files = sorted(data_folder.iterdir(), key=natural_sort_key)
    for file in files:
        if file.suffix == ".txt":
            instances.append(parseTXT.parse_txt(file))
    return instances


def calculate_all_instancen():
    for instance in get_all_instancen():
        vars = Shift_vars(instance)
        solv = Solver(instance, vars)
        sol = solv.solve(max_time_in_seconds=180)
        print(sol.solve_status)
        if (
            sol.solve_status == cp_model.OPTIMAL
            or sol.solve_status == cp_model.FEASIBLE
        ):
            sol.to_json_file(instance.name)
        else:
            print(f"No feasible solution found for {instance.name}")
            return


def print_some_infos():
    instances = get_all_instancen()
    for inst in instances[5 : 5 + 1]:
        print(f"Instance: {inst.name}")
        print("=" * 60)

        # Übersicht für jeden Mitarbeiter
        for emp in inst.employees.values():
            print(f"  Mitarbeiter: {emp.name} (UID: ...{str(emp.uid)[-3:]})")
            print(
                f"    Max. aufeinanderfolgende Arbeitstage: {emp.max_number_consecutive_shifts}"
            )
            print(
                f"    Min. aufeinanderfolgende freie Tage:  {emp.min_number_consecutive_days_off}"
            )
            print()

        print()


def main() -> None:
    # inst = get_tes_data()
    # x = inst
    # # t_single_day_validation()
    # get_test_constraint_deactivation()
    # get_test_solution_from_model()
    # sol = Solution.from_json_file("Instance1")
    # get_test_solution_from_model()
    # try_compare_solutions()
    run_lns_example()
    # calculate_all_instancen()
    # print_some_infos()


if __name__ == "__main__":
    main()
