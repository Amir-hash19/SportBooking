import random
import uuid
from datetime import datetime, timedelta, date as date_type
from time import time as time_type

from django.db import transaction
from django.utils import timezone

from backend.apps.bookings.models import Booking, Payment
from backend.apps.venues.models import PitchSchedule


DAY_MAP = {
    0: "monday",
    1: "tuesday",
    2: "wednesday",
    3: "thursday",
    4: "friday",
    5: "saturday",
    6: "sunday",
}


def merge_time_ranges(schedules):

    ranges = sorted(
        [(s.start_time, s.end_time) for s in schedules],
        key=lambda x: x[0],
    )

    merged = []
    for start, end in ranges:
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))

    return merged


def get_available_slots(pitch, booking_date, slot_minutes=60):
    day_name = DAY_MAP[booking_date.weekday()]

    schedules = PitchSchedule.objects.filter(
        pitch=pitch,
        day_of_week=day_name,
    )

    if not schedules.exists():
        return []

    merged_schedules = merge_time_ranges(schedules)

    booked_ranges = list(
        Booking.objects.filter(
            pitch=pitch,
            booking_date=booking_date,
            status__in=["pending", "confirmed"],
        ).values_list("start_time", "end_time")
    )

    slots = []
    for s_start, s_end in merged_schedules:
        current = datetime.combine(booking_date, s_start)
        end = datetime.combine(booking_date, s_end)

        while current + timedelta(minutes=slot_minutes) <= end:
            slot_start = current.time()
            slot_end = (current + timedelta(minutes=slot_minutes)).time()

            is_available = not any(
                slot_start < b_end and slot_end > b_start
                for b_start, b_end in booked_ranges
            )

            slots.append({
                "start": slot_start.strftime("%H:%M"),
                "end": slot_end.strftime("%H:%M"),
                "is_available": is_available,
            })

            current += timedelta(minutes=slot_minutes)

    return slots


def _validate_slot_in_schedule(pitch, booking_date, start_time, end_time):
    day_name = DAY_MAP[booking_date.weekday()]
    schedules = PitchSchedule.objects.filter(pitch=pitch, day_of_week=day_name)
    merged = merge_time_ranges(schedules)

    valid = any(
        s_start <= start_time and end_time <= s_end
        for s_start, s_end in merged
    )
    if not valid:
        raise ValueError("This slot did not find.")


def create_booking(user, pitch, booking_date, start_time, end_time):
    _validate_slot_in_schedule(pitch, booking_date, start_time, end_time)

    with transaction.atomic():
        conflicting = (
            Booking.objects.select_for_update()
            .filter(
                pitch=pitch,
                booking_date=booking_date,
                status__in=["pending", "confirmed"],
                start_time__lt=end_time,
                end_time__gt=start_time,
            )
        )

        if conflicting.exists():
            raise ValueError("the slot is already booked.")

        booking = Booking.objects.create(
            user=user,
            pitch=pitch,
            booking_date=booking_date,
            start_time=start_time,
            end_time=end_time,
        )
        return booking


def process_mock_payment(booking):
    with transaction.atomic():
        booking = Booking.objects.select_for_update().get(pk=booking.pk)

        if booking.status != "pending":
            raise ValueError("Only pending reservations is availabe to pay.")

        if timezone.now() > booking.expires_at:
            booking.status = "expired"
            booking.save(update_fields=["status"])
            raise ValueError("booking time is over.")

        success = True

        payment = Payment.objects.create(
            booking=booking,
            amount=booking.total_price,
            status="success" if success else "failed",
            transaction_id=uuid.uuid4().hex,
        )

        booking.status = "confirmed" if success else "cancelled"
        booking.save(update_fields=["status"])

        return payment