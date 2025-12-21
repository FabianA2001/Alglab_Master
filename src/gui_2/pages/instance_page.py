from pathlib import Path

from nicegui import ui

from ...parseData import parseTXT
from .. import state

# Constants
DATA_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent / "data" / "instance_raw"
)


# Helper Functions
def load_available_instances() -> list[str]:
    """Lädt alle verfügbaren Instance-Dateien aus dem DATA_DIR.

    Returns:
        list[str]: Sortierte Liste der Instance-Namen (mit Endung)
    """
    if not DATA_DIR.exists():
        return []

    txt_files = sorted([f.name for f in DATA_DIR.glob("*.txt")])
    return txt_files


# UI Component Functions
def render_instance_info() -> None:
    """Rendert Informationen über die aktuell geladene Instance."""
    with ui.card().classes("w-full mb-4"):
        ui.label("Aktuelle Instance").classes("text-xl font-bold mb-2")

        instance = state.get_instance()
        if instance is None:
            ui.label("Keine Instance geladen").classes("text-gray-500 italic")
            return

        # Grundlegende Informationen
        ui.label(f"Anzahl Schichttypen: {len(instance.shift_types)}")
        ui.label(f"Anzahl Mitarbeiter: {len(instance.employees)}")
        ui.label(f"Anzahl Tage: {instance.number_of_days}")


# Main Page Function
def instance_page():
    """Seite für Instance-Verwaltung und -Laden."""

    def load_instance(instance_name: str) -> None:
        """Lädt eine Instance und aktualisiert den globalen State.

        Args:
            instance_name: Name der zu ladenden Instance-Datei
        """
        try:
            instance_path = DATA_DIR / instance_name
            loaded_instance = parseTXT.parse_txt(instance_path)

            # Setze Instance im globalen State
            state.set_instance(loaded_instance)

            update_instance_display()
            ui.notify(
                f"Instance '{instance_name}' erfolgreich geladen", type="positive"
            )
        except Exception as e:
            ui.notify(f"Fehler beim Laden: {str(e)}", type="negative")

    def update_instance_display() -> None:
        """Aktualisiert die Anzeige der Instance-Details."""
        instance_container.clear()

        with instance_container:
            render_instance_info()

    # UI Layout
    with ui.card().classes("w-full mb-4"):
        ui.label("Instance Manager").classes("text-2xl font-bold mb-4")

        # Instance-Auswahl
        available_instances = load_available_instances()

        if not available_instances:
            ui.label("Keine Instances gefunden").classes("text-orange-500")
            ui.label(f"Pfad: {DATA_DIR}").classes("text-sm text-gray-500")
        else:
            ui.label(f"{len(available_instances)} Instances verfügbar").classes(
                "text-sm text-gray-600 mb-2"
            )

            with ui.row().classes("w-full gap-4 items-center"):
                instance_select = ui.select(
                    options=available_instances,
                    label="Instance auswählen",
                    on_change=lambda e: load_instance(e.value) if e.value else None,
                ).classes("flex-grow")

                ui.button(
                    "Neu laden",
                    icon="refresh",
                    on_click=lambda: [
                        instance_select.set_options(load_available_instances()),
                        ui.notify("Instances aktualisiert", type="info"),
                    ],
                ).props("flat")

    # Container für die Instance-Anzeige
    instance_container = ui.column().classes("w-full")

    # Zeige aktuelle Instance beim Laden der Seite
    if state.get_instance() is not None:
        update_instance_display()
