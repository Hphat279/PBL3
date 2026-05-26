from django.contrib import messages, auth
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, FormView, RedirectView, UpdateView
from rest_framework.generics import UpdateAPIView
from django.conf import settings

try:
    from allauth.socialaccount.models import SocialApp
except Exception:
    SocialApp = None

from accounts.forms import (
    DoctorRegistrationForm,
    PatientRegistrationForm,
    UserLoginForm,
    ProfileCompletionForm,
)
from accounts.models import User
from accounts.serializers import BasicUserInformationSerializer
from utils.htmx import render_toast_message_for_api


class RegisterDoctorView(CreateView):
    model = User
    form_class = DoctorRegistrationForm
    template_name = "accounts/register.html"
    success_url = "/"

    extra_context = {"title": "Register"}

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        try:
            ctx["google_enabled"] = (
                SocialApp.objects.filter(provider="google", sites__id=settings.SITE_ID).exists()
                if SocialApp is not None
                else False
            )
        except Exception:
            ctx["google_enabled"] = False
        return ctx

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return HttpResponseRedirect(self.success_url)
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        form = self.form_class(data=request.POST)

        if form.is_valid():
            user = form.save(commit=False)
            password = form.cleaned_data.get("password1")
            user.set_password(password)
            # mark as doctor and require admin approval
            try:
                user.role = "doctor"
            except Exception:
                pass
            user.is_active = False
            user.save()
            messages.success(
                request,
                "Yêu cầu tạo tài khoản bác sĩ đã được gửi. Vui lòng chờ quản trị viên duyệt."
            )
            return redirect("accounts:login")
        else:
            return render(request, "accounts/register.html", {"form": form})


class RegisterPatientView(CreateView):
    form_class = PatientRegistrationForm
    template_name = "accounts/register.html"
    success_url = "/"

    extra_context = {"title": "Register"}

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        try:
            ctx["google_enabled"] = (
                SocialApp.objects.filter(provider="google", sites__id=settings.SITE_ID).exists()
                if SocialApp is not None
                else False
            )
        except Exception:
            ctx["google_enabled"] = False
        return ctx

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return HttpResponseRedirect(self.success_url)
        return super().dispatch(request, *args, **kwargs)


def google_login_view(request):
    """
    Placeholder for Google login. If full OAuth isn't configured,
    redirect back to login with a helpful message.
    """
    messages.error(
        request,
        "Đăng nhập bằng Google chưa được cấu hình trên môi trường này. Vui lòng cấu hình OAuth hoặc đăng nhập bằng tài khoản nội bộ.",
    )
    return redirect("accounts:login")


class LoginView(FormView):
    """
    Provides the ability to login as a user with an email and password
    """

    success_url = "/"
    form_class = UserLoginForm
    template_name = "accounts/login.html"

    extra_context = {"title": "Login"}

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        try:
            ctx["google_enabled"] = (
                SocialApp.objects.filter(provider="google", sites__id=settings.SITE_ID).exists()
                if SocialApp is not None
                else False
            )
        except Exception:
            ctx["google_enabled"] = False
        return ctx

    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            return HttpResponseRedirect(self.get_success_url())
        return super().dispatch(self.request, *args, **kwargs)

    def get_success_url(self):
        if "next" in self.request.GET and self.request.GET["next"] != "":
            return self.request.GET["next"]
        user = getattr(self.request, 'user', None)
        try:
            if user:
                role = getattr(user, 'role', None)
                if role == 'doctor':
                    return reverse_lazy('doctors:dashboard')
                elif role == 'dept_doctor':
                    return reverse_lazy('doctors:dept-dashboard')
                elif role == 'pharmacist':
                    return reverse_lazy('pharmacy:dashboard')
                elif role == 'patient':
                    return reverse_lazy('patients:dashboard')
        except Exception:
            pass
        return self.success_url

    def get_form_class(self):
        return self.form_class

    def form_valid(self, form):
        user = form.get_user()
        auth.login(self.request, user)
        try:
            role = getattr(user, 'role', None)
            if role == 'doctor':
                return HttpResponseRedirect(reverse_lazy('doctors:dashboard'))
            elif role == 'dept_doctor':
                return HttpResponseRedirect(reverse_lazy('doctors:dept-dashboard'))
            elif role == 'pharmacist':
                return HttpResponseRedirect(reverse_lazy('pharmacy:dashboard'))
            elif role == 'patient':
                return HttpResponseRedirect(reverse_lazy('patients:dashboard'))
        except Exception:
            pass
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        """If the form is invalid, render the invalid form."""
        return self.render_to_response(self.get_context_data(form=form))


class DoctorLoginView(LoginView):
    """Login view for doctors — only allows users with role 'doctor' and active to login."""

    extra_context = {"title": "Đăng nhập Bác sĩ"}

    def form_valid(self, form):
        user = form.get_user()
        # ensure user is a doctor and active
        role = getattr(user, "role", None)
        if role != "doctor" or not user.is_active:
            messages.error(self.request, "Tài khoản này không có quyền bác sĩ hoặc chưa được kích hoạt.")
            return self.form_invalid(form)
        auth.login(self.request, user)
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        # After doctor login, always redirect to doctor dashboard
        return reverse_lazy("doctors:dashboard")


class LogoutView(RedirectView):
    """
    Provides users the ability to logout
    """

    url = reverse_lazy("accounts:login")

    def get(self, request, *args, **kwargs):
        auth.logout(request)
        messages.success(request, "Bạn đã đăng xuất")
        return super(LogoutView, self).get(request, *args, **kwargs)


class UpdateBasicUserInformationAPIView(LoginRequiredMixin, UpdateAPIView):
    serializer_class = BasicUserInformationSerializer

    def get_object(self):
        return self.request.user

    def put(self, request, *args, **kwargs):
        try:
            user = request.user
            # Handle both JSON and form data
            data = request.data if hasattr(request, 'data') else request.POST
            files = request.FILES

            # Update user information
            user.first_name = data.get("first_name", user.first_name)
            user.last_name = data.get("last_name", user.last_name)
            user.save()

            # Update profile information
            user_profile = user.profile
            user_profile.dob = data.get("dob")
            user_profile.phone = data.get("phone")

            # Handle avatar file upload
            if "avatar" in files:
                user_profile.avatar = files["avatar"]

            user_profile.save()

            return render_toast_message_for_api(
                "Information", "Updated successfully", "success"
            )
        except Exception as e:
            return render_toast_message_for_api("Error", str(e), "error")


class CompleteProfileView(LoginRequiredMixin, FormView):
    """Force user to complete required profile fields (email, names)."""
    template_name = "accounts/complete_profile.html"
    form_class = ProfileCompletionForm

    def get_initial(self):
        user = self.request.user
        return {
            "email": user.email or "",
            "first_name": user.first_name or "",
            "last_name": user.last_name or "",
            "phone": getattr(getattr(user, 'profile', None), 'phone', ''),
            "dob": getattr(getattr(user, 'profile', None), 'dob', None),
            "gender": getattr(getattr(user, 'profile', None), 'gender', ''),
            "address": getattr(getattr(user, 'profile', None), 'address', ''),
            "city": getattr(getattr(user, 'profile', None), 'city', ''),
            "state": getattr(getattr(user, 'profile', None), 'state', ''),
            "postal_code": getattr(getattr(user, 'profile', None), 'postal_code', ''),
            "country": getattr(getattr(user, 'profile', None), 'country', ''),
            "blood_group": getattr(getattr(user, 'profile', None), 'blood_group', ''),
            "allergies": getattr(getattr(user, 'profile', None), 'allergies', ''),
            "medical_conditions": getattr(getattr(user, 'profile', None), 'medical_conditions', ''),
        }

    def form_valid(self, form):
        user = self.request.user
        data = form.cleaned_data
        from django.contrib.auth import get_user_model
        UserModel = get_user_model()
        existing = UserModel.objects.filter(email__iexact=data['email']).exclude(pk=user.pk)
        if existing.exists():
            form.add_error('email', 'Email này đã có người sử dụng.')
            return self.form_invalid(form)

        user.email = data['email']
        user.first_name = data['first_name']
        user.last_name = data['last_name']
        user.save()

        # ensure profile exists
        try:
            prof = user.profile
        except Exception:
            from accounts.models import Profile
            prof = Profile.objects.create(user=user)

        prof.phone = data.get('phone') or prof.phone
        prof.dob = data.get('dob') or prof.dob
        prof.gender = data.get('gender') or prof.gender
        prof.address = data.get('address') or prof.address
        prof.city = data.get('city') or prof.city
        prof.state = data.get('state') or prof.state
        prof.postal_code = data.get('postal_code') or prof.postal_code
        prof.country = data.get('country') or prof.country
        prof.blood_group = data.get('blood_group') or prof.blood_group
        prof.allergies = data.get('allergies') or prof.allergies
        prof.medical_conditions = data.get('medical_conditions') or prof.medical_conditions
        prof.save()

        next_url = self.request.GET.get('next') or '/'
        return HttpResponseRedirect(next_url)

    def form_invalid(self, form):
        print("FORM INVALID ERRORS:", form.errors)
        return super().form_invalid(form)

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        if user.email and user.first_name and user.last_name:
            return HttpResponseRedirect('/')
        return super().dispatch(request, *args, **kwargs)
