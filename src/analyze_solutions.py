"""
Analysiert fertige Solutions und berechnet:
- Wie viel Prozent der Wünsche erfüllt werden
- Wie voll die Schichten prozentual sind
"""

from pathlib import Path
from typing import Optional
import json
from .solution import Solution


def analyze_solution_quality(solution: Solution) -> dict:
    """
    Analysiert eine Solution bezüglich:
    - Erfüllter Wünsche (auf/ab Wünsche)
    - Schichtauslastung (% der preferred employees)

    Args:
        solution: Die zu analysierende Solution

    Returns:
        Dict mit Analyseergebnissen
    """
    instance = solution.instance
    vars_map = solution.vars

    # ===== WÜNSCHE ANALYSIEREN =====
    total_wishes = 0
    satisfied_wishes = 0
    wish_details = []

    for day, day_shift_dict in instance.shifts.items():
        for type_uid, shift in day_shift_dict.items():
            # Positive Wünsche: Mitarbeiter möchte an diesem Tag arbeiten
            for emp_uid, weight_pos in shift.penalty_assigned_day_employee.items():
                if weight_pos > 0:
                    total_wishes += 1
                    is_assigned = vars_map.get((day, type_uid, emp_uid), 0) == 1
                    if is_assigned:
                        satisfied_wishes += 1
                    wish_details.append(
                        {
                            "type": "on_request",
                            "day": day,
                            "shift_type": type_uid,
                            "employee": emp_uid,
                            "satisfied": is_assigned,
                            "weight": weight_pos,
                        }
                    )

            # Negative Wünsche: Mitarbeiter möchte NICHT an diesem Tag arbeiten
            for emp_uid, weight_neg in shift.penalty_not_assigned_day_employee.items():
                if weight_neg > 0:
                    total_wishes += 1
                    is_not_assigned = vars_map.get((day, type_uid, emp_uid), 0) == 0
                    if is_not_assigned:
                        satisfied_wishes += 1
                    wish_details.append(
                        {
                            "type": "off_request",
                            "day": day,
                            "shift_type": type_uid,
                            "employee": emp_uid,
                            "satisfied": is_not_assigned,
                            "weight": weight_neg,
                        }
                    )

    wish_satisfaction_rate = (
        (satisfied_wishes / total_wishes * 100) if total_wishes > 0 else 0
    )

    # ===== SCHICHTAUSLASTUNG ANALYSIEREN =====
    shift_utilization = []
    total_preferred = 0
    total_assigned = 0

    for day, day_shift_dict in instance.shifts.items():
        for type_uid, shift in day_shift_dict.items():
            preferred = shift.preffert_number_employees

            # Zähle wie viele Mitarbeiter dieser Schicht zugeordnet sind
            assigned = sum(
                1
                for (d, t, e), v in vars_map.items()
                if d == day and t == type_uid and v == 1
            )

            if preferred > 0:
                utilization_percent = (assigned / preferred) * 100
            else:
                utilization_percent = 0 if assigned == 0 else 100

            total_preferred += preferred
            total_assigned += assigned

            shift_utilization.append(
                {
                    "day": day,
                    "shift_type": type_uid,
                    "preferred": preferred,
                    "assigned": assigned,
                    "utilization_percent": utilization_percent,
                    "below_preferred": solution.below_prefferd_vars.get(
                        (day, type_uid), 0
                    ),
                    "above_preferred": solution.above_prefferd_vars.get(
                        (day, type_uid), 0
                    ),
                }
            )

    overall_utilization = (
        (total_assigned / total_preferred * 100) if total_preferred > 0 else 0
    )

    # ===== ZUSAMMENFASSUNG =====
    return {
        "instance_name": instance.name,
        "num_days": instance.number_of_days,
        "num_employees": len(instance.employees),
        "num_shift_types": len(instance.shift_types),
        # Wünsche
        "wishes": {
            "total_wishes": total_wishes,
            "satisfied_wishes": satisfied_wishes,
            "satisfaction_rate_percent": wish_satisfaction_rate,
            "satisfaction_rate": satisfied_wishes / total_wishes
            if total_wishes > 0
            else 0,
        },
        # Schichtauslastung
        "shifts": {
            "total_preferred": total_preferred,
            "total_assigned": total_assigned,
            "overall_utilization_percent": overall_utilization,
            "overall_utilization": total_assigned / total_preferred
            if total_preferred > 0
            else 0,
            "details": shift_utilization,
        },
        # Solver Info
        "objective_value": solution.objective_value,
        "solve_time": solution.solve_time,
        "solve_status": solution.solve_status,
    }


def analyze_all_solutions(solutions_dir: Optional[Path] = None) -> dict:
    """
    Analysiert alle fertigen Solutions aus dem solutions Verzeichnis.

    Args:
        solutions_dir: Pfad zum solutions Verzeichnis (Default: data/solutions)

    Returns:
        Dict mit Analysen für alle Solutions
    """
    if solutions_dir is None:
        solutions_dir = Path(__file__).resolve().parent.parent / "data" / "solutions"

    if not solutions_dir.exists():
        print(f"Solutions Verzeichnis nicht gefunden: {solutions_dir}")
        return {}

    results = {}
    json_files = list(solutions_dir.glob("*.json"))

    print(f"\nFinde {len(json_files)} Solution-Dateien in {solutions_dir}\n")

    for json_file in sorted(json_files):
        try:
            solution = Solution.from_json_file(json_file.stem)
            analysis = analyze_solution_quality(solution)
            results[json_file.stem] = analysis
            print(f"✓ Analysiert: {json_file.stem}")
        except Exception as e:
            print(f"✗ Fehler bei {json_file.stem}: {e}")

    return results


def print_analysis_summary(analysis_results: dict) -> None:
    """
    Gibt eine lesbare Zusammenfassung der Analysen aus.

    Args:
        analysis_results: Dict mit Analyseergebnissen von analyze_all_solutions()
    """
    if not analysis_results:
        print("Keine Analyseergebnisse vorhanden.")
        return

    print("\n" + "=" * 80)
    print("ANALYSE DER SOLUTIONS")
    print("=" * 80)

    for solution_name, analysis in sorted(analysis_results.items()):
        print(f"\n{'─' * 80}")
        print(f"📊 {solution_name}")
        print(f"{'─' * 80}")

        print(f"  Instance: {analysis['instance_name']}")
        print(
            f"  Größe: {analysis['num_days']} Tage, {analysis['num_employees']} Mitarbeiter, {analysis['num_shift_types']} Schichttypen"
        )

        print("\n  🎯 WÜNSCHE:")
        wishes = analysis["wishes"]
        print(f"    Gesamt: {wishes['total_wishes']} Wünsche")
        print(f"    Erfüllt: {wishes['satisfied_wishes']} Wünsche")
        print(f"    Quote: {wishes['satisfaction_rate_percent']:.1f}%")

        print("\n  📋 SCHICHTAUSLASTUNG:")
        shifts = analysis["shifts"]
        print(f"    Gewünscht: {shifts['total_preferred']} Mitarbeiter")
        print(f"    Zugeteilt: {shifts['total_assigned']} Mitarbeiter")
        print(f"    Auslastung: {shifts['overall_utilization_percent']:.1f}%")

        # Top 10 unterbelegte und überbelegte Schichten
        details = sorted(shifts["details"], key=lambda x: x["utilization_percent"])

        print("\n  📉 Unterbelegte Schichten (Top 5):")
        for item in details[:5]:
            if item["utilization_percent"] < 100:
                shift_name = f"Tag {item['day']}, Schicht {item['shift_type']}"
                print(
                    f"    {shift_name}: {item['assigned']}/{item['preferred']} ({item['utilization_percent']:.1f}%)"
                )

        print("\n  📈 Überbelegte Schichten (Top 5):")
        for item in reversed(details[-5:]):
            if item["utilization_percent"] > 100:
                shift_name = f"Tag {item['day']}, Schicht {item['shift_type']}"
                print(
                    f"    {shift_name}: {item['assigned']}/{item['preferred']} ({item['utilization_percent']:.1f}%)"
                )

        print("\n  ⏱️ Solver Info:")
        print(f"    Objective Value: {analysis['objective_value']}")
        print(f"    Solve Time: {analysis['solve_time']:.2f}s")
        print(f"    Solve Status: {analysis['solve_status']}")


def save_analysis_to_json(
    analysis_results: dict, output_path: Optional[Path] = None
) -> None:
    """
    Speichert die Analyseergebnisse als JSON-Datei.

    Args:
        analysis_results: Dict mit Analyseergebnissen
        output_path: Pfad zur Output-Datei (Default: analyses_summary.json)
    """
    if output_path is None:
        output_path = (
            Path(__file__).resolve().parent.parent / "data" / "analyses_summary.json"
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(analysis_results, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Analysen gespeichert in: {output_path}")


if __name__ == "__main__":
    # Alle Solutions analysieren
    results = analyze_all_solutions()

    # Ergebnisse ausdrucken
    print_analysis_summary(results)

    # Als JSON speichern
    save_analysis_to_json(results)
