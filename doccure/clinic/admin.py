from django.contrib import admin

from clinic.models import (
    Role,
    ClinicUser,
    UserRole,
    StaffProfile,
    Patient,
    Appointment,
    VitalSigns,
    MedicalRecord,
    ServiceCategory,
    Service,
    ServiceOrder,
    Medicine,
    ClinicPrescription,
    PrescriptionItem,
    Invoice,
    Payment,
)


# ---------------------------------------------------------------------------
# Inline helpers
# ---------------------------------------------------------------------------

class UserRoleInline(admin.TabularInline):
    model = UserRole
    extra = 1


class VitalSignsInline(admin.StackedInline):
    model = VitalSigns
    extra = 0


class ServiceOrderInline(admin.TabularInline):
    model = ServiceOrder
    extra = 0


class PrescriptionItemInline(admin.TabularInline):
    model = PrescriptionItem
    extra = 1


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0


# ---------------------------------------------------------------------------
# Model admins
# ---------------------------------------------------------------------------

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("id", "role_name", "description")
    search_fields = ("role_name",)


@admin.register(ClinicUser)
class ClinicUserAdmin(admin.ModelAdmin):
    list_display = ("id", "username", "email", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("username", "email")
    inlines = [UserRoleInline]


@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "full_name", "specialty", "phone", "certificate_code")
    search_fields = ("full_name", "specialty")


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("id", "patient_code", "full_name", "gender", "birthday", "phone")
    search_fields = ("patient_code", "full_name", "phone")
    list_filter = ("gender", "blood_type")


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "doctor", "appointment_date", "status")
    list_filter = ("status",)
    search_fields = ("patient__full_name", "doctor__full_name")
    inlines = [VitalSignsInline]


@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "doctor", "visit_date")
    search_fields = ("patient__full_name", "doctor__full_name")
    inlines = [ServiceOrderInline]


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name")


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("id", "service_name", "category", "price", "is_active")
    list_filter = ("category", "is_active")
    search_fields = ("service_name",)


@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ("id", "medicine_name", "active_ingredient", "unit", "stock_quantity", "price")
    search_fields = ("medicine_name", "active_ingredient")


@admin.register(ClinicPrescription)
class ClinicPrescriptionAdmin(admin.ModelAdmin):
    list_display = ("id", "medical_record", "created_at")
    inlines = [PrescriptionItemInline]


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "total_amount", "discount", "final_amount", "payment_status", "created_at")
    list_filter = ("payment_status",)
    search_fields = ("patient__full_name",)
    inlines = [PaymentInline]
