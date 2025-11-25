// Shift Plan Table JavaScript
'use strict';
import { Streamlit} from "streamlit-component-lib"
// Verwende die Konfiguration (wird von außen geladen)
// Shift Plan Table Configuration
const CONFIG = {
    // Farben
    spacing: {
        cellPadding: '12px',
        badgeGap: '6px',
        badgePadding: '4px 8px',
        containerPadding: '20px',
        filterMarginBottom: '16px',
        infoMarginTop: '12px'
    },
    colors: {

        // Highlight Farben (für Suche)
        highlightBackground: '#fff9c4',
        highlightBadgeBackground: '#ffeb3b',
        highlightBadgeText: '#000000',
        
        // Differenz-Anzeige Farben
        differencePositiveColor: '#ff9800',  // Orange für zu viele Mitarbeiter
        differenceNegativeColor: '#f44336',  // Rot für zu wenige Mitarbeiter
        differencePerfectColor: '#4CAF50',   // Grün für perfekte Anzahl

    },

    // Text und Labels
    text: {
        infoTemplate: (shiftTypes, days, assignments) => 
            `Gesamt: ${shiftTypes} Schichttypen, ${days} Tage, ${assignments} Zuweisungen`
    },

};

let filteredEmployee = '';

export var dataDict = {"cover_weights": {}, "added_employees": {}, "removed_employees": {}};

function createHeaderColumn(shiftTypeInfo) {
    // Shift type cell with multi-line layout
        const tdShiftType = document.createElement('td');
        tdShiftType.className = 'row-cell';

        // Create container for the shift type info
        const shiftTypeContainer = document.createElement('div');

        // Name (bold)
        const nameDiv = document.createElement('div');
        nameDiv.textContent = shiftTypeInfo.name;
        nameDiv.className = 'shift-name';
        shiftTypeContainer.appendChild(nameDiv);

        // Start time
        const startDiv = document.createElement('div');
        startDiv.className = 'shift-time';
        startDiv.textContent = `Start: ${shiftTypeInfo.start_time}`;
        shiftTypeContainer.appendChild(startDiv);

        // End time
        const endDiv = document.createElement('div');
        endDiv.className = 'shift-time';
        endDiv.textContent = `Ende: ${shiftTypeInfo.end_time}`;
        shiftTypeContainer.appendChild(endDiv);

        tdShiftType.appendChild(shiftTypeContainer);
        return tdShiftType;
}

function createShiftFullness(cellData) {
    const diffDiv = document.createElement('div');
    diffDiv.className = 'diff-info';

    const diff = cellData.difference;
    if (diff > 0) {
        diffDiv.textContent = `+${diff} (${cellData.actual}/${cellData.preferred})`;
        diffDiv.style.color = CONFIG.colors?.differencePositiveColor || '#ff9800'; // Orange for a lot
    } else if (diff < 0) {
        diffDiv.textContent = `${diff} (${cellData.actual}/${cellData.preferred})`;
        diffDiv.style.color = CONFIG.colors?.differenceNegativeColor || '#f44336'; // Red for less then desired
    } else {
        diffDiv.textContent = `✓ (${cellData.actual}/${cellData.preferred})`;
        diffDiv.style.color = CONFIG.colors?.differencePerfectColor || '#4CAF50'; // Green for perfect
    }

    return diffDiv;
}

function createCoverModifications(shiftTypeInfo, cellData, day){
    // Create container for the upper part
    const cover_weight = document.createElement('div');
    cover_weight.className = 'cover-weight';

    // Unique identifiers using day and shiftType
    const checkboxId = `checkbox-${day}-${shiftTypeInfo.name}`;
    const textFieldId = `textfield-${day}-${shiftTypeInfo.name}`;

    // Create checkbox
    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.id = checkboxId;
    checkbox.className = 'cover-requirement-checkbox';

    // Create text field
    const textField = document.createElement('input');
    textField.type = 'number';
    textField.disabled = true;
    textField.style.width = '100%';
    textField.id = textFieldId;
    textField.className = 'cover-requirement-textfield';
    textField.value = cellData.weight;

    // Event listener for the checkbox
    checkbox.addEventListener('change', () => {
        textField.disabled = !checkbox.checked; // Enable/disable text field
    });

    // Append checkbox and text field to upper part
    cover_weight.appendChild(checkbox);
    cover_weight.appendChild(textField);
    
    checkbox.addEventListener('change', () => updateData(day, shiftTypeInfo.name));
    textField.addEventListener('input', () => {
        if (checkbox.checked) {
            dataDict["cover_weights"][day][shiftTypeInfo.name] = parseInt(textField.value) || 0;
        }
    });

    return cover_weight;
}

// Render the table with data
function renderTable(shiftPlanData, read_only) {
    if (!shiftPlanData) {
        console.error('No shift plan data available');
        return;
    }

    const headerRow = document.getElementById('headerRow');
    const tableBody = document.getElementById('tableBody');
    const tableInfo = document.getElementById('tableInfo');

    if (!headerRow || !tableBody || !tableInfo) {
        console.error('Table elements not found');
        return;
    }

    // Clear existing content
    headerRow.innerHTML = '';
    tableBody.innerHTML = '';

    // Create header row
    const thShiftType = document.createElement('th');
    thShiftType.textContent = 'Schichttyp';
    thShiftType.className = 'shift-type-header';
    headerRow.appendChild(thShiftType);

    // Add day headers
    for (let day = 0; day < shiftPlanData.num_days; day++) {
        const th = document.createElement('th');
        th.textContent = `Tag ${day}`;
        th.className = 'day-header';
        headerRow.appendChild(th);
    }

    // Create data rows
    let totalAssignments = 0;
    shiftPlanData.shift_types_info.forEach((shiftTypeInfo, index) => {
        // rows
        const tr = document.createElement('tr');

        // Add column header cell
        tr.appendChild(createHeaderColumn(shiftTypeInfo));

        // Day cells
        for (let day = 0; day < shiftPlanData.num_days; day++) {
            const td = document.createElement('td');
            td.className = 'row-cell';
            const cellData = shiftPlanData.data[index][day];

            // Day Shift Cell
            const cellContainer = document.createElement('div');
            cellContainer.className = 'cell-container';

            // Show how many people are working per shift
            if (cellData.preferred !== undefined) {

                // Add Cover weight modification capability
                cellContainer.appendChild(createCoverModifications(shiftTypeInfo, cellData, day));

                td.appendChild(createShiftFullness(cellData));

            }

            let employees = cellData.employees;
            const force_assigned_employees = cellData.force_assigned_employees;
            const banned_employees = cellData.banned_employees;
            //remove extra forced assigned (Constraint employee = 1) employees, so that we can add them at the end of this function as forced assigned
            employees = employees.filter(item => !force_assigned_employees.includes(item))
            employees.push(...banned_employees)

            
            // Create container for removed employees add it the end
            const removedEmployeeList = document.createElement('div');
            removedEmployeeList.className = 'employee-list removed-employee-list';
            const employeeList = document.createElement('div');
            employeeList.className = 'employee-list';

            // Create a new employee badge container for adding employees
            const addEmployeeContainer = document.createElement('div');
            addEmployeeContainer.className = 'employee-badge-container';

            // Create a button for adding employees to the current day and shift
            const addEmployeeButton = document.createElement('button');
            addEmployeeButton.textContent = 'Add Employee';
            addEmployeeButton.className = 'add-employee-button';
            // Event listener for the Add Employee button
            addEmployeeButton.addEventListener('click', () => {
                // Toggle visibility of the selection container
                selectionContainer.style.display = selectionContainer.style.display === 'none' ? 'block' : 'none';
            });

            // Create a dropdown for employee selection
            const selectionContainer = document.createElement('div');
            selectionContainer.className = 'employee-selection-container';
            selectionContainer.style.display = 'none'; // Initially hidden
            selectionContainer.style.position = 'absolute'; // Position it absolutely

            // Get remaining employees
            const employeeOptions = shiftPlanData.employee_names.filter(item => !employees.includes(item));

            employeeOptions.forEach(empName => {
                const option = document.createElement('div');
                option.className = 'employee-option';
                option.id = `employee-${empName}-option-day-${day}-shift-${shiftTypeInfo.name}`;
                option.textContent = empName;

                // Event listener to add the selected employee without removing functionality
                option.addEventListener('click', () => {
                    const badgeContainer = document.createElement('div');
                    badgeContainer.className = 'employee-badge-container';

                    const badge = document.createElement('span');
                    badge.className = 'added-employee-badge';
                    badge.textContent = empName;

                    const removeButton = document.createElement('span');
                    removeButton.innerHTML = '&times;';
                    removeButton.className = 'added-employee-remove-button';
                    addEmployee(option, empName, day, shiftTypeInfo.name)

                    // Event listener for removing employee
                    removeButton.addEventListener('click', () => {
                        removeEmployee(badgeContainer, empName, day, shiftTypeInfo.name);
                        option.style.display = 'block';
                    });

                    badgeContainer.appendChild(badge);
                    badgeContainer.appendChild(removeButton);
                    employeeList.appendChild(badgeContainer);
                    selectionContainer.style.display = 'none'; // Hide options after selection
                });

                selectionContainer.appendChild(option);
            });

            // Append elements to the badge container
            addEmployeeContainer.appendChild(addEmployeeButton);
            addEmployeeContainer.appendChild(selectionContainer);
            employeeList.appendChild(addEmployeeContainer);

            if (employees && employees.length > 0) {

                employees.forEach((empName, index) => {
                    const badgeContainer = document.createElement('div');
                    badgeContainer.className = 'employee-badge-container';

                    const badge = document.createElement('span');
                    badge.className = 'employee-badge';
                    badge.textContent = empName;
                    badge.id = `badge-${shiftTypeInfo.name}-${day}-${index}`;
                    
                    const removeButton = document.createElement('span');
                    removeButton.innerHTML = '&times;';
                    removeButton.id = `remove-employee-${empName}-day-${day}-shift-${shiftTypeInfo.name}-button`
                    removeButton.className = 'remove-employee-button';

                    // Event listener for removing employee
                    removeButton.addEventListener('click', () => {
                        moveToRemovedList(badgeContainer, removedEmployeeList, empName, day, shiftTypeInfo.name);
                    });

                    badgeContainer.appendChild(badge);
                    badgeContainer.appendChild(removeButton);
                    employeeList.appendChild(badgeContainer);
                });

                cellContainer.appendChild(employeeList);
                td.appendChild(cellContainer);
                totalAssignments += employees.length - banned_employees.length + force_assigned_employees.length;
            } else {
                // Füge einen Platzhalter für "Keine Mitarbeiter" hinzu
                const emptyDiv = document.createElement('div');
                emptyDiv.className = 'employee-list';
                emptyDiv.textContent = '-';
                cellContainer.appendChild(emptyDiv);
                td.appendChild(cellContainer);
            }
            // Removed employees list
            td.appendChild(removedEmployeeList);
            
            const submit_day_shift = document.createElement('button');
            submit_day_shift.textContent = 'Send day and shift';
            submit_day_shift.className = 'send-day-shift';

            // Event listener for removing employee
            submit_day_shift.addEventListener('click', () => {
                dataDict["change_day_shift"] = {}
                dataDict["change_day_shift"][day] = shiftTypeInfo.name;
                Streamlit.setComponentValue(dataDict);
                reset_dataDict();
            });

            td.appendChild(submit_day_shift)
            tr.appendChild(td);
            set_employees_options(force_assigned_employees, banned_employees, day, shiftTypeInfo.name, read_only);
        }

        tableBody.appendChild(tr);
    });
    // Set table info
    tableInfo.textContent = `Gesamt: ${shiftPlanData.shift_types_info.length} Schichttypen, ${shiftPlanData.num_days} Tage, ${totalAssignments} Zuweisungen`;
}

function handleSearch(event) {
    const filteredEmployee = event.target.value.trim(); // Trim whitespace

    let filteredBadges = document.querySelectorAll(".employee-badge");

    // If the input is empty, reset all badges and return
    if (filteredEmployee === "") {
        filteredBadges.forEach((element) => {
            element.parentElement.parentElement.className = "employee-list"; // Reset to default class
        });
        return; // Exit the function early
    }

    const searchTerms = filteredEmployee.split(" "); // Split input into search terms

    // Create a map to track whether each parent should be marked
    const parentMap = new Map();

    filteredBadges.forEach((element) => {
        const textContent = element.textContent.toLowerCase();
        const isMatch = searchTerms.some(term => textContent.includes(term.toLowerCase()));

        // Get the parent element
        const parentElement = element.parentElement.parentElement;

        // Track if this parent should be marked
        if (!parentMap.has(parentElement)) {
            parentMap.set(parentElement, false); // Initialize as not marked
        }

        if (isMatch) {
            parentMap.set(parentElement, true); // Mark this parent if a match is found
        }
    });

    // Apply classes based on the parentMap
    parentMap.forEach((shouldMark, parent) => {
        if (shouldMark) {
            parent.className = "marked employee-list"; // Mark if a match was found
        } else {
            parent.className = "employee-list"; // Reset if no matches were found
        }
    });
}

// Export initialization function
/**
 * 
 * @param {dictionary} data: A solution?
 */
export function initShiftPlanTable(data, read_only) {
    renderTable(data, read_only);

    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.placeholder = 'Nach Mitarbeiter suchen...';
        searchInput.addEventListener('input', function (e) {
            handleSearch(e, data, read_only);
        });
    }
};

// Function to update the dictionary based on checkbox and text field
function updateData(dayIndex, shiftType) {
    const checkbox = document.querySelector(`#checkbox-${dayIndex}-${shiftType}`);
    const textField = document.querySelector(`#textfield-${dayIndex}-${shiftType}`);

    if (checkbox.checked) {
        // Add entry if checkbox is checked
        dataDict["cover_weights"][dayIndex] = {}
        dataDict["cover_weights"][dayIndex][shiftType] = 150;
    } else {
        // Remove entry if checkbox is unchecked
        delete dataDict["cover_weights"][dayIndex][shiftType];
    }
}

function reset_cover_requirement_options() {
    // Select all checkboxes created for the shifts
    const checkboxes = document.querySelectorAll('input[type="checkbox"].cover-requirement-checkbox');
    const textfields = document.querySelectorAll('input[type="number"].cover-requirement-textfield');
    checkboxes.forEach((checkbox) => {
        checkbox.checked = false;
    });
    textfields.forEach((textfield) => {
        textfield.disabled = true;
    });
}

export function reset_dataDict() {
    dataDict = {"cover_weights": {}, "added_employees": {}, "removed_employees": {}};
    reset_cover_requirement_options();
}

export function reset_employees_options() {
    const added_employees = document.querySelectorAll('span.added-employee-remove-button');
    added_employees.forEach(el => el.click());
    const removed_employees = document.querySelectorAll('.re-add-employee-button');
    removed_employees.forEach(el => el.click());
}

function set_employees_options(force_assigned_employees, banned_employees, day, shift_type, read_only) {
    const observer = new MutationObserver(() => {
        let allFound = true;
        force_assigned_employees.forEach((empName) => {
            const element = document.getElementById(`employee-${empName}-option-day-${day}-shift-${shift_type}`); // Check by ID
            if (!element) {
                allFound = false;
            }
        });
        banned_employees.forEach((empName) => {
            const element = document.getElementById(`remove-employee-${empName}-day-${day}-shift-${shift_type}-button`); // Check by ID
            if (!element) {
                allFound = false;
            }
        });

        // Disconnect observer if all IDs are found
        if (allFound) {
            force_assigned_employees.forEach(empName => document.getElementById(`employee-${empName}-option-day-${day}-shift-${shift_type}`).click());
            banned_employees.forEach(empName => document.getElementById(`remove-employee-${empName}-day-${day}-shift-${shift_type}-button`).click());
            observer.disconnect();
            if (read_only) {
                remove_changable_employee_options();
            }
        }
    });

    // Start observing changes in the document body
    observer.observe(document.body, {
        childList: true, // Observe direct children
        subtree: true,   // Observe all descendants
    });
}

export function set_coverage_unchangable() {
    const checkboxes = document.querySelectorAll('input[type="checkbox"].cover-requirement-checkbox');
    checkboxes.forEach((checkbox) => {
        checkbox.disabled = true;
    });
}

export function remove_changable_employee_options() {
    const removed_employees = document.querySelectorAll('.remove-employee-button');
    removed_employees.forEach(el => el.remove());
    const add_employee_buttons = document.querySelectorAll('.add-employee-button');
    add_employee_buttons.forEach(el => el.remove());
    const send_day_shift_buttons = document.querySelectorAll('.send-day-shift');
    send_day_shift_buttons.forEach(el => el.remove());
    const added_employee_remove_buttons = document.querySelectorAll('.added-employee-remove-button');
    added_employee_remove_buttons.forEach(el => el.remove());
    const re_add_employee_button = document.querySelectorAll('.re-add-employee-button');
    re_add_employee_button.forEach(el => el.remove());
}


function moveToRemovedList(badge, removedEmployeeList, empName, day, shiftType) {
    if (!dataDict["removed_employees"][day]) {
        dataDict["removed_employees"][day] = {};
    }
    if (!dataDict["removed_employees"][day][shiftType]) {
        dataDict["removed_employees"][day][shiftType] = [];
    }
    dataDict["removed_employees"][day][shiftType].push(empName); // Add to removed employees list
    // Remove the badge from the middle part
    const parentList = badge.parentElement;
    const childBadge = badge
    badge.remove();

    // Create container for the removed employee badge
    const badgeContainer = document.createElement('div');
    badgeContainer.className = 'employee-badge-container';

    // Create a badge for removed employees
    const removedBadge = document.createElement('span');
    removedBadge.className = 'removed-employee-badge';
    removedBadge.textContent = empName;

    // Create a re-add button for removed employees
    const reAddButton = document.createElement('span');
    reAddButton.innerHTML = '&plus;'; // Use HTML entity for "+"
    reAddButton.id = `re-add-employee-button-${empName}-day-${day}-shift-${shiftType}`
    reAddButton.className = 're-add-employee-button';

    // Event listener for re-adding employee
    reAddButton.addEventListener('click', () => {
        reAddEmployee(removedBadge, childBadge, parentList, empName, day, shiftType);
    });

    // Append badge and button to the badge container
    badgeContainer.appendChild(removedBadge);
    badgeContainer.appendChild(reAddButton);

    // Append badge container to the removed employee list
    removedEmployeeList.appendChild(badgeContainer);
}

function reAddEmployee(removedBadge, childBadge, badgeParent, empName, day, shiftType) {
    // Remove from the removed employee list
    const badgeContainer = removedBadge.parentElement; // Get the existing badge container
    badgeContainer.remove(); // Remove the badge container from the removed list

    // Remove employee from dataDict
    if (dataDict["removed_employees"] && dataDict["removed_employees"][day] && dataDict["removed_employees"][day][shiftType]) {
        const removedIndex = dataDict["removed_employees"][day][shiftType].indexOf(empName);
        if (removedIndex > -1) {
            dataDict["removed_employees"][day][shiftType].splice(removedIndex, 1); // Remove from removed employees
        }
        // Check if the inner list is empty
        if (dataDict["removed_employees"][day][shiftType].length === 0) {
            delete dataDict["removed_employees"][day][shiftType]; // Remove the day entry
            
            // Check if all days are removed
            if (Object.keys(dataDict["removed_employees"][day]).length === 0) {
                delete dataDict["removed_employees"][day]; // Remove the day entirely if empty
            }
        }

    }
    // Append the existing badge container back to the original employee list
    badgeParent.appendChild(childBadge);
}


function addEmployee(option, empName, day, shiftType){
    if (!dataDict["added_employees"][day]) {
        dataDict["added_employees"][day] = {};
    }
    if (!dataDict["added_employees"][day][shiftType]) {
        dataDict["added_employees"][day][shiftType] = [];
    }
    dataDict["added_employees"][day][shiftType].push(empName); // Add to removed employees list
    option.style.display = 'none';
}

function removeEmployee(badgeContainer, empName, day, shiftType) {
    badgeContainer.remove();
        // Remove employee from dataDict
    if (dataDict["added_employees"] && dataDict["added_employees"][day] && dataDict["added_employees"][day][shiftType]) {
        const addedIndex = dataDict["added_employees"][day][shiftType].indexOf(empName);
        if (addedIndex > -1) {
            dataDict["added_employees"][day][shiftType].splice(addedIndex, 1); // Remove from added employees
        }
        // Check if the inner list is empty
        if (dataDict["added_employees"][day][shiftType].length === 0) {
            delete dataDict["added_employees"][day][shiftType]; // Remove the day entry
            
            // Check if all days are removed
            if (Object.keys(dataDict["added_employees"][day]).length === 0) {
                delete dataDict["added_employees"][day]; // Remove the day entirely if empty
            }
        }

    }
}