from pathlib import Path

import pandas as pd
import streamlit as st

from ...solution import Solution


def show():
    """Zeigt eine Übersicht aller gespeicherten Solutions an."""

    st.title("📊 Solutions Übersicht")

    # Pfad zum Solutions-Verzeichnis
    solutions_dir = (
        Path(__file__).resolve().parent.parent.parent.parent / "data" / "solutions"
    )

    # Alle JSON-Dateien im Solutions-Verzeichnis finden
    json_files = list(solutions_dir.glob("*.json"))

    if not json_files:
        st.warning("⚠️ Keine Solutions gefunden im Verzeichnis: `data/solutions/`")
        return

    solution_names = [file.stem for file in json_files]
    # Liste für die Tabellendaten
    table_data = []

    # Jede Solution einlesen
    for solution_name in sorted(solution_names):
        try:
            # Solution laden
            sol = Solution.from_json_file(solution_name)

            # Daten zur Tabelle hinzufügen
            table_data.append(
                {
                    "Name": solution_name,
                    "Objective Value": f"{sol.objective_value:.2f}",
                    "Laufzeit (s)": f"{sol.solve_time:.3f}",
                    "Status": sol.solve_status,
                }
            )

        except Exception as e:
            st.error(f"❌ Fehler beim Laden von `{solution_name}`: {str(e)}")
            continue
    if table_data:
        # DataFrame erstellen
        df = pd.DataFrame(table_data)

        # Statistiken anzeigen
        st.metric("Anzahl Solutions", len(table_data))

        st.markdown("---")

        # Tabelle anzeigen mit erweiterten Optionen
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Name": st.column_config.TextColumn("Solution Name", width="medium"),
                "Objective Value": st.column_config.NumberColumn(
                    "Objective Value", width="small"
                ),
                "Laufzeit (s)": st.column_config.NumberColumn(
                    "Laufzeit (s)", width="small"
                ),
                "Status": st.column_config.NumberColumn("Solver Status", width="small"),
                "Timestamp": st.column_config.TextColumn("Erstellt am", width="medium"),
                "Tage": st.column_config.NumberColumn("Tage", width="small"),
                "Mitarbeiter": st.column_config.NumberColumn(
                    "Mitarbeiter", width="small"
                ),
            },
        )

        # Download-Option für CSV
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Tabelle als CSV herunterladen",
            data=csv,
            file_name="solutions_overview.csv",
            mime="text/csv",
        )
    else:
        st.error("❌ Keine Solutions konnten erfolgreich geladen werden.")
