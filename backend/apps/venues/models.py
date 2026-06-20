from django.core.exceptions import ValidationError
from django.db import models

from backend.apps.accounts.models import UserAccount


class Venue(models.Model):
    """
    Represents a sports venue that can be managed, verified, and made available
    for reservations.

    Each venue is associated with a single manager account and stores
    essential information such as contact details, address, facilities,
    operational rules, and cancellation policies. The model also tracks
    activation and verification statuses to control visibility and usage
    within the system.

    Attributes:
        manager (UserAccount):
            The user account responsible for managing the venue.
            A one-to-one relationship ensures that each manager can own
            only one venue.

        venue_name (str):
            The name of the venue.

        description (str):
            An optional detailed description of the venue.

        address (str):
            The physical address of the venue.

        phone (str):
            A unique contact phone number for the venue.

        facilities (str):
            Optional information about available facilities and amenities.

        rules (str):
            Optional venue-specific rules and regulations.

        cancellation_policy (str):
            Optional description of booking cancellation terms.

        is_active (bool):
            Indicates whether the venue is currently active and available
            for public use.

        is_verified (bool):
            Indicates whether the venue has been reviewed and approved
            by the platform.

        created_at (datetime):
            Timestamp when the venue record was created.

        updated_at (datetime):
            Timestamp when the venue record was last updated.

        slug (str):
            A unique URL-friendly identifier for the venue.

    Meta:
        ordering:
            Orders venues by creation date in descending order.

        indexes:
            Database indexes to improve query performance for active,
            verified, and recently created venues.

    Returns:
        str:
            A human-readable representation containing the venue name
            and its active status.
    """

    manager = models.OneToOneField(
        to=UserAccount,
        on_delete=models.CASCADE,
        related_name="managed_venue",
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
            models.Index(fields=["-created_at"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.venue_name} - {self.is_active}"




class Pitch(models.Model):
    """
    Represents a playable sports pitch within a venue.

    A pitch is associated with a specific venue and contains information
    about the sport type, playing surface, capacity, pricing, and available
    amenities. The model supports different pricing for weekends and allows
    administrators to control whether a pitch is available for booking.

    Attributes:
        venue (Venue):
            The venue that owns and contains this pitch.

        pitch_name (str):
            The name or identifier of the pitch within the venue.

        sport_type (str):
            The type of sport supported by the pitch.
            Available options include football, futsal, volleyball, and tennis.

        surface_type (str):
            The playing surface material of the pitch.
            Available options include grass, artificial turf, and parquet.

        capacity (int):
            The maximum number of participants the pitch can accommodate.

        price_per_hour (Decimal):
            The standard hourly rental price for the pitch.

        weekend_price (Decimal | None):
            The hourly rental price during weekends. If not specified,
            the value of ``price_per_hour`` should be used.

        has_lighting (bool):
            Indicates whether the pitch has lighting facilities for
            evening or night usage.

        has_changing_room (bool):
            Indicates whether changing rooms are available.

        has_parking (bool):
            Indicates whether parking facilities are available.

        has_cafeteria (bool):
            Indicates whether a cafeteria or refreshment area is available.

        is_active (bool):
            Indicates whether the pitch is currently available for booking.

        created_at (datetime):
            Timestamp when the pitch record was created.

        updated_at (datetime):
            Timestamp when the pitch record was last updated.

    Meta:
        db_table:
            Stores pitch records in the ``pitches`` database table.

        ordering:
            Orders pitches by venue and pitch name.

        indexes:
            Database indexes optimized for filtering by venue, sport type,
            activity status, pricing, capacity, and creation date.

    Returns:
        str:
            A human-readable representation containing the venue name
            and pitch name.
    """
    SPORT_TYPES = [
        ("football", "football"),
        ("futsal", "futsal"),
        ("volleyball", "volleyball"),
        ("tennis", "tennis"),
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
    

    class Meta:
        db_table = "pitches"

        indexes = [
            models.Index(fields=["venue", "is_active"]),
            models.Index(fields=["sport_type"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["price_per_hour"]),
            models.Index(fields=["capacity"]),
            
            models.Index(fields=["-created_at"]),
        ]
        ordering = ["venue", "pitch_name"]

    def __str__(self):
        return f"{self.venue.venue_name} - {self.pitch_name}"





class PitchSchedule(models.Model):
    """
    Defines the weekly operating schedule for a sports pitch.

    Each schedule entry represents a time interval during which a pitch
    is available on a specific day of the week. Multiple schedule records
    can be associated with a single pitch to support different operating
    hours throughout the week.

    Attributes:
        pitch (Pitch):
            The pitch to which this schedule belongs.

        day_of_week (str):
            The day of the week for which the schedule applies.
            Valid values are Saturday, Sunday, Monday, Tuesday,
            Wednesday, Thursday, and Friday.

        start_time (time):
            The beginning of the availability period.

        end_time (time):
            The end of the availability period.

    Meta:
        ordering:
            Orders schedule records by day of the week and start time
            in ascending order.

    Notes:
        The time range defined by ``start_time`` and ``end_time`` should
        represent a valid availability period where ``start_time`` occurs
        before ``end_time``. This validation should be enforced at the
        application or model validation level.
    """
    DAYS_OF_WEEK = [
        ("saturday", "saturday"),
        ("sunday", "sunday"),
        ("monday", "monday"),
        ("tuesday", "tuesday"),
        ("wednesday", "wednesday"),
        ("thursday", "thursday"),
        ("friday", "friday"),
    ]

    pitch = models.ForeignKey(
        Pitch,
        on_delete=models.CASCADE,
        related_name="schedules"
    )

    day_of_week = models.CharField(
        max_length=10,
        choices=DAYS_OF_WEEK,
        db_index=True
    )

    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        ordering = ["day_of_week", "start_time"]


def pitch_image_path(instance, filename):
    return f"pitches/{instance.pitch.id}/images/{filename}"


def validate_image_size(value):
    filesize = value.size
    if filesize > 5 * 1024 * 1024:
        raise ValidationError("Images must be less than 5 megabyte")



class Image(models.Model):
    """
    Represents an image associated with a sports pitch.

    This model stores uploaded images that showcase a pitch, such as
    photos of the playing area, facilities, or surrounding environment.
    Images are validated before upload and organized using a custom
    upload path function.

    Attributes:
        pitch (Pitch):
            The pitch to which the image belongs.

        image (ImageField):
            The uploaded image file. Files are stored using the
            ``pitch_image_path`` upload function and validated through
            ``validate_image_size`` to ensure they meet size restrictions.

        uploaded_at (datetime):
            Timestamp indicating when the image was uploaded.

    Meta:
        db_table:
            Stores image records in the ``pitch_images`` database table.

        ordering:
            Orders images by upload time in ascending order.

        indexes:
            Database indexes optimized for querying images belonging
            to a specific pitch.

    Notes:
        Uploaded image files are limited to a maximum size of 5 MB
        as enforced by the configured validator.

    Returns:
        str:
            A human-readable representation of the image, including
            the associated pitch and image identifier.
    """
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
