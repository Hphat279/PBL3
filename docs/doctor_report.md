# Báo cáo mô-đun bác sĩ

## Mục đích
Tài liệu này mô tả luồng chức năng chính của app `doctors`: các view, route, kiểm soát truy cập và cách dữ liệu được xây dựng.

## Vị trí
- Views: `doctors/views.py`
- URLs: `doctors/urls.py`
- Templates: `templates/doctors/` và `templates/dashboard/`
- Models: `accounts.models.User`, `doctors.models.*`, `bookings.models.Booking`, `bookings.models.Prescription`
- Kiểm soát truy cập: `mixins.custom_mixins.DoctorRequiredMixin`, `core.decorators.user_is_doctor`
- Tham chiếu dòng:
  - `doctors/urls.py` route bắt đầu từ dòng 26.
  - `doctors/views.py` các class và function chính ở các dòng 58, 110, 139, 148, 181, 210, 358, 375, 393, 472, 488, 516, 541, 573, 597, 625, 664.

## Kiểm soát truy cập
- `DoctorRequiredMixin` bảo vệ hầu hết các view class-based dành cho bác sĩ.
  - Áp dụng cho các view: `DoctorDashboardView`, `AppointmentListView`, `AppointmentDetailView`, `MyPatientsView`, `AppointmentHistoryView`, `DoctorProfileUpdateView`, `DoctorChangePasswordView`, `PrescriptionCreateView`, `PrescriptionDetailView`.
- `@user_is_doctor` bảo vệ view function-based.
  - `schedule_timings` chỉ cho bác sĩ đăng nhập truy cập.

## Bản đồ route quan trọng
Routes trong `doctors/urls.py`:
- `doctors/` → `DoctorsListView` (`doctors:list`) [doctors/urls.py:26, doctors/views.py:393]
- `doctors/dashboard/` → `DoctorDashboardView` (`doctors:dashboard`) [doctors/urls.py:27, doctors/views.py:58]
- `doctors/schedule-timings/` → `schedule_timings` (`doctors:schedule-timings`) [doctors/urls.py:28, doctors/views.py:110]
- `doctors/profile-settings/` → `DoctorProfileUpdateView` (`doctors:profile-setting`) [doctors/urls.py:29, doctors/views.py:139]
- `doctors/<str:username>/profile/` → `DoctorProfileView` (`doctors:doctor-profile`) [doctors/urls.py:34, doctors/views.py:148]
- `doctors/update-education` → `UpdateEducationAPIView` (`doctors:update-education`) [doctors/urls.py:39, doctors/views.py:181]
- `doctors/update-experience` → `UpdateExperienceAPIView` (`doctors:update-experience`) [doctors/urls.py:44, doctors/views.py:210]
- `doctors/update-registration-number` → `UpdateRegistrationNumberAPIView` (`doctors:update-registration-number`) [doctors/urls.py:49, doctors/views.py:358]
- `doctors/update-specialization` → `UpdateSpecializationAPIView` (`doctors:update-specialization`) [doctors/urls.py:54, doctors/views.py:375]
- `doctors/appointments/` → `AppointmentListView` (`doctors:appointments`) [doctors/urls.py:59, doctors/views.py:472]
- `doctors/appointments/<int:pk>/` → `AppointmentDetailView` (`doctors:appointment-detail`) [doctors/urls.py:64, doctors/views.py:488]
- `doctors/appointments/<int:pk>/<str:action>/` → `AppointmentActionView` (`doctors:appointment-action`) [doctors/urls.py:69, doctors/views.py:516]
- `doctors/my-patients/` → `MyPatientsView` (`doctors:my-patients`) [doctors/urls.py:74, doctors/views.py:541]
- `doctors/my-patients/<int:patient_id>/history/` → `AppointmentHistoryView` (`doctors:appointment-history`) [doctors/urls.py:75, doctors/views.py:573]
- `doctors/change-password/` → `DoctorChangePasswordView` (`doctors:change-password`) [doctors/urls.py:80, doctors/views.py:597]
- `doctors/appointment/<int:booking_id>/prescription/add/` → `PrescriptionCreateView` (`doctors:add-prescription`) [doctors/urls.py:85, doctors/views.py:625]
- `doctors/prescription/<int:pk>/` → `PrescriptionDetailView` (`doctors:prescription-detail`) [doctors/urls.py:90, doctors/views.py:664]

## Luồng view chi tiết

### 1. `DoctorDashboardView`
- Template: `templates/doctors/dashboard.html`
- Mục đích: hiển thị dashboard bác sĩ.
- Dữ liệu:
  - `total_patients`: dòng 67 - truy vấn `Booking` để đếm số `patient` khác nhau đã đặt lịch với bác sĩ hiện tại. Mục đích là hiểu quy mô bệnh nhân đã từng tiếp nhận.
  - `today_patients`: dòng 73 - truy vấn `Booking` theo `doctor=self.request.user` và `appointment_date=today`, trả số bệnh nhân hôm nay. Mục đích là xem lượng bệnh nhân trong ngày.
  - `total_appointments`: dòng 77 - truy vấn tổng booking của bác sĩ hiện tại. Mục đích là hiển thị tổng số cuộc hẹn đã tạo cho bác sĩ.
  - `upcoming_appointments`: dòng 83 - truy vấn `Booking` với `select_related('patient', 'patient__profile')` để tải thông tin bệnh nhân và profile, lọc theo `appointment_date__gte=today` và `status` trong `pending`/`confirmed`, sắp xếp theo ngày/giờ. Mục đích là hiển thị danh sách cuộc hẹn sắp tới.
  - `today_appointments`: dòng 94 - truy vấn tương tự nhưng chỉ lấy booking của ngày hôm nay. Mục đích là hiển thị lịch làm việc hôm nay.
- Truy cập: `DoctorRequiredMixin`

### 2. `DoctorsListView`
- Template: `templates/doctors/list.html`
- Mục đích: danh sách bác sĩ công khai cho bệnh nhân tìm kiếm.
- Dữ liệu:
  - Truy vấn `User` để lấy bác sĩ đang hoạt động, không phải superuser, và join sẵn profile (`select_related('profile')`). Mục đích là hiển thị danh sách bác sĩ đủ điều kiện.
  - Nếu có tìm kiếm, dùng `Q(...)` lọc tên, chuyên môn, hoặc thành phố ở profile. Mục đích là mở rộng tìm kiếm theo từ khóa.
  - Nếu có bộ lọc giới tính hoặc chuyên môn, áp dụng `profile__gender__in` và `profile__specialization__in`. Mục đích là cho phép lọc theo đặc tính bác sĩ.
  - Nếu có tham số `sort`, sắp xếp theo `price_per_consultation`, `rating`, hoặc `experience`. Mục đích là thay đổi thứ tự hiển thị theo nhu cầu người dùng.
  - Thêm danh sách `specializations` distinct từ hồ sơ để dùng trong filter checkbox.

### 3. `DoctorProfileView`
- Template: `templates/doctors/profile.html`
- Mục đích: trang hồ sơ bác sĩ công khai.
- Dữ liệu:
  - Thực hiện truy vấn `User` theo `username` và `role=DOCTOR` để đảm bảo đó là tài khoản bác sĩ. Mục đích là bảo mật trang hồ sơ.
  - Dùng `select_related('profile')` và `prefetch_related(...)` để tải sẵn profile, giáo dục, kinh nghiệm và lịch làm việc từng ngày, tránh nhiều lần query khi render.
  - Lấy review của bác sĩ qua `doctor.reviews_received.select_related('patient', 'patient__profile').order_by('-created_at')` để hiển thị đánh giá gần nhất.
- Nếu không tìm thấy bác sĩ, trả `Http404`.

### 4. `schedule_timings`
- Template: `templates/doctors/schedule-timings.html`
- Mục đích: quản lý khung giờ làm việc hàng tuần.
- Luồng:
  - Với POST, lặp 7 ngày, đọc `day_i`, `start_time_i`, `end_time_i`.
  - Chuyển định dạng 12h sang 24h bằng `convert_to_24_hour_format` (dòng 102).
  - Tạo hoặc lấy `TimeRange` với `TimeRange.objects.get_or_create(start=start, end=end)` (dòng 120).
  - Lấy hoặc tạo object ngày bằng `days[i].objects.get_or_create(user=request.user)` (dòng 123).
  - Thêm `time_range` vào `day.time_range` khi chưa tồn tại.
  - Sau khi lưu xong, redirect lại chính route.
- Kiểm soát: `login_required` + `@user_is_doctor`

### 5. `DoctorProfileUpdateView`
- Template: `templates/doctors/profile-settings.html`
- Mục đích: bác sĩ cập nhật thông tin cá nhân.
- Dữ liệu:
  - Model là `accounts.models.User`.
  - Form sử dụng `DoctorProfileForm`.
  - `get_object()` trả về `self.request.user`.
- Truy cập: `DoctorRequiredMixin`

### 6. API cập nhật hồ sơ chuyên môn
- `UpdateEducationAPIView` (dòng 240): đọc nhiều trường POST, cập nhật nếu `ids[i]` tồn tại, nếu không tạo mới.
- `UpdateExperienceAPIView` (dòng 300): đọc nhiều trường POST, cập nhật hoặc tạo mới kinh nghiệm.
- `UpdateRegistrationNumberAPIView` (dòng 358): cập nhật số đăng ký bằng serializer trên `request.user`.
- `UpdateSpecializationAPIView` (dòng 375): cập nhật `instance.profile.specialization` và lưu profile.
- Tất cả đều dùng `DoctorRequiredMixin` và trả về thông báo toast qua HTMX.

### 7. `AppointmentListView`
- Template: `templates/doctors/appointments.html`
- Mục đích: danh sách cuộc hẹn của bác sĩ.
- Dữ liệu:
  - Truy vấn `Booking` chỉ lấy những cuộc hẹn của bác sĩ hiện tại (`filter(doctor=self.request.user)`).
  - Dùng `select_related('doctor', 'doctor__profile', 'patient', 'patient__profile')` để tải sẵn thông tin liên quan bác sĩ và bệnh nhân, tránh truy vấn lặp lại khi hiển thị từng bản ghi.
  - Sắp xếp theo ngày và giờ giảm dần để hiển thị cuộc hẹn gần nhất trước.

### 8. `AppointmentDetailView`
- Template: `templates/doctors/appointment-detail.html`
- Mục đích: xem chi tiết cuộc hẹn.
- Dữ liệu:
  - Lấy `Booking` chi tiết theo `pk` và `doctor=self.request.user` để chỉ cho bác sĩ xem cuộc hẹn của mình.
  - Lấy lịch sử bệnh nhân với cùng bác sĩ bằng query `Booking.objects.select_related('doctor', 'doctor__profile').filter(..., appointment_date__lt=self.object.appointment_date)`.
  - Tính `total_visits` từ các booking `status='completed'` của bệnh nhân này với bác sĩ hiện tại.
- Mục đích: hiển thị đầy đủ ngữ cảnh bệnh nhân và lịch sử điều trị trước đó.

### 9. `AppointmentActionView`
- Mục đích: thay đổi trạng thái cuộc hẹn.
- Dữ liệu:
  - Lấy `Booking` bằng `get_object_or_404(Booking, pk=pk, doctor=request.user, status__in=['pending', 'confirmed'])` (dòng 518). Điều này đảm bảo chỉ thay đổi được cuộc hẹn đang chờ hoặc đã xác nhận, do chính bác sĩ đang quản lý.
  - Cập nhật `appointment.status` theo hành động `accept`, `cancel`, hoặc `completed`.
- Tác dụng:
  - `accept`: đặt cuộc hẹn thành `confirmed`.
  - `cancel`: đặt thành `cancelled`.
  - `completed`: đặt thành `completed`.
- Sau đó redirect về `doctors:dashboard`.

### 10. `MyPatientsView`
- Template: `templates/doctors/my-patients.html`
- Mục đích: danh sách bệnh nhân riêng của bác sĩ.
- Dữ liệu:
  - Truy vấn `User.objects.filter(patient_appointments__doctor=self.request.user, role='patient').distinct().select_related('profile')` (dòng 548). Điều này lấy các bệnh nhân đã có ít nhất một booking với bác sĩ hiện tại.
  - Mỗi bệnh nhân được tính `total_appointments` và `completed_appointments` bằng query `Booking.objects.filter(doctor=self.request.user, patient=patient).aggregate(...)` (dòng 560). Mục đích là hiển thị tần suất và kết quả điều trị.

### 11. `AppointmentHistoryView`
- Template: `templates/doctors/appointment-history.html`
- Mục đích: xem lịch sử cuộc hẹn của một bệnh nhân cụ thể.
- Dữ liệu:
  - Lọc `Booking` bằng `self.model.objects.select_related('patient', 'patient__profile').filter(doctor=self.request.user, patient_id=self.kwargs['patient_id']).order_by('-appointment_date', '-appointment_time')`.
  - Lấy chi tiết bệnh nhân bằng `get_object_or_404(User.objects.select_related('profile'), id=self.kwargs['patient_id'], role='patient')`. Mục đích là hiển thị danh tính và profile của bệnh nhân đang xem lịch sử.

### 12. `DoctorChangePasswordView`
- Template: `templates/doctors/change-password.html`
- Mục đích: đổi mật khẩu bác sĩ.
- Dữ liệu:
  - Không có truy vấn dữ liệu mới, chỉ sử dụng `request.user` để xác thực mật khẩu cũ và cập nhật mật khẩu mới.
- Luồng:
  - GET: hiển thị `ChangePasswordForm`.
  - POST: kiểm tra mật khẩu cũ, lưu mật khẩu mới, gọi `update_session_auth_hash` để giữ phiên đăng nhập.
  - Hiển thị thông báo thành công hoặc lỗi.

### 13. `PrescriptionCreateView`
- Template: `templates/doctors/add_prescription.html`
- Mục đích: tạo đơn thuốc cho cuộc hẹn hoàn thành.
- Dữ liệu:
  - Lấy `Booking` bằng `get_object_or_404(Booking, id=booking_id, doctor=self.request.user)`. Điều này đảm bảo bác sĩ chỉ có thể kê đơn cho cuộc hẹn của chính mình.
  - Kiểm tra `booking.status != 'completed'` để chỉ cho phép tạo đơn khi cuộc hẹn đã hoàn thành.
  - Nếu form hợp lệ, gán `booking`, `doctor`, `patient` vào `Prescription` và lưu.
- Luồng:
  - Lưu đơn thuốc và redirect về chi tiết cuộc hẹn.

### 14. `PrescriptionDetailView`
- Template: `templates/doctors/prescription_detail.html`
- Mục đích: hiển thị đơn thuốc của bác sĩ.
- Dữ liệu:
  - Lấy `Prescription` bằng `Prescription.objects.filter(doctor=self.request.user).select_related('doctor', 'doctor__profile', 'patient', 'patient__profile', 'booking')`. Mục đích là chỉ cho bác sĩ xem đơn thuốc do mình tạo và tải sẵn các thông tin liên quan.
- Hạn chế truy cập: chỉ bác sĩ đã tạo đơn mới xem được.

## Quan hệ dữ liệu
- `accounts.models.User` với `role=DOCTOR` là thực thể bác sĩ.
- `Booking.doctor` liên kết cuộc hẹn với bác sĩ.
- `Booking.patient` liên kết với người bệnh.
- `Prescription` liên kết `doctor`, `patient`, `booking`.
- Lịch làm việc của bác sĩ lưu trong các model ngày trong `doctors.models.general`.

## Ghi chú thiết kế
- Mô-đun bác sĩ vừa chứa trang công khai tìm bác sĩ vừa chứa dashboard quản lý nội bộ.
- Nhiều view dùng generic class-based view để chuẩn hóa list/detail/create/update.
- Các API cập nhật chuyên môn dùng Django REST Framework và trả thông báo HTMX.
- Truy cập bảo mật được kiểm soát bằng mixin và decorator tùy theo loại view.
