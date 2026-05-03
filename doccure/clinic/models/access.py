"""
clinic/models/access.py
Quản trị & Phân quyền 
"""

from django.db import models


class Role(models.Model):
    """
    //Bảng `roles` 
     ADMIN, DOCTOR, NURSE, RECEPTIONIST, PHARMACIST
    """
    role_name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Tên vai trò",
    )
    description = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Mô tả",
    )

    class Meta:
        db_table = "roles"
        verbose_name = "Vai trò"
        verbose_name_plural = "Vai trò"

    def __str__(self):
        return self.role_name


class ClinicUser(models.Model):
    """
    Bảng `users` 
    """
    class TrangThai(models.TextChoices):
        HOAT_DONG = "active", "Hoạt động"
        KHONG_HOAT_DONG = "inactive", "Không hoạt động"
        BI_KHOA = "locked", "Bị khóa"

    username = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Tên đăng nhập",
    )
    password = models.CharField(max_length=255, verbose_name="Mật khẩu")
    email = models.CharField(max_length=100, unique=True, verbose_name="Email")
    status = models.CharField(
        max_length=10,
        choices=TrangThai.choices,
        default=TrangThai.HOAT_DONG,
        verbose_name="Trạng thái",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")

    class Meta:
        db_table = "clinic_users"
        verbose_name = "Tài khoản"
        verbose_name_plural = "Tài khoản"

    def __str__(self):
        return self.username


class UserRole(models.Model):
    """
    Bảng `user_roles` 
    """
    user = models.ForeignKey(
        ClinicUser,
        on_delete=models.CASCADE,
        related_name="user_roles",
        verbose_name="Tài khoản",
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name="user_roles",
        verbose_name="Vai trò",
    )

    class Meta:
        db_table = "user_roles"
        verbose_name = "Phân quyền"
        verbose_name_plural = "Phân quyền"
        unique_together = [("user", "role")]

    def __str__(self):
        return f"{self.user.username} → {self.role.role_name}"
