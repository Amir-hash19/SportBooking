import uuid
import secrets
from datetime import datetime, timezone, timedelta

from django.core.exceptions import ValidationError
from django.db import models

from backend.apps.accounts.models import UserAccount
from backend.apps.venues.models import Pitch




class Booking(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("cancelled", "Cancelled"),
        ("expired", "Expired"),
    ]

    user = models.ForeignKey(UserAccount, on_delete=models.CASCADE, related_name="bookings")
    pitch = models.ForeignKey(Pitch, on_delete=models.CASCADE, related_name="bookings")

    booking_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    total_price = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending", db_index=True)
    tracking_code = models.CharField(max_length=50, unique=True, blank=True)
    expires_at = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "bookings"
        indexes = [
            models.Index(fields=["pitch", "booking_date"]),
            models.Index(fields=["user", "status"]),
            models.Index(fields=["expires_at"]), 
        ]

        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                condition=models.Q(status="pending"),
                name="unique_pending_booking_per_user",
            )
        ]    


    def calculate_total_price(self):
        start = datetime.combine(self.booking_date, self.start_time)
        end = datetime.combine(self.booking_date, self.end_time)
        duration = (end - start).total_seconds() / 3600

        is_weekend = self.booking_date.weekday() in [4, 5]
        hourly_price = (
            self.pitch.weekend_price
            if is_weekend and self.pitch.weekend_price
            else self.pitch.price_per_hour
        )
        return hourly_price * duration    



    def save(self, *args, **kwargs):
        if not self.tracking_code:
            self.tracking_code = uuid.uuid4().hex[:10].upper()
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=10)
        if not self.total_price:
            self.total_price = self.calculate_total_price()
            
        super().save(*args, **kwargs)



class Payment(models.Model):
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name="payment")
    amount = models.DecimalField(max_digits=10, decimal_places=0)
    status = models.CharField(
        max_length=20,
        choices=[("pending", "Pending"), ("success", "Success"), ("failed", "Failed")],
        default="pending"
    )
    transaction_id = models.CharField(max_length=100, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "payments"