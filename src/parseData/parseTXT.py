from pathlib import Path

from ..inputTypes import instace


def parse_txt(txt_file_path: Path) -> instace.Instance:
    with open(txt_file_path, "r") as file:
        number_of_days = 0
        for line in file:
            if line.startswith("#"):
                continue
            if line.startswith("#"):
                print(line)
