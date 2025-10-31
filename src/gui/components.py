from ..inputTypes import instace


def solver_component(result_var="result"):
    return f"""
## Solver
<|Solve|button|on_action=on_button_click|>

### Result
<|{{{result_var}}}|text|>
"""

def instance_info_component(path, inst: instace.Instance):
    return f"""
## Instance Info
- Path: {path}
- number of shift typs: {len(inst.shift_types)}
- number of employees: {len(inst.employees)}

"""
