from django.conf import settings
from django.db import models


class Notification(models.Model):
    """
    Stores in-app notifications for users.
    Supports filtering by type and read status.
    """
    class NotificationType(models.TextChoices):
        BOOKING_CREATED = "booking_created", "Booking Created"
        BOOKING_CONFIRMED = "booking_confirmed", "Booking Confirmed"
        BOOKING_CANCELLED = "booking_cancelled", "Booking Cancelled"
        PAYMENT_SUCCESS = "payment_success", "Payment Successful"
        SYSTEM_ALERT = "system_alert", "System Alert"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(
        max_length=30, choices=NotificationType.choices, db_index=True
    )
    link = models.CharField(max_length=500, blank=True)
    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notifications"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "is_read"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        return f"{self.title} - {self.user.username}"
