"""Main constraint checker module that coordinates all validation functions."""

from typing import Callable, List, Tuple

import streamlit as st

from ...solution import Solution
from .basic_constraints import (
    check_cover_requirements_constraint,
    check_days_off_constraint,
    check_shift_rotation_constraint,
    check_single_day_constraint,
)
from .shift_constraints import (
    check_lim_shifts_type_constraint,
    check_max_cons_shifts_constraint,
    check_min_cons_shifts_constraint,
    check_min_max_worktime_constraint,
)
from .weekend_constraints import (
    check_max_weekend_days_constraint,
    check_min_cons_days_constraint,
)


def get_all_constraint_checks() -> List[
    Tuple[str, Callable[[Solution], Tuple[bool, List[str]]]]
]:
    """Gibt eine Liste aller Constraint-Check-Funktionen zurück."""
    return [
        ("Cover Requirements", check_cover_requirements_constraint),
        ("Days Off", check_days_off_constraint),
        ("Limited Shifts per Type", check_lim_shifts_type_constraint),
        ("Max Consecutive Shifts", check_max_cons_shifts_constraint),
        ("Max Weekend Days", check_max_weekend_days_constraint),
        ("Min Consecutive Days Off", check_min_cons_days_constraint),
        ("Min Consecutive Shifts", check_min_cons_shifts_constraint),
        ("Min/Max Worktime", check_min_max_worktime_constraint),
        ("Single Day Assignment", check_single_day_constraint),
        ("Shift Rotation", check_shift_rotation_constraint),
    ]


def check_all_constraints(sol: Solution) -> Tuple[bool, dict]:
    """
    Prüft alle Constraints und gibt Ergebnisse zurück.

    Returns:
        Tuple[bool, dict]: (alle_erfüllt, {constraint_name: (is_valid, violations)})
    """
    constraints = get_all_constraint_checks()
    results = {}
    all_valid = True

    for constraint_name, check_func in constraints:
        is_valid, violations = check_func(sol)
        results[constraint_name] = (is_valid, violations)
        if not is_valid:
            all_valid = False

    return all_valid, results


def show_constraint_violations(sol: Solution):
    """Zeigt alle Constraint-Verletzungen auf der Streamlit-Seite an."""
    st.write("### 🔍 Constraint-Validierung")

    constraints = get_all_constraint_checks()
    all_valid = True

    for constraint_name, check_func in constraints:
        is_valid, violations = check_func(sol)

        if is_valid:
            st.success(f"✅ **{constraint_name}**: Erfüllt")
        else:
            all_valid = False
            with st.expander(
                f"❌ **{constraint_name}**: {len(violations)} Verletzung(en)",
                expanded=True,
            ):
                for violation in violations:
                    st.write(f"- {violation}")

    if all_valid:
        st.success("Alle Constraints sind erfüllt!")
    else:
        st.warning("Es gibt Constraint-Verletzungen in dieser Lösung.")
