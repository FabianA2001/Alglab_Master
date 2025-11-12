from pathlib import Path

from src.help_functions import compare_solutions


def test_compare_returns_summary_keys():
    base = Path(__file__).resolve().parent.parent / "data" / "solutions"
    a = base / "Instance1.json"
    b = base / "Instance2.json"

    res = compare_solutions(str(a), str(b), include_details=True)

    assert "employees_with_changes" in res
    assert "total_changed_days" in res
    assert isinstance(res["employees_with_changes"], int)
    assert isinstance(res["total_changed_days"], int)
    # if details requested, ensure per_employee_changes structure exists
    assert "per_employee_changes" in res
    assert "per_day_changes" in res
