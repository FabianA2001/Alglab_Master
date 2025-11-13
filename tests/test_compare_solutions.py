from pathlib import Path

from src.help_functions import compare_solutions
from src.solution import Solution


def test_compare_returns_summary_keys():
    base = Path(__file__).resolve().parent.parent / "data" / "solutions"
    a_path = base / "Instance1"
    b_path = base / "Instance2"

    sol_a = Solution.from_json_file(a_path.name)
    sol_b = Solution.from_json_file(b_path.name)

    res = compare_solutions(sol_a, sol_b, include_details=True)

    assert "employees_with_changes" in res
    assert "total_changed_days" in res
    assert isinstance(res["employees_with_changes"], int)
    assert isinstance(res["total_changed_days"], int)
    # if details requested, ensure per_employee_changes structure exists
    assert "per_employee_changes" in res
    assert "per_day_changes" in res
