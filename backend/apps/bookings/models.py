from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from datetime import timedelta, datetime
from backend.apps.accounts.models import UserAccount, Profile
from backend.apps.venues.models import Pitch, Venue, Image
from datetime import datetime, timedelta, timezone
import secrets


class Booking(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("cancelled", "Cancelled"),
        ("completed", "Completed"),
        ("rejected", "Rejected"),
    ]

    user = models.ForeignKey(
        to=UserAccount, on_delete=models.CASCADE, related_name="bookings"
    )
    pitch = models.ForeignKey(
        to=Pitch, on_delete=models.CASCADE, related_name="bookings"
    )

    booking_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    total_price = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    is_paid = models.BooleanField(default=False, db_index=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending", db_index=True
    )

    notes = models.TextField(blank=True, verbose_name="user_explanation")
    admin_notes = models.TextField(blank=True)

    tracking_code = models.CharField(max_length=50, unique=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    cancelled_at = models.DateTimeField(blank=True, null=True)
    confirmed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "bookings"
        ordering = ["-booking_date", "-start_time"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["pitch", "booking_date"]),
            models.Index(fields=["tracking_code"]),
            models.Index(fields=["booking_date", "start_time"]),
        ]
        permissions = [
            ("can_confirm_booking", "Can confirm booking"),
            ("can_cancel_any_booking", "Can cancel any booking"),
            ("can_view_all_bookings", "Can view all bookings"),
        ]

    def clean(self):
        """اعتبارسنجی رزرو"""
        if self.start_time >= self.end_time:
            raise ValidationError("زمان شروع باید قبل از زمان پایان باشد")

        if self.booking_date < timezone.now().date():
            raise ValidationError("نمیتوانید در گذشته رزرو کنید")

        overlapping_bookings = Booking.objects.filter(
            pitch=self.pitch,
            booking_date=self.booking_date,
            status__in=["pending", "confirmed"],
            start_time__lt=self.end_time,
            end_time__gt=self.start_time,
        ).exclude(id=self.id)

        if overlapping_bookings.exists():
            raise ValidationError("این زمان قبلاً رزرو شده است")

    def calculate_duration(self):
        """محاسبه مدت زمان به ساعت"""
        start = datetime.combine(self.booking_date, self.start_time)
        end = datetime.combine(self.booking_date, self.end_time)
        return (end - start).total_seconds() / 3600

    def calculate_total_price(self):
        """محاسبه خودکار قیمت بر اساس ساعت و قیمت زمین"""
        duration = self.calculate_duration()
        is_weekend = self.booking_date.weekday() in [4, 5]  # پنجشنبه و جمعه

        if is_weekend and self.pitch.weekend_price:
            hourly_price = self.pitch.weekend_price
        else:
            hourly_price = self.pitch.price_per_hour

        return hourly_price * duration

    def save(self, *args, **kwargs):

        if not self.tracking_code:
            import uuid

            self.tracking_code = uuid.uuid4().hex[:10].upper()

        if not self.total_price:
            self.total_price = self.calculate_total_price()

        if self.status == "confirmed" and not self.confirmed_at:
            self.confirmed_at = timezone.now()
        elif self.status == "cancelled" and not self.cancelled_at:
            self.cancelled_at = timezone.now()
        elif self.status != "confirmed":
            self.confirmed_at = None
        elif self.status != "cancelled":
            self.cancelled_at = None

        self.full_clean()

        super().save(*args, **kwargs)

    def __str__(self):
        user_name = self.user.get_full_name() or self.user.username
        pitch_name = self.pitch.name  # یا self.pitch.pitch_name
        return f"{user_name} - {pitch_name} - {self.booking_date}"


class Payment(models.Model):
    PAYMENT_STATUS = [
        ("pending", "Pending"),
        ("success", "Success"),
        ("failed", "Failed"),
        ("refunded", "Refunded"),
    ]

    booking = models.OneToOneField(
        Booking,
        on_delete=models.CASCADE,
        related_name="payment",
    )
    amount = models.DecimalField(max_digits=10, decimal_places=0)
    transaction_id = models.CharField(max_length=100, db_index=True, unique=True)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default="pending")
    payment_date = models.DateTimeField(auto_now_add=True)
    callback_data = models.JSONField(default=dict, blank=True)

    def clean(self):
        if self.amount != self.booking.total_price:
            raise ValidationError("The price should be queal to reservation")

    def mark_as_success(self, transaction_id=None):
        """
        Docstring for mark_as_success
        method helps to return True
        if payment was successful

        :param self: Description
        :param transaction_id: Description
        """
        self.status = "success"
        if transaction_id:
            self.transaction_id = transaction_id
        self.payment_date = timezone.now()
        self.save()
        self.booking.is_paid = True
        self.booking.save(update_fields=["is_paid"])

    def mark_as_failed(self, reason=None):
        """Mark as failed transaction"""
        self.status = "failed"
        if reason:
            self.callback_data["failure_reason"] = reason
        self.save()

    def save(self, *args, **kwargs):

        if self.pk:
            old_status = (
                Payment.objects.filter(pk=self.pk)
                .values_list("status", flat=True)
                .first()
            )
            if old_status == "success" and self.status != "success":
                raise ValidationError("Cannot change status of a successful payment!")

        self.full_clean()
        super().save(*args, **kwargs)

    def generate_local_transaction_id(self):

        timestamp = timezone.now().strftime("%Y%m%d%H%M%S")
        random_part = secrets.token_hex(4).upper()
        return f"PAY-{timestamp}-{random_part}"

    class Meta:
        db_table = "payments"
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["transaction_id"]),
            models.Index(fields=["-payment_date"]),
            models.Index(fields=["booking", "status"]),
        ]

    def __str__(self):
        return f"payment {self.amount} toman - {self.booking.tracking_code}"
