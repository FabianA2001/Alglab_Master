import streamlit as st


def show():
    st.title("✅ Solution")
    st.write("Zeige die berechnete Lösung an.")

    # Check if solution exists in session state
    if "solution" in st.session_state:
        solution = st.session_state["solution"]

        st.subheader("Lösung Details")

        # Display solution details
        st.write(solution)

        # Add visualization, tables, or export options here

    else:
        st.warning("Keine Lösung verfügbar. Bitte zuerst den Solver ausführen.")
        st.info("Gehe zur Solver-Seite um eine Lösung zu berechnen.")
