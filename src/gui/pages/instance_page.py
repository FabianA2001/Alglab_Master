import re
from pathlib import Path

import streamlit as st

from ...parseData import parseTXT

from ...inputTypes import employee, instace, shiftType

from ..modifiers import instance_modifier

from datetime import datetime

DATA_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent / "data" / "instance_raw"
)
DEFAULT_PATH = DATA_DIR / "Instance1.txt"


def natural_sort_key(filename):
    """Erstellt einen Sortierschlüssel für natürliche Sortierung von Dateinamen"""
    return [
        int(text) if text.isdigit() else text.lower()
        for text in re.split(r"(\d+)", filename)
    ]


def get_instance_files():
    """Holt alle .txt Dateien aus dem data Ordner"""
    if DATA_DIR.exists():
        txt_files = list(DATA_DIR.glob("*.txt"))
        return sorted([f.name for f in txt_files], key=natural_sort_key)
    return []


def show_instance_information(instance):
    """
    Zeigt detaillierte Informationen über eine geladene Instanz an.

    Args:
        instance: Die Instanz, deren Informationen angezeigt werden sollen
    """
    if instance is None:
        st.info("Keine Instanz zum Anzeigen vorhanden.")
        return

    st.header("📊 Instance Details")

    # Grundlegende Informationen
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Name", instance.name)
    with col2:
        st.metric("Anzahl Tage", instance.number_of_days)
    with col3:
        st.metric("Wochenenden", len(instance.weekend_days))

    # Shift Types
    st.subheader("🔄 Schichttypen")
    if instance.shift_types:
        shift_data = []
        for shift_type in instance.shift_types.values():
            # Namen der gesperrten Schichten ermitteln
            blocked_names = []
            if shift_type.blocked_shifts_after:
                for blocked_uid in shift_type.blocked_shifts_after:
                    blocked_shift = instance.shift_types.get(blocked_uid)
                    if blocked_shift:
                        blocked_names.append(blocked_shift.name)
                    else:
                        blocked_names.append(f"UID ...{str(blocked_uid)[-4:]}")

            shift_data.append(
                {
                    "Name": shift_type.name,
                    "UID": f"...{str(shift_type.uid)[-4:]}",
                    "Startzeit": shift_type.start_time.strftime("%H:%M"),
                    "Dauer (Min)": shift_type.length,
                    "Gesperrt nach": ", ".join(blocked_names)
                    if blocked_names
                    else "Keine",
                }
            )
        st.dataframe(shift_data, hide_index=True)
        shift_df = st.data_editor(shift_data, hide_index=True, key="shift_data_editor")
        if st.button("Change shifts types"):
            shift_types_dict: dict[shiftType.TypeUid, shiftType.ShiftType] = {}
            for shift_dict in shift_df:
                print(shift_dict)
                hour = shift_dict["Startzeit"].split(":")[0]
                minute = shift_dict["Startzeit"].split(":")[1]
                forbidden = shift_dict["Gesperrt nach"].split(", ")
                blocked_shifts_after = set()
                if not (forbidden == ["Keine"]):
                    for fs in forbidden:
                        blocked_shifts_after.add(hash(int(fs)))
                shift_types_dict[hash(shift_dict["Name"])] = shiftType.ShiftType(
                    # TODO add case where a new shift type is added
                    # uid=hash(shift_dict["Name"])
                    uid=hash(shift_dict["Name"]),
                    length=shift_dict["Dauer (Min)"],
                    blocked_shifts_after=blocked_shifts_after,
                    start_time=datetime(2005, 1, 1, int(hour), int(minute)),
                    name=shift_dict["Name"],
                )
            st.session_state["instance"] = instance_modifier.create_new_instance(
                instance=st.session_state["instance"],
                shift_types=shift_types_dict,
                name="test_instance_shifts_types",
            )
            updated_shift_data = shift_df
            st.write("Updated Shift Data:", updated_shift_data)
            print(
                "instance in show instance information: \n",
                st.session_state["instance"].shift_types,
            )
            st.session_state["instance_modified"] = True

    else:
        st.info("Keine Schichttypen definiert.")

    # Employees
    st.subheader("👥 Mitarbeiter")
    if instance.employees:
        emp_data = []
        for emp in instance.employees.values():
            emp_data.append(
                {
                    "Name": emp.name,
                    "UID": f"...{str(emp.uid)[-4:]}",
                    "Max Schichten": sum(emp.max_numbers_of_shifts.values())
                    if emp.max_numbers_of_shifts
                    else 0,
                    "Min Minuten": emp.min_minutes_assigned,
                    "Max Minuten": emp.max_minutes_assigned
                    if emp.max_minutes_assigned < 1000000
                    else "∞",
                    "Max aufeinander": emp.max_number_consecutive_shifts
                    if emp.max_number_consecutive_shifts < 1000000
                    else "∞",
                    "Min aufeinander": emp.min_number_consecutive_shifts,
                    "Min Tage frei": emp.min_number_consecutive_days_off,
                    "Max Wochenenden": emp.max_number_weekends
                    if emp.max_number_weekends < 1000000
                    else "∞",
                    "Gesperrte Tage": emp.blocked_shifts,
                }
            )
        st.dataframe(emp_data, hide_index=True)
        emp_data = st.data_editor(emp_data, hide_index=True, key="employee_data_editor")
        if st.button("Change employees content"):
            employee_types_dict: dict[employee.EmployeeUid, employee.Employee] = {}
            for emp_dict in emp_data:
                employee_instance = employee.Employee(
                    uid=hash(
                        emp_dict["Name"]
                    ),  # Make sure you use the correct attribute here
                    name=emp_dict["Name"],
                    blocked_shifts=emp_dict["Gesperrte Tage"],
                    # TODO make it possible to changge max number of shifts per type
                    max_numbers_of_shifts=instance.employees[
                        hash(emp_dict["Name"])
                    ].max_numbers_of_shifts,  # Assuming this is a dictionary of shift types
                    min_minutes_assigned=emp_dict["Min Minuten"],
                    max_minutes_assigned=(
                        emp_dict["Max Minuten"]
                        if emp_dict["Max Minuten"] != "∞"
                        else 1000000
                    ),
                    min_number_consecutive_shifts=emp_dict["Min aufeinander"],
                    max_number_consecutive_shifts=(
                        emp_dict["Max aufeinander"]
                        if emp_dict["Max aufeinander"] != "∞"
                        else 1000000
                    ),
                    min_number_consecutive_days_off=emp_dict["Min Tage frei"],
                    max_number_weekends=(
                        emp_dict["Max Wochenenden"]
                        if emp_dict["Max Wochenenden"] != "∞"
                        else 1000000
                    ),
                )
                employee_types_dict[hash(emp_dict["Name"])] = employee_instance
                st.session_state["instance"] = instance_modifier.create_new_instance(
                    instance=st.session_state["instance"],
                    employees=employee_types_dict,
                    name="test_instance_employee",
                )
                st.write("Updated Shift Data:", emp_data)
                print(
                    "instance in show instance information: \n",
                    st.session_state["instance"].employees,
                )
                st.session_state["instance_modified"] = True
    else:
        st.info("Keine Mitarbeiter definiert.")

    # Wochenenden Details
    if instance.weekend_days:
        st.subheader("📅 Wochenenden (Samstage)")
        weekend_cols = st.columns(min(len(instance.weekend_days), 5))
        for idx, weekend_day in enumerate(sorted(instance.weekend_days)):
            with weekend_cols[idx % 5]:
                st.info(f"Tag {weekend_day}")

    # Erweiterte Mitarbeiter-Details (ausklappbar)
    with st.expander("📋 Detaillierte Mitarbeiter-Informationen"):
        for emp in instance.employees.values():
            st.markdown(f"**{emp.name}** (UID: ...{str(emp.uid)[-4:]})")

            col1, col2 = st.columns(2)
            with col1:
                st.write("**Schichtbeschränkungen:**")
                if emp.max_numbers_of_shifts:
                    for (
                        shift_type_uid,
                        max_count,
                    ) in emp.max_numbers_of_shifts.items():
                        shift_type = instance.shift_types.get(shift_type_uid)
                        shift_name = (
                            shift_type.name
                            if shift_type
                            else f"UID ...{str(shift_type_uid)[-4:]}"
                        )
                        st.write(f"- {shift_name}: max {max_count}")
                else:
                    st.write("Keine spezifischen Beschränkungen")

                if emp.blocked_shifts:
                    st.write(
                        f"**Gesperrte Tage:** {', '.join(map(str, sorted(emp.blocked_shifts)))}"
                    )

            with col2:
                st.write("**Zeitbeschränkungen:**")
                st.write(f"- Min. Minuten: {emp.min_minutes_assigned}")
                max_min = (
                    emp.max_minutes_assigned
                    if emp.max_minutes_assigned < 1000000
                    else "Unbegrenzt"
                )
                st.write(f"- Max. Minuten: {max_min}")
                st.write(
                    f"- Min. aufeinanderfolgende Schichten: {emp.min_number_consecutive_shifts}"
                )
                max_cons = (
                    emp.max_number_consecutive_shifts
                    if emp.max_number_consecutive_shifts < 1000000
                    else "Unbegrenzt"
                )
                st.write(f"- Max. aufeinanderfolgende Schichten: {max_cons}")
                st.write(
                    f"- Min. aufeinanderfolgende freie Tage: {emp.min_number_consecutive_days_off}"
                )
                max_we = (
                    emp.max_number_weekends
                    if emp.max_number_weekends < 1000000
                    else "Unbegrenzt"
                )
                st.write(f"- Max. Wochenenden: {max_we}")

            st.divider()

    # Schicht-Details (ausklappbar)
    with st.expander("📆 Schicht-Details und Präferenzen"):
        day_options = list(range(instance.number_of_days))
        selected_day = st.selectbox(
            "Tag auswählen", day_options, format_func=lambda x: f"Tag {x}"
        )

        if selected_day in instance.shifts:
            for shift_type_uid, shift in instance.shifts[selected_day].items():
                shift_type = instance.shift_types.get(shift_type_uid)
                shift_type_name = (
                    shift_type.name
                    if shift_type
                    else f"UID ...{str(shift_type_uid)[-4:]}"
                )

                st.markdown(
                    f"**{shift_type_name}** {'🌙 (Wochenende)' if shift.is_weekend else ''}"
                )

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write("**Bevorzugte Besetzung:**")
                    st.write(f"Anzahl: {shift.preffert_number_employees}")
                    st.write(f"Strafe unter: {shift.weight_below_preferred}")
                    st.write(f"Strafe über: {shift.weight_above_preferred}")

                with col2:
                    st.write("**Zuweisungswünsche (ON):**")
                    if shift.penalty_assigned_day_employee:
                        for (
                            emp_uid,
                            penalty,
                        ) in shift.penalty_assigned_day_employee.items():
                            emp = instance.employees.get(emp_uid)
                            emp_name = (
                                emp.name if emp else f"UID ...{str(emp_uid)[-4:]}"
                            )
                            st.write(f"- {emp_name}: Gewicht {penalty}")
                    else:
                        st.write("Keine")

                with col3:
                    st.write("**Ablehnungswünsche (OFF):**")
                    if shift.penalty_not_assigned_day_employee:
                        for (
                            emp_uid,
                            penalty,
                        ) in shift.penalty_not_assigned_day_employee.items():
                            emp = instance.employees.get(emp_uid)
                            emp_name = (
                                emp.name if emp else f"UID ...{str(emp_uid)[-4:]}"
                            )
                            st.write(f"- {emp_name}: Gewicht {penalty}")
                    else:
                        st.write("Keine")

                st.divider()


def show_select_instance():
    # Dropdown für Dateien aus dem data Ordner
    instance_files = get_instance_files()

    if instance_files:
        # Standardauswahl auf Instance1.txt setzen, falls vorhanden
        default_index = 0
        if "Instance1.txt" in instance_files:
            default_index = instance_files.index("Instance1.txt")

        selected_file = st.selectbox(
            "Wähle eine Instance aus dem data Ordner",
            instance_files,
            index=default_index,
        )

        path = DATA_DIR / selected_file
        if path.exists():
            inst = parseTXT.parse_txt(path)
            st.session_state["instance"] = inst
            st.success(f"Datei geladen: {selected_file}")
        else:
            st.error("Datei nicht gefunden.")
    else:
        st.error("Keine Instanz-Dateien im data Ordner gefunden.")


def show():
    st.title("📁 Instance")
    st.write("Lade und zeige Instanzdaten an.")

    show_select = True
    if "solution" in st.session_state and st.session_state["solution"] is not None:
        st.warning(
            "Der Solver hat bereits eine Lösung gefunden. Bitte starte die Anwendung neu, um den Solver erneut zu verwenden."
        )
        show_select = False

    if st.session_state["solver_running"]:
        st.warning(
            "Die Instanz kann nicht geändert werden, da der Solver bereits gestartet wurde."
        )
        show_select = False

    if show_select and "instance_modified" not in st.session_state:
        show_select_instance()
        print("in get instance from files\n")

    # Zeige die geladene Instanz an
    if "instance" in st.session_state and st.session_state["instance"] is not None:
        print("instance in show: \n")
        print(st.session_state["instance"].shift_types)
        show_instance_information(st.session_state["instance"])
    else:
        st.info("Bitte lade zuerst eine Instanz.")
