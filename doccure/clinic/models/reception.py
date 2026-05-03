"""
clinic/models/reception.py
Nhóm 3: Tiếp nhận & Chỉ số sinh tồn (.
"""

from django.db import models
from clinic.models.hr import Patient, StaffProfile


class Appointment(models.Model):
    """
    Bảng `appointments` 
    Trạng thái: scheduled → confirmed → completed / cancelled
    """
    class TrangThai(models.TextChoices):
        CHO_KHAM = "scheduled", "Chờ khám"
        DA_XAC_NHAN = "confirmed", "Đã xác nhận"
        HOAN_THANH = "completed", "Hoàn thành"
        HUY = "cancelled", "Đã hủy"

    patient = models.ForeignKey(
        Patient,
        on_delete=models.PROTECT,
        related_name="appointments",
        verbose_name="Bệnh nhân",
    )
    doctor = models.ForeignKey(
        StaffProfile,
        on_delete=models.PROTECT,
        related_name="appointments",
        verbose_name="Bác sĩ phụ trách",
    )
    appointment_date = models.DateTimeField(verbose_name="Ngày & giờ hẹn")
    reason = models.TextField(
        blank=True,
        null=True,
        verbose_name="Lý do khám",
    )
    status = models.CharField(
        max_length=20,
        choices=TrangThai.choices,
        default=TrangThai.CHO_KHAM,
        verbose_name="Trạng thái",
    )

    class Meta:
        db_table = "clinic_appointments"
        verbose_name = "Lịch hẹn"
        verbose_name_plural = "Lịch hẹn"
        ordering = ["appointment_date"]

    def __str__(self):
        return f"#{self.pk} – {self.patient.full_name} ({self.appointment_date:%d/%m/%Y %H:%M})"


class VitalSigns(models.Model):
    """
    Bảng `vital_signs` 
    Mỗi lịch hẹn chỉ có 1 bộ chỉ số sinh tồn (OneToOne).
    Gồm: cân nặng, chiều cao, thân nhiệt, nhịp tim, huyết áp.
    """
    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.CASCADE,
        related_name="vital_signs",
        verbose_name="Lịch hẹn",
    )
    # Cân nặng (kg) – ví dụ: 65.50
    weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Cân nặng (kg)",
    )
    # Chiều cao (cm) – ví dụ: 170.00
    height = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Chiều cao (cm)",
    )
    # Thân nhiệt (°C) – ví dụ: 36.8
    temperature = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        blank=True,
        null=True,
        verbose_name="Thân nhiệt (°C)",
    )
    # Nhịp tim (lần/phút)
    heart_rate = models.IntegerField(
        blank=True,
        null=True,
        verbose_name="Nhịp tim (lần/phút)",
    )
    # Huyết áp – ví dụ: "120/80"
    blood_pressure = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Huyết áp (mmHg)",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Thời điểm ghi")

    class Meta:
        db_table = "vital_signs"
        verbose_name = "Chỉ số sinh tồn"
        verbose_name_plural = "Chỉ số sinh tồn"

    def __str__(self):
        return f"Sinh tồn – Lịch hẹn #{self.appointment_id}"

    @property
    def bmi(self):
        """Tính BMI nếu có đủ cân nặng và chiều cao"""
        if self.weight and self.height and self.height > 0:
            h_m = float(self.height) / 100
            return round(float(self.weight) / (h_m ** 2), 1)
        return None
