# Báo cáo mô-đun bệnh nhân

## Mục đích
Tài liệu này mô tả luồng chính của app `patients`: dashboard, cập nhật hồ sơ, quản lý cuộc hẹn, đổi mật khẩu và đánh giá.

## Vị trí
- Views: `patients/views.py`
- URLs: `patients/urls.py`
- Templates: `templates/patients/`
- Models: `accounts.models.User`, `bookings.models.Booking`, `core.models.Review`
- Kiểm soát truy cập: `mixins.custom_mixins.PatientRequiredMixin`
- Tham chiếu dòng:
  - `patients/urls.py`: route bắt đầu từ dòng 16.
  - `patients/views.py`: view chính ở các dòng 18, 31, 94, 105, 121, 138, 165.

## Bản đồ route
Routes trong `patients/urls.py`:
- `patients/dashboard/` → `PatientDashboardView` (`patients:dashboard`) [patients/urls.py:16, patients/views.py:18]
- `patients/profile-settings/` → `PatientProfileUpdateView` (`patients:profile-setting`) [patients/urls.py:17-20, patients/views.py:31]
- `patients/appointments/<int:pk>/` → `AppointmentDetailView` (`patients:appointment-detail`) [patients/urls.py:22-25, patients/views.py:94]
- `patients/appointments/<int:pk>/cancel/` → `AppointmentCancelView` (`patients:appointment-cancel`) [patients/urls.py:27-30, patients/views.py:105]
- `patients/appointments/<int:pk>/print/` → `AppointmentPrintView` (`patients:appointment-print`) [patients/urls.py:32-35, patients/views.py:121]
- `patients/change-password/` → `ChangePasswordView` (`patients:change-password`) [patients/urls.py:37-40, patients/views.py:138]
- `patients/appointment/<int:booking_id>/review/` → `AddReviewView` (`patients:add-review`) [patients/urls.py:42-45, patients/views.py:165]

## Kiểm soát truy cập
- `PatientRequiredMixin` bảo vệ các view dành riêng cho bệnh nhân.
- Áp dụng cho:
  - `PatientDashboardView`
  - `PatientProfileUpdateView`
  - `ChangePasswordView`
  - `AddReviewView`
- Các view chi tiết, huỷ và in lịch hẹn cũng lọc theo `patient=self.request.user` để đảm bảo quyền sở hữu.

## Luồng view chi tiết

### 1. `PatientDashboardView`
- Template: `templates/patients/dashboard.html`
- Mục đích: hiển thị các cuộc hẹn của bệnh nhân.
- Dữ liệu:
  - Gọi `Booking.objects.select_related('doctor', 'doctor__profile').filter(patient=self.request.user).order_by('-appointment_date', '-appointment_time')` để lấy tất cả booking thuộc bệnh nhân hiện tại và tải sẵn thông tin bác sĩ liên quan.
  - Mục đích: hiển thị lịch sử và các cuộc hẹn sắp tới của bệnh nhân cùng chi tiết bác sĩ.

### 2. `PatientProfileUpdateView`
- Template: `templates/patients/profile-setting.html`
- Mục đích: bệnh nhân cập nhật hồ sơ cá nhân.
- Dữ liệu:
  - `get_object()` trả về `self.request.user`, tức là profile người dùng đang đăng nhập.
  - Form cập nhật dữ liệu `User` và `profile` liên kết.
  - Nếu có `request.FILES['avatar']`, upload avatar mới và gán vào `profile.image`.
  - Cập nhật các trường profile như `dob`, `blood_group`, `gender`, `phone`, `medical_conditions`, `allergies`, `address`, `city`, `state`, `postal_code`, `country`.
  - Lưu cả `user.save()` và `profile.save()` để lưu dữ liệu vào cơ sở dữ liệu.
- Mục đích: cho phép bệnh nhân chỉnh sửa thông tin cá nhân và thông tin y tế cơ bản.
- Context bổ sung: `blood_group_choices`.

### 3. `AppointmentDetailView`
- Template: `templates/patients/appointment-detail.html`
- Mục đích: xem chi tiết lịch hẹn.
- Dữ liệu:
  - Truy vấn `Booking` theo bệnh nhân hiện tại (`filter(patient=self.request.user)`) và dùng `select_related` để tải thông tin bác sĩ, profile bác sĩ, cũng như profile bệnh nhân.
  - Mục đích: hiển thị chi tiết cuộc hẹn kèm đầy đủ thông tin liên quan.

### 4. `AppointmentCancelView`
- Mục đích: bệnh nhân huỷ lịch hẹn.
- Dữ liệu:
  - Gọi `get_object_or_404` với `Booking`, `pk`, `patient=request.user` và `status__in=['pending', 'confirmed']` để đảm bảo chỉ huỷ được lịch hẹn đang chờ hoặc đã xác nhận của chính bệnh nhân.
  - Sau khi lấy booking hợp lệ, đặt `status = 'cancelled'` và lưu.
  - Redirect về `patients:dashboard` với thông báo thành công.

### 5. `AppointmentPrintView`
- Template: `templates/patients/appointment-print.html`
- Mục đích: xuất bản in lịch hẹn.
- Dữ liệu:
  - Dùng cùng queryset với `AppointmentDetailView` để lấy booking bệnh nhân và thông tin liên quan.
  - Render HTML bằng `render_to_string`, truyền `request` để template có access đến dữ liệu phiên.
  - Trả `HttpResponse` chứa nội dung HTML sẵn sàng in.

### 6. `ChangePasswordView`
- Template: `templates/patients/change-password.html`
- Mục đích: thay đổi mật khẩu.
- Dữ liệu:
  - Không truy vấn thêm dữ liệu, chỉ dùng `request.user`.
  - POST kiểm tra `user.check_password(form.cleaned_data['old_password'])` rồi cập nhật `user.set_password(...)`.
  - Gọi `update_session_auth_hash(request, user)` để giữ phiên đang đăng nhập.
- Mục đích: bảo đảm bệnh nhân có thể đổi mật khẩu an toàn mà không bị đăng xuất.

### 7. `AddReviewView`
- Template: `templates/patients/add_review.html`
- Mục đích: gửi đánh giá cho cuộc hẹn đã hoàn thành.
- Dữ liệu:
  - Gọi `get_object_or_404(Booking, id=booking_id, patient=self.request.user)` để lấy booking của bệnh nhân hiện tại.
  - Nếu booking chưa `completed`, không cho phép review.
  - Kiểm tra review trùng bằng `Review.objects.filter(booking=booking).exists()` để tránh đánh giá nhiều lần cùng một cuộc hẹn.
- Luồng:
  - Nếu hợp lệ, gán `review.patient`, `review.doctor`, `review.booking` rồi lưu.
  - Redirect về chi tiết cuộc hẹn.

## Quan hệ dữ liệu
- `Booking.patient` liên kết lịch hẹn với bệnh nhân.
- `Booking.doctor` và `Booking.doctor__profile` dùng để hiển thị thông tin bác sĩ.
- `Review` chỉ tạo khi cuộc hẹn hoàn thành và gắn với `patient` + `doctor`.
- Thông tin hồ sơ bệnh nhân lưu trên đối tượng profile liên kết với `User`.

## Ghi chú thiết kế
- Mô-đun bệnh nhân kết hợp generic view và view thủ công nhẹ.
- Quyền sở hữu được đảm bảo bởi mixin và lọc queryset.
- Flow đánh giá chỉ cho phép review sau khi appointment hoàn thành, tránh tạo review trùng.
- Cập nhật profile xử lý đồng bộ user và profile.
