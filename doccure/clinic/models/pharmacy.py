"""
clinic/models/pharmacy.py
Nhóm 5: Dược phẩm 
Danh mục thuốc, đơn thuốc và chi tiết từng dòng thuốc.
"""

from django.db import models
from clinic.models.clinical import MedicalRecord


class Medicine(models.Model):
    """
    Bảng `medicines` c.
    Theo dõi tồn kho và đơn giá bán.
    """
    medicine_name = models.CharField(
        max_length=255,
        verbose_name="Tên thuốc",
    )
    # Hoạt chất chính của thuốc (ví dụ: Paracetamol, Amoxicillin)
    active_ingredient = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Hoạt chất",
    )
    # Đơn vị tính: Viên, Gói, Chai, Lọ, Ống…
    unit = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Đơn vị tính",
    )
    # Số lượng tồn kho hiện tại
    stock_quantity = models.IntegerField(
        default=0,
        verbose_name="Tồn kho",
    )
    price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name="Đơn giá (VNĐ)",
    )

    class Meta:
        db_table = "medicines"
        verbose_name = "Thuốc"
        verbose_name_plural = "Danh mục thuốc"
        ordering = ["medicine_name"]

    def __str__(self):
        return f"{self.medicine_name} ({self.unit})" if self.unit else self.medicine_name

    @property
    def con_hang(self):
        """Kiểm tra thuốc còn hàng trong kho"""
        return self.stock_quantity > 0


class ClinicPrescription(models.Model):
    """
    Bảng `prescriptions` .
    Mỗi bệnh án chỉ có 1 đơn thuốc (OneToOne).
    Chi tiết từng dòng thuốc nằm trong PrescriptionItem.
    """
    medical_record = models.OneToOneField(
        MedicalRecord,
        on_delete=models.CASCADE,
        related_name="clinic_prescription",
        verbose_name="Bệnh án",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Ngày kê đơn",
    )

    class Meta:
        db_table = "prescriptions"
        verbose_name = "Đơn thuốc"
        verbose_name_plural = "Đơn thuốc"

    def __str__(self):
        return f"Đơn thuốc #{self.pk} – Bệnh án #{self.medical_record_id}"

    @property
    def tong_tien(self):
        """Tính tổng tiền đơn thuốc"""
        return sum(
            item.medicine.price * item.quantity
            for item in self.items.select_related("medicine")
        )


class PrescriptionItem(models.Model):
    """
    Bảng `prescription_items` .
    Mỗi dòng chứa: thuốc, số lượng, liều dùng, cách dùng.
    """
    prescription = models.ForeignKey(
        ClinicPrescription,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Đơn thuốc",
    )
    medicine = models.ForeignKey(
        Medicine,
        on_delete=models.PROTECT,
        related_name="prescription_items",
        verbose_name="Thuốc",
    )
    quantity = models.IntegerField(verbose_name="Số lượng")
    # Liều dùng: ví dụ "2 viên/ngày", "1 viên x 3 lần/ngày"
    dosage = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Liều dùng",
    )
    # Cách dùng: ví dụ "Uống sau ăn no", "Ngậm dưới lưỡi"
    instructions = models.TextField(
        blank=True,
        null=True,
        verbose_name="Cách dùng",
    )

    class Meta:
        db_table = "prescription_items"
        verbose_name = "Chi tiết đơn thuốc"
        verbose_name_plural = "Chi tiết đơn thuốc"

    def __str__(self):
        return f"{self.medicine.medicine_name} × {self.quantity} – Đơn #{self.prescription_id}"

    @property
    def thanh_tien(self):
        """Thành tiền = đơn giá × số lượng"""
        return self.medicine.price * self.quantity
