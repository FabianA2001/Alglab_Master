from pathlib import Path

from cpsat_utils.testing import AssertModelFeasible
from ortools.sat.python import cp_model

from . import shift_vars
from .inputTypes import employee, instace, shiftType
from .parseData.parseXML import print_xml_structure


def sayHello(name="World") -> str:
    return f"Hello, {name}!"


def get_tes_data():
    test_file = Path.joinpath(
        Path(__file__).resolve().parent.parent, "data", "Instance1.ros"
    )
    print_xml_structure(test_file)


def t_single_day_validation():
    with AssertModelFeasible() as model:
        lokal_shift_type = shiftType.ShiftType()
        employees = [employee.Employee() for _ in range(2)]
        instance = instace.Instance(
            number_of_days=1,
            shift_typs=[lokal_shift_type],
            emplyees=employees,
        )
        instance.get_shift(0, lokal_shift_type.uid).preffert_number_employees = 1

        vars = shift_vars.Shift_vars(instance, model)
        for lokal_employee in employees:
            vars.model.add(
                vars.vars[(0, lokal_shift_type.uid, lokal_employee.uid)] == 1
            )
        solver = cp_model.CpSolver()
        status = solver.Solve(vars.model)
        assert status == cp_model.OPTIMAL or status == cp_model.FEASIBLE
        assert solver.Value(vars.get_above_prefferd_var(0, lokal_shift_type.uid)) == 1


def main() -> None:
    # get_tes_data()
    t_single_day_validation()


if __name__ == "__main__":
    main()
