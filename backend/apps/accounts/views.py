from rest_framework import generics
from .models import UserAccount, Profile
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from rest_framework.views import Response
from rest_framework.views import APIView
from django.db import transaction
from . import serializers



class CreateUserAccountView(APIView):
    permission_classes = [AllowAny]
    
    @transaction.atomic
    def post(self, request):
        serializer = serializers.UserSignupSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()

            refresh = RefreshToken.for_user(user)

            return Response({
                "detail":"User Account created Successfully.",
                "access":str(refresh.access_token),
                "refresh":str(refresh)
            }, status=status.HTTP_201_CREATED)
        return Response(
            serializer.errors, status=status.HTTP_400_BAD_REQUEST
        )


