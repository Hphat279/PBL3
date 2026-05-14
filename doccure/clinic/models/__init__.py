"""
clinic/models/__init__.py
Export tất cả model của clinic app để dùng như:
    from clinic.models import Patient, MedicalRecord, ...

Lưu ý: ClinicUser đã bị xoá — hệ thống giờ dùng accounts.User chung.
Lưu ý: Role/UserRole đã bị xoá — phân quyền dùng accounts.User.role.
"""

# Nhóm 2: Nhân viên & Bệnh nhân
from clinic.models.hr import StaffProfile, Patient

# Nhóm 3: Tiếp nhận & Chỉ số sinh tồn
from clinic.models.reception import Appointment, VitalSigns

# Nhóm 4: Bệnh án & Dịch vụ
from clinic.models.clinical import (
    MedicalRecord,
    ServiceCategory,
    Service,
    ServiceOrder,
)

# Nhóm 5: Dược phẩm
from clinic.models.pharmacy import Medicine, ClinicPrescription, PrescriptionItem

# Nhóm 6: Tài chính
from clinic.models.billing import Invoice, Payment

__all__ = [
    # Nhân viên & Bệnh nhân
    "StaffProfile",
    "Patient",
    # Tiếp nhận
    "Appointment",
    "VitalSigns",
    # Bệnh án & Dịch vụ
    "MedicalRecord",
    "ServiceCategory",
    "Service",
    "ServiceOrder",
    # Dược phẩm
    "Medicine",
    "ClinicPrescription",
    "PrescriptionItem",
    # Tài chính
    "Invoice",
    "Payment",
]
