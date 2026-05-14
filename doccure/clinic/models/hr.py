"""
clinic/models/hr.py
Nhóm 2: Nhân viên & Bệnh nhân.

- StaffProfile: Hồ sơ chuyên môn của nhân viên (liên kết accounts.User).
  Dùng cho bác sĩ, điều dưỡng, tiếp tân, dược sĩ...
- Patient: Hồ sơ bệnh nhân phòng khám — độc lập, không bắt buộc có tài khoản.
  Có thể liên kết tùy chọn với accounts.User nếu bệnh nhân có tài khoản online.
"""

from django.conf import settings
from django.db import models


class StaffProfile(models.Model):
    """
    Bảng `staff_profiles` — Hồ sơ chuyên môn nhân viên phòng khám.
    Liên kết OneToOne với accounts.User (hệ thống đăng nhập chung).
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="clinic_staff_profile",
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
    Bảng `clinic_patients` — Hồ sơ bệnh nhân phòng khám.
    Mã bệnh nhân tự sinh theo định dạng BN<năm><số thứ tự> (VD: BN20260001).

    Field `user` là tùy chọn (nullable):
    - Nếu bệnh nhân có tài khoản Doccure → liên kết vào accounts.User
    - Nếu bệnh nhân walk-in (vãng lai) → để trống (null)
    """
    class GioiTinh(models.TextChoices):
        NAM  = "male",   "Nam"
        NU   = "female", "Nữ"
        KHAC = "other",  "Khác"

    # Liên kết tùy chọn với tài khoản Doccure (nullable)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="clinic_patient_profile",
        verbose_name="Tài khoản Doccure (nếu có)",
    )

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
