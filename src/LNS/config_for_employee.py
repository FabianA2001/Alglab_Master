spacer = " " * 3


class Config_for_employee:
    max_consecutive_shifts_start: int = -1
    max_consecutive_shifts_end: int = -1
    min_consecutive_shifts_start: int = -1
    min_consecutive_shifts_end: int = -1
    min_consecutive_days_off_start: int = -1
    min_consecutive_days_off_end: int = -1

    def __str__(self) -> str:
        x = ""
        # f"\n{spacer}max_consecutive_shifts_start={self.max_consecutive_shifts_start}, "
        # f"\n{spacer}max_consecutive_shifts_end={self.max_consecutive_shifts_end}, "
        if self.min_consecutive_shifts_start > 0:
            x += f"\n{spacer}min_consecutive_shifts_start={self.min_consecutive_shifts_start}, "
        if self.min_consecutive_shifts_end > 0:
            x += f"\n{spacer}min_consecutive_shifts_end={self.min_consecutive_shifts_end}, "
        # f"\n{spacer}min_consecutive_days_off_start={self.min_consecutive_days_off_start}, "
        # f"\n{spacer}min_consecutive_days_off_end={self.min_consecutive_days_off_end}"
        return x
