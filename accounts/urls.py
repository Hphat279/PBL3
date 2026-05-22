from django.urls import path, include

from .views.common_views import *
from .views.google_views import GoogleStartView, GoogleVerifyView
from .views.common_views import CompleteProfileView

app_name = "accounts"

urlpatterns = [
    path(
        "patient/register/",
        RegisterPatientView.as_view(),
        name="patient-register",
    ),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("login/", LoginView.as_view(), name="login"),
    path("doctor/login/", DoctorLoginView.as_view(), name="doctor-login"),
    path("social/", include("allauth.urls")),
    path("google-login/", google_login_view, name="google-login"),
    path("google/start/", GoogleStartView.as_view(), name="google-start"),
    path("google/verify/", GoogleVerifyView.as_view(), name="google-verify"),
    path(
        "update-basic-information/",
        UpdateBasicUserInformationAPIView.as_view(),
        name="update-basic-information",
    ),
    path(
        "complete-profile/",
        CompleteProfileView.as_view(),
        name="complete-profile",
    ),
]
