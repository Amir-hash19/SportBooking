from django.urls import path
from . import views


urlpatterns = [
    path("venue/", views.CreateVenueView.as_view(), name="create_venue"),



    path(
        "venues/",
        views.ListVenueView.as_view(),
        name="list-venue"
    ),

    path(
        "pitch/",
        views.PitchCreateView.as_view(),
        name="create-pitch-with-time"
    ),

    path(
        "pitchs/",
        views.PitchAvailableSlotsAPIView.as_view(),
        name="available-slots"
    ),
    path(
        "pitch/<int:pk>/",
        views.RetrievePitchView.as_view(),
        name="pitch-detail"
    ),

    path(
        "pitchs/list/",
        views.PitchListView.as_view(),
        name="pitch-list-by-permission"
    ),

    path(
        "pitchs/<int:pk>/",
        views.PitchUpdateDeleteView.as_view(),
        name="pitch-detail-delete"
    ),
    
]
