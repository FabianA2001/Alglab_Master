// Shift Plan Table JavaScript
'use strict';

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

export var dataDict = {};

// Render the table with data
function renderTable(shiftPlanData) {
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
        const tr = document.createElement('tr');

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
        tr.appendChild(tdShiftType);

        // Day cells
        for (let day = 0; day < shiftPlanData.num_days; day++) {
            const td = document.createElement('td');
            td.className = 'row-cell';
            const cellData = shiftPlanData.data[index][day];

            // Erstelle Container für die Zelle
            const cellContainer = document.createElement('div');
            cellContainer.className = 'cell-container';

            // Zeige Differenz-Information an der Spitze
            if (cellData.preferred !== undefined) {
                const diffDiv = document.createElement('div');
                diffDiv.className = 'diff-info';

                const diff = cellData.difference;
                if (diff > 0) {
                    diffDiv.textContent = `+${diff} (${cellData.actual}/${cellData.preferred})`;
                    diffDiv.style.color = CONFIG.colors?.differencePositiveColor || '#ff9800'; // Orange für zu viele
                } else if (diff < 0) {
                    diffDiv.textContent = `${diff} (${cellData.actual}/${cellData.preferred})`;
                    diffDiv.style.color = CONFIG.colors?.differenceNegativeColor || '#f44336'; // Rot für zu wenige
                } else {
                    diffDiv.textContent = `✓ (${cellData.actual}/${cellData.preferred})`;
                    diffDiv.style.color = CONFIG.colors?.differencePerfectColor || '#4CAF50'; // Grün für perfekt
                }

                cellContainer.appendChild(diffDiv);

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

                // Positioning the upper part in the cell
                cellContainer.appendChild(cover_weight);

                td.appendChild(diffDiv);

                checkbox.addEventListener('change', () => updateData(day, shiftTypeInfo.name));
                textField.addEventListener('input', () => {
                    if (checkbox.checked) {
                        dataDict[day][shiftTypeInfo.name] = parseInt(textField.value) || 0;
                    }
                });
            }
            const employees = cellData.employees || cellData;
            
            // Create container for removed employees add it the end
            const removedEmployeeList = document.createElement('div');
            removedEmployeeList.className = 'removed-employee-list';

            if (employees && employees.length > 0) {
                const employeeList = document.createElement('div');
                employeeList.className = 'employee-list';

                employees.forEach((empName, index) => {
                    const badgeContainer = document.createElement('div');
                    badgeContainer.className = 'employee-badge-container';

                    const badge = document.createElement('span');
                    badge.className = 'employee-badge';
                    badge.textContent = empName;
                    badge.id = `badge-${shiftTypeInfo.name}-${day}-${index}`; // Unique ID for the badge
                    
                    const removeButton = document.createElement('span');
                    removeButton.innerHTML = '&times;';
                    removeButton.className = 'remove-employee-button';

                    // Event listener for removing employee
                    removeButton.addEventListener('click', () => {
                        moveToRemovedList(badgeContainer, empName, removedEmployeeList, day, shiftTypeInfo.name);
                    });

                    badgeContainer.appendChild(badge);
                    badgeContainer.appendChild(removeButton);
                    employeeList.appendChild(badgeContainer);
                });

                cellContainer.appendChild(employeeList);
                td.appendChild(cellContainer);
                totalAssignments += employees.length;
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

            tr.appendChild(td);
        }

        tableBody.appendChild(tr);
    });
    // Set table info
    tableInfo.textContent = `Gesamt: ${shiftPlanData.shift_types_info.length} Schichttypen, ${shiftPlanData.num_days} Tage, ${totalAssignments} Zuweisungen`;
}

// Handle search input
function handleSearch(event, shiftPlanData) {
    filteredEmployee = event.target.value;
    renderTable(shiftPlanData);
}

// Export initialization function
/**
 * 
 * @param {dictionary} data: A solution?
 */
export function initShiftPlanTable(data) {
    renderTable(data);

    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.placeholder = 'Nach Mitarbeiter suchen...';
        searchInput.addEventListener('input', function (e) {
            handleSearch(e, data);
        });
    }
};

// Function to update the dictionary based on checkbox and text field
function updateData(dayIndex, shiftType) {
    const checkbox = document.querySelector(`#checkbox-${dayIndex}-${shiftType}`);
    const textField = document.querySelector(`#textfield-${dayIndex}-${shiftType}`);

    if (checkbox.checked) {
        // Add entry if checkbox is checked
        dataDict[dayIndex] = {}
        dataDict[dayIndex][shiftType] = 1000;
    } else {
        // Remove entry if checkbox is unchecked
        delete dataDict[dayIndex][shiftType];
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
    dataDict = {};
    reset_cover_requirement_options();
}

export function set_coverage_unchangable() {
    const checkboxes = document.querySelectorAll('input[type="checkbox"].cover-requirement-checkbox');
    console.log("checkboxes")
    console.log(checkboxes)
    checkboxes.forEach((checkbox) => {
        checkbox.disabled = true;
    });
}


function moveToRemovedList(badge, empName, removedEmployeeList, day, shiftType) {
    // Add employee to dataDict as removed
    if (!dataDict["removed_employees"]) {
        dataDict["removed_employees"] = {};
    }
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
    reAddButton.className = 're-add-employee-button';

    // Event listener for re-adding employee
    reAddButton.addEventListener('click', () => {
        reAddEmployee(removedBadge, empName, childBadge, parentList, day, shiftType);
    });

    // Append badge and button to the badge container
    badgeContainer.appendChild(removedBadge);
    badgeContainer.appendChild(reAddButton);

    // Append badge container to the removed employee list
    removedEmployeeList.appendChild(badgeContainer);
    console.log(dataDict)
}

function reAddEmployee(removedBadge, empName, childBadge, badgeParent, day, shiftType) {
    // Remove from the removed employee list
    const badgeContainer = removedBadge.parentElement; // Get the existing badge container
    badgeContainer.remove(); // Remove the badge container from the removed list

    // Remove employee from dataDict
    if (dataDict["removed_employees"] && dataDict["removed_employees"][day] && dataDict["removed_employees"][day][shiftType]) {
        const removedIndex = dataDict["removed_employees"][day][shiftType].indexOf(empName);
        if (removedIndex > -1) {
            dataDict["removed_employees"][day][shiftType].splice(removedIndex, 1); // Remove from removed employees
        }
    }
    console.log(badgeParent)
    // Append the existing badge container back to the original employee list
    badgeParent.appendChild(childBadge);
    console.log(dataDict)
}