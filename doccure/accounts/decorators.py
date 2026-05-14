from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages


class AdminRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            messages.error(
                request, "Bạn không có quyền truy cập trang này."
            )
            return redirect("core:home")
        return super().dispatch(request, *args, **kwargs)
