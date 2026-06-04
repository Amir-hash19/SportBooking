import logging

from django.db import IntegrityError
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status
from rest_framework.generics import (
    CreateAPIView,
    ListAPIView,
    RetrieveAPIView,
    UpdateAPIView,
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

from . import serializers
from .filters import UserFilter, ComplexManagerRequestFilter
from .models import UserAccount, Profile, ComplexManagerRequest
from .paginations import UserPagination
from .permissions import IsSuperAdmin
from .throttles import UserListThrottle


logger = logging.getLogger(__name__)


class CreateUserAccountView(APIView):
    """
    Docstring for CreateUserAccountView

    :args:
        name,
        last_name,
        phone_number,
        email,
        password,
        password_confirm
    :kwargs:
        national_id,
        is_complex_manager,
        is_active,
        is_staff,
        date_created,
        updated_at

    :OutPut:
            status code 201 created
            access token and refresh token
            data = data
    :success: True | and the message is User account created successfully
    """

    permission_classes = [AllowAny]

    def post(self, request):
        logger.info(f"User signup attempt from IP: {self.get_client_ip(request)}")

        try:
            serializer = serializers.UserSignupSerializer(data=request.data)

            if not serializer.is_valid():
                logger.warning(f"User signup validation failed: {serializer.errors}")
                return Response(
                    {
                        "success": False,
                        "errors": serializer.errors,
                        "message": "Validation failed",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                user = serializer.save()
                logger.info(f"User created successfully: {user.email} (ID: {user.id})")
            except IntegrityError as e:
                logger.error(f"Integrity error creating user: {str(e)}")
                return Response(
                    {
                        "success": False,
                        "message": "User with this email or phone number already exists",
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            try:
                refresh = RefreshToken.for_user(user)
                logger.info(
                    f"Tokens generated for user {user.id}", extra={"user_id": user.id}
                )
            except TokenError as e:
                logger.error(f"Token generation failed for user {user.id}: {str(e)}")
                return Response(
                    {
                        "success": False,
                        "message": "User created but failed to generate tokens",
                        "error_code": "TOKEN_GENERATION_FAILED",
                    },
                    status=status.HTTP_401_UNAUTHORIZED,
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
                        "phone_number": str(user.phone_number),
                    },
                    "tokens": {
                        "access": str(refresh.access_token),
                        "refresh": str(refresh),
                        "token_type": "Bearer",
                    },
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            logger.exception(f"Unexpected error in user signup: {str(e)}")
            return Response(
                {
                    "success": False,
                    "message": "An unexpected error occurred",
                    "error_code": "INTERNAL_SERVER_ERROR",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip


class LoginView(APIView):
    """Login API

    permission level is allow any
    every body can login
    HEADER is empty

    args:
        1) phone_number as string
        2) password as string
    kwargs:
        None

    OutPut:
        status code 200 Ok
        success: True
        tokens :
            refresh token
            access token
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = serializers.LoginSerializer(data=request.data)

        if not serializer.is_valid():
            logger.warning(f"User Login validation failed: {serializer.errors}")
            return Response(
                {
                    "success": False,
                    "errors": serializer.errors,
                    "message": "Login validation failed, data was invalid",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = serializer.validated_data["user"]

        try:
            refresh = RefreshToken.for_user(user)
        except TokenError as e:
            logger.error(f"Token creation failed for user {user.id}: {str(e)}")
            return Response(
                {"success": False, "message": "Failed to create authentication token"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {
                "success": True,
                "message": "Login was successful",
                "data": {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                    "user": {
                        "email": str(user.phone_number),
                        "name": user.name,
                        "last_name": user.last_name,
                    },
                },
            },
            status=status.HTTP_200_OK,
        )


class CreateAdminUserView(APIView):
    """
    Promote an existing user to the SuperAdmin role.
    Accessible only by users with SuperAdmin privileges.
    """

    permission_classes = [IsSuperAdmin]
    serializer_class = serializers.AddAdminUserSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)

        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        return Response(
            {
                "message": "User Promoted to SuperAdmin",
                "user_email": user.email,
                "phone_number": str(user.phone_number),
            },
            status=status.HTTP_200_OK,
        )


class SubmitComplexManagerRequestView(APIView):
    """
    users send rquest to be a Complex Manager
    this request would be accept by admin

    args:
        user must have access to this endpoint 
        should be Authenticated
        send request without body data
        JWT token

    returns:
            "message": "Your request has been submitted",
            "request_id": manager_request.id,
            "status": manager_request.status,
            status code 201 created
    """
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.CreateComplexManagerRequestSerializer

    def post(self, request):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )

        serializer.is_valid(raise_exception=True)

        manager_request = serializer.save()

        return Response(
            {
                "message": "Your request has been submitted",
                "request_id": manager_request.id,
                "status": manager_request.status,
            },
            status=status.HTTP_201_CREATED,
        )


@method_decorator(cache_page(60 * 15), name="dispatch")
class UserListView(ListAPIView):
    """
        api will return a list of users with their profiles for admin

        args:
            required IsSuperAdmin permission
            HTTP method : GET
            JWT token
        returns:
                list of users 
                provides searching and filtering data
                200 OK status code  

    """
    permission_classes = [IsSuperAdmin]
    serializer_class = serializers.ListUserSerializer

    throttle_classes = [UserListThrottle]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    pagination_class = UserPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    search_fields = ["phone_number", "email"]
    filterset_class = UserFilter

    def get_queryset(self):
        return UserAccount.objects.select_related("profile").only(
            "name",
            "last_name",
            "email",
            "phone_number",
            "national_id",
            "is_complex_manager",
            "is_staff",
            "date_created",
            "profile__avatar",
            "profile__address",
            "profile__gender",
            "profile__second_number",
        )


class DetailUserAccount(RetrieveAPIView):
    """
        the endpoint returns user details account and profile together

        args:
            must be authenticated
            HTTP method : GET
        returns:
                user data without password
                users can not send request more than the limitaions sets
                status code 200 OK    

    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserListThrottle]
    serializer_class = serializers.ListUserSerializer

    def get_object(self):
        return UserAccount.objects.select_related("profile").get(
            pk=self.request.user.pk
        )


class EditUserProfileView(UpdateAPIView):
    """
        client can edit their own account and profile
        but can not edit the password
        must be authenticated

        args:
            JWT token in header
            HTTP method: PUT or PATCH (for partial update)
        
        returns:
                user data
                status code 200 OK
                
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserListThrottle]
    serializer_class = serializers.ListUserSerializer

    def get_object(self):
        return self.request.user


class LogOutView(APIView):
    """
        Logout user by blacklisting the provided JWT refresh token.
        Requires authentication. Accepts POST request with 'refresh' token in body.
        Returns 205 on success, 400 if token is invalid or missing.

    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response(
                    {"detail": "Refresh token required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(
                {"message": "User Logout was Successful"},
                status=status.HTTP_205_RESET_CONTENT,
            )
        except TokenError:
            return Response(
                {"detail": "Invalid Token"}, status=status.HTTP_400_BAD_REQUEST
            )


class ChangePasswordView(APIView):
    """
        Change authenticated user's password via POST request.
        Validates old password before setting the new one.
        Returns 200 on success, 409 if old password is wrong, 400 for invalid data.

    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserListThrottle]
    serializer_class = serializers.ChangePasswordSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            user = request.user

            if not user.check_password(serializer.validated_data["old_password"]):
                return Response(
                    {"detail": "Old password is incorrect"},
                    status=status.HTTP_409_CONFLICT,
                )

            user.set_password(serializer.validated_data["new_password"])
            user.save()

            return Response(
                {"detail": "Password changed successfully"}, status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RemoveAdminUserView(CreateAPIView):
    """
        Remove a user from the SuperAdmin group. Accessible only by SuperAdmins.
        Accepts POST with user data, validates via serializer, then downgrades the user.
        Returns 200 with phone number on success, 400 for invalid data.

    """
    permission_classes = [IsSuperAdmin]
    throttle_classes = [UserListThrottle]

    serializer_class = serializers.RemoveAdminUserSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        return Response(
            {
                "message": "User removed from SuperAdmin group successfully.",
                "phone_number": str(user.phone_number),
            },
            status=status.HTTP_200_OK,
        )



class ReviewUserManagerRequestView(UpdateAPIView):
    """

        Update status and review note of a complex manager request by SuperAdmin.
        Accepts partial PATCH request. Sets reviewed_by automatically from authenticated user.
        Returns 200 on success, 400 for invalid data, 404 if request not found.
   
    """
    permission_classes = [IsSuperAdmin]
    throttle_classes = [UserListThrottle]
    serializer_class = serializers.ReviewUserManagerRequestSerializer
    lookup_field = "pk"
    queryset = ComplexManagerRequest.objects.all()

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {"message":"Request reviewed successfully"}
        ,status=status.HTTP_200_OK)
        



@method_decorator(cache_page(60 * 15), name="dispatch")
class ListUserRequestManagerView(ListAPIView):
    """
        api will return a list of users request whoam want to be a complex manager for admin
        admin can review their request 

        args:
            required IsSuperAdmin permission
            HTTP method : GET
            JWT token
        returns:
                list of users requests 
                provides searching and filtering data
                200 OK status code  

    """
    permission_classes = [IsSuperAdmin]
    serializer_class = serializers.UserRequestManagerSerializer
    pagination_class = UserPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = ["status"]
    filterset_class = ComplexManagerRequestFilter
    throttle_classes = [UserListThrottle]

    def get_queryset(self):
        return ComplexManagerRequest.objects.select_related("user__profile","reviewed_by__profile").all()
        