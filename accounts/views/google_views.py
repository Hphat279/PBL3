from django.conf import settings
from django.contrib import messages, auth
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.core.mail import send_mail
import random
import logging

from accounts.forms import GoogleStartForm, GoogleVerifyForm
from accounts.models import GoogleVerification, User

logger = logging.getLogger(__name__)


class GoogleStartView(View):
    template_name = "accounts/google_start.html"

    def get(self, request):
        form = GoogleStartForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = GoogleStartForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            # only allow Gmail for this simplified flow
            if not email.lower().endswith("@gmail.com"):
                messages.error(request, "Vui lòng sử dụng địa chỉ Gmail cho đăng nhập Google giả lập.")
                return render(request, self.template_name, {"form": form})

            code = "%06d" % random.randint(0, 999999)
            gv = GoogleVerification.objects.create(email=email, code=code)

            subject = "Mã xác thực đăng ký/đăng nhập Doccure"
            message = f"Mã xác thực của bạn: {code}\nNếu bạn không yêu cầu mã này, hãy bỏ qua email." 
            from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@example.com")
            try:
                send_mail(subject, message, from_email, [email])
                messages.success(request, "Mã xác thực đã được gửi tới email của bạn. Vui lòng kiểm tra Gmail.")
            except Exception as e:
                # fallback: log and show code in message for local dev
                logger.exception("Failed to send verification email")
                messages.warning(request, f"Không thể gửi email (dev). Mã: {code}")

            request.session["google_verif_id"] = gv.id
            request.session["google_email"] = email
            return redirect(reverse("accounts:google-verify"))

        return render(request, self.template_name, {"form": form})


class GoogleVerifyView(View):
    template_name = "accounts/google_verify.html"

    def get(self, request):
        form = GoogleVerifyForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = GoogleVerifyForm(request.POST)
        ver_id = request.session.get("google_verif_id")
        email = request.session.get("google_email")
        if not ver_id or not email:
            messages.error(request, "Phiên xác thực đã hết. Vui lòng thử lại.")
            return redirect(reverse("accounts:google-start"))

        gv = get_object_or_404(GoogleVerification, id=ver_id)

        if form.is_valid():
            code = form.cleaned_data["code"].strip()
            if gv.used or gv.code != code:
                messages.error(request, "Mã xác thực không hợp lệ.")
                return render(request, self.template_name, {"form": form})

            # check expiry (15 minutes)
            if timezone.now() - gv.created_at > timezone.timedelta(minutes=15):
                messages.error(request, "Mã xác thực đã hết hạn. Vui lòng yêu cầu lại.")
                return redirect(reverse("accounts:google-start"))

            # mark used
            gv.used = True
            gv.save()

            # create or login user
            try:
                user = User.objects.filter(email__iexact=email).first()
                if user:
                    # login existing user
                    auth.login(request, user)
                    messages.success(request, "Đăng nhập thành công.")
                    return redirect(getattr(settings, "LOGIN_REDIRECT_URL", "/"))

                # create new user
                username = form.cleaned_data["username"]
                # ensure username unique
                base = username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base}{counter}"
                    counter += 1

                user = User.objects.create(username=username, email=email, first_name=form.cleaned_data.get("first_name", ""), last_name=form.cleaned_data.get("last_name", ""), role="patient", is_active=True)
                user.set_password(form.cleaned_data["password1"])
                user.save()
                auth.login(request, user)
                messages.success(request, "Tạo tài khoản và đăng nhập thành công.")
                return redirect(getattr(settings, "LOGIN_REDIRECT_URL", "/"))
            except Exception as e:
                logger.exception("Error creating/logging user in GoogleVerifyView")
                messages.error(request, "Có lỗi khi tạo/đăng nhập người dùng.")
                return render(request, self.template_name, {"form": form})

        return render(request, self.template_name, {"form": form})
