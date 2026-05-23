from django.contrib import admin
from .models import Medicine, PrescriptionDispensation, PrescriptionDispensationItem


class PrescriptionDispensationItemInline(admin.TabularInline):
    
    model = PrescriptionDispensationItem
    extra = 0  # Không hiển thị sẵn các dòng trống thừa
    raw_id_fields = ["medicine"]  # Sử dụng ô nhập ID thuốc (thay vì dropdown) để tối ưu hiệu suất khi kho có hàng nghìn thuốc


@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    """
    Cấu hình hiển thị và quản lý danh sách Thuốc 
    """
    list_display = ["sku", "name", "unit", "quantity", "price", "is_active"]  # Các cột hiển thị ngoài danh sách
    list_filter = ["is_active"]  # Bộ lọc nhanh theo trạng thái hoạt động bên cột phải
    search_fields = ["sku", "name"]  # Ô tìm kiếm hỗ trợ tìm theo SKU hoặc Tên thuốc


@admin.register(PrescriptionDispensation)
class PrescriptionDispensationAdmin(admin.ModelAdmin):
    """
    Cấu hình hiển thị và quản lý Phiếu phát thuốc 
    """
    list_display = ["prescription", "pharmacist", "dispensed_at", "total_cost"]  # Các cột thông tin chính
    list_filter = ["dispensed_at"]  # Bộ lọc nhanh theo ngày phát thuốc
    search_fields = [
        "prescription__patient__username",
        "prescription__patient__first_name",
        "prescription__patient__last_name",
        "pharmacist__username",
    ]  # Tìm kiếm nhanh theo tên bệnh nhân hoặc dược sĩ
    inlines = [PrescriptionDispensationItemInline]  # Tích hợp chi tiết các dòng thuốc phát lồng bên trong phiếu phát thuốc
