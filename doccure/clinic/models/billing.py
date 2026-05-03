"""
clinic/models/billing.py
 Tài chính 

"""

from django.db import models
from clinic.models.hr import Patient
from clinic.models.clinical import MedicalRecord


class Invoice(models.Model):
    """
    Bảng `invoices` – Hóa đơn thanh toán cho một lần khám.
     dịch vụ + thuốc + tiền khám.
    """
    class TrangThaiThanh(models.TextChoices):
        CHUA_THANH_TOAN = "unpaid", "Chưa thanh toán"
        DA_THANH_TOAN = "paid", "Đã thanh toán"
        THANH_TOAN_MOT_PHAN = "partially_paid", "Thanh toán một phần"

    patient = models.ForeignKey(
        Patient,
        on_delete=models.PROTECT,
        related_name="invoices",
        verbose_name="Bệnh nhân",
    )
    medical_record = models.ForeignKey(
        MedicalRecord,
        on_delete=models.PROTECT,
        related_name="invoices",
        verbose_name="Bệnh án",
    )
    # Tổng tiền trước giảm giá
    total_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name="Tổng tiền (VNĐ)",
    )
    # Số tiền giảm giá (mặc định 0)
    discount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        verbose_name="Giảm giá (VNĐ)",
    )
    # Số tiền thực thu = total_amount - discount
    final_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name="Thực thu (VNĐ)",
    )
    payment_status = models.CharField(
        max_length=20,
        choices=TrangThaiThanh.choices,
        default=TrangThaiThanh.CHUA_THANH_TOAN,
        verbose_name="Trạng thái thanh toán",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Ngày lập hóa đơn",
    )

    class Meta:
        db_table = "invoices"
        verbose_name = "Hóa đơn"
        verbose_name_plural = "Hóa đơn"
        ordering = ["-created_at"]

    def __str__(self):
        return f"HĐ#{self.pk} – {self.patient.full_name} [{self.get_payment_status_display()}]"

    def save(self, *args, **kwargs):
        """Tự động tính final_amount khi lưu"""
        self.final_amount = self.total_amount - self.discount
        super().save(*args, **kwargs)


class Payment(models.Model):
    """
    Bảng `payments` 
    Một hóa đơn có thể có nhiều giao dịch (thanh toán từng phần).
    """
    class PhuongThuc(models.TextChoices):
        TIEN_MAT = "cash", "Tiền mặt"
        CHUYEN_KHOAN = "transfer", "Chuyển khoản"
        THE_NGAN_HANG = "credit_card", "Thẻ ngân hàng"

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.PROTECT,
        related_name="payments",
        verbose_name="Hóa đơn",
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PhuongThuc.choices,
        blank=True,
        null=True,
        verbose_name="Phương thức thanh toán",
    )
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name="Số tiền (VNĐ)",
    )
    # Mã giao dịch ngân hàng (nếu chuyển khoản)
    transaction_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Mã giao dịch",
    )
    paid_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Thời điểm thanh toán",
    )

    class Meta:
        db_table = "payments"
        verbose_name = "Giao dịch thanh toán"
        verbose_name_plural = "Giao dịch thanh toán"
        ordering = ["-paid_at"]

    def __str__(self):
        return f"TT#{self.pk} – {self.amount:,.0f}đ – {self.get_payment_method_display()}"
