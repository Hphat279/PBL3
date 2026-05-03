"""
clinic/models/clinical.py
Nhóm 4: Lõi bệnh án & Dịch vụ .
"""

from django.db import models
from clinic.models.hr import Patient, StaffProfile


class MedicalRecord(models.Model):
    """
    Bảng `medical_records` .
    Lưu toàn bộ thông tin lâm sàng của một lần khám:
    triệu chứng, chẩn đoán sơ bộ, chẩn đoán xác định (ICD-10), hướng điều trị.
    """
    patient = models.ForeignKey(
        Patient,
        on_delete=models.PROTECT,
        related_name="medical_records",
        verbose_name="Bệnh nhân",
    )
    doctor = models.ForeignKey(
        StaffProfile,
        on_delete=models.PROTECT,
        related_name="medical_records",
        verbose_name="Bác sĩ",
    )
    visit_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Ngày khám",
    )
    # Triệu chứng bệnh nhân mô tả
    symptoms = models.TextField(
        blank=True,
        null=True,
        verbose_name="Triệu chứng",
    )
    # Chẩn đoán ban đầu của bác sĩ
    initial_diagnosis = models.TextField(
        blank=True,
        null=True,
        verbose_name="Chẩn đoán sơ bộ",
    )
    # Chẩn đoán xác định sau khi có kết quả cận lâm sàng (chuẩn ICD-10)
    final_diagnosis = models.TextField(
        blank=True,
        null=True,
        verbose_name="Chẩn đoán xác định (ICD-10)",
    )
    # Phác đồ điều trị: nội khoa, ngoại khoa, vật lý trị liệu…
    treatment_plan = models.TextField(
        blank=True,
        null=True,
        verbose_name="Hướng điều trị",
    )
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Ghi chú",
    )

    class Meta:
        db_table = "medical_records"
        verbose_name = "Bệnh án"
        verbose_name_plural = "Bệnh án"
        ordering = ["-visit_date"]

    def __str__(self):
        return f"BA#{self.pk} – {self.patient.full_name} ({self.visit_date:%d/%m/%Y})"


class ServiceCategory(models.Model):
    """
    Bảng `service_categories` – Danh mục dịch vụ.
     Xét nghiệm, Siêu âm, Nội soi, Khám chuyên khoa, X-quang…
    """
    name = models.CharField(max_length=100, verbose_name="Tên danh mục")

    class Meta:
        db_table = "service_categories"
        verbose_name = "Danh mục dịch vụ"
        verbose_name_plural = "Danh mục dịch vụ"

    def __str__(self):
        return self.name


class Service(models.Model):
    """
    Bảng `services` .
    Mỗi dịch vụ thuộc một danh mục và có đơn giá.
    """
    category = models.ForeignKey(
        ServiceCategory,
        on_delete=models.PROTECT,
        related_name="services",
        verbose_name="Danh mục",
    )
    service_name = models.CharField(max_length=255, verbose_name="Tên dịch vụ")
    price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name="Đơn giá (VNĐ)",
    )
    is_active = models.BooleanField(default=True, verbose_name="Đang hoạt động")

    class Meta:
        db_table = "services"
        verbose_name = "Dịch vụ"
        verbose_name_plural = "Dịch vụ"

    def __str__(self):
        return f"{self.service_name} – {self.category}"


class ServiceOrder(models.Model):
    """
    Bảng `service_orders` .
    Bác sĩ chỉ định dịch vụ cho bệnh nhân trong bệnh án.
    Trạng thái: pending → paid → processing → completed / cancelled

    result_json: lưu đường dẫn ảnh kết quả, ví dụ ["url1", "url2"]
    """
    class TrangThai(models.TextChoices):
        CHO_THANH_TOAN = "pending", "Chờ thanh toán"
        DA_THANH_TOAN = "paid", "Đã thanh toán"
        DANG_THUC_HIEN = "processing", "Đang thực hiện"
        HOAN_THANH = "completed", "Hoàn thành"
        HUY = "cancelled", "Đã hủy"

    medical_record = models.ForeignKey(
        MedicalRecord,
        on_delete=models.PROTECT,
        related_name="service_orders",
        verbose_name="Bệnh án",
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.PROTECT,
        related_name="service_orders",
        verbose_name="Dịch vụ",
    )
    status = models.CharField(
        max_length=20,
        choices=TrangThai.choices,
        default=TrangThai.CHO_THANH_TOAN,
        verbose_name="Trạng thái",
    )
    # Kết quả dạng văn bản (mô tả của kỹ thuật viên)
    result_text = models.TextField(
        blank=True,
        null=True,
        verbose_name="Kết quả (văn bản)",
    )
    # Kết quả dạng JSON: đường dẫn ảnh, file PDF…
    result_json = models.JSONField(
        blank=True,
        null=True,
        verbose_name="Kết quả (JSON / file đính kèm)",
    )
    # Kỹ thuật viên hoặc nhân viên thực hiện dịch vụ
    performer = models.ForeignKey(
        StaffProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="performed_service_orders",
        verbose_name="Người thực hiện",
    )
    performed_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Thời điểm thực hiện",
    )

    class Meta:
        db_table = "service_orders"
        verbose_name = "Phiếu chỉ định dịch vụ"
        verbose_name_plural = "Phiếu chỉ định dịch vụ"

    def __str__(self):
        return f"Chỉ định #{self.pk} – {self.service.service_name} [{self.get_status_display()}]"
