from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from . import views


urlpatterns = [
    path("token/", TokenRefreshView.as_view(), name="token_refresh"),
    path("token/verify/", TokenVerifyView.as_view(), name="token_verify"),


    path(
        "user/signup/"
        ,views.CreateUserAccountView.as_view(),
        name="user-signup"
    ),

    path(
        "user/login/",
        views.LoginView.as_view(),
        name="user-loggin"
    ),


    path(
        "users/super-admin/promotions/",
        views.CreateAdminUserView.as_view(),
        name="user_promotion"
    ),

    path(
        "manager-request/",
        views.SubmitComplexManagerRequestView.as_view(),
        name='submit_manager_request'
        ),

    path(
        "user/list/",
        views.UserListView.as_view(),
        name="list_user"
    )    
]
