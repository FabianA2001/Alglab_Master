"""Display constraint activation status."""

import streamlit as st

from ...module.solverConstraints import SolverConstraints
from ...solution import Solution

# Mapping zwischen SolverConstraints Enum und den Constraint-Namen in der Validierung
CONSTRAINT_NAME_MAPPING = {
    SolverConstraints.cover_requirements: "Cover Requirements",
    SolverConstraints.days_off: "Days Off",
    SolverConstraints.limited_shifts_per_type_validation: "Limited Shifts per Type",
    SolverConstraints.max_Cons_Shifts: "Max Consecutive Shifts",
    SolverConstraints.max_weekend_days: "Max Weekend Days",
    SolverConstraints.minimum_consecutive_days_off: "Min Consecutive Days Off",
    SolverConstraints.minimum_consecutive_shifts: "Min Consecutive Shifts",
    SolverConstraints.minMaxWorkTime: "Min/Max Worktime",
    SolverConstraints.shift_assignment_single_day_validation: "Single Day Assignment",
    SolverConstraints.shift_rotation_constraint: "Shift Rotation",
    SolverConstraints.assign_employee_day_shift: "Assign Employees",
    SolverConstraints.ban_employee_day_shift: "Ban Employees",
}


def show_active_constraints(sol: Solution):
    """Zeigt an, welche Constraints beim Lösen aktiv waren."""
    st.write("### 🎯 Aktive Constraints")

    all_constraints = list(SolverConstraints)
    disabled_constraints = (
        sol.disabled_constraints if hasattr(sol, "disabled_constraints") else []
    )

    # Gruppiere Constraints in zwei Listen
    active = []
    inactive = []

    for constraint in all_constraints:
        constraint_name = CONSTRAINT_NAME_MAPPING.get(
            constraint, constraint.name.replace("_", " ")
        )
        if constraint in disabled_constraints:
            inactive.append(constraint_name)
        else:
            active.append(constraint_name)

    # Zeige aktive Constraints
    if active:
        st.write("**Aktive Constraints:**")
        cols = st.columns(2)
        for idx, constraint_name in enumerate(sorted(active)):
            with cols[idx % 2]:
                st.success(f"✅ {constraint_name}")

    # Zeige deaktivierte Constraints
    if inactive:
        st.write("**Deaktivierte Constraints:**")
        cols = st.columns(2)
        for idx, constraint_name in enumerate(sorted(inactive)):
            with cols[idx % 2]:
                st.warning(f"⚠️ {constraint_name}")

    if not inactive:
        st.info("ℹ️ Alle Constraints waren beim Lösen aktiv.")


def show_constraint_violations(sol: Solution):
    """Zeigt alle Constraint-Verletzungen auf der Streamlit-Seite an."""
    st.write("### 🔍 Constraint-Validierung")

    all_valid, constraints = sol.checkt_constraints

    for name, (is_valid, violations) in constraints.items():
        if is_valid:
            st.success(f"✅ **{name}**: Erfüllt")
        else:
            all_valid = False
            with st.expander(
                f"❌ **{name}**: {len(violations)} Verletzung(en)",
                expanded=True,
            ):
                for violation in violations:
                    st.write(f"- {violation}")

    if all_valid:
        st.success("Alle Constraints sind erfüllt!")
    else:
        st.warning("Es gibt Constraint-Verletzungen in dieser Lösung.")
