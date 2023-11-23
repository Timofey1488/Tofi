from django.urls import path
from django.contrib.auth import views as auth_views
from .views import (UserRegistrationView, LogoutView, UserLoginView, UserProfileView, change_password, CardCreateView,
                    CardListView, verify_email)

app_name = 'accounts'

urlpatterns = [
    path(
        "login/", UserLoginView.as_view(),
        name="user_login"
    ),
    path(
        "logout/", LogoutView.as_view(),
        name="user_logout"
    ),
    path(
        "register/", UserRegistrationView.as_view(),
        name="user_registration"
    ),
    path(
        "profile/", UserProfileView.as_view(),
        name="user_profile"
    ),
    path(
        'password_change/', change_password,
        name='password_change'
    ),
    path(
        'password_change_done/', auth_views.PasswordChangeDoneView.as_view(),
        name='password_change_done'
    ),
    path(
        'create_card/', CardCreateView.as_view(),
        name='create_card'
    ),
    path(
        'card_list/', CardListView.as_view(),
        name='card_list'
    ),
    path(
        'verify-email/', verify_email, name='verify_email'
    ),
]
