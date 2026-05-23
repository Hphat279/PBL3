from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal

from accounts.models import User
from bookings.models import Booking, Prescription
from pharmacy.models import Medicine, PrescriptionDispensation, PrescriptionDispensationItem
from pharmacy.forms import MedicineForm
from core.templatetags.currency_filters import multiply


class PharmacyTests(TestCase):
   
    def setUp(self):
        # Hàm thiết lập dữ liệu mẫu (môi trường test) trước khi chạy mỗi ca kiểm thử.
        
        # 1. Tạo các tài khoản người dùng mẫu đầy đủ thông tin để pass qua ProfileCompletionMiddleware
        self.pharmacist = User.objects.create_user(
            username="pharmacist_test",
            password="password123",
            role="pharmacist",
            first_name="Dược sĩ",
            last_name="Test",
            email="pharmacist_test@example.com"
        )
        self.doctor = User.objects.create_user(
            username="doctor_test",
            password="password123",
            role="doctor",
            first_name="Bác sĩ",
            last_name="Test",
            email="doctor_test@example.com"
        )
        self.patient = User.objects.create_user(
            username="patient_test",
            password="password123",
            role="patient",
            first_name="Bệnh nhân",
            last_name="Test",
            email="patient_test@example.com"
        )

        # 2. Tạo thuốc mẫu trong kho (cả thuốc đang kích hoạt và đã ẩn)
        self.med1 = Medicine.objects.create(
            sku="MED-001",
            name="Paracetamol",
            unit="viên",
            quantity=100,
            price=Decimal("1500.00")
        )
        self.med2 = Medicine.objects.create(
            sku="MED-002",
            name="Amoxicillin",
            unit="viên",
            quantity=50,
            price=Decimal("5000.00")
        )
        self.inactive_med = Medicine.objects.create(
            sku="MED-003",
            name="Inactive Medicine",
            unit="viên",
            quantity=10,
            price=Decimal("10000.00"),
            is_active=False
        )

        # 3. Tạo một lượt đặt lịch khám (Booking) và Đơn thuốc (Prescription) mẫu ở trạng thái chờ phát (pending)
        self.booking = Booking.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            appointment_date=timezone.now().date(),
            appointment_time="10:00:00",
            status="completed"
        )
        self.prescription = Prescription.objects.create(
            booking=self.booking,
            doctor=self.doctor,
            patient=self.patient,
            symptoms="Đau đầu",
            diagnosis="Sốt nhẹ",
            medications="Paracetamol 500mg x 10 viên",
            status="pending"
        )

    def test_multiply_filter(self):
        """Kiểm thử bộ lọc nhân (multiply filter) dùng cho tính toán giá trị."""
        self.assertEqual(multiply(10, 5), Decimal("50"))
        self.assertEqual(multiply(Decimal("1500.00"), 5), Decimal("7500.00"))
        self.assertEqual(multiply("invalid", 5), 0)

    def test_pharmacist_dashboard_view_permissions(self):
        """Kiểm tra quyền truy cập vào trang Dashboard của Dược sĩ (chỉ cho phép Dược sĩ)."""
        url = reverse("pharmacy:dashboard")

        # Khách vãng lai (Chưa đăng nhập) -> Bị chuyển hướng (302) về trang đăng nhập
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        # Đăng nhập vai trò Bệnh nhân (Patient) -> Bị từ chối truy cập (403)
        self.client.login(username="patient_test", password="password123")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.client.logout()

        # Đăng nhập vai trò Bác sĩ (Doctor) -> Bị từ chối truy cập (403)
        self.client.login(username="doctor_test", password="password123")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.client.logout()

        # Đăng nhập vai trò Dược sĩ (Pharmacist) -> Truy cập thành công (200) và dùng đúng template dashboard.html
        self.client.login(username="pharmacist_test", password="password123")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pharmacy/dashboard.html")

    def test_medicine_list_and_search(self):
        """Kiểm thử xem danh sách thuốc và tính năng tìm kiếm thuốc."""
        self.client.login(username="pharmacist_test", password="password123")
        url = reverse("pharmacy:medicine-list")

        # Xem danh sách cơ bản: Phải chứa các thuốc đang hoạt động và ẩn các thuốc ngừng hoạt động
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Paracetamol")
        self.assertContains(response, "Amoxicillin")
        self.assertNotContains(response, "Inactive Medicine")

        # Kiểm tra tính năng tìm kiếm: Gửi từ khóa "Para" -> Chỉ hiển thị "Paracetamol"
        response = self.client.get(url, {"q": "Para"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Paracetamol")
        self.assertNotContains(response, "Amoxicillin")

    def test_medicine_create_form_and_view(self):
        """Kiểm thử chức năng thêm mới một loại thuốc vào kho."""
        self.client.login(username="pharmacist_test", password="password123")
        url = reverse("pharmacy:medicine-create")

        # Yêu cầu GET hiển thị trang form thêm thuốc
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Gửi dữ liệu POST hợp lệ để tạo mới thuốc
        data = {
            "sku": "MED-004",
            "name": "Ibuprofen",
            "unit": "viên",
            "quantity": 200,
            "price": "2500.00",
            "is_active": True
        }
        response = self.client.post(url, data)
        # Kiểm tra chuyển hướng về trang danh sách sau khi thêm thành công
        self.assertRedirects(response, reverse("pharmacy:medicine-list"))
        # Xác nhận thuốc mới đã tồn tại trong CSDL
        self.assertTrue(Medicine.objects.filter(sku="MED-004").exists())

    def test_prescription_list_views(self):
        """Kiểm thử danh sách đơn thuốc lọc theo trạng thái."""
        self.client.login(username="pharmacist_test", password="password123")
        url = reverse("pharmacy:prescription-list")

        # Lọc các đơn thuốc đang chờ phát (pending): Phải có tên bệnh nhân mẫu
        response = self.client.get(url, {"status": "pending"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.patient.get_full_name())

        # Lọc các đơn thuốc đã phát (dispensed): Hiện tại phải trống/không chứa bệnh nhân này
        response = self.client.get(url, {"status": "dispensed"})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.patient.get_full_name())

    def test_prescription_dispense_form(self):
        """Kiểm thử hiển thị form phát thuốc (GET request)."""
        self.client.login(username="pharmacist_test", password="password123")
        url = reverse("pharmacy:prescription-dispense", args=[self.prescription.pk])

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Form phải chứa thông tin các thuốc mẫu khả dụng để chọn phát
        self.assertContains(response, "Paracetamol")

    def test_successful_prescription_dispensing(self):
        """Kiểm thử kịch bản phát đơn thuốc thành công."""
        self.client.login(username="pharmacist_test", password="password123")
        url = reverse("pharmacy:prescription-dispense", args=[self.prescription.pk])

        # Chọn phát 10 Paracetamol và 5 Amoxicillin
        data = {
            "medicine_id[]": [self.med1.pk, self.med2.pk],
            "quantity[]": [10, 5],
            "notes": "Phát thuốc cho bệnh nhân kèm lời dặn uống sau khi ăn no."
        }

        response = self.client.post(url, data)

        # 1. Xác thực hóa đơn phát thuốc đã được tạo và chuyển hướng đến trang chi tiết hóa đơn
        dispensations = PrescriptionDispensation.objects.filter(prescription=self.prescription)
        self.assertTrue(dispensations.exists())
        dispensation = dispensations.first()
        self.assertRedirects(response, reverse("pharmacy:dispense-detail", args=[dispensation.pk]))

        # 2. Xác thực trạng thái đơn thuốc đổi từ "pending" sang "dispensed"
        self.prescription.refresh_from_db()
        self.assertEqual(self.prescription.status, "dispensed")

        # 3. Xác thực số lượng thuốc tồn kho đã được trừ chính xác (100-10 = 90, 50-5 = 45)
        self.med1.refresh_from_db()
        self.med2.refresh_from_db()
        self.assertEqual(self.med1.quantity, 90)
        self.assertEqual(self.med2.quantity, 45)

        # 4. Xác thực chi tiết phiếu phát thuốc chứa các mặt hàng đã chọn với số lượng đúng
        items = dispensation.items.all()
        self.assertEqual(items.count(), 2)
        self.assertEqual(items.filter(medicine=self.med1).first().quantity, 10)
        self.assertEqual(items.filter(medicine=self.med2).first().quantity, 5)

        # 5. Xác thực tổng hóa đơn tính đúng tiền
        self.assertEqual(dispensation.total_cost, Decimal("10") * Decimal("1500.00") + Decimal("5") * Decimal("5000.00"))

    def test_failed_prescription_dispensing_insufficient_stock(self):
        """Kiểm thử kịch bản phát thuốc thất bại do số lượng yêu cầu vượt quá tồn kho."""
        self.client.login(username="pharmacist_test", password="password123")
        url = reverse("pharmacy:prescription-dispense", args=[self.prescription.pk])

        # Phát 120 viên Paracetamol (Trong kho chỉ có 100 viên)
        data = {
            "medicine_id[]": [self.med1.pk],
            "quantity[]": [120],
            "notes": ""
        }

        response = self.client.post(url, data)
        # Hệ thống phải render lại form kèm theo thông báo lỗi
        self.assertEqual(response.status_code, 200)

        # Số lượng thuốc trong kho không được thay đổi
        self.med1.refresh_from_db()
        self.assertEqual(self.med1.quantity, 100)

        # Trạng thái đơn thuốc vẫn phải là 'pending' (chưa phát)
        self.prescription.refresh_from_db()
        self.assertEqual(self.prescription.status, "pending")

        # Không được phép tạo hóa đơn phát thuốc
        self.assertFalse(PrescriptionDispensation.objects.filter(prescription=self.prescription).exists())

    def test_pharmacist_change_password(self):
        """Kiểm thử tính năng Dược sĩ đổi mật khẩu."""
        self.client.login(username="pharmacist_test", password="password123")
        url = reverse("pharmacy:change-password")

        # GET request
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # POST request gửi mật khẩu mới hợp lệ
        data = {
            "old_password": "password123",
            "new_password": "newpassword123",
            "confirm_password": "newpassword123"
        }
        response = self.client.post(url, data)
        # Phải chuyển hướng về Dashboard sau khi đổi mật khẩu thành công
        self.assertRedirects(response, reverse("pharmacy:dashboard"))

        # Xác minh mật khẩu mới đã được cập nhật thành công trong CSDL
        self.pharmacist.refresh_from_db()
        self.assertTrue(self.pharmacist.check_password("newpassword123"))
