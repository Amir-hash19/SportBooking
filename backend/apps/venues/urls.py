from django.urls import path
from . import views


urlpatterns = [
    path("venue/", views.CreateVenueView.as_view(), name="create_venue"),



    path(
        "venues/",
        views.ListVenueView.as_view(),
        name="list_venue"
    )
]
