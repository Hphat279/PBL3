from django.urls import path
from . import views

# Đăng ký namespace cho app 'pharmacy' để sử dụng khi gọi{% url 'pharmacy:xxx' %} trong template
app_name = "pharmacy"

urlpatterns = [
    # Đường dẫn trang Bảng điều khiển (Dashboard) của Dược sĩ
    path("", views.PharmacistDashboardView.as_view(), name="dashboard"),
    
    # Đường dẫn xem danh sách thuốc trong kho
    path("medicines/", views.MedicineListView.as_view(), name="medicine-list"),
    
    # Đường dẫn thêm thuốc mới vào kho
    path("medicines/add/", views.MedicineCreateView.as_view(), name="medicine-create"),
    
    # Đường dẫn chỉnh sửa thông tin thuốc có mã ID cụ thể (pk)
    path("medicines/<int:pk>/edit/", views.MedicineUpdateView.as_view(), name="medicine-update"),
    
    # Đường dẫn xem danh sách đơn thuốc cần phát/đã phát từ bác sĩ gửi xuống
    path("prescriptions/", views.PrescriptionListView.as_view(), name="prescription-list"),
    
    # Đường dẫn thực hiện phát thuốc theo mã đơn thuốc (pk)
    path("prescriptions/<int:pk>/dispense/", views.PrescriptionDispenseView.as_view(), name="prescription-dispense"),
    
    # Đường dẫn xem hóa đơn phát thuốc chi tiết đã phát thành công theo mã hóa đơn (pk)
    path("dispensations/<int:pk>/", views.DispensationDetailView.as_view(), name="dispense-detail"),
    
    # Đường dẫn đổi mật khẩu của Dược sĩ
    path("change-password/", views.PharmacistChangePasswordView.as_view(), name="change-password"),
]
