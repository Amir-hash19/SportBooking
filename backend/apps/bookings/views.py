import logging
from datetime import date as date_type
from datetime import datetime, timedelta, time
from django.db import IntegrityError
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
from backend.apps.venues.models import Pitch, PitchSchedule
from .models import Booking


from .serializers import BookingCreateSerializer, BookingDetailSerializer, PaymentSerializer
from .services import create_booking, get_available_slots, process_mock_payment







class PitchAvailableSlotsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pitch_id):
        date_str = request.query_params.get("date")
        slot_minutes = request.query_params.get("slot", 60)

        if not date_str:
            return Response({"detail": "date must be given. (YYYY-MM-DD)"}, status=400)

        try:
            booking_date = date_type.fromisoformat(date_str)
            slot_minutes = int(slot_minutes)
        except ValueError:
            return Response({"detail": "data or slot is invalid."}, status=400)

        try:
            pitch = Pitch.objects.get(id=pitch_id, is_active=True)
        except Pitch.DoesNotExist:
            return Response({"detail": "pitch did not find."}, status=404)

        slots = get_available_slots(pitch, booking_date, slot_minutes)

        return Response({
            "pitch_id": pitch_id,
            "date": date_str,
            "slot_minutes": slot_minutes,
            "slots": slots,
        })




class BookingCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = BookingCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            booking = create_booking(
                user=request.user,
                **serializer.validated_data,
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_409_CONFLICT)
        
        return Response(
            BookingDetailSerializer(booking).data,
            status=status.HTTP_201_CREATED
        )
    

class BookingPayView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            booking = Booking.objects.get(pk=pk, user=request.user)
        except Booking.DoesNotExist:
            return Response({"detail": "booked reservation did not find."}, status=404)

        try:
            payment = process_mock_payment(booking)
        except ValueError as e:
            return Response({"detail": str(e)}, status=400)

        return Response(PaymentSerializer(payment).data)
    


                