// Shift Plan Table JavaScript
(function() {
    'use strict';

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
        shiftPlanData.shift_types.forEach((shiftType, index) => {
            const tr = document.createElement('tr');
            
            // Shift type cell
            const tdShiftType = document.createElement('td');
            tdShiftType.textContent = shiftType;
            tdShiftType.style.fontWeight = 'bold';
            tr.appendChild(tdShiftType);

            // Day cells
            for (let day = 0; day < shiftPlanData.num_days; day++) {
                const td = document.createElement('td');
                const employees = shiftPlanData.data[index][day];
                
                if (employees && employees.length > 0) {
                    const employeeList = document.createElement('div');
                    employeeList.className = 'employee-list';
                    
                    employees.forEach(empName => {
                        const badge = document.createElement('span');
                        badge.className = 'employee-badge';
                        badge.textContent = empName;
                        
                        // Highlight if matches filter
                        if (filteredEmployee && empName.toLowerCase().includes(filteredEmployee.toLowerCase())) {
                            badge.style.backgroundColor = '#ffeb3b';
                            badge.style.color = '#000';
                            td.classList.add('highlight');
                        }
                        
                        employeeList.appendChild(badge);
                    });
                    
                    td.appendChild(employeeList);
                    totalAssignments += employees.length;
                } else {
                    td.textContent = '-';
                    td.className = 'empty-cell';
                }
                
                tr.appendChild(td);
            }

            tableBody.appendChild(tr);
        });

        // Update table info
        tableInfo.textContent = `Gesamt: ${shiftPlanData.shift_types.length} Schichttypen, ${shiftPlanData.num_days} Tage, ${totalAssignments} Zuweisungen`;
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
        
        // Setup search functionality
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            searchInput.addEventListener('input', function(e) {
                handleSearch(e, data);
            });
        }
    };
})();
