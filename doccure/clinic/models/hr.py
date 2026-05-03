"""
clinic/models/hr.py
 Nhân viên & Bệnh nhân 
Hồ sơ nhân viên và thông tin bệnh nhân.
"""

from django.db import models
from clinic.models.access import ClinicUser


class StaffProfile(models.Model):
    """
    Bảng `staff_profiles` .
    Mở rộng từ ClinicUser, lưu thông tin chuyên môn.
    """
    user = models.OneToOneField(
        ClinicUser,
        on_delete=models.CASCADE,
        related_name="staff_profile",
        verbose_name="Tài khoản",
    )
    full_name = models.CharField(max_length=100, verbose_name="Họ và tên")
    specialty = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Chuyên khoa",
    )
    phone = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        verbose_name="Số điện thoại",
    )
    certificate_code = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Chứng chỉ hành nghề",
    )

    class Meta:
        db_table = "staff_profiles"
        verbose_name = "Hồ sơ nhân viên"
        verbose_name_plural = "Hồ sơ nhân viên"

    def __str__(self):
        return self.full_name


class Patient(models.Model):
    """
    Bảng `patients` .
    Mã bệnh nhân tự sinh theo định dạng BN2026xxxx.
    """
    class GioiTinh(models.TextChoices):
        NAM = "male", "Nam"
        NU = "female", "Nữ"
        KHAC = "other", "Khác"

    # Mã bệnh nhân: BN2026xxxx
    patient_code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Mã bệnh nhân",
    )
    full_name = models.CharField(max_length=100, verbose_name="Họ và tên")
    gender = models.CharField(
        max_length=10,
        choices=GioiTinh.choices,
        blank=True,
        null=True,
        verbose_name="Giới tính",
    )
    birthday = models.DateField(verbose_name="Ngày sinh")
    phone = models.CharField(max_length=15, verbose_name="Số điện thoại")
    address = models.TextField(blank=True, null=True, verbose_name="Địa chỉ")
    blood_type = models.CharField(
        max_length=5,
        blank=True,
        null=True,
        verbose_name="Nhóm máu",
    )
    allergy_history = models.TextField(
        blank=True,
        null=True,
        verbose_name="Tiền sử dị ứng",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày đăng ký")

    class Meta:
        db_table = "clinic_patients"
        verbose_name = "Bệnh nhân"
        verbose_name_plural = "Bệnh nhân"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.patient_code} – {self.full_name}"

    def tuoi(self):
        """Tính tuổi bệnh nhân"""
        from django.utils import timezone
        today = timezone.now().date()
        return today.year - self.birthday.year - (
            (today.month, today.day) < (self.birthday.month, self.birthday.day)
        )
