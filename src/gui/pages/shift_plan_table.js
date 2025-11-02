// Shift Plan Table JavaScript
(function() {
    'use strict';

    // Verwende die Konfiguration (wird von außen geladen)
    const CONFIG = window.SHIFT_PLAN_CONFIG || {};
    console.log('CONFIG loaded in main script:', CONFIG);
    console.log('Column widths:', CONFIG.columns);

    let filteredEmployee = '';

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
        thShiftType.style.minWidth = CONFIG.columns?.shiftTypeMinWidth || '150px';
        thShiftType.style.backgroundColor = CONFIG.colors?.shiftTypeHeaderBackground || '#4CAF50';
        thShiftType.style.color = CONFIG.colors?.shiftTypeHeaderText || '#ffffff';
        headerRow.appendChild(thShiftType);

        // Add day headers
        for (let day = 0; day < shiftPlanData.num_days; day++) {
            const th = document.createElement('th');
            th.textContent = `${CONFIG.text?.dayHeaderPrefix || 'Tag'} ${day}`;
            th.className = 'day-header';
            th.style.minWidth = CONFIG.columns?.dayMinWidth || '200px';
            th.style.backgroundColor = CONFIG.colors?.headerBackground || '#f5f5f5';
            headerRow.appendChild(th);
        }

        // Create data rows
        let totalAssignments = 0;
        shiftPlanData.shift_types.forEach((shiftType, index) => {
            const tr = document.createElement('tr');
            
            // Shift type cell
            const tdShiftType = document.createElement('td');
            tdShiftType.textContent = shiftType;
            tdShiftType.style.fontWeight = 'bold';
            tdShiftType.style.minWidth = CONFIG.columns?.shiftTypeMinWidth || '150px';
            tr.appendChild(tdShiftType);

            // Day cells
            for (let day = 0; day < shiftPlanData.num_days; day++) {
                const td = document.createElement('td');
                td.style.minWidth = CONFIG.columns?.dayMinWidth || '200px';
                const employees = shiftPlanData.data[index][day];
                
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
                    
                    td.appendChild(employeeList);
                    totalAssignments += employees.length;
                } else {
                    td.textContent = CONFIG.text?.emptyCell || '-';
                    td.style.color = CONFIG.colors?.emptyCellText || '#999';
                    td.style.fontStyle = 'italic';
                }
                
                tr.appendChild(td);
            }

            tableBody.appendChild(tr);
        });

        // Update table info
        if (CONFIG.text?.infoTemplate && typeof CONFIG.text.infoTemplate === 'function') {
            tableInfo.textContent = CONFIG.text.infoTemplate(
                shiftPlanData.shift_types.length,
                shiftPlanData.num_days,
                totalAssignments
            );
        } else {
            tableInfo.textContent = `Gesamt: ${shiftPlanData.shift_types.length} Schichttypen, ${shiftPlanData.num_days} Tage, ${totalAssignments} Zuweisungen`;
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
    window.initShiftPlanTable = function(data) {
        console.log('Initializing shift plan table with data:', data);
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
})();
