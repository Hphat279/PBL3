"""
clinic/views/medical_views.py
Views cho module Bệnh án & Dịch vụ.

Chức năng:
- Xem danh sách bệnh nhân
- Tạo / xem bệnh án
- Chỉ định dịch vụ cận lâm sàng
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.views import View

from clinic.models import (
    Patient,
    MedicalRecord,
    StaffProfile,
    ServiceCategory,
    Service,
    ServiceOrder,
)


class DanhSachBenhNhan(View):
    """
    Danh sách bệnh nhân đã đăng ký trong hệ thống.
    Có tìm kiếm theo tên / mã bệnh nhân / số điện thoại.
    """
    template_name = "clinic/benh_nhan_list.html"

    def get(self, request):
        q = request.GET.get("q", "").strip()
        benh_nhans = Patient.objects.all()

        if q:
            benh_nhans = benh_nhans.filter(
                full_name__icontains=q
            ) | benh_nhans.filter(
                patient_code__icontains=q
            ) | benh_nhans.filter(
                phone__icontains=q
            )

        benh_nhans = benh_nhans.order_by("-created_at")
        context = {
            "benh_nhans": benh_nhans,
            "q": q,
            "tong_so": benh_nhans.count(),
        }
        return render(request, self.template_name, context)


class ThemBenhNhan(View):
    """Thêm bệnh nhân mới vào hệ thống."""
    template_name = "clinic/benh_nhan_them.html"

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        from django.utils import timezone

        # Tự sinh mã bệnh nhân: BN + năm + số thứ tự
        nam = timezone.now().year
        so_thu_tu = Patient.objects.filter(
            patient_code__startswith=f"BN{nam}"
        ).count() + 1
        patient_code = f"BN{nam}{so_thu_tu:04d}"

        try:
            Patient.objects.create(
                patient_code=patient_code,
                full_name=request.POST.get("full_name"),
                gender=request.POST.get("gender"),
                birthday=request.POST.get("birthday"),
                phone=request.POST.get("phone"),
                address=request.POST.get("address", ""),
                blood_type=request.POST.get("blood_type", ""),
                allergy_history=request.POST.get("allergy_history", ""),
            )
            messages.success(request, f"Đã thêm bệnh nhân với mã {patient_code}!")
            return redirect("clinic:benh-nhan")
        except Exception as e:
            messages.error(request, f"Lỗi: {str(e)}")
            return render(request, self.template_name, {"post_data": request.POST})


class BenhAnView(View):
    """
    Tạo / xem bệnh án cho một cuộc khám.
    Gồm 3 tab:
      - Tab 1: Thông tin khám bệnh (triệu chứng, chẩn đoán, hướng điều trị)
      - Tab 2: Cận lâm sàng (danh sách dịch vụ đã chỉ định + kết quả)
      - Tab 3: Kê đơn thuốc (link sang pharmacy)
    """
    template_name = "clinic/benh_an.html"

    def get(self, request, patient_id):
        benh_nhan = get_object_or_404(Patient, pk=patient_id)
        # Lấy bệnh án mới nhất (hoặc tạo mới nếu chưa có)
        benh_ans = MedicalRecord.objects.filter(
            patient=benh_nhan
        ).select_related("doctor").order_by("-visit_date")

        # Danh mục dịch vụ để chỉ định
        danh_muc_dv = ServiceCategory.objects.prefetch_related("services").all()

        context = {
            "benh_nhan": benh_nhan,
            "benh_ans": benh_ans,
            "benh_an_hien_tai": benh_ans.first(),
            "danh_muc_dv": danh_muc_dv,
        }
        return render(request, self.template_name, context)


class TaoBenhAn(View):
    """Tạo bệnh án mới cho bệnh nhân."""

    def post(self, request, patient_id):
        benh_nhan = get_object_or_404(Patient, pk=patient_id)
        doctor_id = request.POST.get("doctor_id")

        benh_an = MedicalRecord.objects.create(
            patient=benh_nhan,
            doctor_id=doctor_id,
            symptoms=request.POST.get("symptoms", ""),
            initial_diagnosis=request.POST.get("initial_diagnosis", ""),
            final_diagnosis=request.POST.get("final_diagnosis", ""),
            treatment_plan=request.POST.get("treatment_plan", ""),
            notes=request.POST.get("notes", ""),
        )
        messages.success(request, f"Đã tạo bệnh án #{benh_an.pk}!")
        return redirect("clinic:benh-an", patient_id=patient_id)


class ChiDinhDichVu(View):
    """
    Chỉ định dịch vụ cận lâm sàng cho một bệnh án.
    Ví dụ: Xét nghiệm máu, Siêu âm bụng, X-quang ngực…
    """

    def post(self, request, record_id):
        benh_an = get_object_or_404(MedicalRecord, pk=record_id)
        service_id = request.POST.get("service_id")

        ServiceOrder.objects.create(
            medical_record=benh_an,
            service_id=service_id,
            status="pending",
        )
        messages.success(request, "Đã chỉ định dịch vụ thành công!")
        return redirect("clinic:benh-an", patient_id=benh_an.patient_id)
