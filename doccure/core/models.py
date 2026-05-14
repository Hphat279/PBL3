from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Speciality(models.Model):
    """Chuyên khoa – phân loại bác sĩ theo lĩnh vực chuyên môn."""

    name = models.CharField(max_length=255, unique=True, verbose_name="Tên chuyên khoa")
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField(null=True, blank=True, verbose_name="Mô tả")
    image = models.ImageField(upload_to="specialities/", null=True, blank=True, verbose_name="Hình ảnh")
    is_active = models.BooleanField(default=True, verbose_name="Đang hoạt động")

    class Meta:
        verbose_name = "Chuyên khoa"
        verbose_name_plural = "Chuyên khoa"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("doctors:list") + f"?speciality={self.slug}"

    @property
    def doctor_count(self):
        return self.doctor_set.filter(is_active=True).count()

    @property
    def image_url(self):
        if self.image:
            return self.image.url
        return "/static/assets/img/specialities/default.png"


class Review(models.Model):
    """Đánh giá – bệnh nhân đánh giá bác sĩ sau khi khám."""

    RATING_CHOICES = (
        (1, "1"),
        (2, "2"),
        (3, "3"),
        (4, "4"),
        (5, "5"),
    )

    patient = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, related_name="reviews_given",
        verbose_name="Bệnh nhân",
    )
    doctor = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="reviews_received",
        verbose_name="Bác sĩ",
    )
    booking = models.OneToOneField(
        "bookings.Booking", on_delete=models.CASCADE,
        verbose_name="Lịch hẹn",
    )
    rating = models.IntegerField(choices=RATING_CHOICES, verbose_name="Điểm đánh giá")
    review = models.TextField(verbose_name="Nội dung đánh giá")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Cập nhật lần cuối")

    class Meta:
        ordering = ["-created_at"]
        unique_together = ["patient", "booking"]
        verbose_name = "Đánh giá"
        verbose_name_plural = "Đánh giá"

    def __str__(self):
        return f"Đánh giá của {self.patient} cho BS. {self.doctor}"

    @property
    def rating_percent(self):
        return (self.rating / 5) * 100
