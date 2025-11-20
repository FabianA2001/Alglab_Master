#!/usr/bin/env python3
"""
Script zum Analysieren aller fertigen Solutions.
Zeigt für jede Solution an:
- Wie viel Prozent der Wünsche erfüllt werden
- Wie voll die Schichten prozentual sind
"""

import sys
from pathlib import Path

# Füge Alglab_Master zum Python Path hinzu
sys.path.insert(0, str(Path(__file__).parent))

from src.analyze_solutions import (
    analyze_all_solutions,
    print_analysis_summary,
    save_analysis_to_json,
)


if __name__ == "__main__":
    print("🔍 Analysiere alle Solutions...\n")

    # Alle Solutions analysieren
    results = analyze_all_solutions()

    if results:
        # Ergebnisse ausdrucken
        print_analysis_summary(results)

        # Als JSON speichern
        save_analysis_to_json(results)
    else:
        print("❌ Keine Solutions gefunden!")
