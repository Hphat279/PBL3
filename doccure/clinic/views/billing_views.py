"""
clinic/views/billing_views.py
Views cho module Tài chính (Billing).

Chức năng:
- Xem danh sách hóa đơn
- Xem chi tiết hóa đơn
- Thanh toán hóa đơn
- In hóa đơn
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.views import View
from django.db.models import Sum

from clinic.models import Invoice, Payment, MedicalRecord, Patient


class DanhSachHoaDon(View):
    """
    Danh sách tất cả hóa đơn, có thể lọc theo trạng thái thanh toán.
    """
    template_name = "clinic/hoa_don_list.html"

    def get(self, request):
        trang_thai = request.GET.get("status", "")
        hoa_dons = Invoice.objects.select_related(
            "patient", "medical_record"
        ).order_by("-created_at")

        if trang_thai:
            hoa_dons = hoa_dons.filter(payment_status=trang_thai)

        # Thống kê nhanh
        tong_doanh_thu = Invoice.objects.filter(
            payment_status="paid"
        ).aggregate(Sum("final_amount"))["final_amount__sum"] or 0

        context = {
            "hoa_dons": hoa_dons,
            "trang_thai_filter": trang_thai,
            "tong_doanh_thu": tong_doanh_thu,
            "chua_thanh_toan": Invoice.objects.filter(payment_status="unpaid").count(),
        }
        return render(request, self.template_name, context)


class ChiTietHoaDon(View):
    """
    Xem chi tiết một hóa đơn và lịch sử các giao dịch thanh toán.
    """
    template_name = "clinic/hoa_don_detail.html"

    def get(self, request, invoice_id):
        hoa_don = get_object_or_404(
            Invoice.objects.select_related("patient", "medical_record__doctor"),
            pk=invoice_id,
        )
        giao_dich = hoa_don.payments.order_by("-paid_at")
        da_thanh_toan = giao_dich.aggregate(Sum("amount"))["amount__sum"] or 0
        con_lai = hoa_don.final_amount - da_thanh_toan

        context = {
            "hoa_don": hoa_don,
            "giao_dich": giao_dich,
            "da_thanh_toan": da_thanh_toan,
            "con_lai": con_lai,
        }
        return render(request, self.template_name, context)


class ThanhToanHoaDon(View):
    """
    Xử lý thanh toán cho hóa đơn.
    Cập nhật trạng thái hóa đơn sau khi thanh toán.
    """

    def post(self, request, invoice_id):
        hoa_don = get_object_or_404(Invoice, pk=invoice_id)
        so_tien = float(request.POST.get("amount", 0))
        phuong_thuc = request.POST.get("payment_method", "cash")
        ma_gd = request.POST.get("transaction_id", "")

        if so_tien <= 0:
            messages.error(request, "Số tiền thanh toán không hợp lệ!")
            return redirect("clinic:hoa-don-chi-tiet", invoice_id=invoice_id)

        # Tạo giao dịch thanh toán
        Payment.objects.create(
            invoice=hoa_don,
            payment_method=phuong_thuc,
            amount=so_tien,
            transaction_id=ma_gd or None,
        )

        # Tính tổng đã thanh toán
        from django.db.models import Sum
        da_tt = hoa_don.payments.aggregate(Sum("amount"))["amount__sum"] or 0

        # Cập nhật trạng thái hóa đơn
        if da_tt >= hoa_don.final_amount:
            hoa_don.payment_status = "paid"
            hoa_don.save()
            messages.success(request, "Hóa đơn đã được thanh toán đầy đủ! ✓")
        else:
            hoa_don.payment_status = "partially_paid"
            hoa_don.save()
            con_lai = hoa_don.final_amount - da_tt
            messages.info(request, f"Đã ghi nhận thanh toán. Còn lại: {con_lai:,.0f}đ")

        return redirect("clinic:hoa-don-chi-tiet", invoice_id=invoice_id)


class TaoHoaDon(View):
    """
    Tự động tạo hóa đơn từ bệnh án.
    Tổng hợp tiền từ dịch vụ + đơn thuốc.
    """

    def post(self, request, record_id):
        benh_an = get_object_or_404(
            MedicalRecord.objects.select_related("patient"),
            pk=record_id,
        )

        # Tính tiền từ dịch vụ đã chỉ định
        tien_dv = sum(
            order.service.price
            for order in benh_an.service_orders.filter(
                status__in=["paid", "completed"]
            ).select_related("service")
        )

        # Tính tiền từ đơn thuốc (nếu có)
        tien_thuoc = 0
        if hasattr(benh_an, "clinic_prescription"):
            tien_thuoc = benh_an.clinic_prescription.tong_tien

        tong_tien = tien_dv + tien_thuoc
        giam_gia = float(request.POST.get("discount", 0))

        hoa_don = Invoice.objects.create(
            patient=benh_an.patient,
            medical_record=benh_an,
            total_amount=tong_tien,
            discount=giam_gia,
            final_amount=tong_tien - giam_gia,
            payment_status="unpaid",
        )

        messages.success(request, f"Đã tạo hóa đơn #{hoa_don.pk}!")
        return redirect("clinic:hoa-don-chi-tiet", invoice_id=hoa_don.pk)
