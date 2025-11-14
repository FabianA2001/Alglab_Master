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