from datetime import datetime, timedelta, time
from .models import PitchSchedule

def generate_slots(start_time, end_time, slot_minutes=30):
    slots = []

    current = datetime.combine(datetime.today(), start_time)
    end = datetime.combine(datetime.today(), end_time)

    delta = timedelta(minutes=slot_minutes)

    while current + delta <= end:
        slots.append({
            "start": current.time(),
            "end": (current + delta).time()
        })
        current += delta

    return slots




def get_pitch_slots(pitch, day_of_week, slot_minutes=30):
    schedules = PitchSchedule.objects.filter(
        pitch=pitch,
        day_of_week=day_of_week
    )

    all_slots = []

    for s in schedules:
        slots = generate_slots(
            s.start_time,
            s.end_time,
            slot_minutes
        )
        all_slots.extend(slots)

    return all_slots








def merge_time_ranges(schedules):
    """
    schedules: queryset of PitchSchedule
    return: list of (start_time, end_time) بدون overlap
    """

    intervals = sorted(
        [(s.start_time, s.end_time) for s in schedules],
        key=lambda x: x[0]
    )

    if not intervals:
        return []

    merged = [list(intervals[0])]

    for current_start, current_end in intervals[1:]:
        last_start, last_end = merged[-1]

        # overlap condition
        if current_start <= last_end:
            # merge
            merged[-1][1] = max(last_end, current_end)
        else:
            merged.append([current_start, current_end])

    return merged




WEEKDAY_MAP = {
    0: "monday", 1: "tuesday", 2: "wednesday",
    3: "thursday", 4: "friday", 5: "saturday", 6: "sunday",
}