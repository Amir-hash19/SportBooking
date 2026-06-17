from .models import PitchSchedule


def check_schedule_overlap(pitch, day, start, end, exclude_id=None):
    qs = PitchSchedule.objects.filter(
        pitch=pitch,
        day_of_week=day,
        start_time__lt=end,
        end_time__gt=start
    )

    if exclude_id:
        qs = qs.exclude(id=exclude_id)

    return qs.exists()
    