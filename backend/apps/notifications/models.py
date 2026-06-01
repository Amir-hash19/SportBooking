from django.db import models
from django.conf import settings
from django.utils import timezone


class Notification(models.Model):
    class NotificationType(models.TextChoices):
        BOOKING_CREATED = "booking_created", "رزرو جدید"
        BOOKING_CONFIRMED = "booking_confirmed", "تایید رزرو"
        BOOKING_CANCELLED = "booking_cancelled", "لغو رزرو"
        PAYMENT_SUCCESS = "payment_success", "پرداخت موفق"
        SYSTEM_ALERT = "system_alert", "اخطار سیستمی"

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
