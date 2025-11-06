from pathlib import Path

from ... import solution
from ..validation.constraint_checker import check_all_constraints

OVERVIEW_DATA_APTH = (
    Path(__file__).resolve().parent.parent.parent.parent / "data" / "overview.json"
)


def get_overview_data() -> dict[str, tuple[float, float]]:
    import json

    try:
        with open(OVERVIEW_DATA_APTH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except (json.JSONDecodeError, FileNotFoundError):
        return {}


def update_table(sol: solution.Solution):
    import json

    valide, _ = check_all_constraints(sol)
    if not valide:
        return
    data = get_overview_data()
    inst_name = sol.instance.name
    objective_value = sol.objective_value
    solve_time = sol.solve_time
    if inst_name not in data:
        data[inst_name] = (objective_value, solve_time)
    else:
        prev_objective, prev_time = data[inst_name]
        if objective_value > prev_objective:
            return
        data[inst_name] = (objective_value, solve_time)

    # Save the updated data back to the file
    with open(OVERVIEW_DATA_APTH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def show():
    pass
