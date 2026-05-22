from django.db import models
from django.conf import settings


class Medicine(models.Model):
    sku = models.CharField(max_length=50, unique=True, verbose_name="Mã thuốc")
    name = models.CharField(max_length=255, verbose_name="Tên thuốc")
    description = models.TextField(blank=True, verbose_name="Mô tả")
    unit = models.CharField(max_length=50, default="viên", verbose_name="Đơn vị tính")
    quantity = models.PositiveIntegerField(default=0, verbose_name="Số lượng tồn")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Đơn giá")
    is_active = models.BooleanField(default=True, verbose_name="Hoạt động")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Thuốc trong kho"
        verbose_name_plural = "Thuốc trong kho"

    def __str__(self):
        return f"{self.name} ({self.sku}) - {self.quantity} {self.unit} còn lại"


class PrescriptionDispensation(models.Model):
    prescription = models.OneToOneField(
        "bookings.Prescription",
        on_delete=models.CASCADE,
        related_name="dispensation",
        verbose_name="Đơn thuốc",
    )
    pharmacist = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to={"role": "pharmacist"},
        verbose_name="Dược sĩ",
    )
    dispensed_at = models.DateTimeField(auto_now_add=True, verbose_name="Thời gian phát")
    notes = models.TextField(blank=True, verbose_name="Ghi chú")

    class Meta:
        ordering = ["-dispensed_at"]
        verbose_name = "Phiếu phát thuốc"
        verbose_name_plural = "Phiếu phát thuốc"

    def __str__(self):
        return f"Dispensation for Prescription #{self.prescription.id} at {self.dispensed_at}"

    @property
    def total_cost(self):
        return sum(item.quantity * item.price for item in self.items.all())


class PrescriptionDispensationItem(models.Model):
    dispensation = models.ForeignKey(
        PrescriptionDispensation,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Phiếu phát thuốc",
    )
    medicine = models.ForeignKey(
        Medicine,
        on_delete=models.CASCADE,
        verbose_name="Thuốc",
    )
    quantity = models.PositiveIntegerField(verbose_name="Số lượng")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Đơn giá lúc phát")

    class Meta:
        verbose_name = "Chi tiết thuốc phát"
        verbose_name_plural = "Chi tiết thuốc phát"

    def __str__(self):
        return f"{self.medicine.name} x {self.quantity}"
