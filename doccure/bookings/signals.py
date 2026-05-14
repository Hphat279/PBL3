"""
bookings/signals.py
Tín hiệu đồng bộ: Khi tạo / cập nhật Booking online → tự động đồng bộ
vào hệ thống phòng khám (clinic.Appointment, clinic.Patient).

Luồng xử lý:
  1. Bệnh nhân đặt lịch online → tạo bookings.Booking
  2. Signal bắt sự kiện post_save trên Booking
  3. Tự động tạo clinic.Patient (nếu chưa có) cho bệnh nhân online
  4. Tự động tạo clinic.StaffProfile (nếu chưa có) cho bác sĩ
  5. Tự động tạo clinic.Appointment liên kết với Booking
  6. Khi cập nhật status Booking → đồng bộ status Appointment
"""

import logging
from datetime import datetime

from django.db.models.signals import post_save
from django.dispatch import receiver

from bookings.models import Booking

logger = logging.getLogger(__name__)

# Bảng ánh xạ trạng thái: bookings.Booking → clinic.Appointment
STATUS_MAP = {
    "pending":   "scheduled",
    "confirmed": "confirmed",
    "completed": "completed",
    "cancelled": "cancelled",
    "no_show":   "cancelled",
}


@receiver(post_save, sender=Booking)
def sync_booking_to_clinic(sender, instance, created, **kwargs):
    """
    Khi Booking được tạo hoặc cập nhật → đồng bộ sang hệ thống clinic.
    """
    # Import tại đây để tránh circular import
    from clinic.models import Patient, StaffProfile, Appointment

    booking = instance

    if created:
        # --- Bước 1: Tạo hoặc lấy clinic.Patient ---
        clinic_patient, patient_created = Patient.objects.get_or_create(
            user=booking.patient,
            defaults={
                "patient_code": _generate_patient_code(),
                "full_name": booking.patient.get_full_name(),
                "gender": getattr(booking.patient.profile, "gender", None) or "",
                "birthday": getattr(booking.patient.profile, "dob", None) or "2000-01-01",
                "phone": getattr(booking.patient.profile, "phone", None) or "",
                "address": getattr(booking.patient.profile, "address", None) or "",
            },
        )
        if patient_created:
            logger.info(
                f"[SYNC] Tạo clinic.Patient '{clinic_patient.patient_code}' "
                f"cho user '{booking.patient.username}'"
            )

        # --- Bước 2: Tạo hoặc lấy clinic.StaffProfile cho bác sĩ ---
        staff_profile, staff_created = StaffProfile.objects.get_or_create(
            user=booking.doctor,
            defaults={
                "full_name": booking.doctor.get_full_name(),
                "specialty": getattr(booking.doctor.profile, "specialization", None) or "",
                "phone": getattr(booking.doctor.profile, "phone", None) or "",
            },
        )
        if staff_created:
            logger.info(
                f"[SYNC] Tạo clinic.StaffProfile cho bác sĩ '{booking.doctor.username}'"
            )

        # --- Bước 3: Tạo clinic.Appointment ---
        appointment_date = datetime.combine(
            booking.appointment_date, booking.appointment_time
        )
        Appointment.objects.create(
            patient=clinic_patient,
            doctor=staff_profile,
            appointment_date=appointment_date,
            reason=f"Đặt lịch online (Booking #{booking.pk})",
            status=STATUS_MAP.get(booking.status, "scheduled"),
            booking=booking,
        )
        logger.info(
            f"[SYNC] Tạo clinic.Appointment từ Booking #{booking.pk}"
        )

    else:
        # --- Cập nhật: Đồng bộ status ---
        try:
            appointment = Appointment.objects.get(booking=booking)
            new_status = STATUS_MAP.get(booking.status)
            if new_status and appointment.status != new_status:
                appointment.status = new_status
                appointment.save(update_fields=["status"])
                logger.info(
                    f"[SYNC] Cập nhật status clinic.Appointment #{appointment.pk} "
                    f"→ '{new_status}' (từ Booking #{booking.pk})"
                )
        except Appointment.DoesNotExist:
            pass  # Booking cũ không có Appointment tương ứng, bỏ qua


def _generate_patient_code():
    """Sinh mã bệnh nhân dạng BN2026xxxx."""
    from django.utils import timezone
    from clinic.models import Patient

    nam = timezone.now().year
    so_thu_tu = Patient.objects.filter(
        patient_code__startswith=f"BN{nam}"
    ).count() + 1
    return f"BN{nam}{so_thu_tu:04d}"
