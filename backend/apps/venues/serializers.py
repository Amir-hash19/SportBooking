import re
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.models import Group
from django.core.validators import RegexValidator
from django.db import transaction
from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers
from backend.apps.venues.models import Venue, PitchSchedule, Image, Pitch
User = get_user_model()

from backend.apps.venues.validations import check_schedule_overlap


class CreateVenueSerializer(serializers.ModelSerializer):
    class Meta:
        model=Venue
        fields = ["venue_name", "description",
        "address", "phone",
        "facilities", "rules", 
        "cancellation_policy",
        "is_active"] 

    def validate(self, attrs):
        user = self.context["request"].user
        if not user.is_complex_manager:
            raise serializers.ValidationError("You are not a complex manager")
        return attrs

    def create(self, validated_data):
        user = self.context["request"].user
        return Venue.objects.create(manager=user, **validated_data)

        
            


class ListVenueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Venue
        fields = ["venue_name", "description", "address"
        ,"phone","facilities","rules","cancellation_policy"
        ,"created_at"
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)

        if self.context["request"].user.is_superuser:
            data["is_active"] = instance.is_active
            data["is_verified"] = instance.is_verified
            data["updated_at"] = instance.updated_at
            return data






class PitchScheduleSerializer(serializers.ModelSerializer):

    class Meta:
        model = PitchSchedule
        fields = ["day_of_week", "start_time", "end_time"]

    def validate(self, attrs):
        start = attrs["start_time"]
        end = attrs["end_time"]

        if start >= end:
            raise serializers.ValidationError("Invalid time range")

        return attrs 

    def validate_day_of_week(self, value):
        allowed = ["saturday","sunday","monday","tuesday","wednesday","thursday","friday"]
        if value not in allowed:
            raise serializers.ValidationError(
                "Invalid day"
            )
        return value


        



class PitchSerializer(serializers.ModelSerializer):
    schedules = PitchScheduleSerializer(many=True)

    class Meta:
        model = Pitch
        fields = [
            "venue",
            "pitch_name",
            "sport_type",
            "surface_type",
            "capacity",
            "price_per_hour",
            "weekend_price",
            "schedules",
        ]
        extra_kwargs = {
            "venue": {"read_only": True}
        }

    def validate_schedules(self, schedules):
        for i, s1 in enumerate(schedules):
            for s2 in schedules[i+1:]:
                if s1["day_of_week"] == s2["day_of_week"]:
                    if (
                        s1["start_time"] < s2["end_time"]
                        and s1["end_time"] > s2["start_time"]
                    ):
                        raise serializers.ValidationError(
                            "Schedules in request overlap"
                        )
        return schedules

    @transaction.atomic
    def create(self, validated_data):
        user = self.context["request"].user

        venue = getattr(user, "managed_venue", None)
        if not venue:
            raise serializers.ValidationError("You do not have any venue.")

        schedules_data = validated_data.pop("schedules", [])
        pitch = Pitch.objects.create(venue=venue, **validated_data)

        for s in schedules_data:
            if check_schedule_overlap(pitch, s["day_of_week"], s["start_time"], s["end_time"]):
                raise serializers.ValidationError("Overlapping schedule exists")
            PitchSchedule.objects.create(pitch=pitch, **s)

        return pitch
            




class PitchRetrieveSerializer(serializers.ModelSerializer):
    venue_name = serializers.CharField(source='venue.venue_name', read_only=True)
    class Meta:
        model  = Pitch
        fields = [
        'pitch_name', 'sport_type', 'price_per_hour',
        "surface_type","capacity","has_lighting","has_changing_room",
        "has_parking","has_cafeteria","updated_at","venue_name"
        ]



class PitchListSerializer(serializers.ModelSerializer):
    venue_name = serializers.CharField(source='venue.venue_name', read_only=True)
    
    class Meta:
        model = Pitch
        fields = [
            'pitch_name',
            'sport_type',
            'surface_type',
            'capacity',
            'price_per_hour',
            'weekend_price',
            'has_lighting',
            'has_changing_room',
            'has_parking',
            'has_cafeteria',
            'venue_name',
        ]



class PitchAdminListSerializer(PitchListSerializer):
    class Meta(PitchListSerializer.Meta):
        fields = PitchListSerializer.Meta.fields + ["is_active","created_at","updated_at"]
        

  