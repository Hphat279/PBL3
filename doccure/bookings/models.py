from django.db import models
from django.conf import settings
from ckeditor.fields import RichTextField


class Booking(models.Model):
    """Lịch hẹn đặt online – bệnh nhân đặt lịch khám qua website."""

    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="appointments",
        limit_choices_to={"role": "doctor"},
        verbose_name="Bác sĩ",
    )
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="patient_appointments",
        limit_choices_to={"role": "patient"},
        verbose_name="Bệnh nhân",
    )
    appointment_date = models.DateField(verbose_name="Ngày hẹn")
    appointment_time = models.TimeField(verbose_name="Giờ hẹn")
    booking_date = models.DateTimeField(auto_now_add=True, verbose_name="Ngày đặt lịch")
    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Chờ duyệt"),
            ("confirmed", "Đã xác nhận"),
            ("completed", "Hoàn thành"),
            ("cancelled", "Đã hủy"),
            ("no_show", "Vắng mặt"),
        ],
        default="pending",
        verbose_name="Trạng thái",
    )

    class Meta:
        ordering = ["-appointment_date", "-appointment_time"]
        # Ensure no double bookings for same doctor at same time
        unique_together = ["doctor", "appointment_date", "appointment_time"]
        verbose_name = "Lịch hẹn online"
        verbose_name_plural = "Lịch hẹn online"

    def __str__(self):
        return f"Lịch hẹn với BS. {self.doctor.get_full_name()} ngày {self.appointment_date} lúc {self.appointment_time}"


class Prescription(models.Model):
    """Đơn thuốc online – bác sĩ kê sau khi khám xong."""

    booking = models.OneToOneField(
        "Booking", on_delete=models.CASCADE, related_name="prescription",
        verbose_name="Lịch hẹn",
    )
    doctor = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="prescriptions_given",
        verbose_name="Bác sĩ kê đơn",
    )
    patient = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="prescriptions_received",
        verbose_name="Bệnh nhân",
    )
    symptoms = models.TextField(verbose_name="Triệu chứng")
    diagnosis = models.TextField(verbose_name="Chẩn đoán")
    medications = RichTextField(verbose_name="Thuốc kê đơn")
    notes = models.TextField(blank=True, verbose_name="Ghi chú")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Cập nhật lần cuối")

    def __str__(self):
        return f"Đơn thuốc cho {self.patient} bởi BS. {self.doctor}"

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Đơn thuốc online"
        verbose_name_plural = "Đơn thuốc online"
