import logging
import re
from pathlib import Path

from cpsat_utils.testing import AssertModelFeasible
from ortools.sat.python import cp_model

from src.help_functions import (
    compare_solutions,
    find_best_solution_for_modified_instance,
)
from src.solution import Solution

from .inputTypes import employee, instace, shiftType
from .LNS import lns, minimal_change_lns, slice_instance
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


def load_solution_from_first_threshold(instance_name: str) -> Solution:
    """Lädt eine Solution aus dem first_solution_with_below_threshold Ordner.

    Args:
        instance_name: z.B. "Instance9_seed817573_1S0_wv0_o0_1Scp0.025_wvcp0.012_ocn0_new_immediate_first_0"

    Returns:
        Solution: Die geladene Solution
    """
    folder = (
        Path(__file__).resolve().parent.parent / "first_solution_with_below_threshold"
    )
    path = folder / f"{instance_name}.json"
    return Solution.from_json_path(path)


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
    test_file = Path.joinpath(
        Path(__file__).resolve().parent.parent, "data", "instance_raw", "Instance9.txt"
    )
    instance = parseTXT.parse_txt(test_file)
    vars = Shift_vars(instance)
    solv = Solver(instance, vars)
    sol1 = solv.solve_with_early_stop(
        max_time_in_seconds=500, log_search_progress=False
    )
    old_sol = load_solution_from_first_threshold(
        "Instance23_seed9033871_1S0_wv0_o0_1Scp0.025_wvcp0.012_ocn0_new_immediate_first_0"
    )
    inst = get_tes_data()
    lns_solver = lns.LNS(old_sol, timeout_seconds=60)
    improved_solution = lns_solver.solve()
    # improved_solution.print_all_variables_values()
    # print("Objective value before LNS:", old_sol.objective_value)
    print("Objective value after LNS:", improved_solution.objective_value)


def run_lns_minimal_change_example():
    old_sol = Solution.from_json_file("Instance9")
    inst = get_tes_data()
    lns_solver = lns.LNS(
        old_sol,
        timeout_seconds=60,
        start_search_window_size=5,
    )
    improved_solution = minimal_change_lns.solve_changes(
        old_sol, [0], max_solve_time=60
    )
    # improved_solution.print_all_variables_values()
    print("Objective value before LNS:", old_sol.objective_value)
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
        # sol = solv.solve(max_time_in_seconds=180)
        sol = solv.warm_start_greedy(max_time_in_seconds=180, instance=instance)
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


def try_compare_multiple_solutions():
    test_file = Path.joinpath(
        Path(__file__).resolve().parent.parent, "data", "instance_raw", "Instance3.txt"
    )
    instance = parseTXT.parse_txt(test_file)
    vars = Shift_vars(instance)
    solv = Solver(instance, vars)
    sol1 = solv.solve(max_time_in_seconds=180)
    sol2 = solv.solve(max_time_in_seconds=180)
    sol3 = solv.solve(max_time_in_seconds=180)

    # print(
    #     compare_multiple_solutions(
    #         [sol1, sol2, sol3], threshold=2.0, include_details=True
    #     )
    # )
    print(find_best_solution_for_modified_instance([sol1, sol2, sol3], instance))


def try_warmstart_callback():
    test_file = Path.joinpath(
        Path(__file__).resolve().parent.parent, "data", "instance_raw", "Instance3.txt"
    )
    instance = parseTXT.parse_txt(test_file)
    vars = Shift_vars(instance)
    solv = Solver(instance, vars)
    sol1 = solv.solve(max_time_in_seconds=180)
    sollist = solv.warm_start_multi(
        solution=sol1, max_time_in_seconds=180, instance=instance
    )
    for sol in sollist:
        sol2 = sol[1]
        print("Änderungen: ", sol[0])
    print(sol2.solve_status)
    if sol2.solve_status == cp_model.OPTIMAL or sol2.solve_status == cp_model.FEASIBLE:
        sol2.to_json_file(instance.name)
    else:
        print(f"No feasible solution found for {instance.name}")
        return


def run_one_instance():
    test_file = Path.joinpath(
        Path(__file__).resolve().parent.parent, "data", "instance_raw", "Instance4.txt"
    )
    instance = parseTXT.parse_txt(test_file)
    vars = Shift_vars(instance)
    solv = Solver(instance, vars)
    sol1 = solv.solve_with_early_stop(max_time_in_seconds=500)
    print("Objective value:", sol1.objective_value)
    if sol1.solve_status == cp_model.OPTIMAL or sol1.solve_status == cp_model.FEASIBLE:
        sol1.to_json_file(instance.name)
    else:
        print(f"No feasible solution found for {instance.name}")
        return


def t_minimal_changes_lns():
    sol = Solution.from_json_file("Instance4_bearbeitet")
    minimal_change_lns.solve_changes(
        old_solution=sol,
        days_with_change=[0, 1, 2, 3],
        max_solve_time=120,
        log_search_progress=False,
    )


def t_slice_window():
    sol = Solution.from_json_file("error_lns_merge_old_start_6_end_11")
    si = slice_instance.Slice_instance(sol, 6, 11)
    solver = si.get_solver()
    new_sol = solver.solve()
    new_sol.to_json_file("sliced_instance_test")


def t_double_lns():
    sol = Solution.from_json_file("Instance4_bearbeitet")

    ###################
    sol1 = minimal_change_lns.__solve_change(
        sol,
        start_day=0,
        end_day=5,
        max_solve_time=120,
        log_search_progress=False,
    )
    print("Sol1 status:", sol1.solve_status)
    ###################
    sol2 = minimal_change_lns.__solve_change(
        sol,
        start_day=0,
        end_day=sol.instance.number_of_days - 1,
        max_solve_time=120,
        log_search_progress=False,
    )
    print("Sol2 status:", sol2.solve_status)


def check_work_vars():
    """Überprüft ob work_vars und weekend_vars logisch korrekt gesetzt sind."""
    sol = Solution.from_json_file("Instance20_seed6191911")

    print("\n" + "=" * 80)
    print("VALIDIERUNG: Work-Vars und Weekend-Vars Konsistenz")
    print("=" * 80)

    # ===== Check work_vars =====
    print("\n📋 Work-Vars Validierung:")
    work_errors = []

    for (day, employee_uid), work_var_value in sol.work_vars.items():
        # Überprüfe alle Schichten an diesem Tag für diesen Mitarbeiter
        shifts_assigned = [
            value
            for (d, shift_uid, emp_uid), value in sol.vars.items()
            if d == day and emp_uid == employee_uid and value == 1
        ]

        has_shifts = len(shifts_assigned) > 0
        emp_name = sol.instance.employees[employee_uid].name

        # Logik Check: work_var sollte 1 sein wenn Mitarbeiter arbeitet, 0 wenn nicht
        if work_var_value == 1 and not has_shifts:
            work_errors.append(
                f"Tag {day}, {emp_name}: work_var=1 aber keine Schichten zugewiesen"
            )
        elif work_var_value == 0 and has_shifts:
            work_errors.append(
                f"Tag {day}, {emp_name}: work_var=0 aber {len(shifts_assigned)} Schicht(en) zugewiesen"
            )

    if work_errors:
        print(f"   ❌ INVALID - {len(work_errors)} Fehler gefunden:")
        for error in work_errors:
            print(f"      • {error}")
    else:
        print("   ✅ VALID - Alle work_vars sind korrekt gesetzt")

    # ===== Check weekend_vars =====
    print("\n📋 Weekend-Vars Validierung:")
    weekend_errors = []

    for (weekend_idx, employee_uid), weekend_var_value in sol.weekend_vars.items():
        # Finde die Tage, die zu diesem Wochenende gehören (Samstag + Sonntag)
        weekend_days = []
        if weekend_idx in sol.instance.weekend_days:
            weekend_days = [weekend_idx]

            weekend_days.append(weekend_idx - 1)

        # Überprüfe ob der Mitarbeiter an mindestens einem Wochenendtag arbeitet
        works_on_weekend = False
        for day in weekend_days:
            shifts_assigned = [
                value
                for (d, shift_uid, emp_uid), value in sol.vars.items()
                if d == day and emp_uid == employee_uid and value == 1
            ]
            if len(shifts_assigned) > 0:
                works_on_weekend = True
                break

        emp_name = sol.instance.employees[employee_uid].name

        if weekend_var_value == 1 and not works_on_weekend:
            weekend_errors.append(
                f"Wochenende {weekend_idx}, {emp_name}: weekend_var=1 aber keine Schichten"
            )
        elif weekend_var_value == 0 and works_on_weekend:
            weekend_errors.append(
                f"Wochenende {weekend_idx}, {emp_name}: weekend_var=0 aber arbeitet am Wochenende"
            )

    if weekend_errors:
        print(f"   ❌ INVALID - {len(weekend_errors)} Fehler gefunden:")
        for error in weekend_errors:
            print(f"      • {error}")
    else:
        print("   ✅ VALID - Alle weekend_vars sind korrekt gesetzt")

    # ===== Gesamtergebnis =====
    print("\n" + "-" * 80)
    total_errors = len(work_errors) + len(weekend_errors)
    if total_errors == 0:
        print("✅ GESAMTERGEBNIS: Alle Variablen sind logisch korrekt gesetzt")
    else:
        print(f"❌ GESAMTERGEBNIS: {total_errors} Fehler gefunden")
    print("=" * 80 + "\n")


def main() -> None:
    # inst = get_tes_data()
    # x = inst
    # # t_single_day_validation()
    # get_test_constraint_deactivation()
    # get_test_solution_from_model()
    # sol = Solution.from_json_file("Instance1")
    # get_test_solution_from_model()
    # try_compare_solutions()
    # run_lns_example()
    # run_lns_minimal_change_example()
    # run_one_instance()
    # run_lns_example()
    # try_compare_multiple_solutions()
    # try_warmstart_callback()
    # calculate_all_instancen()
    # print_some_infos()
    # t_minimal_changes_lns()
    # test_double_lns()
    # t_slice_window()
    check_work_vars()


if __name__ == "__main__":
    main()
