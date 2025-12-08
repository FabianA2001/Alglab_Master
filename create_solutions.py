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

import subprocess
from pathlib import Path

def main():
    DATA_DIR = Path(__file__).resolve().parent / "data" / "instance_raw"
    json_dir = DATA_DIR
    json_files = list(json_dir.glob("*.txt"))
    dict_constraint = {
        #0:"original",1:"new",2:"Alternative",3:"Alternative_enforce",4:"Alternative_exact",5:"Alternative_exact_Enforce",
                       7:"Alternative_exact_original",8:"Alternative_Enforce_If_original"}
    for json_file in json_files:
        for x in range(0, 3):
            for constraint_number, key in dict_constraint.items():
                print(constraint_number, key)
                print(f"Processing {json_file.name} with iteration {x} key {key}...")
                # Call the secondary script with the current JSON file and iteration x
                subprocess.run(["python", "process_json.py", str(json_file), str(x), str(constraint_number), key])
                subprocess.run(["python", "process_json_immediate.py", str(json_file), str(x), str(constraint_number), key])

if __name__ == "__main__":
    main()