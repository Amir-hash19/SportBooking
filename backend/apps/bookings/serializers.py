from rest_framework import serializers
from .models import Booking, Payment


class BookingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ["pitch", "booking_date", "start_time", "end_time"]

    def validate(self, attrs):
        if attrs["start_time"] >= attrs["end_time"]:
            raise serializers.ValidationError("stat time must be less than end time.")
        return attrs


class BookingDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = [
            "id", "pitch", "booking_date", "start_time", "end_time",
            "total_price", "status", "tracking_code", "expires_at",
        ]
        read_only_fields = fields


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ["id", "amount", "status", "transaction_id", "created_at"]