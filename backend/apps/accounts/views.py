import logging
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from . import serializers

logger = logging.getLogger(__name__)



class CreateUserAccountView(APIView):
    permission_classes = [AllowAny]
    
    @transaction.atomic
    def post(self, request):
        logger.info(f"User signup attempt from IP: {self.get_client_ip(request)}")
        
        try:
            serializer = serializers.UserSignupSerializer(data=request.data)

            if not serializer.is_valid():
                logger.warning(
                    f"User signup validation failed: {serializer.errors}"
                )
                return Response(
                    {
                        "success": False,
                        "errors": serializer.errors,
                        "message": "Validation failed"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            
            try:
                user = serializer.save()
                logger.info(f"User created successfully: {user.email} (ID: {user.id})")
            except IntegrityError as e:
                logger.error(f"Integrity error creating user: {str(e)}")
                return Response({
                    "success": False,
                    "message": "User with this email or phone number already exists"
                }, status=status.HTTP_409_CONFLICT)
            
           
            try:
                refresh = RefreshToken.for_user(user)
                logger.info(
                    f"Tokens generated for user {user.id}",
                    extra={'user_id': user.id}
                )
            except TokenError as e:
                logger.error(f"Token generation failed for user {user.id}: {str(e)}")
                return Response(
                    {
                        "success": False,
                        "message": "User created but failed to generate tokens",
                        "error_code": "TOKEN_GENERATION_FAILED"
                    },
                    status=status.HTTP_201_CREATED  
                )

            return Response(
                {
                    "success": True,
                    "message": "User account created successfully",
                    "data": {
                        "user_id": user.id,
                        "name": user.name,
                        "last_name": user.last_name,
                        "email": user.email,
                        "phone_number": user.phone_number
                    },
                    "tokens": {
                        "access": str(refresh.access_token),
                        "refresh": str(refresh),
                        "token_type": "Bearer"
                    }
                },
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            logger.exception(f"Unexpected error in user signup: {str(e)}")
            return Response(
                {
                    "success": False,
                    "message": "An unexpected error occurred",
                    "error_code": "INTERNAL_SERVER_ERROR"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip



    

class LoginView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = serializers.LoginSerializer(data=request.data)
        
       
        if not serializer.is_valid():
            logger.warning(f"User Login validation failed: {serializer.errors}")
            return Response(
                {
                    "success": False,
                    "errors": serializer.errors,
                    "message": "Login validation failed, data was invalid"
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        
        user = serializer.validated_data["user"]
        
       
        try:
            refresh = RefreshToken.for_user(user)
        except TokenError as e:
            logger.error(f"Token creation failed for user {user.id}: {str(e)}")
            return Response(
                {
                    "success": False,
                    "message": "Failed to create authentication token"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
      
        return Response(
            {
                "success": True,
                "message": "Login was successful",
                "data": {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                    "user": {
                        "id": user.id,
                        "email": user.phone_number,
                        "name": user.name,
                        "last_name": user.last_name
                    }
                }
            },
            status=status.HTTP_200_OK
        )
           


               
                

            

            
           
            

           


               



