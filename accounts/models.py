from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from django.db.models import Avg
import math

from accounts.managers import CustomUserManager
from utils.file_utils import (
    profile_photo_directory_path,
)


class  User(AbstractUser):
    """
    Custom user model with extra fields
    """

    class RoleChoices(models.TextChoices):
        DOCTOR = "doctor", "Doctor"
        PATIENT = "patient", "Patient"

    username = models.CharField(max_length=30, unique=True)
    role = models.CharField(
        choices=RoleChoices.choices,
        max_length=20,
        default="patient",
        error_messages={"required": "Role must be provided"},
    )
    email = models.EmailField(
        blank=True,
        error_messages={
            "unique": "A user with that email already exists.",
        },
    )
    # provider indicates how this account was created (e.g. 'google', 'local')
    provider = models.CharField(max_length=32, blank=True, null=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    registration_number = models.IntegerField(null=True, blank=True)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __unicode__(self):
        return self.username

    class Meta:
        verbose_name = "Người dùng"
        verbose_name_plural = "Người dùng"

    def get_full_name(self):
        """
        Return the first_name plus the last_name, with a space in between.
        """
        full_name = "%s %s" % (self.first_name, self.last_name)
        return full_name.strip() or self.username

    def get_doctor_profile(self):
        """
        Return doctor profile URL
        """
        return reverse(
            "doctors:doctor-profile", kwargs={"username": self.username}
        )

    @property
    def rating(self):
        # Return the average rating as a float (used for display decisions).
        try:
            return float(self.average_rating)
        except Exception:
            return 0.0

    @property
    def average_rating(self):
        # If there are no reviews, default new doctors to 4.5 stars.
        try:
            avg = self.reviews_received.aggregate(Avg("rating"))["rating__avg"]
            if avg is None:
                return 4.5
            return float(avg)
        except Exception:
            return 4.5

    @property
    def has_half_star(self):
        try:
            avg = float(self.average_rating)
            frac = avg - int(avg)
            return frac >= 0.5
        except Exception:
            return False

    @property
    def full_stars(self):
        try:
            return int(math.floor(float(self.average_rating)))
        except Exception:
            return 4

    @property
    def rating_count(self):
        return self.reviews_received.count()

    @property
    def rating_distribution(self):
        distribution = {i: 0 for i in range(1, 6)}
        for rating in self.reviews_received.values_list("rating", flat=True):
            distribution[rating] += 1
        return distribution

    @property
    def pending_appointments_count(self):
        try:
            return self.appointments.filter(status="pending").count()
        except Exception:
            return 0

    @property
    def new_reviews_count(self):
        try:
            if self.last_login:
                return self.reviews_received.filter(created_at__gt=self.last_login).count()
            return self.reviews_received.count()
        except Exception:
            return 0


class Profile(models.Model):
    """
    User profile
    """

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="profile"
    )
    avatar = models.ImageField(
        default="defaults/user.png", upload_to=profile_photo_directory_path
    )
    # optional remote avatar URL (from social providers)
    avatar_url = models.URLField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    dob = models.DateField(blank=True, null=True)
    about = models.TextField(blank=True, null=True)
    specialization = models.CharField(max_length=255, blank=True, null=True)
    gender = models.CharField(
        max_length=10,
        choices=[("male", "Nam"), ("female", "Nữ"), ("other", "Khác")],
        blank=True,
    )
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True)
    price_per_consultation = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    is_available = models.BooleanField(default=True)
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
    )
    allergies = models.TextField(blank=True, null=True)
    medical_conditions = models.TextField(blank=True, null=True)

    def __str__(self):
        return "Profile of {}".format(self.user.username)

    class Meta:
        verbose_name = "Hồ sơ"
        verbose_name_plural = "Hồ sơ"

    @property
    def image(self):
        return (
            self.avatar.url
            if self.avatar.storage.exists(self.avatar.name)
            else "{}defaults/user.png".format(settings.MEDIA_URL)
        )


class GoogleVerification(models.Model):
    """
    Simple model to store email verification codes for the mock Google flow.
    """
    email = models.EmailField()
    code = models.CharField(max_length=8)
    created_at = models.DateTimeField(auto_now_add=True)
    used = models.BooleanField(default=False)

    def __str__(self):
        return f"GoogleVerification({self.email} - {self.code})"
