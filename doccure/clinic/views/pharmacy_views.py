"""
clinic/views/pharmacy_views.py
Views cho module Kê đơn thuốc (Pharmacy).

Chức năng:
- Xem / tạo đơn thuốc cho bệnh án
- Tìm kiếm thuốc trong kho
- Thêm / xóa thuốc khỏi đơn
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.views import View

from clinic.models import (
    MedicalRecord,
    Medicine,
    ClinicPrescription,
    PrescriptionItem,
)


class KeDon(View):
    """
    Kê đơn thuốc cho một bệnh án.
    Tự động tạo đơn thuốc nếu chưa có.
    """
    template_name = "clinic/ke_don.html"

    def get(self, request, record_id):
        benh_an = get_object_or_404(
            MedicalRecord.objects.select_related("patient", "doctor"),
            pk=record_id,
        )
        # Lấy hoặc tạo đơn thuốc
        don_thuoc, _ = ClinicPrescription.objects.get_or_create(
            medical_record=benh_an
        )
        # Danh sách thuốc trong đơn
        chi_tiet = don_thuoc.items.select_related("medicine").all()

        context = {
            "benh_an": benh_an,
            "don_thuoc": don_thuoc,
            "chi_tiet": chi_tiet,
            "tong_tien": don_thuoc.tong_tien,
        }
        return render(request, self.template_name, context)


class ThemThuocVaoDon(View):
    """
    Thêm một dòng thuốc vào đơn.
    POST: prescription_id, medicine_id, quantity, dosage, instructions
    """

    def post(self, request, prescription_id):
        don_thuoc = get_object_or_404(ClinicPrescription, pk=prescription_id)
        medicine_id = request.POST.get("medicine_id")
        quantity = int(request.POST.get("quantity", 1))

        # Kiểm tra tồn kho
        thuoc = get_object_or_404(Medicine, pk=medicine_id)
        if not thuoc.con_hang:
            messages.warning(request, f"Thuốc '{thuoc.medicine_name}' đã hết hàng!")
            return redirect("clinic:ke-don", record_id=don_thuoc.medical_record_id)

        PrescriptionItem.objects.create(
            prescription=don_thuoc,
            medicine=thuoc,
            quantity=quantity,
            dosage=request.POST.get("dosage", ""),
            instructions=request.POST.get("instructions", ""),
        )
        messages.success(request, f"Đã thêm {thuoc.medicine_name} vào đơn thuốc!")
        return redirect("clinic:ke-don", record_id=don_thuoc.medical_record_id)


class XoaThuocKhoiDon(View):
    """Xóa một dòng thuốc khỏi đơn."""

    def post(self, request, item_id):
        item = get_object_or_404(PrescriptionItem, pk=item_id)
        record_id = item.prescription.medical_record_id
        item.delete()
        messages.success(request, "Đã xóa thuốc khỏi đơn!")
        return redirect("clinic:ke-don", record_id=record_id)


class TimKiemThuoc(View):
    """
    API tìm kiếm thuốc theo tên (dùng AJAX / HTMX).
    Trả về JSON danh sách thuốc phù hợp.
    """

    def get(self, request):
        q = request.GET.get("q", "").strip()
        thuocs = []
        if q:
            thuocs = Medicine.objects.filter(
                medicine_name__icontains=q
            ).filter(
                stock_quantity__gt=0  # Chỉ lấy thuốc còn hàng
            ).values("id", "medicine_name", "unit", "price", "stock_quantity")[:10]

        return JsonResponse({"thuocs": list(thuocs)})
