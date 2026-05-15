# Báo cáo mô-đun admin

## Mục đích
Tài liệu này mô tả luồng quản trị trong `accounts.views.admin_views.py`: dashboard, quản lý bệnh nhân/bác sĩ/cuộc hẹn, chuyên khoa, đơn thuốc, đánh giá và báo cáo.

## Vị trí
- Views: `accounts/views/admin_views.py`
- URL routes: `doccure/doccure/urls.py`
- Templates: `templates/dashboard/`, `templates/dashboard/reports/`
- Models: `accounts.models.User`, `core.models.Speciality`, `core.models.Review`, `bookings.models.Booking`, `bookings.models.Prescription`
- Kiểm soát truy cập: `accounts.decorators.AdminRequiredMixin`
- Tham chiếu dòng:
  - `accounts/views/admin_views.py`: class admin chính ở dòng 22, 85, 137, 147, 159, 200, 225, 249, 309.
  - `doccure/doccure/urls.py`: route admin ở dòng 43-98.

## Bản đồ route admin
Các route admin được gắn dưới `admin/`:
- `admin/` → `AdminDashboardView` (`admin-dashboard`) [doccure/doccure/urls.py:43, accounts/views/admin_views.py:22]
- `admin/patients/` → `AdminPatientsView` (`admin-patients`) [doccure/doccure/urls.py:48, accounts/views/admin_views.py:85]
- `admin/doctors/` → `AdminDoctorsView` (`admin-doctors`) [doccure/doccure/urls.py:53, accounts/views/admin_views.py:137]
- `admin/appointments/` → `AdminAppointmentsView` (`admin-appointments`) [doccure/doccure/urls.py:58, accounts/views/admin_views.py:147]
- `admin/specialities/` → `AdminSpecialitiesView` (`admin-specialities`) [doccure/doccure/urls.py:63, accounts/views/admin_views.py:159]
- `admin/specialities/create/` → `SpecialityCreateView` (`admin-speciality-create`) [doccure/doccure/urls.py:68, accounts/views/admin_views.py:169]
- `admin/specialities/<int:pk>/update/` → `SpecialityUpdateView` (`admin-speciality-update`) [doccure/doccure/urls.py:73, accounts/views/admin_views.py:179]
- `admin/specialities/<int:pk>/delete/` → `SpecialityDeleteView` (`admin-speciality-delete`) [doccure/doccure/urls.py:78, accounts/views/admin_views.py:188]
- `admin/prescriptions/` → `AdminPrescriptionsView` (`admin-prescriptions`) [doccure/doccure/urls.py:83, accounts/views/admin_views.py:200]
- `admin/reviews/` → `AdminReviewListView` (`admin-reviews`) [doccure/doccure/urls.py:88, accounts/views/admin_views.py:225]
- `admin/reports/appointments/` → `AppointmentReportView` (`admin-appointment-report`) [doccure/doccure/urls.py:93, accounts/views/admin_views.py:249]
- `admin/reports/revenue/` → `RevenueReportView` (`admin-revenue-report`) [doccure/doccure/urls.py:98, accounts/views/admin_views.py:309]

## Kiểm soát truy cập
- Mỗi view admin đều dùng `AdminRequiredMixin`.
- Mixin này chỉ cho phép người dùng admin truy cập dashboard và các trang quản lý.
- Tất cả các `TemplateView`, `ListView`, `CreateView`, `UpdateView`, `DeleteView` trong file đều được bảo vệ.

## Luồng view chi tiết

### 1. `AdminDashboardView`
- Template: `templates/dashboard/index.html`
- Mục đích: tổng hợp số liệu quản trị.
- Dữ liệu:
  - `doctors_count`: dòng 29 - `User.objects.filter(role='doctor').count()`.
  - `patients_count`: dòng 30 - `User.objects.filter(role='patient').count()`.
  - `appointments_count`: dòng 29-30 - `Booking.objects.count()`.
  - `total_revenue`: dòng 35 - `Booking.objects.filter(status='completed').aggregate(total=Sum('doctor__profile__price_per_consultation'))['total']`.
  - `recent_doctors`: dòng 42-51 - lấy 5 bác sĩ mới nhất và tính `earned` bằng tổng booking hoàn thành của từng bác sĩ.
  - `recent_patients`: dòng 54-63 - lấy 5 bệnh nhân mới nhất và tính `last_visit` cùng `total_paid` từ booking hoàn thành.
  - `recent_appointments`: dòng 73 - `Booking.objects.select_related('doctor', 'doctor__profile', 'patient', 'patient__profile').order_by('-appointment_date')[:5]`.
  - `recent_prescriptions`: dòng 78 - `Prescription.objects.select_related('doctor', 'patient', 'booking').order_by('-created_at')[:10]`.

### 2. `AdminPatientsView`
- Template: `templates/dashboard/patients.html`
- Mục đích: danh sách bệnh nhân kèm thống kê.
- Dữ liệu:
  - Truy vấn `User.objects.filter(role='patient').select_related('profile')` (dòng 92).
  - Với mỗi bệnh nhân tính `last_visit` bằng booking mới nhất của họ.
  - Tính `total_paid` bằng `Booking.objects.filter(patient=patient, status='completed').aggregate(total=Sum('doctor__profile__price_per_consultation'))['total']`.
  - Tính `age` từ `patient.profile.dob`.
  - Tính `total_appointments` và `completed_appointments` bằng các truy vấn booking theo bệnh nhân.

### 3. `AdminDoctorsView`
- Template: `templates/dashboard/doctors.html`
- Mục đích: danh sách bác sĩ.
- Dữ liệu: users với `role="doctor"` bằng `User.objects.filter(role='doctor')` (dòng 144).

### 4. `AdminAppointmentsView`
- Template: `templates/dashboard/appointments.html`
- Mục đích: danh sách booking.
- Dữ liệu:
  - Lấy `Booking` bằng `Booking.objects.select_related('doctor', 'doctor__profile', 'patient', 'patient__profile').order_by('-appointment_date', '-appointment_time')` (dòng 154).

### 5. `AdminSpecialitiesView` + CRUD
- Template: `templates/dashboard/specialities.html`
- Mục đích: quản lý chuyên khoa.
- Các view:
  - `SpecialityCreateView`: thêm chuyên khoa.
  - `SpecialityUpdateView`: sửa chuyên khoa.
  - `SpecialityDeleteView`: xóa chuyên khoa.
- Hành vi:
  - Redirect về `admin-specialities` sau thành công.
  - Thông báo thành công bằng `messages.success()`.

### 6. `AdminPrescriptionsView`
- Template: `templates/dashboard/prescriptions.html`
- Mục đích: liệt kê đơn thuốc.
- Dữ liệu: `Prescription.objects.select_related('doctor', 'doctor__profile', 'patient', 'patient__profile', 'booking').order_by('-created_at')` (dòng 207).
- Context bổ sung: `total_prescriptions`, `prescriptions_today`.

### 7. `AdminReviewListView`
- Template: `templates/dashboard/reviews.html`
- Mục đích: liệt kê đánh giá.
- Dữ liệu: `Review.objects.select_related('doctor', 'doctor__profile', 'patient', 'patient__profile', 'booking').order_by('-created_at')` (dòng 232).
- Context bổ sung: `total_reviews`, `average_rating`.

### 8. Báo cáo
#### `AppointmentReportView`
- Template: `templates/dashboard/reports/appointments.html`
- Mục đích: phân tích cuộc hẹn.
- Dữ liệu:
  - Lọc booking trong 30 ngày gần nhất bằng `Booking.objects.filter(appointment_date__range=[start_date, end_date]).select_related('doctor', 'patient')` (dòng 265).
  - Tính thống kê theo tháng bằng `annotate(month=TruncMonth('appointment_date')).values('month').annotate(total=Count('id'), completed=Count('id', filter=Q(status='completed')), cancelled=Count('id', filter=Q(status='cancelled'))).order_by('month')` (dòng 265).
  - Tính trạng thái phân phối bằng `values('status').annotate(count=Count('id'))` (dòng 279).
  - Tính hiệu suất bác sĩ bằng `values('doctor__first_name', 'doctor__last_name').annotate(...)` (dòng 291).
  - Chuyển dữ liệu sang JSON cho biểu đồ.

#### `RevenueReportView`
- Template: `templates/dashboard/reports/revenue.html`
- Mục đích: phân tích doanh thu.
- Dữ liệu:
  - Lọc booking `status="completed"` trong 30 ngày bằng `Booking.objects.filter(status='completed').select_related('doctor__profile')` (dòng 319).
  - Tính doanh thu theo tháng bằng `annotate(month=TruncMonth('appointment_date')).values('month').annotate(revenue=Sum('doctor__profile__price_per_consultation')).order_by('month')` (dòng 324).
  - Tính doanh thu theo bác sĩ bằng `values('doctor__first_name', 'doctor__last_name').annotate(revenue=Sum('doctor__profile__price_per_consultation'), appointments=Count('id')).order_by('-revenue')` (dòng 337).
  - Chuyển `Decimal` sang `float` để JSON-safe (dòng 332, 347).
  - Tính tổng cuộc hẹn, doanh thu trung bình mỗi cuộc và ngày doanh thu cao nhất.
  - `specialization_revenue` hiện là placeholder.

## Ghi chú thiết kế
- Admin dùng generic view cho phần lớn quản lý danh sách và CRUD.
- Báo cáo được tách riêng để phục vụ biểu đồ và phân tích.
- `select_related` được dùng để tránh N+1 query khi hiển thị dữ liệu liên quan.
- Thông báo thành công và redirect được xử lý nhất quán trong các form view.
