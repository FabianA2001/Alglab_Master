from pathlib import Path
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

import subprocess
from pathlib import Path

def main():
    json_dir = Path(__file__).resolve().parent / "data" / "instance_opt"
    json_files_opt = reversed(list(json_dir.glob("*.txt")))

    json_dir = Path(__file__).resolve().parent / "data" / "instance_immediate"
    json_files_immediate = list(json_dir.glob("*.txt"))

    json_dir = Path(__file__).resolve().parent / "data" / "instance_best_till_time"
    json_files_best_till_time = list(json_dir.glob("*.txt"))


    dict_constraint = {
        # 0:"original"
        # ,1:"new"
        # ,2:"Alternative"
        # ,3:"Alternative_enforce"
        # ,4:"Alternative_exact"
        # ,
        5:"Alternative_exact_Enforce"
        #,7:"Alternative_exact_original"
        }
    # for json_file in json_files_opt:
    #     for x in range(0, 1):
    #         for incrementally in ["True","False"]:
    #             print(f"incrementally {incrementally} opt")
    #             print(f"Processing {json_file.name} with iteration {x} ...")
    #             # Call the secondary script with the current JSON file and iteration x
    #             subprocess.run(["python3", "process_json_solve_employee.py", str(json_file), str(x), "True", incrementally, str(30*60), "False"])

    #for json_file in json_files_immediate:
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

    for json_file in json_files_best_till_time:
        for x in range(0, 3):
            for one_shift_time, work_var_time, opt_time in [(2.5, 2.5, 0), (2.5, 5, 0), (0, 0, 0), (5, 2.5, 0), (5, 5, 0),  (10, 5, 0), (5, 10, 0),  (10, 10, 0), (0, 0, 30), (0, 2.5, 27.5), (2.5, 0, 27.5), (2.5, 2.5, 25), (2.5, 5, 22.5), (5, 2.5, 22.5), (5, 5, 20), (5, 10, 15), (10, 10, 10), (10, 5, 15)]:
                print(f"one_shift, work_var, opt times: {(one_shift_time, work_var_time, opt_time)}")
                print(f"Processing {json_file.name} with iteration {x} ...")
                # Call the secondary script with the current JSON file and iteration x
                instance = parseTXT.parse_txt(json_file)
                solver_employee = solve_employee(instance)

                solution = solver_employee.solve_instance_one_shift(one_shift_max_time=one_shift_time, fixed_work_var_opt_max_time=work_var_time, general_optimization_max_time=opt_time)

                if opt_time != 0:
                    if solution.solve_status in [cp_model.OPTIMAL]:
                        filename = f"{solution.instance.name}_1S{one_shift_time}_wv{work_var_time}_o{opt_time}_opt_{x}"
                        solution.to_json_file(filename)
                    elif solution.solve_status in [cp_model.FEASIBLE]:
                        filename = f"{solution.instance.name}_1S{one_shift_time}_wv{work_var_time}_o{opt_time}_time_out_30_{x}"
                        solution.to_json_file(filename)
                    else:
                        error_filename = f"{solution.instance.name}_1S{one_shift_time}_wv{work_var_time}_o{opt_time}"
                        with open('error_log.txt', 'a') as error_file:
                            error_file.write(error_filename + '\n')
                else:
                    filename = f"{solution.instance.name}_1S{one_shift_time}_wv{work_var_time}_o{opt_time}_immediate_first_{x}"
                    solution.to_json_file(filename)
                    

if __name__ == "__main__":
    main()
