from pathlib import Path
import time
from typing import Optional
import json
from src.solution import Solution
from src.parseData import parseTXT
from src.shift_vars import Shift_vars
from src.solver import Solver
from src.solution import Solution
from typing import List
from ortools.sat.python import cp_model
import gc
from src.solve_employees import solve_employee
from src.LNS import lns

import subprocess
from pathlib import Path
from src.solverCallback.callback_improvement_slowed import callback_improvement_slowed
from src.solverCallback.callback_until_objective_value import (
    callback_until_objective_value,
)


def main():
    json_dir = Path(__file__).resolve().parent / "data" / "instance_opt"
    json_files_opt = reversed(list(json_dir.glob("*.txt")))

    json_dir = Path(__file__).resolve().parent / "data" / "instance_immediate"
    json_files_immediate = list(json_dir.glob("*.txt"))

    json_dir = Path(__file__).resolve().parent / "data" / "instance_best_till_time"
    json_files_best_till_time = list(json_dir.glob("*.txt"))

    dict_objective_values = {
        "Instance1": 607.0,
        "Instance10": 5358.0,
        "Instance11": 3832.0,
        "Instance12": 5389.0,
        "Instance13": 14379.5,
        "Instance14": 1976.0,
        "Instance15": 5440.0,
        "Instance16": 4867.5,
        "Instance17": 6885.0,
        "Instance18": 6210.0,
        "Instance19": 4311.0,
        "Instance1ExtraLong": 607.0,
        "Instance2": 1333.5,
        "Instance20": 4561.5,
        "Instance21": 24822.5,
        "Instance22": 40563.5,
        "Instance23": 473532.5,
        "Instance3": 1154.0,
        "Instance4": 2727.0,
        "Instance5": 1349.0,
        "Instance6": 2466.5,
        "Instance7": 1086.0,
        "Instance8": 2067.0,
        "Instance9": 2002.0,
    }

    dict_objective_values = {
        "Instance1": 607.0,
        "Instance10": 5356.0,
        "Instance11": 3632.0,
        "Instance12": 5293.0,
        "Instance13": 14400.0,
        "Instance14": 1874.0,
        "Instance15": 5600.5,
        "Instance16": 4973.0,
        "Instance17": 6883.0,
        "Instance18": 6648.0,
        "Instance19": 4847.0,
        "Instance1ExtraLong": 607.0,
        "Instance2": 1233.0,
        "Instance20": 4689.0,
        "Instance21": 24260.0,
        "Instance22": 45968.0,
        "Instance23": 38976.0,
        "Instance3": 1105.0,
        "Instance4": 2725.0,
        "Instance5": 1349.0,
        "Instance6": 2365.0,
        "Instance7": 1086.0,
        "Instance8": 2067.0,
        "Instance9": 1849.0,
    }

    dict_constraint = {
        # 0:"original"
        # ,1:"new"
        # ,2:"Alternative"
        # ,3:"Alternative_enforce"
        # ,4:"Alternative_exact"
        # ,
        5: "Alternative_exact_Enforce"
        # ,7:"Alternative_exact_original"
    }

    # for json_file in json_files_opt:
    #     for x in range(0, 1):
    #         for incrementally in ["True","False"]:
    #             print(f"incrementally {incrementally} opt")
    #             print(f"Processing {json_file.name} with iteration {x} ...")
    #             # Call the secondary script with the current JSON file and iteration x
    #             subprocess.run(["python3", "process_json_solve_employee.py", str(json_file), str(x), "True", incrementally, str(30*60), "False"])

    # for json_file in json_files_immediate:
    #    for x in range(0, 4):
    #        for incrementally in ["False"]:
    #            print(f"incrementally {incrementally} immediate")
    #            print(f"Processing {json_file.name} with iteration {x} ...")
    # Call the secondary script with the current JSON file and iteration x
    #            subprocess.run(["python3", "process_json_solve_employee.py", str(json_file), str(x), "False", incrementally, str(15*60), "False"])

    # for json_file in json_files_best_till_time:
    #     for x in range(0, 3):
    #         for incrementally in ["True","False"]:
    #             print(f"incrementally {incrementally} till time")
    #             print(f"Processing {json_file.name} with iteration {x} ...")
    #             # Call the secondary script with the current JSON file and iteration x
    #             subprocess.run(["python3", "process_json_solve_employee.py", str(json_file), str(x), "True", incrementally, str(30*60), "True"])

    # for one_shift_time, work_var_time, opt_time in [(0,0,30)]:
    #     # ,  (2.5, 0, 0), (1, 0, 0),  (5, 2.5, 0), (5, 5, 0),  (10, 5, 0), (5, 10, 0),  (10, 10, 0), (0, 0, 30), (0, 2.5, 27.5), (2.5, 0, 27.5), (2.5, 2.5, 25), (2.5, 5, 22.5), (5, 2.5, 22.5), (5, 5, 20), (5, 10, 15), (10, 10, 10), (10, 5, 15)
    #     for json_file in json_files_best_till_time:
    #         for x in range(0, 3):
    #             if json_file.stem in dict_objective_values.keys():
    #                 callback_opt = callback_until_objective_value(desired_objective_value=dict_objective_values[json_file.stem])
    #                 print(f"one_shift, work_var, opt times: {(one_shift_time, work_var_time, opt_time)}")
    #                 print(f"Processing {json_file.name} with iteration {x} ...")
    #                 # Call the secondary script with the current JSON file and iteration x
    #                 instance = parseTXT.parse_txt(json_file)
    #                 solver_employee = solve_employee(instance)

    #                 solution = solver_employee.solve_instance_one_shift(one_shift_max_time=one_shift_time*60, fixed_work_var_opt_max_time=work_var_time*60, general_optimization_max_time=opt_time*60, optimization_callback=callback_opt)

    #                 filename = f"{solution.instance.name}_1S{one_shift_time}_wv{work_var_time}_o{opt_time}_till_median_immediate_first_{x}"

    #                 solution.to_json_file(filename)

    # for one_shift_time, work_var_time, opt_time in [(0,0,30)]:
    #     # ,  (2.5, 0, 0), (1, 0, 0),  (5, 2.5, 0), (5, 5, 0),  (10, 5, 0), (5, 10, 0),  (10, 10, 0), (0, 0, 30), (0, 2.5, 27.5), (2.5, 0, 27.5), (2.5, 2.5, 25), (2.5, 5, 22.5), (5, 2.5, 22.5), (5, 5, 20), (5, 10, 15), (10, 10, 10), (10, 5, 15)
    #     for json_file in json_files_best_till_time:
    #         for x in range(0, 2):
    #             print(f"one_shift, work_var, opt times: {(one_shift_time, work_var_time, opt_time)}")
    #             print(f"Processing {json_file.name} with iteration {x} ...")
    #             # Call the secondary script with the current JSON file and iteration x
    #             instance = parseTXT.parse_txt(json_file)
    #             solver_employee = solve_employee(instance)

    #             solution = solver_employee.solve_instance_one_shift(one_shift_max_time=one_shift_time*60, fixed_work_var_opt_max_time=work_var_time*60, general_optimization_max_time=opt_time*60)

    #             if opt_time != 0:
    #                 if solution.solve_status in [cp_model.OPTIMAL]:
    #                     filename = f"{solution.instance.name}_1S{one_shift_time}_wv{work_var_time}_o{opt_time}_opt_{x}"
    #                     solution.to_json_file(filename)
    #                 elif solution.solve_status in [cp_model.FEASIBLE]:
    #                     filename = f"{solution.instance.name}_1S{one_shift_time}_wv{work_var_time}_o{opt_time}_time_out_30_{x}"
    #                     solution.to_json_file(filename)
    #                 else:
    #                     error_filename = f"{solution.instance.name}_1S{one_shift_time}_wv{work_var_time}_o{opt_time}_{x}"
    #                     with open('error_log.txt', 'a') as error_file:
    #                         error_file.write(error_filename + '\n')
    #             else:
    #                 filename = f"{solution.instance.name}_1S{one_shift_time}_wv{work_var_time}_o{opt_time}_immediate_first_{x}"
    #                 solution.to_json_file(filename)

    # create LNS solution using first one_shift method and optimizing after LNS stop finding solutions
    for one_shift_time, work_var_time, opt_time in [(10, 10, 30), (0, 0, 30)]:
        #     # ,  (2.5, 0, 0), (1, 0, 0),  (5, 2.5, 0), (5, 5, 0),  (10, 5, 0), (5, 10, 0),  (10, 10, 0), (0, 0, 30), (0, 2.5, 27.5), (2.5, 0, 27.5), (2.5, 2.5, 25), (2.5, 5, 22.5), (5, 2.5, 22.5), (5, 5, 20), (5, 10, 15), (10, 10, 10), (10, 5, 15)
        for json_file in json_files_best_till_time:
            for x in range(0, 3):
                for (
                    percentual_improvement_shift,
                    time_between_checks_in_seconds_shift,
                    percentual_improvement_work_var,
                    time_between_checks_in_seconds_work_var,
                    numerical_improvement_opt,
                ) in [(0.025, 8, 0.012, 8, 0)]:
                    time_between_checks_in_seconds_opt = 120
                    callback_one_shift = callback_improvement_slowed(
                        percentual_improvement=percentual_improvement_shift,
                        time_between_checks_in_seconds=time_between_checks_in_seconds_shift,
                    )
                    callback_opt_work_var = callback_improvement_slowed(
                        percentual_improvement=percentual_improvement_work_var,
                        time_between_checks_in_seconds=time_between_checks_in_seconds_work_var,
                    )
                    callback_opt = callback_improvement_slowed(
                        numerical_improvement=numerical_improvement_opt,
                        time_between_checks_in_seconds=time_between_checks_in_seconds_opt,
                    )
                    print(
                        f"one_shift, work_var, opt times: {(one_shift_time, work_var_time, opt_time)}"
                    )
                    print(f"Processing {json_file.name} with iteration {x} ...")
                    # Call the secondary script with the current JSON file and iteration x
                    instance = parseTXT.parse_txt(json_file)
                    solver_employee = solve_employee(instance)
                    start_time = time.time()
                    solution = solver_employee.solve_instance_one_shift(
                        one_shift_max_time=one_shift_time * 60,
                        fixed_work_var_opt_max_time=work_var_time * 60,
                        general_optimization_max_time=0 * 60,
                        one_shift_callback=callback_one_shift,
                        fixed_work_var_opt_callback=callback_opt_work_var,
                    )

                    timeout_seconds = opt_time * 60 - (time.time() - start_time)
                    first_opt_time = time.time() - start_time

                    print(opt_time * 60 - (time.time() - start_time))
                    for not_better_stop_timer in [30]:
                        lns_start_time = time.time()
                        solution_lns = lns.LNS(
                            sol_or_instance=solution.model_copy(deep=True),
                            timeout_seconds=timeout_seconds,
                            log_level=20,
                        ).solve(not_better_break_after=not_better_stop_timer * 60)

                        only_lns_time = time.time() - lns_start_time
                        full_time = only_lns_time + first_opt_time
                        if solution_lns.solve_status in [
                            cp_model.FEASIBLE
                        ] or solution_lns.solve_status in [cp_model.OPTIMAL]:
                            solution_lns.solve_time = full_time
                            filename = f"{solution.instance.name}_1S{one_shift_time}_wv{work_var_time}_o{opt_time}_1Scp{percentual_improvement_shift}_wvcp{percentual_improvement_work_var}_ocn{numerical_improvement_opt}_timer{not_better_stop_timer}_lns_time_out_30_{x}"
                            solution_lns.to_json_file(filename)
                            filename = f"{solution.instance.name}_1S{one_shift_time}_wv{work_var_time}_o{opt_time}_1Scp{percentual_improvement_shift}_wvcp{percentual_improvement_work_var}_ocn{numerical_improvement_opt}_timer{not_better_stop_timer}_lns_immediate_first_{x}"
                            solution_lns.to_json_file(filename)

                            solution_lns.solve_time = only_lns_time
                            filename = f"{solution.instance.name}_1S{one_shift_time}_wv{work_var_time}_o{opt_time}_1Scp{percentual_improvement_shift}_wvcp{percentual_improvement_work_var}_ocn{numerical_improvement_opt}_timer{not_better_stop_timer}_onlylns_time_out_30_{x}"
                            solution_lns.to_json_file(filename)
                            filename = f"{solution.instance.name}_1S{one_shift_time}_wv{work_var_time}_o{opt_time}_1Scp{percentual_improvement_shift}_wvcp{percentual_improvement_work_var}_ocn{numerical_improvement_opt}_timer{not_better_stop_timer}_onlylns_immediate_first_{x}"
                            solution_lns.to_json_file(filename)

                        else:
                            error_filename = f"{solution.instance.name}_1S{one_shift_time}_wv{work_var_time}_o{opt_time}_1Scp{percentual_improvement_shift}_wvcp{percentual_improvement_work_var}_ocn{numerical_improvement_opt}_timer{not_better_stop_timer}_onlylns_{x}"
                            with open("error_log.txt", "a") as error_file:
                                error_file.write(error_filename + "\n")

                        print(f"time : {opt_time * 60 - (time.time() - start_time)}")
                        solution_opt = Solver(
                            instance.model_copy(deep=True),
                            Shift_vars(instance.model_copy(deep=True)),
                        ).warm_start_generalized(
                            hint_solution=solution_lns.model_copy(deep=True),
                            max_time_in_seconds=opt_time * 60
                            - (time.time() - start_time),
                        )

                        solution_opt.solve_time = (
                            time.time() - lns_start_time
                        ) + first_opt_time
                        if solution_opt.solve_status in [cp_model.OPTIMAL]:
                            filename = f"{solution.instance.name}_1S{one_shift_time}_wv{work_var_time}_o{opt_time}_1Scp{percentual_improvement_shift}_wvcp{percentual_improvement_work_var}_ocn{numerical_improvement_opt}_lns_alt_opt_{x}"
                            solution_opt.to_json_file(filename)
                        if solution_opt.solve_status in [
                            cp_model.FEASIBLE
                        ] or solution_opt.solve_status in [cp_model.OPTIMAL]:
                            filename = f"{solution.instance.name}_1S{one_shift_time}_wv{work_var_time}_o{opt_time}_1Scp{percentual_improvement_shift}_wvcp{percentual_improvement_work_var}_ocn{numerical_improvement_opt}_lns_alt_time_out_30_{x}"
                            solution_opt.to_json_file(filename)
                        else:
                            error_filename = f"{solution.instance.name}_1S{one_shift_time}_wv{work_var_time}_o{opt_time}_1Scp{percentual_improvement_shift}_wvcp{percentual_improvement_work_var}_ocn{numerical_improvement_opt}_lns_alt_opt_{x}"
                            with open("error_log.txt", "a") as error_file:
                                error_file.write(error_filename + "\n")

    # # create solutions using first solution from one_shift method and optimizing using normal optimization
    # for one_shift_time, work_var_time, opt_time in [(0, 0, 0), (0, 0, 30)]:
    #     #     # ,  (2.5, 0, 0), (1, 0, 0),  (5, 2.5, 0), (5, 5, 0),  (10, 5, 0), (5, 10, 0),  (10, 10, 0), (0, 0, 30), (0, 2.5, 27.5), (2.5, 0, 27.5), (2.5, 2.5, 25), (2.5, 5, 22.5), (5, 2.5, 22.5), (5, 5, 20), (5, 10, 15), (10, 10, 10), (10, 5, 15)
    #     for json_file in json_files_best_till_time:
    #         for x in range(0, 3):
    #             for (
    #                 percentual_improvement_shift,
    #                 time_between_checks_in_seconds_shift,
    #                 percentual_improvement_work_var,
    #                 time_between_checks_in_seconds_work_var,
    #                 numerical_improvement_opt,
    #             ) in [(0.025, 8, 0.012, 8, 0)]:
    #                 time_between_checks_in_seconds_opt = 120
    #                 callback_one_shift = callback_improvement_slowed(
    #                     percentual_improvement=percentual_improvement_shift,
    #                     time_between_checks_in_seconds=time_between_checks_in_seconds_shift,
    #                 )
    #                 callback_opt_work_var = callback_improvement_slowed(
    #                     percentual_improvement=percentual_improvement_work_var,
    #                     time_between_checks_in_seconds=time_between_checks_in_seconds_work_var,
    #                 )
    #                 callback_opt = callback_improvement_slowed(
    #                     numerical_improvement=numerical_improvement_opt,
    #                     time_between_checks_in_seconds=time_between_checks_in_seconds_opt,
    #                 )
    #                 print(
    #                     f"one_shift, work_var, opt times: {(one_shift_time, work_var_time, opt_time)}"
    #                 )
    #                 print(f"Processing {json_file.name} with iteration {x} ...")
    #                 # Call the secondary script with the current JSON file and iteration x
    #                 instance = parseTXT.parse_txt(json_file)
    #                 solver_employee = solve_employee(instance)

    #                 solution = solver_employee.solve_instance_one_shift(
    #                     one_shift_max_time=one_shift_time * 60,
    #                     fixed_work_var_opt_max_time=work_var_time * 60,
    #                     general_optimization_max_time=opt_time * 60,
    #                     one_shift_callback=callback_one_shift,
    #                     fixed_work_var_opt_callback=callback_opt_work_var,
    #                 )

    #                 if opt_time != 0:
    #                     if solution.solve_status in [cp_model.OPTIMAL]:
    #                         filename = f"{solution.instance.name}_1S{one_shift_time}_wv{work_var_time}_o{opt_time}_1Scp{percentual_improvement_shift}_wvcp{percentual_improvement_work_var}_ocn{numerical_improvement_opt}_alt_opt_{x}"
    #                         solution.to_json_file(filename)
    #                     if solution.solve_status in [
    #                         cp_model.FEASIBLE
    #                     ] or solution.solve_status in [cp_model.OPTIMAL]:
    #                         filename = f"{solution.instance.name}_1S{one_shift_time}_wv{work_var_time}_o{opt_time}_1Scp{percentual_improvement_shift}_wvcp{percentual_improvement_work_var}_ocn{numerical_improvement_opt}_alt_time_out_30_{x}"
    #                         solution.to_json_file(filename)
    #                     else:
    #                         error_filename = f"{solution.instance.name}_1S{one_shift_time}_wv{work_var_time}_o{opt_time}_{x}"
    #                         with open("error_log.txt", "a") as error_file:
    #                             error_file.write(error_filename + "\n")
    #                 else:
    #                     filename = f"{solution.instance.name}_1S{one_shift_time}_wv{work_var_time}_o{opt_time}_1Scp{percentual_improvement_shift}_wvcp{percentual_improvement_work_var}_ocn{numerical_improvement_opt}_alt_immediate_first_{x}"
    #                     solution.to_json_file(filename)

    # # create solutions using one_shift method and optimizing after finding an ok solution using one_shift method
    # for one_shift_time, work_var_time, opt_time in [(10, 10, 10)]:
    #     #     # ,  (2.5, 0, 0), (1, 0, 0),  (5, 2.5, 0), (5, 5, 0),  (10, 5, 0), (5, 10, 0),  (10, 10, 0), (0, 0, 30), (0, 2.5, 27.5), (2.5, 0, 27.5), (2.5, 2.5, 25), (2.5, 5, 22.5), (5, 2.5, 22.5), (5, 5, 20), (5, 10, 15), (10, 10, 10), (10, 5, 15)
    #     for json_file in json_files_best_till_time:
    #         for x in range(0, 3):
    #             for (
    #                 percentual_improvement_shift,
    #                 time_between_checks_in_seconds_shift,
    #                 percentual_improvement_work_var,
    #                 time_between_checks_in_seconds_work_var,
    #                 numerical_improvement_opt,
    #             ) in [(0.025, 8, 0.012, 8, 0), (0.05, 16, 0.024, 16, 0)]:
    #                 time_between_checks_in_seconds_opt = 120
    #                 callback_one_shift = callback_improvement_slowed(
    #                     percentual_improvement=percentual_improvement_shift,
    #                     time_between_checks_in_seconds=time_between_checks_in_seconds_shift,
    #                 )
    #                 callback_opt_work_var = callback_improvement_slowed(
    #                     percentual_improvement=percentual_improvement_work_var,
    #                     time_between_checks_in_seconds=time_between_checks_in_seconds_work_var,
    #                 )
    #                 callback_opt = callback_improvement_slowed(
    #                     numerical_improvement=numerical_improvement_opt,
    #                     time_between_checks_in_seconds=time_between_checks_in_seconds_opt,
    #                 )
    #                 print(
    #                     f"one_shift, work_var, opt times: {(one_shift_time, work_var_time, opt_time)}"
    #                 )
    #                 print(f"Processing {json_file.name} with iteration {x} ...")
    #                 # Call the secondary script with the current JSON file and iteration x
    #                 instance = parseTXT.parse_txt(json_file)
    #                 solver_employee = solve_employee(instance)

    #                 solution = solver_employee.solve_instance_one_shift(
    #                     one_shift_max_time=one_shift_time * 60,
    #                     fixed_work_var_opt_max_time=work_var_time * 60,
    #                     general_optimization_max_time=opt_time * 60,
    #                     one_shift_callback=callback_one_shift,
    #                     fixed_work_var_opt_callback=callback_opt_work_var,
    #                 )

    #                 if opt_time != 0:
    #                     if solution.solve_status in [cp_model.OPTIMAL]:
    #                         filename = f"{solution.instance.name}_1S{one_shift_time}_wv{work_var_time}_o{opt_time}_1Scp{percentual_improvement_shift}_wvcp{percentual_improvement_work_var}_ocn{numerical_improvement_opt}_alt_opt_{x}"
    #                         solution.to_json_file(filename)
    #                     if solution.solve_status in [
    #                         cp_model.FEASIBLE
    #                     ] or solution.solve_status in [cp_model.OPTIMAL]:
    #                         filename = f"{solution.instance.name}_1S{one_shift_time}_wv{work_var_time}_o{opt_time}_1Scp{percentual_improvement_shift}_wvcp{percentual_improvement_work_var}_ocn{numerical_improvement_opt}_alt_time_out_30_{x}"
    #                         solution.to_json_file(filename)
    #                     else:
    #                         error_filename = f"{solution.instance.name}_1S{one_shift_time}_wv{work_var_time}_o{opt_time}_{x}"
    #                         with open("error_log.txt", "a") as error_file:
    #                             error_file.write(error_filename + "\n")
    #                 else:
    #                     filename = f"{solution.instance.name}_1S{one_shift_time}_wv{work_var_time}_o{opt_time}_1Scp{percentual_improvement_shift}_wvcp{percentual_improvement_work_var}_ocn{numerical_improvement_opt}_alt_immediate_first_{x}"
    #                     solution.to_json_file(filename)


if __name__ == "__main__":
    main()
