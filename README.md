# Alglab Master

### Aufgabe
[Instances](https://www.schedulingbenchmarks.org/nrp/)

[Constraints](https://www.schedulingbenchmarks.org/nrp/instances1_24.html)

### Installation
`pip install -e ".[dev]"`

### Run
`main`

### Test
`pytest`

### Frontend
* Run the following commands in the folder [src/gui/pages/component_solution/my_component/frontend/](src/gui/pages/component_solution/my_component/frontend/): 
1. "npm install"
2. "npm start"
* In case of an error related to patch-package, please install it with pip using: "npm i patch-package" and repeat
* You need to have npm installed (possibly also nodejs)

### GUI
First run the frontend

`streamlit run run_gui.py`


### Branches

- Dev Branch
- Merge Main in Dev Branch
- Pull request
    - add description with important chanages
- Optional Copilot Review
- accapt diffrent Person

### Commit
- fix(class, file): fix a bug
- feat(class, file): add feature
- refactor(class,file): doesn't change logik
- remove: remove feature
- docs: add/edit comment
- type(class, file) [BROKEN]: Commit doesn't work
- type(class,file): small discription

### Benchmarks: Ergebnisse visualisieren

Das Projekt enthält ein Skript zum Erstellen von Diagrammen aus den Benchmark-Ergebnisdateien (JSON) in `benchmarks/`. Das Skript befindet sich in `benchmarks/visualize_results.py` und bietet mehrere Modi:

- Einzelne Ergebnisdatei visualisieren (erstellt Balken- und kumulatives Diagramm):

```bash
python -m benchmarks.visualize_results --input benchmarks/results_first/results_20251203_210153.json --output benchmarks/graphs
```

- Alle JSON-Dateien in einem Ordner verarbeiten (je File eigene Graphen):

```bash
python -m benchmarks.visualize_results --input benchmarks/results_first --all --output benchmarks/graphs
```

- Mehrere Läufe vergleichen (pro Instanz Balken nebeneinander):

```bash
python -m benchmarks.visualize_results --inputs \
    benchmarks/results_first/results_20251201_202044.json \
    benchmarks/results_first/results_20251201_202352.json \
    --compare --output benchmarks/graphs
```

- Ganzen Ordner vergleichen und zusätzlich eine gruppierte Gesamt-Ansicht erstellen (eine Grafik mit mehreren Balken pro Instanz):

```bash
python -m benchmarks.visualize_results --input benchmarks/results_first --all --compare --grouped --output benchmarks/graphs
```

- Anzeigen statt Speichern (öffnet die Plots interaktiv):

```bash
python -m benchmarks.visualize_results --input benchmarks/results_first/results_20251203_210153.json --show
```

Ausgabe:
- Standardmäßig werden PNG-Dateien unter `benchmarks/graphs/` abgelegt.
- Beim Vergleich mehrerer Läufe wird ein Unterordner `compare_<labels>/` angelegt; dort findest du für jede Instanz `compare_<InstanceName>.png` und (wenn `--grouped`) `grouped_compare.png`.

Hinweis: Falls viele Dateien verglichen werden, wird der Ordnername gekürzt/gehasht, um Probleme mit zu langen Pfaden zu vermeiden.