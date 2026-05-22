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
        # Create users
        self.pharmacist = User.objects.create_user(
            username="pharmacist_test",
            password="password123",
            role="pharmacist",
            first_name="Dược sĩ",
            last_name="Test"
        )
        self.doctor = User.objects.create_user(
            username="doctor_test",
            password="password123",
            role="doctor"
        )
        self.patient = User.objects.create_user(
            username="patient_test",
            password="password123",
            role="patient"
        )

        # Create active medicines
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

        # Create a booking & prescription
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
        """Test the custom multiply filter."""
        self.assertEqual(multiply(10, 5), Decimal("50"))
        self.assertEqual(multiply(Decimal("1500.00"), 5), Decimal("7500.00"))
        self.assertEqual(multiply("invalid", 5), 0)

    def test_pharmacist_dashboard_view_permissions(self):
        """Test that only pharmacists can access the dashboard."""
        url = reverse("pharmacy:dashboard")

        # Anonymous user gets redirected to login
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        # Patient gets 403 permission denied
        self.client.login(username="patient_test", password="password123")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.client.logout()

        # Doctor gets 403 permission denied
        self.client.login(username="doctor_test", password="password123")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.client.logout()

        # Pharmacist succeeds
        self.client.login(username="pharmacist_test", password="password123")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pharmacy/dashboard.html")

    def test_medicine_list_and_search(self):
        """Test listing and searching medicines."""
        self.client.login(username="pharmacist_test", password="password123")
        url = reverse("pharmacy:medicine-list")

        # Basic list
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Paracetamol")
        self.assertContains(response, "Amoxicillin")
        self.assertNotContains(response, "Inactive Medicine") # Should exclude inactive medicines

        # Search query
        response = self.client.get(url, {"q": "Para"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Paracetamol")
        self.assertNotContains(response, "Amoxicillin")

    def test_medicine_create_form_and_view(self):
        """Test adding a new medicine."""
        self.client.login(username="pharmacist_test", password="password123")
        url = reverse("pharmacy:medicine-create")

        # GET request
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # POST request (valid data)
        data = {
            "sku": "MED-004",
            "name": "Ibuprofen",
            "unit": "viên",
            "quantity": 200,
            "price": "2500.00",
            "is_active": True
        }
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse("pharmacy:medicine-list"))
        self.assertTrue(Medicine.objects.filter(sku="MED-004").exists())

    def test_prescription_list_views(self):
        """Test listing prescriptions by status."""
        self.client.login(username="pharmacist_test", password="password123")
        url = reverse("pharmacy:prescription-list")

        # Test pending prescriptions
        response = self.client.get(url, {"status": "pending"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.patient.get_full_name())

        # Test dispensed prescriptions (currently empty)
        response = self.client.get(url, {"status": "dispensed"})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.patient.get_full_name())

    def test_prescription_dispense_form(self):
        """Test prescription dispensing form GET request."""
        self.client.login(username="pharmacist_test", password="password123")
        url = reverse("pharmacy:prescription-dispense", args=[self.prescription.pk])

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Paracetamol")

    def test_successful_prescription_dispensing(self):
        """Test successful dispensing of a prescription."""
        self.client.login(username="pharmacist_test", password="password123")
        url = reverse("pharmacy:prescription-dispense", args=[self.prescription.pk])

        data = {
            "medicine_id[]": [self.med1.pk, self.med2.pk],
            "quantity[]": [10, 5],
            "notes": "Phát thuốc cho bệnh nhân kèm lời dặn uống sau khi ăn no."
        }

        response = self.client.post(url, data)

        # Verify redirection to dispensation detail page
        dispensations = PrescriptionDispensation.objects.filter(prescription=self.prescription)
        self.assertTrue(dispensations.exists())
        dispensation = dispensations.first()
        self.assertRedirects(response, reverse("pharmacy:dispense-detail", args=[dispensation.pk]))

        # Verify prescription status changed to dispensed
        self.prescription.refresh_from_db()
        self.assertEqual(self.prescription.status, "dispensed")

        # Verify stock deduction
        self.med1.refresh_from_db()
        self.med2.refresh_from_db()
        self.assertEqual(self.med1.quantity, 90)
        self.assertEqual(self.med2.quantity, 45)

        # Verify items created
        items = dispensation.items.all()
        self.assertEqual(items.count(), 2)
        self.assertEqual(items.filter(medicine=self.med1).first().quantity, 10)
        self.assertEqual(items.filter(medicine=self.med2).first().quantity, 5)

        # Verify total cost property
        self.assertEqual(dispensation.total_cost, Decimal("10") * Decimal("1500.00") + Decimal("5") * Decimal("5000.00"))

    def test_failed_prescription_dispensing_insufficient_stock(self):
        """Test dispensing fails when requested quantity is greater than stock."""
        self.client.login(username="pharmacist_test", password="password123")
        url = reverse("pharmacy:prescription-dispense", args=[self.prescription.pk])

        data = {
            "medicine_id[]": [self.med1.pk],
            "quantity[]": [120], # Stock is 100
            "notes": ""
        }

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200) # Re-renders form on error

        # Verify stock not modified
        self.med1.refresh_from_db()
        self.assertEqual(self.med1.quantity, 100)

        # Verify prescription status still pending
        self.prescription.refresh_from_db()
        self.assertEqual(self.prescription.status, "pending")

        # Verify dispensation not created
        self.assertFalse(PrescriptionDispensation.objects.filter(prescription=self.prescription).exists())

    def test_pharmacist_change_password(self):
        """Test pharmacist change password view."""
        self.client.login(username="pharmacist_test", password="password123")
        url = reverse("pharmacy:change-password")

        # GET request
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # POST request (valid)
        data = {
            "old_password": "password123",
            "new_password": "newpassword123",
            "confirm_password": "newpassword123"
        }
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse("pharmacy:dashboard"))

        # Verify password changed
        self.pharmacist.refresh_from_db()
        self.assertTrue(self.pharmacist.check_password("newpassword123"))
