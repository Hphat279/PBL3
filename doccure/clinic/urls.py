"""
clinic/urls.py
Cấu hình URL cho toàn bộ module phòng khám.

Prefix: /clinic/
"""

from django.urls import path
from clinic.views.reception_views import HangDoiHomNay, TaoLichHen, NhapSinhHieu
from clinic.views.medical_views import (
    DanhSachBenhNhan,
    ThemBenhNhan,
    BenhAnView,
    TaoBenhAn,
    ChiDinhDichVu,
)
from clinic.views.pharmacy_views import KeDon, ThemThuocVaoDon, XoaThuocKhoiDon, TimKiemThuoc
from clinic.views.billing_views import (
    DanhSachHoaDon,
    ChiTietHoaDon,
    ThanhToanHoaDon,
    TaoHoaDon,
)

app_name = "clinic"

urlpatterns = [
    # -------------------------------------------------------------------------
    # Tiếp nhận bệnh nhân
    # -------------------------------------------------------------------------
    path("tiep-nhan/", HangDoiHomNay.as_view(), name="tiep-nhan"),
    path("tiep-nhan/them/", TaoLichHen.as_view(), name="tao-lich-hen"),
    path("tiep-nhan/<int:appointment_id>/sinh-hieu/", NhapSinhHieu.as_view(), name="sinh-hieu"),

    # -------------------------------------------------------------------------
    # Bệnh nhân
    # -------------------------------------------------------------------------
    path("benh-nhan/", DanhSachBenhNhan.as_view(), name="benh-nhan"),
    path("benh-nhan/them/", ThemBenhNhan.as_view(), name="them-benh-nhan"),

    # -------------------------------------------------------------------------
    # Bệnh án
    # -------------------------------------------------------------------------
    path("benh-an/<int:patient_id>/", BenhAnView.as_view(), name="benh-an"),
    path("benh-an/<int:patient_id>/tao/", TaoBenhAn.as_view(), name="tao-benh-an"),
    path("dich-vu/<int:record_id>/chi-dinh/", ChiDinhDichVu.as_view(), name="chi-dinh-dich-vu"),

    # -------------------------------------------------------------------------
    # Kê đơn thuốc
    # -------------------------------------------------------------------------
    path("ke-don/<int:record_id>/", KeDon.as_view(), name="ke-don"),
    path("ke-don/<int:prescription_id>/them-thuoc/", ThemThuocVaoDon.as_view(), name="them-thuoc"),
    path("ke-don/xoa/<int:item_id>/", XoaThuocKhoiDon.as_view(), name="xoa-thuoc"),
    path("thuoc/tim-kiem/", TimKiemThuoc.as_view(), name="tim-thuoc"),

    # -------------------------------------------------------------------------
    # Hóa đơn & Thanh toán
    # -------------------------------------------------------------------------
    path("hoa-don/", DanhSachHoaDon.as_view(), name="hoa-don"),
    path("hoa-don/<int:invoice_id>/", ChiTietHoaDon.as_view(), name="hoa-don-chi-tiet"),
    path("hoa-don/<int:invoice_id>/thanh-toan/", ThanhToanHoaDon.as_view(), name="thanh-toan"),
    path("hoa-don/tao/<int:record_id>/", TaoHoaDon.as_view(), name="tao-hoa-don"),
]
