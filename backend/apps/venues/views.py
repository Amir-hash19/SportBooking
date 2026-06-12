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

from backend.apps.accounts.throttles import VenueCreateThrottle, VenueListThrottle
from backend.apps.venues.paginations import VenuePagination

from django.core.cache import cache


class CreateVenueView(VenueCreateMixin, CreateAPIView):
    permission_classes = [IsComplexManager & IsProfileComplete]
    serializer_class = serializers.CreateVenueSerializer
    throttle_classes = [VenueCreateThrottle]




class ListVenueView(ListAPIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [VenueListThrottle]
    queryset = Venue.objects.select_related("manager").order_by("-created_at")
    serializer_class = serializers.ListVenueSerializer
    pagination_class = VenuePagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    def get_cache_key(self, request):
        user_type = "admin" if request.user.is_superuser else "user"
        return f"venue_list_{user_type}_{request.GET.urlencode()}"
    

    def list(self, request, *args, **kwargs):
        cache_key = self.get_cache_key(request)
        cached = cache.get(cache_key)
        if cached:
            return Response(cached)
        
        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, 60 * 20)
        return response
            