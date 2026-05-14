from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from django.db.models import Avg

from accounts.managers import CustomUserManager
from utils.file_utils import (
    profile_photo_directory_path,
)


class User(AbstractUser):
    """
    Model người dùng tuỳ chỉnh – hệ thống đăng nhập chung cho toàn bộ Doccure.
    Vai trò (role) quyết định quyền truy cập và giao diện hiển thị.
    """

    class RoleChoices(models.TextChoices):
        DOCTOR       = "doctor",       "Bác sĩ"
        PATIENT      = "patient",      "Bệnh nhân"
        NURSE        = "nurse",        "Điều dưỡng"
        RECEPTIONIST = "receptionist", "Tiếp tân"
        PHARMACIST   = "pharmacist",   "Dược sĩ"
        ADMIN        = "admin",        "Quản trị viên"

    username = models.CharField(max_length=30, unique=True, verbose_name="Tên đăng nhập")
    role = models.CharField(
        choices=RoleChoices.choices,
        max_length=20,
        default="patient",
        error_messages={"required": "Vai trò là bắt buộc"},
        verbose_name="Vai trò",
    )
    email = models.EmailField(
        blank=True,
        error_messages={
            "unique": "Email này đã được sử dụng.",
        },
        verbose_name="Email",
    )
    first_name = models.CharField(max_length=150, blank=True, verbose_name="Họ")
    last_name = models.CharField(max_length=150, blank=True, verbose_name="Tên")
    registration_number = models.IntegerField(null=True, blank=True, verbose_name="Số đăng ký hành nghề")

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    class Meta:
        verbose_name = "Người dùng"
        verbose_name_plural = "Người dùng"

    def __unicode__(self):
        return self.username

    def get_full_name(self):
        """
        Trả về họ tên đầy đủ, nếu không có thì trả về username.
        """
        full_name = "%s %s" % (self.first_name, self.last_name)
        return full_name.strip() or self.username

    def get_doctor_profile(self):
        """
        Trả về URL hồ sơ bác sĩ.
        """
        return reverse(
            "doctors:doctor-profile", kwargs={"username": self.username}
        )

    @property
    def rating(self):
        # Implement your rating logic here
        return 4  # Default value

    @property
    def average_rating(self):
        return (
            self.reviews_received.aggregate(Avg("rating"))["rating__avg"] or 0
        )

    @property
    def rating_count(self):
        return self.reviews_received.count()

    @property
    def rating_distribution(self):
        distribution = {i: 0 for i in range(1, 6)}
        for rating in self.reviews_received.values_list("rating", flat=True):
            distribution[rating] += 1
        return distribution


class Profile(models.Model):
    """Hồ sơ chi tiết người dùng – thông tin cá nhân, y tế, địa chỉ."""

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="profile",
        verbose_name="Người dùng",
    )
    avatar = models.ImageField(
        default="defaults/user.png", upload_to=profile_photo_directory_path,
        verbose_name="Ảnh đại diện",
    )
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Số điện thoại")
    dob = models.DateField(blank=True, null=True, verbose_name="Ngày sinh")
    about = models.TextField(blank=True, null=True, verbose_name="Giới thiệu")
    specialization = models.CharField(max_length=255, blank=True, null=True, verbose_name="Chuyên khoa")
    gender = models.CharField(
        max_length=10,
        choices=[("male", "Nam"), ("female", "Nữ"), ("other", "Khác")],
        blank=True,
        verbose_name="Giới tính",
    )
    address = models.TextField(blank=True, null=True, verbose_name="Địa chỉ")
    city = models.CharField(max_length=100, blank=True, verbose_name="Thành phố")
    state = models.CharField(max_length=100, blank=True, verbose_name="Tỉnh/Bang")
    postal_code = models.CharField(max_length=20, blank=True, verbose_name="Mã bưu điện")
    country = models.CharField(max_length=100, blank=True, verbose_name="Quốc gia")
    price_per_consultation = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        verbose_name="Giá khám (VNĐ)",
    )
    is_available = models.BooleanField(default=True, verbose_name="Đang hoạt động")
    blood_group = models.CharField(
        max_length=5,
        choices=[
            ("A+", "A+"),
            ("A-", "A-"),
            ("B+", "B+"),
            ("B-", "B-"),
            ("O+", "O+"),
            ("O-", "O-"),
            ("AB+", "AB+"),
            ("AB-", "AB-"),
        ],
        blank=True,
        null=True,
        verbose_name="Nhóm máu",
    )
    allergies = models.TextField(blank=True, null=True, verbose_name="Dị ứng")
    medical_conditions = models.TextField(blank=True, null=True, verbose_name="Bệnh nền")

    class Meta:
        verbose_name = "Hồ sơ"
        verbose_name_plural = "Hồ sơ"

    def __str__(self):
        return "Hồ sơ của {}".format(self.user.username)

    @property
    def image(self):
        return (
            self.avatar.url
            if self.avatar.storage.exists(self.avatar.name)
            else "{}defaults/user.png".format(settings.MEDIA_URL)
        )
