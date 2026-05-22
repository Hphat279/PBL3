from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView, View
from django.urls import reverse_lazy
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.db.models import Q
from django.contrib.auth import update_session_auth_hash

from mixins.custom_mixins import PharmacistRequiredMixin
from bookings.models import Prescription
from patients.forms import ChangePasswordForm
from .models import Medicine, PrescriptionDispensation, PrescriptionDispensationItem
from .forms import MedicineForm


class PharmacistDashboardView(PharmacistRequiredMixin, TemplateView):
    template_name = "pharmacy/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()

        context["total_medicines"] = Medicine.objects.filter(is_active=True).count()
        context["pending_prescriptions"] = Prescription.objects.filter(status="pending").count()
        context["dispensed_prescriptions"] = Prescription.objects.filter(status="dispensed").count()
        context["total_dispensed_today"] = PrescriptionDispensation.objects.filter(
            dispensed_at__date=today
        ).count()

        # Latest pending prescriptions
        context["recent_prescriptions"] = (
            Prescription.objects.select_related("patient", "patient__profile", "doctor", "doctor__profile")
            .filter(status="pending")
            .order_by("-created_at")[:5]
        )

        return context


class MedicineListView(PharmacistRequiredMixin, ListView):
    model = Medicine
    template_name = "pharmacy/medicine_list.html"
    context_object_name = "medicines"
    paginate_by = 10

    def get_queryset(self):
        queryset = Medicine.objects.filter(is_active=True)
        search_query = self.request.GET.get("q")
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) | Q(sku__icontains=search_query)
            )
        return queryset.order_by("name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_query"] = self.request.GET.get("q", "")
        return context


class MedicineCreateView(PharmacistRequiredMixin, CreateView):
    model = Medicine
    form_class = MedicineForm
    template_name = "pharmacy/medicine_form.html"
    success_url = reverse_lazy("pharmacy:medicine-list")

    def form_valid(self, form):
        messages.success(self.request, "Thêm thuốc vào kho thành công.")
        return super().form_valid(form)


class MedicineUpdateView(PharmacistRequiredMixin, UpdateView):
    model = Medicine
    form_class = MedicineForm
    template_name = "pharmacy/medicine_form.html"
    success_url = reverse_lazy("pharmacy:medicine-list")

    def form_valid(self, form):
        messages.success(self.request, "Cập nhật thông tin thuốc thành công.")
        return super().form_valid(form)


class PrescriptionListView(PharmacistRequiredMixin, ListView):
    model = Prescription
    template_name = "pharmacy/prescription_list.html"
    context_object_name = "prescriptions"
    paginate_by = 10

    def get_queryset(self):
        status = self.request.GET.get("status", "pending")
        queryset = Prescription.objects.select_related(
            "patient", "patient__profile", "doctor", "doctor__profile"
        ).filter(status=status)

        search_query = self.request.GET.get("q")
        if search_query:
            queryset = queryset.filter(
                Q(patient__first_name__icontains=search_query)
                | Q(patient__last_name__icontains=search_query)
                | Q(patient__username__icontains=search_query)
                | Q(doctor__first_name__icontains=search_query)
                | Q(doctor__last_name__icontains=search_query)
            )
        return queryset.order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["current_status"] = self.request.GET.get("status", "pending")
        context["search_query"] = self.request.GET.get("q", "")
        return context


class PrescriptionDispenseView(PharmacistRequiredMixin, View):
    template_name = "pharmacy/dispense_form.html"

    def get(self, request, pk):
        prescription = get_object_or_404(
            Prescription.objects.select_related("patient", "patient__profile", "doctor", "doctor__profile"),
            pk=pk
        )
        if prescription.status == "dispensed":
            messages.warning(request, "Đơn thuốc này đã được phát.")
            return redirect("pharmacy:dispense-detail", pk=prescription.dispensation.pk)

        # Get active medicines in stock
        medicines = Medicine.objects.filter(is_active=True, quantity__gt=0)
        return render(request, self.template_name, {
            "prescription": prescription,
            "medicines": medicines
        })

    def post(self, request, pk):
        prescription = get_object_or_404(Prescription, pk=pk)
        if prescription.status == "dispensed":
            messages.warning(request, "Đơn thuốc này đã được phát.")
            return redirect("pharmacy:dispense-detail", pk=prescription.dispensation.pk)

        # Get list of selected medicine ids and their quantities
        med_ids = request.POST.getlist("medicine_id[]")
        quantities = request.POST.getlist("quantity[]")
        notes = request.POST.get("notes", "")

        if not med_ids or len(med_ids) == 0:
            messages.error(request, "Vui lòng chọn ít nhất một loại thuốc để phát.")
            return self.get(request, pk)

        # Process inside a transaction
        try:
            with transaction.atomic():
                dispensation = PrescriptionDispensation.objects.create(
                    prescription=prescription,
                    pharmacist=request.user,
                    notes=notes
                )

                for med_id, qty_str in zip(med_ids, quantities):
                    if not med_id or not qty_str:
                        continue
                    qty = int(qty_str)
                    if qty <= 0:
                        raise ValueError("Số lượng phát phải lớn hơn 0.")

                    # Fetch and lock medicine row for update to prevent race conditions
                    medicine = Medicine.objects.select_for_update().get(pk=med_id)
                    if medicine.quantity < qty:
                        raise ValueError(f"Thuốc '{medicine.name}' không đủ số lượng trong kho (Còn lại: {medicine.quantity} {medicine.unit}).")

                    # Deduct stock
                    medicine.quantity -= qty
                    medicine.save()

                    # Create dispensation item
                    PrescriptionDispensationItem.objects.create(
                        dispensation=dispensation,
                        medicine=medicine,
                        quantity=qty,
                        price=medicine.price
                    )

                # Update prescription status
                prescription.status = "dispensed"
                prescription.save()

                messages.success(request, "Phát thuốc và cập nhật kho thành công.")
                return redirect("pharmacy:dispense-detail", pk=dispensation.pk)

        except ValueError as e:
            messages.error(request, str(e))
            return self.get(request, pk)
        except Exception as e:
            messages.error(request, f"Đã xảy ra lỗi hệ thống: {str(e)}")
            return self.get(request, pk)


class DispensationDetailView(PharmacistRequiredMixin, DetailView):
    model = PrescriptionDispensation
    template_name = "pharmacy/dispense_detail.html"
    context_object_name = "dispensation"

    def get_queryset(self):
        return PrescriptionDispensation.objects.select_related(
            "prescription",
            "prescription__patient",
            "prescription__patient__profile",
            "prescription__doctor",
            "prescription__doctor__profile",
            "pharmacist"
        ).prefetch_related("items", "items__medicine")


class PharmacistChangePasswordView(PharmacistRequiredMixin, View):
    template_name = "pharmacy/change-password.html"

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

                messages.success(request, "Đổi mật khẩu thành công.")
                return redirect("pharmacy:dashboard")
            else:
                messages.error(request, "Mật khẩu hiện tại không đúng.")

        return render(request, self.template_name, {"form": form})
