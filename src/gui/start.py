from pathlib import Path

import streamlit as st

from .. import shift_vars, solution, solver
from ..parseData import parseTXT


def get_solution() -> solution.Solution:
    test_file = Path.joinpath(
        Path(__file__).resolve().parent.parent.parent, "data", "Instance1.txt"
    )
    inst = parseTXT.parse_txt(test_file)
    sol = solver.Solver(inst, shift_vars.Shift_vars(inst))
    return sol.solve()


def start_gui():
    # Page configuration
    st.set_page_config(page_title="Algorithm Lab", page_icon="🔬", layout="wide")

    # Navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Gehe zu:", ["Instance", "Solver", "Solution"])

    # Import and display selected page
    if page == "Instance":
        from .pages import instance_page

        instance_page.show()
    elif page == "Solver":
        from .pages import solver_page

        solver_page.show()
    elif page == "Solution":
        from .pages import solution_page

        solution_page.show()


if __name__ == "__main__":
    start_gui()
