from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from .models import UserAccount, Profile
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from django.contrib.auth import authenticate
from backend.apps.accounts.models import UserAccount, ComplexManagerRequest
from django.db import transaction
from django.contrib.auth.models import Group
from phonenumber_field.serializerfields import PhoneNumberField
import re


User = get_user_model()

SUPER_ADMIN_GROUP = "SuperAdmin"

class UserSignupSerializer(serializers.ModelSerializer):
   
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        validators=[
            RegexValidator(
                regex=r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$',
                message='Password must be at least 8 characters and contain uppercase, lowercase, number and special character'
            )
        ]
    )
    confirm_password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    
    class Meta:
        model = User
        fields = ["name", "last_name", "phone_number", "email", "password", "confirm_password"]
        extra_kwargs = {
            'email': {'required': True},
            'phone_number': {'required': True},
        }
    
    def validate_phone_number(self, value):
        
       
        value = re.sub(r'[\s\-]', '', value)
        
      
        if not re.match(r'^(09|00989|\+989|989)[0-9]{9}$', value):
            raise serializers.ValidationError("Enter a valid Iranian phone number")
        
      
        if User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("A user with this phone number already exists")
        
        return value
    

    
    def validate_name(self, value):
       
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Name must be at least 2 characters")
        return value.strip()
    

    def validate_last_name(self, value):
       
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Last name must be at least 2 characters")
        return value.strip()
    

    def validate(self, attrs):
        
        password = attrs.get("password")
        confirm_password = attrs.get("confirm_password")
        
        if password != confirm_password:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match"})
        
        return attrs
    

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["phone_number"] = str(instance.phone_number) 
        return data
    
    @transaction.atomic
    def create(self, validated_data):
       
        validated_data.pop("confirm_password")      
        user = User.objects.create_user(**validated_data)
        return user






class LoginSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField()
    password = serializers.CharField(write_only=True, style={"input":"password"})

    class Meta:
        model = UserAccount
        fields = ["phone_number", "password"]

    def validate(self, data):
        phone_number = data.get("phone_number")
        password = data.get("password")
        try:
            UserAccount.objects.get(phone_number=phone_number)

        except UserAccount.DoesNotExist:
            raise serializers.ValidationError(
                "user did not find with given phone_number"
            )    
        
    
        user = authenticate(phone_number=phone_number, password=password)
        if not user:
            raise serializers.ValidationError(
                "phone number or passoword is wrong"
            )
        if not user.is_active:
            raise serializers.ValidationError(
                "this user is deactivated"
            )
        
        data["user"]=user
        return data
    





class AddAdminUserSerializer(serializers.Serializer):
    """

    Validate a user by phone number and promote them to SuperAdmin.
    Adds the user to the SuperAdmin group upon successful validation.

    """
    phone_number = PhoneNumberField()

    def validate_phone_number(self, value):
        try:
            user = UserAccount.objects.get(
                phone_number=value
            )
        except UserAccount.DoesNotExist:
            raise serializers.ValidationError(
                "User not found."
            )

        if user.groups.filter(
            name=SUPER_ADMIN_GROUP
        ).exists():
            raise serializers.ValidationError(
                "User is already a SuperAdmin."
            )

        return user

    def create(self, validated_data):
        """
            Add the validated user to the SuperAdmin group.
            Returns the updated user instance.
        """
        user = validated_data["phone_number"]

        group = Group.objects.get(
            name=SUPER_ADMIN_GROUP
        )

        user.groups.add(group)

        return user

    


class CreateComplexManagerRequestSerializer(
    serializers.ModelSerializer
):
    class Meta:
        model = ComplexManagerRequest
        fields = []

    def validate(self, attrs):
        user = self.context["request"].user

        if user.is_complex_manager:
            raise serializers.ValidationError(
                "You are already a complex manager"
            )      
        
        if ComplexManagerRequest.objects.filter(
            user=user,
            status=ComplexManagerRequest.Status.PENDING
        ).exists():
            raise serializers.ValidationError(
                "You already have a pending request"
            )

        return attrs
    
    def create(self, validated_data):
        return ComplexManagerRequest.objects.create(
            user=self.context["request"].user
        )