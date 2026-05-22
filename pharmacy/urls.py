from django.urls import path
from . import views

app_name = "pharmacy"

urlpatterns = [
    path("", views.PharmacistDashboardView.as_view(), name="dashboard"),
    path("medicines/", views.MedicineListView.as_view(), name="medicine-list"),
    path("medicines/add/", views.MedicineCreateView.as_view(), name="medicine-create"),
    path("medicines/<int:pk>/edit/", views.MedicineUpdateView.as_view(), name="medicine-update"),
    path("prescriptions/", views.PrescriptionListView.as_view(), name="prescription-list"),
    path("prescriptions/<int:pk>/dispense/", views.PrescriptionDispenseView.as_view(), name="prescription-dispense"),
    path("dispensations/<int:pk>/", views.DispensationDetailView.as_view(), name="dispense-detail"),
    path("change-password/", views.PharmacistChangePasswordView.as_view(), name="change-password"),
]
