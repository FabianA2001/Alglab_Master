export function setCoverageUnchangeable() {
    const checkboxes = document.querySelectorAll('input[type="checkbox"].cover-requirement-checkbox');
    checkboxes.forEach((checkbox) => {
        checkbox.disabled = true;
    });
}

export function removeChangeableEmployeeOptions() {
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
