import re
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.models import Group
from django.core.validators import RegexValidator
from django.db import transaction
from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers
from backend.apps.venues.models import Venue, Pitch, Image
User = get_user_model()




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







