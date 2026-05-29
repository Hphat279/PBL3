from django.urls import path

from .views import (
    DoctorDashboardView,
    schedule_timings,
    DoctorProfileUpdateView,
    DoctorProfileView,
    UpdateEducationAPIView,
    UpdateExperienceAPIView,
    UpdateRegistrationNumberAPIView,
    UpdateSpecializationAPIView,
    DoctorsListView,
    AppointmentListView,
    AppointmentDetailView,
    AppointmentActionView,
    MyPatientsView,
    AppointmentHistoryView,
    DoctorChangePasswordView,
    PrescriptionCreateView,
    PrescriptionDetailView,
    ReviewListView,
    DepartmentQueueView,
    ReferralResultView,
    ReferralCreateView,
)

app_name = "doctors"

urlpatterns = [
    path("list/", DoctorsListView.as_view(), name="list"),
    path("", DoctorsListView.as_view(), name="list-alt"),
    path("dashboard/", DoctorDashboardView.as_view(), name="dashboard"),
    path("schedule-timings/", schedule_timings, name="schedule-timings"),
    path(
        "profile-settings/",
        DoctorProfileUpdateView.as_view(),
        name="profile-settings",
    ),
    path(
        "<str:username>/profile/",
        DoctorProfileView.as_view(),
        name="doctor-profile",
    ),
    path(
        "update-education",
        UpdateEducationAPIView.as_view(),
        name="update-education",
    ),
    path(
        "update-experience",
        UpdateExperienceAPIView.as_view(),
        name="update-experience",
    ),
    path(
        "update-registration-number",
        UpdateRegistrationNumberAPIView.as_view(),
        name="update-registration-number",
    ),
    path(
        "update-specialization",
        UpdateSpecializationAPIView.as_view(),
        name="update-specialization",
    ),
    path(
        "appointments/",
        AppointmentListView.as_view(),
        name="appointments",
    ),
    path(
        "appointments/<int:pk>/",
        AppointmentDetailView.as_view(),
        name="appointment-detail",
    ),
    path(
        "appointments/<int:appointment_id>/refer/",
        ReferralCreateView.as_view(),
        name="referral-create",
    ),
    path(
        "appointments/<int:pk>/<str:action>/",
        AppointmentActionView.as_view(),
        name="appointment-action",
    ),
    path("my-patients/", MyPatientsView.as_view(), name="my-patients"),
    path("reviews/", ReviewListView.as_view(), name="reviews"),
    path(
        "my-patients/<int:patient_id>/history/",
        AppointmentHistoryView.as_view(),
        name="patient-history",
    ),
    path(
        "change-password/",
        DoctorChangePasswordView.as_view(),
        name="change-password",
    ),
    path(
        "appointment/<int:booking_id>/prescription/add/",
        PrescriptionCreateView.as_view(),
        name="prescription-create",
    ),
    path(
        "prescription/<int:pk>/",
        PrescriptionDetailView.as_view(),
        name="prescription-detail",
    ),
    path(
        "dept/dashboard/",
        DepartmentQueueView.as_view(),
        name="dept-dashboard",
    ),
    path(
        "dept/referral/<int:referral_id>/",
        ReferralResultView.as_view(),
        name="dept-referral",
    ),
]
