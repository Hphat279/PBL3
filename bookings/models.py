from django.db import models
from django.conf import settings
from ckeditor.fields import RichTextField


class Booking(models.Model):
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="appointments",
        limit_choices_to={"role": "doctor"},
    )
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="patient_appointments",
        limit_choices_to={"role": "patient"},
    )
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    booking_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("confirmed", "Confirmed"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
            ("no_show", "No Show"),
        ],
        default="pending",
    )

    class Meta:
        ordering = ["-appointment_date", "-appointment_time"]
        # Ensure no double bookings for same doctor at same time
        unique_together = ["doctor", "appointment_date", "appointment_time"]
        verbose_name = "Lịch khám"
        verbose_name_plural = "Lịch khám"

    def __str__(self):
        return f"Appointment with Dr. {self.doctor.get_full_name()} on {self.appointment_date} at {self.appointment_time}"


class Prescription(models.Model):
    booking = models.OneToOneField(
        "Booking", on_delete=models.CASCADE, related_name="prescription"
    )
    doctor = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="prescriptions_given",
    )
    patient = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="prescriptions_received",
    )
    symptoms = models.TextField()
    diagnosis = models.TextField()
    medications = RichTextField()
    notes = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Chờ phát thuốc"),
            ("dispensed", "Đã phát thuốc"),
        ],
        default="pending",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Prescription for {self.patient} by Dr. {self.doctor}"

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Đơn thuốc"
        verbose_name_plural = "Đơn thuốc"


class PrescriptionMedicine(models.Model):
    prescription = models.ForeignKey(
        Prescription, on_delete=models.CASCADE, related_name="medicines"
    )
    medicine = models.ForeignKey(
        "pharmacy.Medicine", on_delete=models.CASCADE
    )
    quantity = models.PositiveIntegerField(default=1, verbose_name="Số lượng/ngày")
    dosage = models.CharField(max_length=100, blank=True, verbose_name="Liều dùng")
    frequency = models.CharField(max_length=100, blank=True, verbose_name="Tần suất")
    duration = models.CharField(max_length=100, blank=True, verbose_name="Thời gian dùng")
    instructions = models.TextField(blank=True, verbose_name="Hướng dẫn")

    class Meta:
        verbose_name = "Thuốc trong đơn"
        verbose_name_plural = "Thuốc trong đơn"

    def __str__(self):
        return f"{self.medicine.name} x{self.quantity}"


class Referral(models.Model):
    booking = models.ForeignKey(
        Booking, on_delete=models.CASCADE, related_name="referrals"
    )
    department = models.ForeignKey(
        "core.Department", on_delete=models.CASCADE, related_name="referrals"
    )
    general_doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="referrals_given",
    )
    reason = models.TextField(blank=True)
    result = models.TextField(blank=True)
    result_data = models.JSONField(blank=True, default=dict)
    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Chờ"),
            ("in_progress", "Đang khám"),
            ("completed", "Hoàn thành"),
        ],
        default="pending",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Chỉ định chuyên khoa"
        verbose_name_plural = "Chỉ định chuyên khoa"

    def __str__(self):
        return f"{self.department.name} — {self.booking.patient}"
