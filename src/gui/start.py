from pathlib import Path

import streamlit as st

from .. import shift_vars, solution, solver
from ..parseData import parseTXT
from .pages import instance_page, overview_page, solution_page, solver_page


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

    if "solver_running" not in st.session_state:
        st.session_state["solver_running"] = False
    if "instance" not in st.session_state:
        inst = parseTXT.parse_txt(instance_page.DEFAULT_PATH)
        st.session_state["instance"] = inst

    # Navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Gehe zu:", ["Instance", "Solver", "Solution", "Overview"])

    # Import and display selected page
    if page == "Instance":
        instance_page.show()
    elif page == "Solver":
        solver_page.show()
    elif page == "Solution":
        solution_page.show()
    elif page == "Overview":
        overview_page.show()


if __name__ == "__main__":
    start_gui()
