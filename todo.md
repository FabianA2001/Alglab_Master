
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

### Solver:
* Right now we set each alternative constraint manually, add the alternative constraints to the enum of solverConstraints, to do it automatically. (possibly only allow one constraint for each constraint type)

### Bugs:
- A problem happen when the solver doesn't get an optimal or a solution

https://d-krupke.github.io/cpsat-primer/test_driven_optimization.html#full-solver




lns: https://d-krupke.github.io/cpsat-primer/09_lns.html