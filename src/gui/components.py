from ..inputTypes import instace


def main_solver_component(**kwargs):
    return f"""
## Solver
<|Solve|button|on_action=on_button_click|>  
{instance_info_component(kwargs.get("inst"))}
### Result
<|{{solution_result.objective_value if solution_result else "No solution available."}}|text|>
"""


def instance_info_component(inst: instace.Instance | None = None):
    if inst is None:
        return "no instance loaded."
    return f"""
## Instance Info
- number of shift typs: {len(inst.shift_types)}
- number of employees: {len(inst.employees)}

"""
