from django.contrib.auth.mixins import LoginRequiredMixin


class PatientRequiredMixin(LoginRequiredMixin):
    """Chỉ cho phép bệnh nhân (role=patient) truy cập."""

    permission_denied_message = "Bạn không có quyền truy cập trang này"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        if request.user.role != "patient":
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class DoctorRequiredMixin(LoginRequiredMixin):
    """Chỉ cho phép bác sĩ (role=doctor) truy cập."""

    permission_denied_message = "Bạn không có quyền truy cập trang này"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        if request.user.role != "doctor":
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class NurseRequiredMixin(LoginRequiredMixin):
    """Chỉ cho phép điều dưỡng (role=nurse) truy cập."""

    permission_denied_message = "Bạn không có quyền truy cập trang này"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        if request.user.role != "nurse":
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class ReceptionistRequiredMixin(LoginRequiredMixin):
    """Chỉ cho phép tiếp tân (role=receptionist) truy cập."""

    permission_denied_message = "Bạn không có quyền truy cập trang này"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        if request.user.role != "receptionist":
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class PharmacistRequiredMixin(LoginRequiredMixin):
    """Chỉ cho phép dược sĩ (role=pharmacist) truy cập."""

    permission_denied_message = "Bạn không có quyền truy cập trang này"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        if request.user.role != "pharmacist":
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class ClinicStaffRequiredMixin(LoginRequiredMixin):
    """
    Cho phép tất cả nhân viên phòng khám truy cập
    (doctor, nurse, receptionist, pharmacist, admin).
    """

    permission_denied_message = "Bạn không có quyền truy cập trang này"
    CLINIC_ROLES = {"doctor", "nurse", "receptionist", "pharmacist", "admin"}

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        if request.user.role not in self.CLINIC_ROLES:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
