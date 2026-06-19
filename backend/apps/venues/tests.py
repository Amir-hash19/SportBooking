from rest_framework.test import APIClient, APITestCase
from django.urls import reverse
from rest_framework import status
from django.contrib.auth import get_user_model
from unittest.mock import patch
from backend.apps.accounts.models import ComplexManagerRequest
from django.contrib.auth.models import Group
from django.core.cache import cache
from .models import Venue, Pitch


User = get_user_model()






class ListVenuetests(APITestCase):
    def setUp(self):
        cache.clear()

        self.user = User.objects.create_user(
            name = "testuser2",
            last_name = "testuser_tes2t",
            phone_number = "+9891244444",
            password="oldpassword123"
        )
        self.url = reverse("list-venue")

        self.manager = User.objects.create_user(
            name = "managertest1",
            last_name = "managertest1",
            phone_number = "+9891255555",
            password="oldpassword123",
            is_complex_manager = True
        )
        Venue.objects.create(
            manager = self.manager,
            venue_name = "test_venue",
            address = "tehran, tajrish, yekta, num1",
            phone = "+989955555"
        )

    def test_list_venues(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)

        self.assertEqual(
        response.status_code,
        status.HTTP_200_OK
        )

        self.assertEqual(
        response.data["count"],
        1
        )


