from prometheus_client import Gauge

from .models import UserAccount
from backend.apps.bookings.models import Booking, Payment
from backend.apps.notifications.models import Notification
from backend.apps.venues.models import Venue, Pitch, PitchSchedule, Image




users_total = Gauge(
    "sportbooking_users_total",
    "Total number of users"
)

bookings_total = Gauge(
    "sportbooking_bookings_total",
    "Total number of bookings"
)

venues_total = Gauge(
    "sportbooking_venues_total",
    "Total number of venues",
)

notifications_total = Gauge(
    "sportbooking_notifications_total",
    "Total number of notifications",
)

pitch_total = Gauge(
    "sportbooking_pitches_total",
    "Total number of pitches",
)

pitchSchedule_total = Gauge(
    "sportbooking_pitchSchedule_total",
    "Total number of pitchSchedule",
)

payment_total = Gauge(
    "sportbooking_payment_total",
    "Total number of payment",
)



users_total.set_function(
    lambda: UserAccount.objects.count()
)

bookings_total.set_function(
    lambda: Booking.objects.count()
)

payment_total.set_function(
    lambda: Payment.objects.count()
)

venues_total.set_function(
    lambda: Venue.objects.count()
)

pitch_total.set_function(
    lambda: Pitch.objects.count()
)

notifications_total.set_function(
    lambda: Notification.objects.count()
)

pitchSchedule_total.set_function(
    lambda: PitchSchedule.objects.count()
)