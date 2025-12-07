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

    for json_file in json_files:
        for x in range(2):
            print(f"Processing {json_file.name} with iteration {x}...")
            # Call the secondary script with the current JSON file and iteration x
            subprocess.run(["python", "process_json.py", str(json_file), str(x)])

if __name__ == "__main__":
    main()