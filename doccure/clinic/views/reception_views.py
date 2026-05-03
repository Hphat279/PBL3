"""
clinic/views/reception_views.py
Views cho module Tiếp nhận bệnh nhân.

Chức năng:
- Xem hàng đợi bệnh nhân hôm nay
- Tạo lịch hẹn mới
- Nhập chỉ số sinh tồn (cân nặng, chiều cao, nhiệt độ, huyết áp)
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.views import View

from clinic.models import Appointment, VitalSigns, Patient, StaffProfile


class HangDoiHomNay(View):
    """
    Hiển thị danh sách bệnh nhân chờ khám hôm nay.
    Lọc theo ngày hiện tại và sắp xếp theo giờ hẹn.
    """
    template_name = "clinic/tiep_nhan.html"

    def get(self, request):
        hom_nay = timezone.now().date()
        # Lấy tất cả lịch hẹn hôm nay (chưa hủy)
        hang_doi = Appointment.objects.filter(
            appointment_date__date=hom_nay,
        ).exclude(
            status="cancelled"
        ).select_related("patient", "doctor").order_by("appointment_date")

        context = {
            "hang_doi": hang_doi,
            "ngay_hom_nay": hom_nay,
            "tong_so": hang_doi.count(),
            "cho_kham": hang_doi.filter(status="scheduled").count(),
            "da_kham": hang_doi.filter(status="completed").count(),
        }
        return render(request, self.template_name, context)


class TaoLichHen(View):
    """
    Tạo lịch hẹn mới cho bệnh nhân.
    """
    template_name = "clinic/tiep_nhan_them.html"

    def get(self, request):
        benh_nhans = Patient.objects.all().order_by("full_name")
        bac_sis = StaffProfile.objects.all().order_by("full_name")
        context = {
            "benh_nhans": benh_nhans,
            "bac_sis": bac_sis,
        }
        return render(request, self.template_name, context)

    def post(self, request):
        patient_id = request.POST.get("patient_id")
        doctor_id = request.POST.get("doctor_id")
        appointment_date = request.POST.get("appointment_date")
        reason = request.POST.get("reason", "")

        try:
            appointment = Appointment.objects.create(
                patient_id=patient_id,
                doctor_id=doctor_id,
                appointment_date=appointment_date,
                reason=reason,
                status="scheduled",
            )
            messages.success(request, f"Đã tạo lịch hẹn #{appointment.pk} thành công!")
            return redirect("clinic:tiep-nhan")
        except Exception as e:
            messages.error(request, f"Lỗi khi tạo lịch hẹn: {str(e)}")
            return redirect("clinic:tao-lich-hen")


class NhapSinhHieu(View):
    """
    Nhập hoặc cập nhật chỉ số sinh tồn cho một lịch hẹn.
    Được thực hiện bởi điều dưỡng trước khi bệnh nhân vào khám.
    """
    template_name = "clinic/sinh_hieu.html"

    def get(self, request, appointment_id):
        appointment = get_object_or_404(
            Appointment.objects.select_related("patient", "doctor"),
            pk=appointment_id,
        )
        # Nếu đã có sinh hiệu thì load lên form để cập nhật
        sinh_hieu = getattr(appointment, "vital_signs", None)
        context = {
            "appointment": appointment,
            "sinh_hieu": sinh_hieu,
        }
        return render(request, self.template_name, context)

    def post(self, request, appointment_id):
        appointment = get_object_or_404(Appointment, pk=appointment_id)

        # Lấy hoặc tạo mới bản ghi sinh hiệu
        sinh_hieu, _ = VitalSigns.objects.get_or_create(appointment=appointment)

        # Cập nhật các chỉ số
        sinh_hieu.weight = request.POST.get("weight") or None
        sinh_hieu.height = request.POST.get("height") or None
        sinh_hieu.temperature = request.POST.get("temperature") or None
        sinh_hieu.heart_rate = request.POST.get("heart_rate") or None
        sinh_hieu.blood_pressure = request.POST.get("blood_pressure") or None
        sinh_hieu.save()

        # Chuyển trạng thái lịch hẹn sang "confirmed"
        appointment.status = "confirmed"
        appointment.save()

        messages.success(request, "Đã lưu chỉ số sinh tồn thành công!")
        return redirect("clinic:tiep-nhan")
