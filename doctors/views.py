import json
from datetime import datetime, date

from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.http import (
    HttpRequest,
    HttpResponse,
    Http404,
    HttpResponsePermanentRedirect,
)
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import generic
from django.views.generic import (
    ListView,
    DetailView,
    View,
    CreateView,
    UpdateView,
)
from django.views.generic.base import TemplateView
from rest_framework.generics import UpdateAPIView
from rest_framework.response import Response
from django.db.models import Q
from django.db.models import Count
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash

from bookings.models import Booking, Prescription, Referral
from core.models import Review, Department
from core.dept_fields import DEPARTMENT_FIELDS
from core.decorators import user_is_doctor
from doctors.forms import DoctorProfileForm, PrescriptionForm
from doctors.models import Experience
from doctors.models.general import *
from doctors.serializers import (
    EducationSerializer,
    ExperienceSerializer,
    RegistrationNumberSerializer,
    SpecializationSerializer,
)
from mixins.custom_mixins import DoctorRequiredMixin, DepartmentDoctorRequiredMixin
from patients.forms import ChangePasswordForm
from utils.htmx import render_toast_message_for_api
from accounts.models import User

days = {
    0: Sunday,
    1: Monday,
    2: Tuesday,
    3: Wednesday,
    4: Thursday,
    5: Friday,
    6: Saturday,
}

class DoctorDashboardView(DoctorRequiredMixin, TemplateView):
    template_name = "doctors/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()

        # Get appointment counts
        context["total_patients"] = ( 
            Booking.objects.filter(doctor=self.request.user)
            .values("patient")
            .distinct()
            .count()
        )

        context["today_patients"] = Booking.objects.filter(
            doctor=self.request.user, appointment_date=today
        ).count()

        context["total_appointments"] = Booking.objects.filter(
            doctor=self.request.user
        ).count()

        # Get upcoming appointments
        context["upcoming_appointments"] = (
            Booking.objects.select_related("patient", "patient__profile")
            .filter(
                doctor=self.request.user,
                appointment_date__gte=today,
                status__in=["pending", "confirmed"],
            )
            .order_by("appointment_date", "appointment_time")[:10]
        )

        # Get today's appointments
        context["today_appointments"] = (
            Booking.objects.select_related("patient", "patient__profile")
            .filter(doctor=self.request.user, appointment_date=today)
            .order_by("appointment_time")
        )

        # Recent reviews for this doctor
        context["recent_reviews"] = (
            Review.objects.select_related("patient", "patient__profile")
            .filter(doctor=self.request.user)
            .order_by("-created_at")[:10]
        )

        # Recent prescriptions for display on dashboard
        context["recent_prescriptions"] = (
            Prescription.objects.select_related("patient", "patient__profile")
            .filter(doctor=self.request.user)
            .order_by("-created_at")[:5]
        )

        return context


def convert_to_24_hour_format(time_str):
    if time_str == "00:00 AM":
        time_str = "12:00 AM"
    return datetime.strptime(time_str, "%I:%M %p").time()


@login_required
@user_is_doctor
def schedule_timings(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        data = request.POST
        for i in range(7):
            if data.get(f"day_{i}", None):
                start_times = data.getlist(f"start_time_{i}", default=[])
                end_times = data.getlist(f"end_time_{i}", default=[])
                for index in range(len(start_times)):
                    start = convert_to_24_hour_format(start_times[index])
                    end = convert_to_24_hour_format(end_times[index])
                    time_range, time_created = TimeRange.objects.get_or_create(
                        start=start, end=end
                    )
                    day, created = days[i].objects.get_or_create(
                        user=request.user
                    )
                    ranges = day.time_range
                    if time_range.id not in list(
                        ranges.values_list("id", flat=True)
                    ):
                        day.time_range.add(time_range)

        return HttpResponsePermanentRedirect(
            reverse_lazy("doctors:schedule-timings")
        )

    return render(request, "doctors/schedule-timings.html")


class DoctorProfileUpdateView(DoctorRequiredMixin, generic.UpdateView):
    model = User
    template_name = "doctors/profile-settings.html"
    form_class = DoctorProfileForm

    def get_object(self, queryset=None):
        return self.request.user


class DoctorProfileView(DetailView):
    context_object_name = "doctor"
    model = User
    slug_url_kwarg = "username"
    slug_field = "username"
    template_name = "doctors/profile.html"

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()

        slug = self.kwargs.get(self.slug_url_kwarg)
        queryset = queryset.select_related("profile").prefetch_related(
            "educations",
            "experiences",
            "sunday__time_range",
            "monday__time_range",
            "tuesday__time_range",
            "wednesday__time_range",
            "thursday__time_range",
            "friday__time_range",
            "saturday__time_range",
        )

        try:
            obj = queryset.get(
                **{self.slug_field: slug, "role": User.RoleChoices.DOCTOR}
            )
        except User.DoesNotExist:
            raise Http404(f"No doctor found matching the username")

        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        doctor = self.object

        # Get current day name (map to Vietnamese for display)
        eng_today = datetime.now().strftime("%A")
        day_map = {
            "Sunday": "Chủ Nhật",
            "Monday": "Thứ Hai",
            "Tuesday": "Thứ Ba",
            "Wednesday": "Thứ Tư",
            "Thursday": "Thứ Năm",
            "Friday": "Thứ Sáu",
            "Saturday": "Thứ Bảy",
        }
        current_day = day_map.get(eng_today, eng_today)

        # Prepare business hours with Vietnamese day labels for display
        business_hours = {
            day_map["Sunday"]: (
                doctor.sunday.time_range.all() if hasattr(doctor, "sunday") else []
            ),
            day_map["Monday"]: (
                doctor.monday.time_range.all() if hasattr(doctor, "monday") else []
            ),
            day_map["Tuesday"]: (
                doctor.tuesday.time_range.all() if hasattr(doctor, "tuesday") else []
            ),
            day_map["Wednesday"]: (
                doctor.wednesday.time_range.all() if hasattr(doctor, "wednesday") else []
            ),
            day_map["Thursday"]: (
                doctor.thursday.time_range.all() if hasattr(doctor, "thursday") else []
            ),
            day_map["Friday"]: (
                doctor.friday.time_range.all() if hasattr(doctor, "friday") else []
            ),
            day_map["Saturday"]: (
                doctor.saturday.time_range.all() if hasattr(doctor, "saturday") else []
            ),
        }

        context.update(
            {
                "current_day": current_day,
                "business_hours": business_hours,
                "reviews": doctor.reviews_received.select_related(
                    "patient", "patient__profile"
                ).order_by("-created_at"),
            }
        )

        return context


class UpdateEducationAPIView(DoctorRequiredMixin, UpdateAPIView):
    queryset = Experience.objects.all()
    serializer_class = EducationSerializer

    def get_object(self):
        return self.request.user

    def perform_update(self, serializer):
        serializer.save(user_id=self.request.user.id)

    def update(self, request, *args, **kwargs):
        data = request.POST
        ids = data.getlist("id", default=[])
        degrees = data.getlist("degree", default=[])
        colleges = data.getlist("college", default=[])
        years = data.getlist("year_of_completion", default=[])
        for i in range(len(degrees)):
            try:
                instance = self.request.user.educations.get(id=ids[i])
                degree = degrees[i]
                college = colleges[i]
                year_of_completion = years[i]
                serializer = self.get_serializer(
                    instance,
                    data={
                        "degree": degree,
                        "college": college,
                        "year_of_completion": year_of_completion,
                    },
                    partial=True,
                )
                serializer.is_valid(raise_exception=True)
                self.perform_update(serializer)
            except:
                degree = degrees[i]
                college = colleges[i]
                year_of_completion = years[i]
                serializer = self.get_serializer(
                    data={
                        "degree": degree,
                        "college": college,
                        "year_of_completion": year_of_completion,
                    }
                )
                serializer.is_valid(raise_exception=True)
                self.perform_update(serializer)

        response = Response({"success": True})
        response.headers["HX-Trigger"] = json.dumps(
            {
                "show-toast": {
                    "level": "success",
                    "title": "Education",
                    "message": "Successfully updated",
                }
            }
        )
        return response


class UpdateExperienceAPIView(DoctorRequiredMixin, UpdateAPIView):
    queryset = Experience.objects.all()
    serializer_class = ExperienceSerializer

    def get_object(self):
        return self.request.user

    def perform_update(self, serializer):
        serializer.save(user_id=self.request.user.id)

    def update(self, request, *args, **kwargs):
        data = request.POST
        ids = data.getlist("id", default=[])
        institutions = data.getlist("institution", default=[])
        from_years = data.getlist("from_year", default=[])
        to_years = data.getlist("to_year", default=[])
        designations = data.getlist("designation", default=[])

        for i in range(len(institutions)):
            try:
                instance = self.request.user.educations.get(id=ids[i])
                institution = institutions[i]
                from_year = from_years[i]
                to_year = to_years[i]
                designation = designations[i]
                serializer = self.get_serializer(
                    instance,
                    data={
                        "institution": institution,
                        "from_year": from_year,
                        "to_year": to_year,
                        "designation": designation,
                    },
                    partial=True,
                )
                serializer.is_valid(raise_exception=True)
                self.perform_update(serializer)
            except:
                institution = institutions[i]
                from_year = from_years[i]
                to_year = to_years[i]
                designation = designations[i]
                serializer = self.get_serializer(
                    data={
                        "institution": institution,
                        "from_year": from_year,
                        "to_year": to_year,
                        "designation": designation,
                    }
                )
                serializer.is_valid(raise_exception=True)
                self.perform_update(serializer)

        return render_toast_message_for_api(
            "Experience", "Updated successfully", "success"
        )


class UpdateRegistrationNumberAPIView(DoctorRequiredMixin, UpdateAPIView):
    serializer_class = RegistrationNumberSerializer

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        data = request.POST
        serializer = self.get_serializer(instance=request.user, data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return render_toast_message_for_api(
            "BM&DC number", "Updated successfully", "success"
        )


class UpdateSpecializationAPIView(DoctorRequiredMixin, UpdateAPIView):
    serializer_class = SpecializationSerializer

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        data = request.POST
        specialist = data.get("specialist")
        instance.profile.specialization = specialist
        instance.profile.save()

        return render_toast_message_for_api(
            "Specialization", "Updated successfully", "success"
        )


class DoctorsListView(ListView):
    model = User
    context_object_name = "doctors"
    template_name = "doctors/list.html"
    paginate_by = 10

    def get_queryset(self):
        queryset = self.model.objects.filter(
            role=User.RoleChoices.DOCTOR, is_superuser=False, is_active=True
        ).select_related("profile")

        # Handle search query
        search_query = self.request.GET.get("q")
        if search_query:
            queryset = queryset.filter(
                Q(first_name__icontains=search_query)
                | Q(last_name__icontains=search_query)
                | Q(profile__specialization__icontains=search_query)
                | Q(profile__city__icontains=search_query)
            )

        # Handle gender filter
        gender = self.request.GET.getlist("gender")
        if gender:
            queryset = queryset.filter(profile__gender__in=gender)

        # Handle specialization filter
        specializations = self.request.GET.getlist("specialization")
        if specializations:
            queryset = queryset.filter(
                profile__specialization__in=specializations
            )

        # Handle sorting
        sort_by = self.request.GET.get("sort")
        if sort_by:
            if sort_by == "price_low":
                queryset = queryset.order_by("profile__price_per_consultation")
            elif sort_by == "price_high":
                queryset = queryset.order_by(
                    "-profile__price_per_consultation"
                )
            elif sort_by == "rating":
                queryset = queryset.order_by("-rating")
            elif sort_by == "experience":
                # Order by number of experience entries (doctors with more experience entries first)
                queryset = queryset.annotate(exp_count=Count("experiences")).order_by("-exp_count")
        else:
            queryset = queryset.order_by("-pk")

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Add search query to context
        context["search_query"] = self.request.GET.get("q")

        # Add unique specializations to context
        specializations = (
            User.objects.filter(role=User.RoleChoices.DOCTOR, is_active=True)
            .exclude(profile__specialization__isnull=True)
            .values_list("profile__specialization", flat=True)
            .distinct()
        )

        context["specializations"] = sorted(
            list(filter(None, specializations))
        )

        # Add selected filters to context
        context["selected_specializations"] = self.request.GET.getlist(
            "specialization"
        )
        context["selected_genders"] = self.request.GET.getlist("gender")
        context["selected_sort"] = self.request.GET.get("sort")

        return context


class AppointmentListView(DoctorRequiredMixin, ListView):
    model = Booking
    context_object_name = "appointments"
    template_name = "doctors/appointments.html"
    paginate_by = 10

    def get_queryset(self):
        return (
            self.model.objects.select_related(
                "doctor", "doctor__profile", "patient", "patient__profile"
            )
            .filter(doctor=self.request.user)
            .order_by("-appointment_date", "-appointment_time")
        )


class AppointmentDetailView(DoctorRequiredMixin, DetailView):
    model = Booking
    template_name = "doctors/appointment-detail.html"
    context_object_name = "appointment"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        patient = self.object.patient

        context["patient_history"] = (
            Booking.objects.select_related("doctor", "doctor__profile")
            .filter(
                doctor=self.request.user,
                patient=patient,
                appointment_date__lt=self.object.appointment_date,
            )
            .order_by("-appointment_date", "-appointment_time")
        )

        context["total_visits"] = Booking.objects.filter(
            doctor=self.request.user, patient=patient, status="completed"
        ).count()

        context["departments"] = Department.objects.filter(is_active=True)

        context["referrals"] = self.object.referrals.select_related(
            "department"
        ).order_by("created_at")

        # Build labeled results for each referral
        for ref in context["referrals"]:
            if ref.result_data:
                fields = DEPARTMENT_FIELDS.get(ref.department.name, [])
                label_map = {f["key"]: f"{f['label']}{' (' + f['unit'] + ')' if f.get('unit') else ''}" for f in fields}
                ref.labeled_results = [
                    {"label": label_map.get(k, k), "value": v}
                    for k, v in ref.result_data.items()
                ]

        referred_ids = list(context["referrals"].values_list("department_id", flat=True))
        if referred_ids:
            context["available_departments"] = context["departments"].exclude(
                id__in=referred_ids
            )
        else:
            context["available_departments"] = context["departments"]

        referral_statuses = [r.status for r in context["referrals"]]
        context["all_referrals_completed"] = (
            len(referral_statuses) > 0
            and all(s == "completed" for s in referral_statuses)
        )

        return context


class AppointmentActionView(DoctorRequiredMixin, View):
    def post(self, request, pk, action):
        appointment = get_object_or_404(
            Booking,
            pk=pk,
            doctor=request.user,
        )

        if action == "accept":
            if appointment.status != "pending":
                messages.warning(request, "Cuộc hẹn này không ở trạng thái chờ.")
                return redirect("doctors:appointment-detail", pk=pk)
            appointment.status = "confirmed"
            messages.success(request, "Xác nhận cuộc hẹn thành công")
        elif action == "cancel":
            if appointment.status not in ["pending", "confirmed"]:
                messages.warning(request, "Không thể hủy cuộc hẹn ở trạng thái này.")
                return redirect("doctors:appointment-detail", pk=pk)
            appointment.status = "cancelled"
            messages.success(request, "Đã huỷ cuộc hẹn thành công")
        elif action == "completed":
            if appointment.status == "completed":
                messages.warning(request, "Cuộc hẹn này đã được hoàn thành.")
                return redirect("doctors:appointment-detail", pk=pk)
            if appointment.status != "confirmed":
                messages.warning(request, "Chỉ có thể hoàn thành cuộc hẹn đã xác nhận.")
                return redirect("doctors:appointment-detail", pk=pk)
            pending_refs = appointment.referrals.exclude(status="completed").exists()
            if pending_refs:
                messages.error(
                    request,
                    "Không thể hoàn thành cuộc hẹn khi vẫn còn chỉ định chuyên khoa chưa có kết quả."
                )
                return redirect("doctors:appointment-detail", pk=pk)
            appointment.status = "completed"
            messages.success(request, "Đã đánh dấu cuộc hẹn là hoàn thành")

        appointment.save()
        # After accepting, redirect to the appointment detail so the doctor can view details
        if action == "accept":
            return redirect("doctors:appointment-detail", pk=appointment.pk)

        # After marking completed, redirect to the prescription creation page for this booking
        if action == "completed":
            return redirect("doctors:prescription-create", booking_id=appointment.pk)

        # Default redirect to dashboard for other actions
        return redirect("doctors:dashboard")


class MyPatientsView(DoctorRequiredMixin, ListView):
    template_name = "doctors/my-patients.html"
    context_object_name = "patients"

    def get_queryset(self):
        # Get unique patients who have appointments with this doctor
        return (
            User.objects.filter(
                patient_appointments__doctor=self.request.user, role="patient"
            )
            .distinct()
            .select_related("profile")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get appointment counts for each patient
        patient_stats = {}
        for patient in context["patients"]:
            stats = Booking.objects.filter(
                doctor=self.request.user, patient=patient
            ).aggregate(
                total_appointments=Count("id"),
                completed_appointments=Count(
                    "id", filter=Q(status="completed")
                ),
            )
            patient_stats[patient.id] = stats
            # Compute age from DOB for display (integer years)
            if getattr(patient, 'profile', None) and patient.profile.dob:
                today = date.today()
                patient.profile.age = (
                    today.year
                    - patient.profile.dob.year
                    - (
                        (today.month, today.day)
                        < (patient.profile.dob.month, patient.profile.dob.day)
                    )
                )
            else:
                if getattr(patient, 'profile', None):
                    patient.profile.age = None
            # Attach last visit (most recent appointment) to patient for template
            last_visit = (
                Booking.objects.filter(doctor=self.request.user, patient=patient)
                .order_by("-appointment_date", "-appointment_time")
                .first()
            )
            patient.last_visit = last_visit
        context["patient_stats"] = patient_stats
        return context


class AppointmentHistoryView(DoctorRequiredMixin, ListView):
    model = Booking
    template_name = "doctors/appointment-history.html"
    context_object_name = "appointments"

    def get_queryset(self):
        return (
            self.model.objects.select_related("patient", "patient__profile")
            .filter(
                doctor=self.request.user, patient_id=self.kwargs["patient_id"]
            )
            .order_by("-appointment_date", "-appointment_time")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["patient"] = get_object_or_404(
            User.objects.select_related("profile"),
            id=self.kwargs["patient_id"],
            role="patient",
        )
        return context


class ReviewListView(DoctorRequiredMixin, ListView):
    model = Review
    template_name = "doctors/reviews.html"
    context_object_name = "reviews"
    paginate_by = 10

    def get_queryset(self):
        return (
            Review.objects.select_related("patient", "patient__profile")
            .filter(doctor=self.request.user)
            .order_by("-created_at")
        )


class DoctorChangePasswordView(DoctorRequiredMixin, View):
    template_name = "doctors/change-password.html"

    def get(self, request, *args, **kwargs):
        return render(
            request, self.template_name, {"form": ChangePasswordForm()}
        )

    def post(self, request, *args, **kwargs):
        form = ChangePasswordForm(request.POST)
        if form.is_valid():
            user = request.user

            if user.check_password(form.cleaned_data["old_password"]):
                user.set_password(form.cleaned_data["new_password"])
                user.save()

                # Update session to prevent logout
                update_session_auth_hash(request, user)

                messages.success(request, "Đổi mật khẩu thành công")
                return redirect("doctors:dashboard")
            else:
                messages.error(request, "Mật khẩu hiện tại không đúng")

        return render(request, self.template_name, {"form": form})


class PrescriptionCreateView(DoctorRequiredMixin, CreateView):
    model = Prescription
    form_class = PrescriptionForm
    template_name = "doctors/add_prescription.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        booking_id = self.kwargs.get("booking_id")
        context["booking"] = get_object_or_404(
            Booking, id=booking_id, doctor=self.request.user
        )
        from pharmacy.models import Medicine
        context["medicines"] = Medicine.objects.filter(is_active=True).order_by("name")
        return context

    def form_valid(self, form):
        booking_id = self.kwargs.get("booking_id")
        booking = get_object_or_404(
            Booking, id=booking_id, doctor=self.request.user
        )

        if booking.status != "completed":
            messages.error(
                self.request,
                "Chỉ có thể thêm đơn thuốc cho các cuộc hẹn đã hoàn thành",
            )
            return redirect("doctors:appointment-detail", pk=booking_id)

        form.instance.booking = booking
        form.instance.doctor = self.request.user
        form.instance.patient = booking.patient

        from bookings.models import PrescriptionMedicine
        from pharmacy.models import Medicine

        selected_meds = self.request.POST.getlist("med_medicine")
        selected_qty = self.request.POST.getlist("med_quantity")
        selected_dosage = self.request.POST.getlist("med_dosage")
        selected_freq = self.request.POST.getlist("med_frequency")
        selected_dur = self.request.POST.getlist("med_duration")
        selected_inst = self.request.POST.getlist("med_instructions")

        lines = []
        prescription = form.save()

        for i in range(len(selected_meds)):
            med_id = selected_meds[i]
            if not med_id:
                continue
            medicine = Medicine.objects.get(pk=int(med_id))
            qty = selected_qty[i] if i < len(selected_qty) else "1"
            dosage = selected_dosage[i] if i < len(selected_dosage) else ""
            freq = selected_freq[i] if i < len(selected_freq) else ""
            dur = selected_dur[i] if i < len(selected_dur) else ""
            inst = selected_inst[i] if i < len(selected_inst) else ""

            PrescriptionMedicine.objects.create(
                prescription=prescription, medicine=medicine,
                quantity=int(qty) if qty.isdigit() else 1,
                dosage=dosage, frequency=freq, duration=dur, instructions=inst,
            )
            line = f"<strong>{medicine.name}</strong> — {dosage}, {freq}, {dur} ngày"
            if inst:
                line += f"<br><em>{inst}</em>"
            lines.append(line)

        prescription.medications = "<ul>" + "".join(f"<li>{l}</li>" for l in lines) + "</ul>" if lines else ""
        prescription.save()
        messages.success(self.request, "Thêm đơn thuốc thành công")
        return redirect("doctors:dashboard")

    def get_success_url(self):
        return reverse_lazy("doctors:dashboard")


class PrescriptionDetailView(DoctorRequiredMixin, DetailView):
    model = Prescription
    template_name = "doctors/prescription_detail.html"
    context_object_name = "prescription"

    def get_queryset(self):
        # Only allow doctors to view prescriptions they wrote
        return Prescription.objects.filter(
            doctor=self.request.user
        ).select_related(
            "doctor",
            "doctor__profile",
            "patient",
            "patient__profile",
            "booking",
        )


class DepartmentQueueView(DepartmentDoctorRequiredMixin, ListView):
    model = Referral
    template_name = "dept/queue.html"
    context_object_name = "referrals"
    paginate_by = 20

    def get_queryset(self):
        dept = self.request.user.profile.department
        return (
            Referral.objects.select_related(
                "booking",
                "booking__patient",
                "booking__patient__profile",
                "general_doctor",
                "department",
            )
            .filter(department=dept)
            .order_by("-created_at")
        )


class ReferralResultView(DepartmentDoctorRequiredMixin, View):
    template_name = "dept/referral_result.html"

    def get_context(self, referral):
        dept_name = referral.department.name
        return {
            "referral": referral,
            "dept_fields": DEPARTMENT_FIELDS.get(dept_name, []),
            "dept_name": dept_name,
        }

    def get(self, request, referral_id):
        dept = request.user.profile.department
        referral = get_object_or_404(
            Referral.objects.select_related(
                "booking",
                "booking__patient",
                "booking__patient__profile",
                "booking__doctor",
                "general_doctor",
                "department",
            ),
            id=referral_id,
            department=dept,
        )
        return render(request, self.template_name, self.get_context(referral))

    def post(self, request, referral_id):
        dept = request.user.profile.department
        referral = get_object_or_404(
            Referral, id=referral_id, department=dept
        )
        action = request.POST.get("action")

        if action == "start":
            referral.status = "in_progress"
            referral.save()
            messages.success(request, "Đã nhận bệnh nhân — đang khám.")

        elif action == "complete":
            fields = DEPARTMENT_FIELDS.get(referral.department.name, [])
            result_data = {}
            result_lines = []
            for f in fields:
                val = request.POST.get(f["key"], "").strip()
                if val:
                    result_data[f["key"]] = val
                    label = f"{f['label']}: {val}"
                    if f.get("unit"):
                        label += f" {f['unit']}"
                    result_lines.append(label)

            if not result_data:
                messages.error(request, "Vui lòng nhập ít nhất một chỉ số.")
                return redirect("doctors:dept-referral", referral_id=referral.id)

            referral.result_data = result_data
            referral.result = "\n".join(result_lines)
            referral.status = "completed"
            referral.save()
            messages.success(request, "Đã hoàn thành và gửi kết quả.")

        else:
            messages.error(request, "Hành động không hợp lệ.")

        return redirect("doctors:dept-dashboard")


class ReferralCreateView(DoctorRequiredMixin, View):
    def post(self, request, appointment_id):
        booking = get_object_or_404(
            Booking, id=appointment_id, doctor=request.user
        )
        department_ids = request.POST.getlist("departments")
        reasons = request.POST.getlist("reasons")

        created = 0
        for i, dept_id in enumerate(department_ids):
            if not dept_id:
                continue
            reason = reasons[i].strip() if i < len(reasons) else ""
            Referral.objects.create(
                booking=booking,
                department_id=dept_id,
                general_doctor=request.user,
                reason=reason,
            )
            created += 1

        if created:
            messages.success(request, f"Đã tạo {created} chỉ định chuyên khoa.")
        return redirect("doctors:appointment-detail", pk=appointment_id)
