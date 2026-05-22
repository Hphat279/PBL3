from django.contrib import admin
from .models import Medicine, PrescriptionDispensation, PrescriptionDispensationItem


class PrescriptionDispensationItemInline(admin.TabularInline):
    model = PrescriptionDispensationItem
    extra = 0
    raw_id_fields = ["medicine"]


@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ["sku", "name", "unit", "quantity", "price", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["sku", "name"]


@admin.register(PrescriptionDispensation)
class PrescriptionDispensationAdmin(admin.ModelAdmin):
    list_display = ["prescription", "pharmacist", "dispensed_at", "total_cost"]
    list_filter = ["dispensed_at"]
    search_fields = [
        "prescription__patient__username",
        "prescription__patient__first_name",
        "prescription__patient__last_name",
        "pharmacist__username",
    ]
    inlines = [PrescriptionDispensationItemInline]
