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

    """
    Serializer for creating a venue.

    Ensures the authenticated user has venue management permissions
    and automatically assigns them as the venue manager.
    """

    class Meta:
        model=Venue
        fields = ["venue_name", "description",
        "address", "phone",
        "facilities", "rules", 
        "cancellation_policy",
        "is_active"] 

    def validate(self, attrs):
        """
        Verify that the authenticated user is allowed to create venues.
        """
        user = self.context["request"].user
        if not user.is_complex_manager:
            raise serializers.ValidationError("You are not a complex manager")
        return attrs


    def create(self, validated_data):
        """
        Create a venue and assign the authenticated user as its manager.
        """
        user = self.context["request"].user
        return Venue.objects.create(manager=user, **validated_data)

        
            


class ListVenueSerializer(serializers.ModelSerializer):
    """
        Serializer for displaying venue details.
        Includes additional administrative fields when the requesting
        user is a superuser.
    """
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
    """
        Serializer for creating and validating pitch schedules.
        Ensures valid operating hours and accepted weekday values.
    """

    class Meta:
        model = PitchSchedule
        fields = ["day_of_week", "start_time", "end_time"]

    def validate(self, attrs):
        """
            Validate that the start time is earlier than the end time.
        """
        start = attrs["start_time"]
        end = attrs["end_time"]

        if start >= end:
            raise serializers.ValidationError("Invalid time range")

        return attrs 

    def validate_day_of_week(self, value):
        """
            Validate that the provided day of week is supported.
        """
        allowed = ["saturday","sunday","monday","tuesday","wednesday","thursday","friday"]
        if value not in allowed:
            raise serializers.ValidationError(
                "Invalid day"
            )
        return value


        



class PitchSerializer(serializers.ModelSerializer):
    """
        Serializer for creating and managing Pitch objects.
        Handles nested schedule creation and validates overlapping time slots
        both within the request payload and against existing database records.
    """
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
        """
            Create a pitch under the user's managed venue and attach schedules.
            Also validates against existing schedule overlaps in the database.
        """
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
    """
        Serializer for retrieving detailed Pitch information.
        Includes computed venue name along with full pitch attributes
        for read-only detailed views.
    """
    venue_name = serializers.CharField(source='venue.venue_name', read_only=True)
    class Meta:
        model  = Pitch
        fields = [
        'pitch_name', 'sport_type', 'price_per_hour',
        "surface_type","capacity","has_lighting","has_changing_room",
        "has_parking","has_cafeteria","updated_at","venue_name"
        ]



class PitchListSerializer(serializers.ModelSerializer):
    """
        Serializer for listing Pitch objects.
        Provides a lightweight representation of pitch data including
        basic attributes and the related venue name.
    """
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
    """
        Admin serializer for listing Pitch objects.
        Extends the public list serializer by including administrative
        fields such as activity status and timestamps.
    """
    class Meta(PitchListSerializer.Meta):
        fields = PitchListSerializer.Meta.fields + ["is_active","created_at","updated_at"]
        

  