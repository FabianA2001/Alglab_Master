from pathlib import Path

from ..inputTypes import instace


def parse_txt(txt_file_path: Path) -> instace.Instance:
    with open(txt_file_path, "r") as file:
        lines = [line.strip() for line in file if line.strip() and not line.startswith("#")]
    
    horizon = 0
    shifts = {}
    staff = {}
    days_off = {}
    shift_on_requests = []
    shift_off_requests = []
    cover_requirements = []
    
    current_section = None
    
    for line in lines:
        if line.startswith("SECTION_"):
            current_section = line
            continue
        
        if current_section == "SECTION_HORIZON":
            horizon = int(line)
        
        elif current_section == "SECTION_SHIFTS":
            parts = line.split(",")
            shift_id = parts[0]
            length = int(parts[1])
            forbidden = parts[2].split("|") if parts[2] else []
            shifts[shift_id] = {"length": length, "forbidden_followers": forbidden}
        
        elif current_section == "SECTION_STAFF":
            parts = line.split(",")
            staff_id = parts[0]
            max_shifts = {}
            for shift_constraint in parts[1].split():
                if "=" in shift_constraint:
                    shift, count = shift_constraint.split("=")
                    max_shifts[shift] = int(count)
            staff[staff_id] = {
                "max_shifts": max_shifts,
                "max_total_minutes": int(parts[2]),
                "min_total_minutes": int(parts[3]),
                "max_consecutive_shifts": int(parts[4]),
                "min_consecutive_shifts": int(parts[5]),
                "min_consecutive_days_off": int(parts[6]),
                "max_weekends": int(parts[7])
            }
        
        elif current_section == "SECTION_DAYS_OFF":
            parts = line.split(",")
            employee_id = parts[0]
            day_indexes = [int(d) for d in parts[1:]]
            days_off[employee_id] = day_indexes
        
        elif current_section == "SECTION_SHIFT_ON_REQUESTS":
            parts = line.split(",")
            shift_on_requests.append({
                "employee_id": parts[0],
                "day": int(parts[1]),
                "shift_id": parts[2],
                "weight": int(parts[3])
            })
        
        elif current_section == "SECTION_SHIFT_OFF_REQUESTS":
            parts = line.split(",")
            shift_off_requests.append({
                "employee_id": parts[0],
                "day": int(parts[1]),
                "shift_id": parts[2],
                "weight": int(parts[3])
            })
        
        elif current_section == "SECTION_COVER":
            parts = line.split(",")
            cover_requirements.append({
                "day": int(parts[0]),
                "shift_id": parts[1],
                "requirement": int(parts[2]),
                "weight_under": int(parts[3]),
                "weight_over": int(parts[4])
            })
    
    return instace.Instance(
        horizon=horizon,
        shifts=shifts,
        staff=staff,
        days_off=days_off,
        shift_on_requests=shift_on_requests,
        shift_off_requests=shift_off_requests,
        cover_requirements=cover_requirements
    )
