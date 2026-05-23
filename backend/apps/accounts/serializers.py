from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from .models import UserAccount, Profile
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import get_user_model


User = get_user_model()



class UserSignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=["validate_password"])
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["name", "last_name", "phone_number", "email", "password", "confirm_password"]

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"password":"passwords does not match"})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop("confirm_password")
        user = User.objects.create_user(**validated_data)
        return user