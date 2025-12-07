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


def benchmark():
    DATA_DIR = Path(__file__).resolve().parent / "data" / "instance_raw"
    json_dir = DATA_DIR
    
    # List all JSON files
    json_files = list(json_dir.glob("*.txt"))

    # Iterate over JSON files
    for json_file in json_files:
        instance = parseTXT.parse_txt(json_file)  # Load the instance from the JSON file
        count = 0
        # Iterate over constraints
        
        solver = Solver(instance, Shift_vars(instance))

        filename = f"{instance.name}_new"
        print("\n" + filename)

        solution = solver.solve_with_early_stop(log_search_progress=False, max_time_in_seconds=15*60).model_copy(deep=True)

    
        

        if solution.solve_status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            # Save the solution to the JSON file
            solution.instance.name = filename
            solution.to_json_file(filename)
        else:
            # Open the file in append mode and add the line
            with open("no_solution_found_new.txt", 'a') as file:
                file.write(filename)
                file.write("\n")

if __name__ == "__main__":
    benchmark()
