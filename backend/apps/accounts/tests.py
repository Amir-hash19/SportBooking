import pytest
from rest_framework.test import APIClient, APITestCase
from django.urls import reverse
from rest_framework import status
from django.contrib.auth import get_user_model
from unittest.mock import patch
from backend.apps.accounts.models import ComplexManagerRequest
from django.contrib.auth.models import Group
from django.core.cache import cache


User = get_user_model()


class UserChangePasswordTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            name = "testuser",
            last_name = "testuser_test",
            phone_number = "+989121111111",
            password="oldpassword123"
        )

        self.url = reverse("user-change-password")

    def test_change_password_successfully(self):
        self.client.force_authenticate(user=self.user)    
        

        payload = {
            "old_password":"oldpassword123",
            "new_password":"newpassword123",
            "confirm_password":"newpassword123"
        }

        response = self.client.post(
            self.url,
            payload,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        
        self.user.refresh_from_db()

        self.assertTrue(
            self.user.check_password("newpassword123")
        )

        self.assertEqual(
            response.data["detail"],
            "Password changed successfully"
        )




class ListUserRequestManagerTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            name = "admintest",
            last_name = "adminuser_test2",
            phone_number = "+989122222222",
            password="adminpassword123"
        )

        super_admin_group,_ = Group.objects.get_or_create(
            name="SuperAdmin"
        )
        self.admin.is_superuser = True
        self.admin.groups.add(super_admin_group)
        self.admin.save()

        self.user = User.objects.create_user(
            name = "testuser2",
            last_name = "testuser_test2",
            phone_number = "+989133333333",
            password="oldpassword123"
        )

        self.url = reverse("admin-list-request")


    def test_admin_can_get_requests(self):
        ComplexManagerRequest.objects.create(
            user = self.user,
            status = "pending"
        )    

        self.client.force_authenticate(self.admin)

        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK

        )

    def test_normal_user_cannot_access(self):
        cache.clear()
        self.client.force_authenticate(self.user)  

        response = self.client.get(self.url)  

        print(response.status_code)

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN
        )