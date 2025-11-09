// Shift Plan Table JavaScript
'use strict';

// Verwende die Konfiguration (wird von außen geladen)
const CONFIG = window.SHIFT_PLAN_CONFIG || {};
console.log('CONFIG loaded in main script:', CONFIG);
console.log('Column widths:', CONFIG.columns);

let filteredEmployee = '';

/**
 * 
 */
export default function(){
// Shift Plan Table JavaScript
'use strict';

// Verwende die Konfiguration (wird von außen geladen)
const CONFIG = window.SHIFT_PLAN_CONFIG || {};
console.log('CONFIG loaded in main script:', CONFIG);
console.log('Column widths:', CONFIG.columns);

let filteredEmployee = '';
}
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
    thShiftType.textContent = CONFIG.text?.shiftTypeHeader || 'Schichttyp';
    thShiftType.className = 'shift-type-header';
    thShiftType.style.width = CONFIG.columns?.shiftTypeMinWidth || '150px';
    thShiftType.style.maxWidth = CONFIG.columns?.shiftTypeMinWidth || '150px';
    thShiftType.style.backgroundColor = CONFIG.colors?.shiftTypeHeaderBackground || '#4CAF50';
    thShiftType.style.color = CONFIG.colors?.shiftTypeHeaderText || '#ffffff';
    headerRow.appendChild(thShiftType);

    // Add day headers
    for (let day = 0; day < shiftPlanData.num_days; day++) {
        const th = document.createElement('th');
        th.textContent = `${CONFIG.text?.dayHeaderPrefix || 'Tag'} ${day}`;
        th.className = 'day-header';
        th.style.width = CONFIG.columns?.dayMinWidth || '200px';
        th.style.maxWidth = CONFIG.columns?.dayMinWidth || '200px';
        th.style.backgroundColor = CONFIG.colors?.headerBackground || '#f5f5f5';
        headerRow.appendChild(th);
    }

    // Create data rows
    let totalAssignments = 0;
    shiftPlanData.shift_types_info.forEach((shiftTypeInfo, index) => {
        const tr = document.createElement('tr');
        
        // Shift type cell with multi-line layout
        const tdShiftType = document.createElement('td');
        tdShiftType.style.width = CONFIG.columns?.shiftTypeMinWidth || '150px';
        tdShiftType.style.maxWidth = CONFIG.columns?.shiftTypeMinWidth || '150px';
        
        // Create container for the shift type info
        const shiftTypeContainer = document.createElement('div');
        
        // Name (bold)
        const nameDiv = document.createElement('div');
        nameDiv.textContent = shiftTypeInfo.name;
        nameDiv.className = 'shift-name';
        shiftTypeContainer.appendChild(nameDiv);
        
        // Start time
        const startDiv = document.createElement('div');
        startDiv.textContent = `Start: ${shiftTypeInfo.start_time}`;
        startDiv.style.fontSize = '0.9em';
        startDiv.style.color = '#555';
        shiftTypeContainer.appendChild(startDiv);
        
        // End time
        const endDiv = document.createElement('div');
        endDiv.textContent = `Ende: ${shiftTypeInfo.end_time}`;
        endDiv.style.fontSize = '0.9em';
        endDiv.style.color = '#555';
        shiftTypeContainer.appendChild(endDiv);
        
        tdShiftType.appendChild(shiftTypeContainer);
        tr.appendChild(tdShiftType);

        // Day cells
        for (let day = 0; day < shiftPlanData.num_days; day++) {
            const td = document.createElement('td');
            td.style.width = CONFIG.columns?.dayMinWidth || '200px';
            td.style.maxWidth = CONFIG.columns?.dayMinWidth || '200px';
            const cellData = shiftPlanData.data[index][day];
            
            // Erstelle Container für die Zelle
            const cellContainer = document.createElement('div');
            cellContainer.className = 'cell-container';
            
            // Zeige Differenz-Information an der Spitze
            if (cellData.preferred !== undefined) {
                const diffDiv = document.createElement('div');
                diffDiv.className = 'diff-info';
                diffDiv.style.fontSize = '0.85em';
                diffDiv.style.fontWeight = 'bold';
                
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
            }
            
            const employees = cellData.employees || cellData;
            
            if (employees && employees.length > 0) {
                const employeeList = document.createElement('div');
                employeeList.className = 'employee-list';
                
                employees.forEach(empName => {
                    const badge = document.createElement('span');
                    badge.className = 'employee-badge';
                    badge.textContent = empName;
                    badge.style.backgroundColor = CONFIG.colors?.employeeBadgeBackground || '#e3f2fd';
                    badge.style.color = CONFIG.colors?.employeeBadgeText || '#1976d2';
                    badge.style.padding = CONFIG.spacing?.badgePadding || '4px 8px';
                    badge.style.borderRadius = CONFIG.borderRadius?.badge || '4px';
                    badge.style.fontSize = CONFIG.fonts?.badgeFontSize || '0.85em';
                    
                    // Highlight if matches filter
                    const caseSensitive = CONFIG.behavior?.caseSensitiveSearch !== false;
                    const empNameCompare = caseSensitive ? empName : empName.toLowerCase();
                    const filterCompare = caseSensitive ? filteredEmployee : filteredEmployee.toLowerCase();
                    
                    if (filteredEmployee && empNameCompare.includes(filterCompare)) {
                        badge.style.backgroundColor = CONFIG.colors?.highlightBadgeBackground || '#ffeb3b';
                        badge.style.color = CONFIG.colors?.highlightBadgeText || '#000';
                        td.style.backgroundColor = CONFIG.colors?.highlightBackground || '#fff9c4';
                    }
                    
                    employeeList.appendChild(badge);
                });
                
                cellContainer.appendChild(employeeList);
                td.appendChild(cellContainer);
                totalAssignments += employees.length;
            } else {
                // Zeige auch bei leeren Zellen die Differenz an
                if (cellData.preferred !== undefined && cellData.preferred > 0) {
                    const diffDiv = document.createElement('div');
                    diffDiv.className = 'diff-info';
                    diffDiv.style.fontSize = '0.85em';
                    diffDiv.style.fontWeight = 'bold';
                    diffDiv.textContent = `${cellData.difference} (${cellData.actual}/${cellData.preferred})`;
                    diffDiv.style.color = CONFIG.colors?.differenceNegativeColor || '#f44336'; // Rot für fehlende Mitarbeiter
                    cellContainer.appendChild(diffDiv);
                    
                    // Füge einen Platzhalter für "Keine Mitarbeiter" hinzu
                    const emptyDiv = document.createElement('div');
                    emptyDiv.textContent = CONFIG.text?.emptyCell || '-';
                    emptyDiv.style.color = CONFIG.colors?.emptyCellText || '#999';
                    emptyDiv.style.fontStyle = 'italic';
                    cellContainer.appendChild(emptyDiv);
                    
                    td.appendChild(cellContainer);
                } else {
                    td.textContent = CONFIG.text?.emptyCell || '-';
                    td.style.color = CONFIG.colors?.emptyCellText || '#999';
                    td.style.fontStyle = 'italic';
                }
            }
            
            tr.appendChild(td);
        }

        tableBody.appendChild(tr);
    });

    // Update table info
    const numShiftTypes = shiftPlanData.shift_types_info ? shiftPlanData.shift_types_info.length : 0;
    
    if (CONFIG.text?.infoTemplate && typeof CONFIG.text.infoTemplate === 'function') {
        tableInfo.textContent = CONFIG.text.infoTemplate(
            numShiftTypes,
            shiftPlanData.num_days,
            totalAssignments
        );
    } else {
        tableInfo.textContent = `Gesamt: ${numShiftTypes} Schichttypen, ${shiftPlanData.num_days} Tage, ${totalAssignments} Zuweisungen`;
    }
    tableInfo.style.color = CONFIG.colors?.infoText || '#666';
    tableInfo.style.fontSize = CONFIG.fonts?.infoFontSize || '0.9em';
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
    // Setup search functionality if enabled
    if (CONFIG.behavior?.enableSearch !== false) {
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            // Set placeholder from config
            searchInput.placeholder = CONFIG.text?.searchPlaceholder || 'Nach Mitarbeiter suchen...';
            
            // Set styling from config
            if (CONFIG.spacing?.filterMarginBottom) {
                const filterContainer = searchInput.parentElement;
                if (filterContainer) {
                    filterContainer.style.marginBottom = CONFIG.spacing.filterMarginBottom;
                }
            }
            
            searchInput.addEventListener('input', function(e) {
                handleSearch(e, data);
            });
        }
    }
};
