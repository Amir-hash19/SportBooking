from django.db import models
from backend.apps.accounts.models import UserAccount, Profile
from django.core.validators import MinValueValidator, MinLengthValidator
from django.core.exceptions import ValidationError


class Venue(models.Model):
    manager = models.ForeignKey(
        to=UserAccount,
        on_delete=models.CASCADE,
        related_name="managed_venues",
        verbose_name="manager of venue",
    )

    venue_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    address = models.TextField()
    phone = models.CharField(max_length=11, unique=True)
    facilities = models.TextField(blank=True)
    rules = models.TextField(blank=True)
    cancellation_policy = models.TextField(blank=True)
    is_active = models.BooleanField(default=False, db_index=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    slug = models.SlugField(unique=True)

    class Meta:
        indexes = [
            models.Index(fields=["is_active", "is_verified"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["venue_name"]),
            models.Index(fields=["slug"]),
            models.Index(fields=["-created_at"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} - {self.is_active}"


class Pitch(models.Model):
    SPORT_TYPES = [
        ("1", "football"),
        ("2", "futsal"),
        ("3", "volleyball"),
        ("4", "tennis"),
    ]

    SURFACE_TYPES = [
        ("grass", "Grass"),
        ("artificial", "Artificial"),
        ("parquet", "Parquet"),
    ]

    venue = models.ForeignKey(
        to=Venue,
        on_delete=models.CASCADE,
        related_name="pitches",
        verbose_name="saloon",
    )

    pitch_name = models.CharField(max_length=100)
    sport_type = models.CharField(max_length=20, choices=SPORT_TYPES)
    surface_type = models.CharField(max_length=20, choices=SURFACE_TYPES)
    capacity = models.PositiveIntegerField(default=0)
    price_per_hour = models.DecimalField(max_digits=12, decimal_places=0)
    weekend_price = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        null=True,
        blank=True,
        help_text="if not set, same as price_per_hour",
    )
    has_lighting = models.BooleanField(default=True, db_index=True)
    has_changing_room = models.BooleanField(default=True, db_index=True)
    has_parking = models.BooleanField(default=False, db_index=True)
    has_cafeteria = models.BooleanField(default=False, db_index=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    slug = models.SlugField(unique=True)

    class Meta:
        db_table = "pitches"

        indexes = [
            models.Index(fields=["venue", "is_active"]),
            models.Index(fields=["sport_type"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["price_per_hour"]),
            models.Index(fields=["capacity"]),
            models.Index(fields=["slug"]),
            models.Index(fields=["-created_at"]),
        ]
        ordering = ["venue", "pitch_name"]

    def __str__(self):
        return f"{self.venue.venue_name} - {self.pitch_name}"


class WorkingHours(models.Model):

    DAYS_OF_WEEK = [
        (1, "saturday"),
        (2, "sunday"),
        (3, "monday"),
        (4, "tuesday"),
        (5, "wednesday"),
        (6, "thursday"),
        (7, "friday"),
    ]
    pitch = models.ForeignKey(
        to=Pitch, on_delete=models.CASCADE, related_name="working_hours"
    )
    day_of_week = models.IntegerField(choices=DAYS_OF_WEEK, db_index=True)
    start_time = models.TimeField(verbose_name="pitch_start_time")
    end_time = models.TimeField(verbose_name="pitch_end_time")
    is_closed = models.BooleanField(default=False)

    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError("The start time must be less than end time")
        overlapping = WorkingHours.objects.filter(
            pitch=self.pitch, day_of_week=self.day_of_week, is_closed=False
        ).exclude(id=self.id)
        for wh in overlapping:
            if self.start_time < wh.end_time and self.end_time > wh.start_time:
                raise ValidationError(f"Conflict hours  {wh.start_time}-{wh.end_time}")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        db_table = "working_hours"
        unique_together = [["pitch", "day_of_week"]]
        indexes = [
            models.Index(fields=["pitch", "day_of_week"]),
            models.Index(fields=["pitch", "is_closed"]),
        ]
        ordering = ["pitch", "day_of_week", "start_time"]

    def __str__(self):
        if self.is_closed:
            return f"{self.pitch.name} - {self.get_day_of_week_display()}: تعطیل"
        return f"{self.pitch.name} - {self.get_day_of_week_display()}: {self.start_time} تا {self.end_time}"


def pitch_image_path(instance, filename):
    return f"pitches/{instance.pitch.id}/images/{filename}"


def validate_image_size(value):
    filesize = value.size
    if filesize > 5 * 1024 * 1024:
        raise ValidationError("Images must be less than 5 megabyte")


class Image(models.Model):
    pitch = models.ForeignKey(to=Pitch, on_delete=models.CASCADE, related_name="images")

    image = models.ImageField(
        upload_to=pitch_image_path,
        validators=[validate_image_size],
        help_text="maximum 5 megabyte",
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "pitch_images"
        ordering = ["uploaded_at"]
        indexes = [
            models.Index(fields=["pitch"]),
        ]

    def __str__(self):
        return f"{self.pitch.name} - {self.title or 'image'} #{self.id}"
