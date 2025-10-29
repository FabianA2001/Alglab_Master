from pathlib import Path

from .inputTypes import employee, instace, shiftType
from .parseData.parseXML import print_xml_structure


def sayHello(name="World") -> str:
    return f"Hello, {name}!"


def get_tes_data():
    test_file = Path.joinpath(
        Path(__file__).resolve().parent.parent, "data", "Instance1.ros"
    )
    print_xml_structure(test_file)


def main() -> None:
    # get_tes_data()
    inst = instace.Instance(14, (), [shiftType.ShiftType()], [employee.Employee()])


if __name__ == "__main__":
    main()
