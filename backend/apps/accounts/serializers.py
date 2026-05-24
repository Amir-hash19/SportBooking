from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from .models import UserAccount, Profile
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
import re
User = get_user_model()



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
    
    def validate_email(self, value):
        
        value = value.lower().strip()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists")
        
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', value):
            raise serializers.ValidationError("Enter a valid email address")
        
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
    
    def create(self, validated_data):
       
        validated_data.pop("confirm_password")
        
        
        validated_data['name'] = validated_data.get('name', '').strip()
        validated_data['last_name'] = validated_data.get('last_name', '').strip()
        validated_data['email'] = validated_data.get('email', '').lower().strip()
        
      
        user = User.objects.create_user(**validated_data)
        return user