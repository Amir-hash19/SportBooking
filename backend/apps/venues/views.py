import logging

from django.db import IntegrityError
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status
from rest_framework.generics import (
    CreateAPIView,
    ListAPIView,
    RetrieveAPIView,
    UpdateAPIView,
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from backend.apps.accounts.permissions import IsComplexManager, IsProfileComplete, IsSuperAdmin
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

from . import serializers
from .models import Venue, Pitch,WorkingHours,Image

from backend.apps.venues.mixins import VenueCreateMixin

from backend.apps.accounts.throttles import VenueCreateThrottle



class CreateVenueView(VenueCreateMixin, CreateAPIView):
    permission_classes = [IsComplexManager & IsProfileComplete]
    serializer_class = serializers.CreateVenueSerializer
    throttle_classes = VenueCreateThrottle

