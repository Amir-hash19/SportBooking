from django.urls import path

from . import views



urlpatterns = [
    path("pitches/<int:pitch_id>/slots/", views.PitchAvailableSlotsAPIView.as_view()),
    path("bookings/", views.BookingCreateView.as_view()),
    path("bookings/<int:pk>/pay/", views.BookingPayView.as_view()),
]