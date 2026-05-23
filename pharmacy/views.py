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
        # Lấy dữ liệu ngữ cảnh (context) để đưa ra giao diện HTML
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()

        # Thống kê tổng số loại thuốc đang hoạt động trong kho
        context["total_medicines"] = Medicine.objects.filter(is_active=True).count()
        # Thống kê số đơn thuốc đang chờ phát (pending)
        context["pending_prescriptions"] = Prescription.objects.filter(status="pending").count()
        # Thống kê số đơn thuốc đã phát hoàn thành (dispensed)
        context["dispensed_prescriptions"] = Prescription.objects.filter(status="dispensed").count()
        # Thống kê số lượng đơn thuốc đã phát trong ngày hôm nay
        context["total_dispensed_today"] = PrescriptionDispensation.objects.filter(
            dispensed_at__date=today
        ).count()

        # Lấy danh sách tối đa 5 đơn thuốc chờ phát mới nhất
        # Sử dụng select_related để tối ưu hóa truy vấn (tránh lỗi N+1 query) bằng cách join bảng bệnh nhân và bác sĩ
        context["recent_prescriptions"] = (
            Prescription.objects.select_related("patient", "patient__profile", "doctor", "doctor__profile")
            .filter(status="pending")
            .order_by("-created_at")[:5]
        )

        return context


class MedicineListView(PharmacistRequiredMixin, ListView):
    """
    Hiển thị danh sách thuốc có trong kho.
    Hỗ trợ phân trang (10 thuốc/trang) và tìm kiếm thuốc theo tên hoặc mã SKU.
    """
    model = Medicine
    template_name = "pharmacy/medicine_list.html"
    context_object_name = "medicines"
    paginate_by = 10

    def get_queryset(self):
        # Mặc định chỉ lấy các loại thuốc đang kích hoạt (is_active=True)
        queryset = Medicine.objects.filter(is_active=True)
        # Lấy từ khóa tìm kiếm 'q' từ tham số GET trên URL
        search_query = self.request.GET.get("q")
        if search_query:
            # Tìm kiếm không phân biệt chữ hoa/thường theo Tên thuốc hoặc mã SKU
            queryset = queryset.filter(
                Q(name__icontains=search_query) | Q(sku__icontains=search_query)
            )
        return queryset.order_by("name")

    def get_context_data(self, **kwargs):
        # Đưa từ khóa tìm kiếm ngược lại giao diện để hiển thị trên thanh tìm kiếm
        context = super().get_context_data(**kwargs)
        context["search_query"] = self.request.GET.get("q", "")
        return context


class MedicineCreateView(PharmacistRequiredMixin, CreateView):
    """
    Thêm một loại thuốc mới vào kho.
    Sử dụng MedicineForm để nhập thông tin và xác thực dữ liệu đầu vào.
    """
    model = Medicine
    form_class = MedicineForm
    template_name = "pharmacy/medicine_form.html"
    success_url = reverse_lazy("pharmacy:medicine-list")

    def form_valid(self, form):
        # Thêm thông báo thành công khi form hợp lệ và lưu dữ liệu thành công
        messages.success(self.request, "Thêm thuốc vào kho thành công.")
        return super().form_valid(form)


class MedicineUpdateView(PharmacistRequiredMixin, UpdateView):
    """
    Cập nhật/Chỉnh sửa thông tin của một loại thuốc đã tồn tại trong kho.
    """
    model = Medicine
    form_class = MedicineForm
    template_name = "pharmacy/medicine_form.html"
    success_url = reverse_lazy("pharmacy:medicine-list")

    def form_valid(self, form):
        # Thêm thông báo thành công khi cập nhật thông tin thuốc thành công
        messages.success(self.request, "Cập nhật thông tin thuốc thành công.")
        return super().form_valid(form)


class PrescriptionListView(PharmacistRequiredMixin, ListView):
    """
    Hiển thị danh sách các đơn thuốc từ bác sĩ gửi xuống.
    Hỗ trợ lọc theo trạng thái đơn thuốc (Chờ phát 'pending' hoặc Đã phát 'dispensed') và phân trang.
    """
    model = Prescription
    template_name = "pharmacy/prescription_list.html"
    context_object_name = "prescriptions"
    paginate_by = 10

    def get_queryset(self):
        # Lấy trạng thái cần lọc từ tham số URL, mặc định là 'pending' (Chờ phát)
        status = self.request.GET.get("status", "pending")
        queryset = Prescription.objects.select_related(
            "patient", "patient__profile", "doctor", "doctor__profile"
        ).filter(status=status)

        # Lấy từ khóa tìm kiếm theo tên bệnh nhân hoặc bác sĩ
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
        # Trả về các tham số hiện tại để giữ trạng thái lọc/tìm kiếm ở giao diện HTML
        context = super().get_context_data(**kwargs)
        context["current_status"] = self.request.GET.get("status", "pending")
        context["search_query"] = self.request.GET.get("q", "")
        return context


class PrescriptionDispenseView(PharmacistRequiredMixin, View):
    """
    Xử lý việc phát thuốc cho bệnh nhân dựa trên đơn thuốc của Bác sĩ.
    - GET: Hiển thị form chi tiết đơn thuốc và danh sách thuốc khả dụng trong kho để lựa chọn.
    - POST: Tiến hành xử lý trừ kho, lưu thông tin hóa đơn phát thuốc trong một Transaction (giao dịch an toàn).
    """
    template_name = "pharmacy/dispense_form.html"

    def get(self, request, pk):
        # Lấy đơn thuốc theo khóa chính (id), nếu không tìm thấy trả về lỗi 404
        prescription = get_object_or_404(
            Prescription.objects.select_related("patient", "patient__profile", "doctor", "doctor__profile"),
            pk=pk
        )
        # Nếu đơn thuốc đã phát rồi thì không cho phép phát lại, chuyển hướng đến trang chi tiết hóa đơn phát thuốc
        if prescription.status == "dispensed":
            messages.warning(request, "Đơn thuốc này đã được phát.")
            return redirect("pharmacy:dispense-detail", pk=prescription.dispensation.pk)

        # Lấy danh sách thuốc đang hoạt động trong kho và có số lượng tồn > 0
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

        # Lấy danh sách mã thuốc (IDs) và số lượng tương ứng được chọn phát từ form gửi lên
        med_ids = request.POST.getlist("medicine_id[]")
        quantities = request.POST.getlist("quantity[]")
        notes = request.POST.get("notes", "")

        # Kiểm tra nếu dược sĩ chưa chọn loại thuốc nào
        if not med_ids or len(med_ids) == 0:
            messages.error(request, "Vui lòng chọn ít nhất một loại thuốc để phát.")
            return self.get(request, pk)

        # Thực thi trong một giao dịch cơ sở dữ liệu (Database Transaction)
        # Nhằm đảm bảo tính toàn vẹn dữ liệu: tất cả thành công hoặc cùng rollback nếu có lỗi xảy ra.
        try:
            with transaction.atomic():
                # 1. Tạo bản ghi Hóa đơn phát thuốc chính (PrescriptionDispensation)
                dispensation = PrescriptionDispensation.objects.create(
                    prescription=prescription,
                    pharmacist=request.user,
                    notes=notes
                )

                # 2. Duyệt qua từng thuốc được chọn phát để kiểm tra tồn kho và trừ số lượng
                for med_id, qty_str in zip(med_ids, quantities):
                    if not med_id or not qty_str:
                        continue
                    qty = int(qty_str)
                    if qty <= 0:
                        raise ValueError("Số lượng phát phải lớn hơn 0.")

                    # Lấy đối tượng thuốc và lock dòng dữ liệu này (select_for_update) để tránh tranh chấp dữ liệu (Race Condition)
                    medicine = Medicine.objects.select_for_update().get(pk=med_id)
                    
                    # Kiểm tra xem trong kho còn đủ thuốc không
                    if medicine.quantity < qty:
                        raise ValueError(f"Thuốc '{medicine.name}' không đủ số lượng trong kho (Còn lại: {medicine.quantity} {medicine.unit}).")

                    # Trừ số lượng tồn kho của thuốc
                    medicine.quantity -= qty
                    medicine.save()

                    # 3. Lưu chi tiết dòng thuốc được phát
                    PrescriptionDispensationItem.objects.create(
                        dispensation=dispensation,
                        medicine=medicine,
                        quantity=qty,
                        price=medicine.price
                    )

                # 4. Cập nhật trạng thái đơn thuốc của bác sĩ thành "đã phát" (dispensed)
                prescription.status = "dispensed"
                prescription.save()

                messages.success(request, "Phát thuốc và cập nhật kho thành công.")
                return redirect("pharmacy:dispense-detail", pk=dispensation.pk)

        except ValueError as e:
            # Bắt các lỗi nghiệp vụ tự định nghĩa (ví dụ: không đủ tồn kho)
            messages.error(request, str(e))
            return self.get(request, pk)
        except Exception as e:
            # Bắt các lỗi hệ thống không mong muốn
            messages.error(request, f"Đã xảy ra lỗi hệ thống: {str(e)}")
            return self.get(request, pk)


class DispensationDetailView(PharmacistRequiredMixin, DetailView):
    """
    Hiển thị thông tin chi tiết của một hóa đơn phát thuốc đã hoàn thành.
    Hiển thị danh sách các thuốc đã phát, đơn giá tại thời điểm phát, tổng chi phí và thông tin Dược sĩ/Bệnh nhân.
    """
    model = PrescriptionDispensation
    template_name = "pharmacy/dispense_detail.html"
    context_object_name = "dispensation"

    def get_queryset(self):
        # Tối ưu hóa truy vấn bằng select_related và prefetch_related để lấy đầy đủ thông tin liên quan trong 1 truy vấn
        return PrescriptionDispensation.objects.select_related(
            "prescription",
            "prescription__patient",
            "prescription__patient__profile",
            "prescription__doctor",
            "prescription__doctor__profile",
            "pharmacist"
        ).prefetch_related("items", "items__medicine")


class PharmacistChangePasswordView(PharmacistRequiredMixin, View):
    """
    Cho phép Dược sĩ thay đổi mật khẩu của chính mình.
    """
    template_name = "pharmacy/change-password.html"

    def get(self, request, *args, **kwargs):
        # Hiển thị form đổi mật khẩu trống
        return render(
            request, self.template_name, {"form": ChangePasswordForm()}
        )

    def post(self, request, *args, **kwargs):
        # Xử lý khi người dùng ấn submit đổi mật khẩu
        form = ChangePasswordForm(request.POST)
        if form.is_valid():
            user = request.user

            # Kiểm tra mật khẩu cũ có chính xác không
            if user.check_password(form.cleaned_data["old_password"]):
                # Thiết lập mật khẩu mới (đã được hash tự động) và lưu lại
                user.set_password(form.cleaned_data["new_password"])
                user.save()

                # Cập nhật session xác thực để người dùng không bị tự động logout sau khi đổi mật khẩu
                update_session_auth_hash(request, user)

                messages.success(request, "Đổi mật khẩu thành công.")
                return redirect("pharmacy:dashboard")
            else:
                messages.error(request, "Mật khẩu hiện tại không đúng.")

        return render(request, self.template_name, {"form": form})
