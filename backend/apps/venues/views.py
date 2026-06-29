import logging

from datetime import datetime, timedelta, date as date_type
from datetime import datetime, timedelta, time
from django.db import IntegrityError
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from rest_framework import filters, status
from rest_framework.generics import (
    CreateAPIView,
    ListAPIView,
    RetrieveAPIView,
    UpdateAPIView,
    RetrieveUpdateDestroyAPIView
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from backend.apps.accounts.permissions import IsComplexManager, IsProfileComplete, IsSuperAdmin, IsPitchOwner
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

from . import serializers
from .models import Venue, Pitch,PitchSchedule,Image
from backend.apps.bookings.models import Booking
from backend.apps.venues.mixins import VenueCreateMixin

from backend.apps.accounts.throttles import VenueCreateThrottle, VenueListThrottle
from backend.apps.venues.paginations import VenuePagination

from django.core.cache import cache

from .serializers import PitchSerializer, PitchScheduleSerializer

from .utils import merge_time_ranges
from .filters import Pitchfilter



class CreateVenueView(VenueCreateMixin, CreateAPIView):
    """
        API endpoint for creating a new Venue.
        Restricts access to complex managers with completed profiles and
        applies rate limiting to prevent abuse.
    """
    permission_classes = [IsComplexManager & IsProfileComplete]
    serializer_class = serializers.CreateVenueSerializer
    throttle_classes = [VenueCreateThrottle]




class ListVenueView(ListAPIView):
    """
        API endpoint for listing venues with filtering, caching, and pagination.
        Supports search, ordering, and role-based cached responses for improved
        performance.
    """
    permission_classes = [IsAuthenticated]
    # throttle_classes = [VenueListThrottle]
    queryset = Venue.objects.select_related("manager").order_by("-created_at")
    serializer_class = serializers.ListVenueSerializer
    pagination_class = VenuePagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    def get_cache_key(self, request):
        """
            Generate a cache key based on user type and query parameters.
        """
        user_type = "admin" if request.user.is_superuser else "user"
        return f"venue_list_{user_type}_{request.GET.urlencode()}"
    

    def list(self, request, *args, **kwargs):
        """
            Return a cached or freshly generated list of venues.
        """
        cache_key = self.get_cache_key(request)
        cached = cache.get(cache_key)
        if cached:
            return Response(cached)
        
        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, 60 * 20)
        return response
            



class PitchCreateView(APIView):
    """
        API endpoint for creating a new Pitch.
        Allows complex managers to create pitches under their managed venue,
        including nested schedule creation.
    """
    permission_classes = [IsComplexManager]
    serializer_class = serializers.PitchSerializer
    def post(self, request):
        serializer = serializers.PitchSerializer(
            data=request.data,
            context={"request": request}  
        )
        serializer.is_valid(raise_exception=True)
        pitch = serializer.save()
        return Response(serializers.PitchSerializer(pitch).data, status=201)






class PitchAvailableSlotsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pitch_id):
       
        day_str = request.query_params.get("day")
        date_str = request.query_params.get("date")  
        slot_minutes = int(request.query_params.get("slot", 60))

        if not day_str or not date_str:
            return Response(
                {"detail": "data or day must be given."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            day = int(day_str)
            booking_date = date_type.fromisoformat(date_str)
        except ValueError:
            return Response({"detail": "data or day is invalid."}, status=400)

        try:
            pitch = Pitch.objects.get(id=pitch_id, is_active=True)
        except Pitch.DoesNotExist:
            return Response({"detail": "pitch did not."}, status=404)

        schedules = PitchSchedule.objects.filter(pitch=pitch, day_of_week=day)
        merged_schedules = merge_time_ranges(schedules)

       
        booked = Booking.objects.filter(
            pitch=pitch,
            booking_date=booking_date,
            status__in=["pending", "confirmed"],
        ).values_list("start_time", "end_time")

        booked_ranges = list(booked)

        result = []
        for start_time, end_time in merged_schedules:
            current = datetime.combine(booking_date, start_time)
            end = datetime.combine(booking_date, end_time)

            while current + timedelta(minutes=slot_minutes) <= end:
                slot_start = current.time()
                slot_end = (current + timedelta(minutes=slot_minutes)).time()

                is_available = not any(
                    slot_start < b_end and slot_end > b_start
                    for b_start, b_end in booked_ranges
                )

                result.append({
                    "start": slot_start.strftime("%H:%M"),
                    "end": slot_end.strftime("%H:%M"),
                    "is_available": is_available,
                })
                current += timedelta(minutes=slot_minutes)

        return Response({
            "pitch_id": pitch_id,
            "date": date_str,
            "day": day,
            "slot_minutes": slot_minutes,
            "slots": result,
        })
    




class RetrievePitchView(RetrieveAPIView):
    """
        API endpoint for retrieving a single active Pitch.
        Exposes detailed pitch information including related venue data.
    """
    permission_classes = [AllowAny]
    queryset = Pitch.objects.select_related("venue").filter(is_active=True)
    serializer_class = serializers.PitchRetrieveSerializer






class PitchListView(ListAPIView):
    """
        API endpoint for listing pitches with filtering and role-based output.
        Returns different serializer representations for super admins and
        regular users, and restricts inactive pitches for non-admin users.
    """
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = Pitchfilter
    ordering_fields = ['price_per_hour', 'created_at']
    ordering = ['created_at']

    def _is_super_admin(self):
        """
            Check whether the requesting user belongs to the SuperAdmin group.
        """
        user = self.request.user
        return user.is_authenticated and user.groups.filter(name="SuperAdmin").exists()
       


    def get_serializer_class(self):
        if self._is_super_admin():
            return serializers.PitchAdminListSerializer
        return serializers.PitchListSerializer

    def get_queryset(self):
        """
            Return queryset filtered by user permissions.
        """
        qs = Pitch.objects.select_related('venue')
        if not self._is_super_admin():
            qs = qs.filter(is_active=True)
        return qs    





class PitchUpdateDeleteView(RetrieveUpdateDestroyAPIView):
    """
        API endpoint for retrieving, updating, and deleting a Pitch.
        Access is restricted to the pitch owner (venue manager) with
        appropriate permissions.
    """
    permission_classes = [IsComplexManager, IsPitchOwner]
    serializer_class = serializers.PitchListSerializer

    def get_queryset(self):
        """
            Return pitches belonging to the requesting user's managed venue.
        """
        return Pitch.objects.select_related('venue').filter(
            venue__manager=self.request.user
        )