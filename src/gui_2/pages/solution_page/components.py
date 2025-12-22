"""UI-Komponenten für die Solution-Page."""

from nicegui import ui

from ....solution import Solution
from .employee_assigments import emplyee_Assigments


def render_basic_info(solution: Solution) -> None:
    """Rendert die grundlegenden Informationen einer Solution.

    Args:
        solution: Die anzuzeigende Solution
    """
    with ui.card().classes("w-full mb-4"):
        ui.label("Grundlegende Informationen").classes("text-xl font-bold mb-2")
        ui.label(f"Timestamp: {solution.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        ui.label(f"Objective Value: {solution.objective_value:.2f}")
        ui.label(f"Solve Time: {solution.solve_time:.2f}s")
        ui.label(f"Solve Status: {solution.solve_status}")

        if solution.disabled_constraints:
            ui.label(
                f"Deaktivierte Constraints: {', '.join(c.name for c in solution.disabled_constraints)}"
            )


def render_constraint_validation(solution: Solution) -> None:
    """Rendert die Constraint-Validierung mit Details.

    Args:
        solution: Die zu validierende Solution
    """
    with ui.card().classes("w-full mb-4"):
        ui.label("Constraint-Validierung").classes("text-xl font-bold mb-2")
        all_valid, results = solution.checkt_constraints

        status_color = "positive" if all_valid else "negative"
        status_text = (
            "Alle Constraints erfüllt ✓" if all_valid else "Constraints verletzt ✗"
        )
        ui.label(status_text).classes(f"text-{status_color} font-bold")

        # Details zu einzelnen Constraints
        with ui.expansion("Constraint Details", icon="info").classes("w-full"):
            for constraint_name, (is_valid, violations) in results.items():
                icon = "check_circle" if is_valid else "error"
                color = "green" if is_valid else "red"

                with ui.row().classes("items-center gap-2"):
                    ui.icon(icon).props(f"color={color}")
                    ui.label(
                        f"{constraint_name}: {'✓' if is_valid else f'✗ ({len(violations)} Verstöße)'}"
                    )

                if violations and len(violations) <= 10:
                    for violation in violations[:10]:
                        ui.label(f"  • {violation}").classes(
                            "text-sm text-gray-600 ml-8"
                        )
                elif violations:
                    ui.label(
                        f"  ... und {len(violations) - 10} weitere Verstöße"
                    ).classes("text-sm text-gray-600 ml-8")


def render_statistics(solution: Solution) -> None:
    """Rendert die Statistiken einer Solution.

    Args:
        solution: Die Solution mit den anzuzeigenden Statistiken
    """
    with ui.card().classes("w-full mb-4"):
        ui.label("Statistiken").classes("text-xl font-bold mb-2")

        # Shift Fulfillment
        with ui.expansion("Schicht-Erfüllung", icon="event").classes("w-full"):
            ui.label(f"Minimal: {solution.minimal_shift_fulfillment():.2%}")
            ui.label(f"Maximal: {solution.maximum_shift_fulfillment():.2%}")
            ui.label(f"Durchschnitt: {solution.average_shift_fulfillment():.2%}")

        # Positive Wishes
        with ui.expansion("Positive Wünsche", icon="thumb_up").classes("w-full"):
            ui.label(f"Minimal: {solution.minimal_employee_positive_wishes_met():.2%}")
            ui.label(f"Maximal: {solution.maximum_employee_positive_wishes_met():.2%}")
            ui.label(
                f"Durchschnitt: {solution.average_employee_positive_wishes_met():.2%}"
            )
            ui.label(f"Median: {solution.median_employee_positive_wishes_met():.2%}")

        # Negative Wishes
        with ui.expansion("Negative Wünsche", icon="thumb_down").classes("w-full"):
            ui.label(f"Minimal: {solution.minimal_employee_negative_wishes_met():.2%}")
            ui.label(f"Maximal: {solution.maximum_employee_negative_wishes_met():.2%}")
            ui.label(
                f"Durchschnitt: {solution.average_employee_negative_wishes_met():.2%}"
            )
            ui.label(f"Median: {solution.median_employee_negative_wishes_met():.2%}")

        ui.label(f"Gesamt erfüllte Wünsche: {solution.total_fulfilled_wishes()}")


def render_employee_assignments(solution: Solution) -> None:
    """Rendert die Mitarbeiter-Zuordnungen pro Tag.

    Args:
        solution: Die Solution mit den Zuordnungen
    """
    emplyee_Assigments(solution)
