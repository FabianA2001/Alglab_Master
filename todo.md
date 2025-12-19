
### generelle Ziele

- website
- - upper / lower bound


- pre commit

- rename solution to report

- *matching*

- edit gui for solution edit:
    - rework
    - "send" in streamlit
    - penalty not assign, penalty assigned, and prefered number.

- Constraints 6 und 7

- lns
    - better slicing
    - seed random

- better objektiv funktion
    - soft 
    - hard maybe

- benchmark compare solver

- Give a variable to decide on the constraints variant to use (Basic/Automat/...)

### Solutions:
* add more comparison parameters for the benchmark, for example: 
    * Minimal, average, and maximal difference to the desired preferred employees per day.
    * Minimal and maximum and average of wishes fulfillment. (Differently for assigned and not assigned wishes)
* Compare the different constraints on all instances for both optimality and limited times and callback break early(although callback break early is possibly very inconsistent)


### Streamlit:
* Create a button that do not use the callback but only the timer.
* Create fields that can pass their content to the callback and other functions that can take parameters
* Create call out choices dialog

### Solver:
* Right now we set each alternative constraint manually, add the alternative constraints to the enum of solverConstraints, to do it automatically. (possibly only allow one constraint for each constraint type)
* In Callback_Early_Stop or another callback, create a ratio for each employee instead of wishes fulfillment over the all employees at the same time. (To avoid bias or prevent that the ratio is met through only the fulfillment of wishes of one employee) Maybe also another ratio of how many of employees have their ratio fulfilled. A problem that could occur with one employee wishes is that he/she have minimal consecutive days of 5 but all their wishes alternate one 5 days, this would cause the wishes to be hard to achieve, so one possibility is to have 40 percent of fulfillment. Or to check for these and not consider them in the ratio.
In the callback save the "best" solution until now. Maybe use the callback to save that instead of stopping (so use only time for stopping)


### Refactor ideas:
* Move store solution functions from both Callback_Top_Solutions and solver to the class solutions somehow.


### Bugs:
- A problem happen when the solver doesn't get an optimal or a solution

https://d-krupke.github.io/cpsat-primer/test_driven_optimization.html#full-solver




lns: https://d-krupke.github.io/cpsat-primer/09_lns.html


# 12.12:
* Greedy working for big instances (finding first solutions fast (less then 15 min)) (Ab instance 19)
* Fest Anzahl von Änderungen von einer Solution. (Oder mehrere lösung speichern, die verschidene Änderungensanzahl haben)
* Gültige lösung mit Greedy
## GUI:
* Zeigen von mehrere Lsungen
* (noch mehr ...)


# In Hinter kopf(ziehmlich weit):
* (Änderungen solver, die hard cosntraint für die Änderungensanzahl hat (dann lässt man, mehrere solver mit verschiedene Anzahl laufen))
* LNS über Instancen (Mehre Windows erstellen => lösen => mergen)

# 19.12:
* Mohammad:
    * solve the problem with the Model being kept when creating new solvers
    * improve the greedy CP method
    * if the Model problem is solved transform from subprocess to normal 
    * Refactor 
* Caro: 
    * LNS
* Fabian:
    * GUI 
