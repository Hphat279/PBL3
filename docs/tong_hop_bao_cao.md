# Báo cáo tổng hợp mô-đun Bác sĩ - Bệnh nhân - Admin

## Mục tiêu
Báo cáo này tổng hợp toàn bộ luồng xử lý và tương tác chính của ba mô-đun: `doctors`, `patients`, và `admin`.
Mục tiêu là giúp người thuyết trình nắm rõ:
- ai gọi đến đâu,
- dữ liệu đi qua như thế nào,
- truy cập được kiểm soát ra sao,
- và mỗi phần trả về gì.

## Cấu trúc chung
- App bác sĩ: `doctors/views.py`, `doctors/urls.py`
- App bệnh nhân: `patients/views.py`, `patients/urls.py`
- App admin: `accounts/views/admin_views.py`, `doccure/doccure/urls.py`
- Dữ liệu chính: `accounts.models.User`, `bookings.models.Booking`, `bookings.models.Prescription`, `core.models.Speciality`, `core.models.Review`
- Kiểm soát truy cập:
  - bác sĩ: `mixins.custom_mixins.DoctorRequiredMixin`, `core.decorators.user_is_doctor`
  - bệnh nhân: `mixins.custom_mixins.PatientRequiredMixin`
  - admin: `accounts.decorators.AdminRequiredMixin`

### Cách báo cáo miệng
- Em sẽ trình bày theo 3 module: bác sĩ, bệnh nhân, admin.
- Với mỗi module, em sẽ chỉ vào file route và file view tương ứng.
- Em sẽ nói rõ: "Route này trong `doctors/urls.py`, xử lý bởi view `X` trong `doctors/views.py`".
- Em sẽ nhấn mạnh các phần chính: quyền truy cập, logic `Booking`, và định tuyến API chuyên môn.

---

## 1. Luồng xử lý mô-đun bác sĩ

### 1.1 Bản đồ route
- `doctors/` → `DoctorsListView` (`doctors/urls.py:26`, `doctors/views.py:393`) (công khai danh sách bác sĩ)
- `doctors/dashboard/` → `DoctorDashboardView` (`doctors/urls.py:27`, `doctors/views.py:58`) (dashboard riêng bác sĩ)
- `doctors/schedule-timings/` → `schedule_timings` (`doctors/urls.py:28`, `doctors/views.py:110`) (quản lý lịch làm việc)
- `doctors/profile-settings/` → `DoctorProfileUpdateView` (`doctors/urls.py:29`, `doctors/views.py:139`) (cập nhật hồ sơ bác sĩ)
- `doctors/<str:username>/profile/` → `DoctorProfileView` (`doctors/urls.py:34`, `doctors/views.py:148`) (xem hồ sơ bác sĩ công khai)
- `doctors/update-education` → `UpdateEducationAPIView` (`doctors/urls.py:39`, `doctors/views.py:240`) (cập nhật học vấn)
- `doctors/update-experience` → `UpdateExperienceAPIView` (`doctors/urls.py:44`, `doctors/views.py:300`) (cập nhật kinh nghiệm)
- `doctors/update-registration-number` → `UpdateRegistrationNumberAPIView` (`doctors/urls.py:49`, `doctors/views.py:358`) (cập nhật số đăng ký y tế)
- `doctors/update-specialization` → `UpdateSpecializationAPIView` (`doctors/urls.py:54`, `doctors/views.py:375`) (cập nhật chuyên môn)
- `doctors/appointments/` → `AppointmentListView` (`doctors/urls.py:59`, `doctors/views.py:472`) (danh sách cuộc hẹn của bác sĩ)
- `doctors/appointments/<int:pk>/` → `AppointmentDetailView` (`doctors/urls.py:64`, `doctors/views.py:488`) (chi tiết cuộc hẹn)
- `doctors/appointments/<int:pk>/<str:action>/` → `AppointmentActionView` (`doctors/urls.py:69`, `doctors/views.py:516`) (xử lý accept/cancel/completed)
- `doctors/my-patients/` → `MyPatientsView` (`doctors/urls.py:74`, `doctors/views.py:541`) (danh sách bệnh nhân của bác sĩ)
- `doctors/my-patients/<int:patient_id>/history/` → `AppointmentHistoryView` (`doctors/urls.py:75`, `doctors/views.py:573`) (lịch sử bệnh nhân)
- `doctors/change-password/` → `DoctorChangePasswordView` (`doctors/urls.py:80`, `doctors/views.py:597`) (đổi mật khẩu)
- `doctors/appointment/<int:booking_id>/prescription/add/` → `PrescriptionCreateView` (`doctors/urls.py:85`, `doctors/views.py:625`) (thêm đơn thuốc)
- `doctors/prescription/<int:pk>/` → `PrescriptionDetailView` (`doctors/urls.py:90`, `doctors/views.py:664`) (xem đơn thuốc)

### 1.2 Quyền hạn và kiểm soát truy cập
- `DoctorRequiredMixin` bảo vệ hầu hết các view class-based của bác sĩ.
- `schedule_timings` dùng `@login_required` và `@user_is_doctor` vì là view function-based.
- Mục tiêu: chỉ bác sĩ mới truy cập được dashboard, lịch, profile, đơn thuốc và thao tác cuộc hẹn.

### 1.3 Luồng chính

#### 1.3.1 `DoctorDashboardView`
Route `doctors/dashboard/` trong `doctors/urls.py:27` gọi `DoctorDashboardView` trong `doctors/views.py:58`, và trong `get_context_data` (doctors/views.py:61) view tính `total_patients` bằng `Booking.objects.filter(doctor=self.request.user).values('patient').distinct().count()`, `today_patients` đếm booking của hôm nay, `total_appointments` là tổng booking của bác sĩ, lấy `upcoming_appointments` và `today_appointments`, đồng thời dùng `select_related('patient', 'patient__profile')` để tải sẵn profile bệnh nhân.

#### 1.3.2 `DoctorsListView`
Route `doctors/` trong `doctors/urls.py:26` gọi `DoctorsListView` trong `doctors/views.py:393`; trong `get_queryset` (doctors/views.py:399) view lọc user role bác sĩ, không lấy superuser và join profile, còn trong `get_context_data` (doctors/views.py:444) view nạp thêm dữ liệu tìm kiếm và phân trang, với các filter tên/chuyên môn/thành phố qua `profile__specialization` và `profile__city`, filter giới tính qua `profile__gender__in`, filter chuyên môn qua `profile__specialization__in`, và nếu có tham số sort thì sẽ sắp xếp theo giá, rating, kinh nghiệm.

#### 1.3.3 `DoctorProfileView`
Route `doctors/<str:username>/profile/` trong `doctors/urls.py:34` gọi `DoctorProfileView` trong `doctors/views.py:148`; `get_object` (doctors/views.py:155) kiểm tra `username` và `role=DOCTOR`, `get_context_data` (doctors/views.py:181) lấy profile, các bản ghi educations, experiences và lịch làm việc bằng `prefetch_related`, và lấy review bác sĩ qua `doctor.reviews_received.select_related('patient', 'patient__profile').order_by('-created_at')`.

#### 1.3.4 `schedule_timings`
Route `doctors/schedule-timings/` trong `doctors/urls.py:28` gọi function `schedule_timings` trong `doctors/views.py:110`; view này nhận POST `day_i`, `start_time_i`, `end_time_i`, dùng helper `convert_to_24_hour_format` trong `doctors/views.py:102` để chuyển giờ, rồi dùng `TimeRange.objects.get_or_create(start, end)` và `days[i].objects.get_or_create(user=request.user)` để lưu khung giờ, sau đó gắn `TimeRange` vào `day.time_range` nếu chưa có.

#### 1.3.5 `DoctorProfileUpdateView`
Route `doctors/profile-settings/` trong `doctors/urls.py:29` gọi `DoctorProfileUpdateView` trong `doctors/views.py:139`; `get_object` (doctors/views.py:144) trả về `self.request.user`, view dùng `DoctorProfileForm` để cập nhật thông tin bác sĩ và nếu upload avatar thì lưu vào `profile.image`.

#### 1.3.6 Cập nhật hồ sơ chuyên môn (API)
Route `doctors/update-education` trong `doctors/urls.py:39` gọi `UpdateEducationAPIView.update` trong `doctors/views.py:250`, route `doctors/update-experience` trong `doctors/urls.py:44` gọi `UpdateExperienceAPIView.update` trong `doctors/views.py:310`, route `doctors/update-registration-number` trong `doctors/urls.py:49` gọi `UpdateRegistrationNumberAPIView.update` trong `doctors/views.py:364`, và route `doctors/update-specialization` trong `doctors/urls.py:54` gọi `UpdateSpecializationAPIView.update` trong `doctors/views.py:381`; view này xử lý POST danh sách học vấn, kinh nghiệm, số đăng ký y tế và chuyên môn, update khi có `id` và tạo mới khi không, rồi lưu `profile.specialization`.

#### 1.3.7 `AppointmentListView`
Route `doctors/appointments/` trong `doctors/urls.py:59` gọi `AppointmentListView` trong `doctors/views.py:472`, và trong `get_queryset` (doctors/views.py:478`) view lấy booking của bác sĩ với `select_related('doctor','doctor__profile','patient','patient__profile')` rồi order by ngày và giờ để hiển thị toàn bộ cuộc hẹn bác sĩ quản lý.

#### 1.3.8 `AppointmentDetailView`
Route `doctors/appointments/<int:pk>/` trong `doctors/urls.py:64` gọi `AppointmentDetailView` trong `doctors/views.py:488`, và trong `get_context_data` (doctors/views.py:493) view lấy booking theo `pk` và `doctor=self.request.user`, sau đó load lịch sử bệnh nhân `patient_history` và tính `total_visits`.

#### 1.3.9 `AppointmentActionView`
Route `doctors/appointments/<int:pk>/<str:action>/` trong `doctors/urls.py:69` gọi `AppointmentActionView` trong `doctors/views.py:516`, và trong `post` (doctors/views.py:517) view lấy booking `pending`/`confirmed` của bác sĩ qua `get_object_or_404`, sau đó nếu action là `accept` chuyển trạng thái `confirmed`, nếu action là `cancel` chuyển `cancelled`, nếu action là `completed` chuyển `completed`.

#### 1.3.10 `MyPatientsView`
Route `doctors/my-patients/` trong `doctors/urls.py:74` gọi `MyPatientsView` trong `doctors/views.py:541`; trong `get_queryset` (doctors/views.py:545) view lấy bệnh nhân đã book với bác sĩ bằng `User.objects.filter(patient_appointments__doctor=self.request.user, role='patient').distinct().select_related('profile')`, còn `get_context_data` (doctors/views.py:555) tính `total_appointments` và `completed_appointments` cho mỗi bệnh nhân.

#### 1.3.11 `AppointmentHistoryView`
Route `doctors/my-patients/<int:patient_id>/history/` trong `doctors/urls.py:75` gọi `AppointmentHistoryView` trong `doctors/views.py:573`; view này dùng `get_queryset` (doctors/views.py:578) và `get_context_data` (doctors/views.py:587) để lấy toàn bộ booking của bệnh nhân đó với bác sĩ hiện tại.

#### 1.3.12 `DoctorChangePasswordView`
Route `doctors/change-password/` trong `doctors/urls.py:80` gọi `DoctorChangePasswordView` trong `doctors/views.py:597`, và trong `post` (doctors/views.py:605) view kiểm tra mật khẩu cũ, cập nhật mật khẩu mới và gọi `update_session_auth_hash`.

#### 1.3.13 `PrescriptionCreateView`
Route `doctors/appointment/<int:booking_id>/prescription/add/` trong `doctors/urls.py:85` gọi `PrescriptionCreateView` trong `doctors/views.py:625`; trong `get_context_data` (doctors/views.py:630) view hiển thị form, `form_valid` (doctors/views.py:638) lấy booking theo `booking_id` và `doctor=self.request.user`, chỉ cho phép khi booking `completed`, rồi lưu `Prescription` với `booking`, `doctor`, `patient`, và `get_success_url` (doctors/views.py:657) điều hướng về trang chi tiết.

#### 1.3.14 `PrescriptionDetailView`
Route `doctors/prescription/<int:pk>/` trong `doctors/urls.py:90` gọi `PrescriptionDetailView` trong `doctors/views.py:664`, và trong `get_queryset` (doctors/views.py:669) view lấy đơn thuốc chỉ của bác sĩ hiện tại, dùng `select_related` để load bác sĩ, profile và booking.

---

## 2. Luồng xử lý mô-đun bệnh nhân

### 2.1 Bản đồ route
- `patients/dashboard/` → `PatientDashboardView` (`patients/urls.py:16`, `patients/views.py:18`)
- `patients/profile-settings/` → `PatientProfileUpdateView` (`patients/urls.py:17-20`, `patients/views.py:31`)
- `patients/appointments/<int:pk>/` → `AppointmentDetailView` (`patients/urls.py:22-25`, `patients/views.py:94`)
- `patients/appointments/<int:pk>/cancel/` → `AppointmentCancelView` (`patients/urls.py:27-30`, `patients/views.py:105`)
- `patients/appointments/<int:pk>/print/` → `AppointmentPrintView` (`patients/urls.py:32-35`, `patients/views.py:121`)
- `patients/change-password/` → `ChangePasswordView` (`patients/urls.py:37-40`, `patients/views.py:138`)
- `patients/appointment/<int:booking_id>/review/` → `AddReviewView` (`patients/urls.py:42-45`, `patients/views.py:165`)

### 2.2 Quyền hạn và kiểm soát truy cập
- `PatientRequiredMixin` bảo vệ dashboard, profile, đổi mật khẩu và thêm review.
- Các view chi tiết, huỷ, in booking đều lọc theo `patient=self.request.user`.
- Mục tiêu: bệnh nhân chỉ thao tác được trên chính lịch hẹn và thông tin của mình.

### 2.3 Luồng chính

#### 2.3.1 `PatientDashboardView`
Route `patients/dashboard/` trong `patients/urls.py:16` gọi `PatientDashboardView` trong `patients/views.py:18`, và trong `get_context_data` (patients/views.py:21) view lấy toàn bộ booking của bệnh nhân bằng `Booking.objects.select_related('doctor', 'doctor__profile').filter(patient=self.request.user).order_by('-appointment_date', '-appointment_time')`, nên đây là phần bệnh nhân xem lịch hẹn đã qua và sắp tới.

#### 2.3.2 `PatientProfileUpdateView`
Route `patients/profile-settings/` trong `patients/urls.py:17-20` gọi `PatientProfileUpdateView` trong `patients/views.py:31`, `get_object` (patients/views.py:37) trả về `request.user`, và trong `form_valid` (patients/views.py:40) view cập nhật user và profile, có thể upload avatar rồi lưu `user` và `profile`, nên đây là phần bệnh nhân quản lý thông tin cá nhân.

#### 2.3.3 `AppointmentDetailView`
Route `patients/appointments/<int:pk>/` trong `patients/urls.py:22-25` gọi `AppointmentDetailView` trong `patients/views.py:94`, và trong `get_queryset` (patients/views.py:99) view lấy booking theo `pk` và `patient=self.request.user`, do đó view chỉ trả về booking của chính bệnh nhân và load profile bác sĩ liên quan, đây là phần xem chi tiết cuộc hẹn.

#### 2.3.4 `AppointmentCancelView`
Route `patients/appointments/<int:pk>/cancel/` trong `patients/urls.py:27-30` gọi `AppointmentCancelView` trong `patients/views.py:105`, và trong `post` (patients/views.py:106) view lấy booking của bệnh nhân với `status` là `pending` hoặc `confirmed`, sau đó đổi trạng thái thành `cancelled`, nên đây là phần bệnh nhân hủy lịch đúng quyền.

#### 2.3.5 `AppointmentPrintView`
Route `patients/appointments/<int:pk>/print/` trong `patients/urls.py:32-35` gọi `AppointmentPrintView` trong `patients/views.py:121`, `get_queryset` (patients/views.py:126) lấy booking giống `AppointmentDetailView`, và `render_to_response` (patients/views.py:131) render HTML để in lịch hẹn, nên đây là phần xuất lịch ra trang in.

#### 2.3.6 `ChangePasswordView`
Route `patients/change-password/` trong `patients/urls.py:37-40` gọi `ChangePasswordView` trong `patients/views.py:138`, và trong `post` (patients/views.py:145) view kiểm tra mật khẩu cũ, cập nhật mật khẩu mới và gọi `update_session_auth_hash`, nên đây là phần đổi mật khẩu an toàn.

#### 2.3.7 `AddReviewView`
Route `patients/appointment/<int:booking_id>/review/` trong `patients/urls.py:42-45` gọi `AddReviewView` trong `patients/views.py:165`, và trong `form_valid` (patients/views.py:170) view lấy booking của bệnh nhân, chỉ cho phép review khi `status == 'completed'`, kiểm tra chưa có review cho booking này trước khi lưu, rồi gán `patient`, `doctor`, `booking` vào review, nên đây là phần bệnh nhân đánh giá bác sĩ sau khi khám xong.

---

## 3. Luồng xử lý mô-đun admin

### 3.1 Bản đồ route
- `admin/` → `AdminDashboardView` (`doccure/doccure/urls.py:43`, `accounts/views/admin_views.py:22`)
- `admin/patients/` → `AdminPatientsView` (`doccure/doccure/urls.py:48`, `accounts/views/admin_views.py:85`)
- `admin/doctors/` → `AdminDoctorsView` (`doccure/doccure/urls.py:53`, `accounts/views/admin_views.py:137`)
- `admin/appointments/` → `AdminAppointmentsView` (`doccure/doccure/urls.py:58`, `accounts/views/admin_views.py:147`)
- `admin/specialities/` → `AdminSpecialitiesView` (`doccure/doccure/urls.py:63`, `accounts/views/admin_views.py:159`)
- `admin/specialities/create/` → `SpecialityCreateView` (`doccure/doccure/urls.py:68`, `accounts/views/admin_views.py:169`)
- `admin/specialities/<int:pk>/update/` → `SpecialityUpdateView` (`doccure/doccure/urls.py:73`, `accounts/views/admin_views.py:179`)
- `admin/specialities/<int:pk>/delete/` → `SpecialityDeleteView` (`doccure/doccure/urls.py:78`, `accounts/views/admin_views.py:188`)
- `admin/prescriptions/` → `AdminPrescriptionsView` (`doccure/doccure/urls.py:83`, `accounts/views/admin_views.py:200`)
- `admin/reviews/` → `AdminReviewListView` (`doccure/doccure/urls.py:88`, `accounts/views/admin_views.py:225`)
- `admin/reports/appointments/` → `AppointmentReportView` (`doccure/doccure/urls.py:93`, `accounts/views/admin_views.py:249`)
- `admin/reports/revenue/` → `RevenueReportView` (`doccure/doccure/urls.py:98`, `accounts/views/admin_views.py:309`)

### 3.2 Quyền hạn và kiểm soát truy cập
- Tất cả admin view dùng `AdminRequiredMixin`.
- Mục tiêu: chỉ admin mới truy cập được dashboard và các trang quản lý tổng.

### 3.3 Luồng chính

#### 3.3.1 `AdminDashboardView`
Route `admin/` trong `doccure/doccure/urls.py:43` gọi `AdminDashboardView` trong `accounts/views/admin_views.py:22`, và trong `get_context_data` (accounts/views/admin_views.py:25) view tổng hợp số bác sĩ, số bệnh nhân, số cuộc hẹn và doanh thu từ booking đã `completed`, đồng thời lấy danh sách recent để hiển thị trên dashboard.

#### 3.3.2 `AdminPatientsView`
Route `admin/patients/` trong `doccure/doccure/urls.py:48` gọi `AdminPatientsView` trong `accounts/views/admin_views.py:85`, và trong `get_queryset` (accounts/views/admin_views.py:91) view lấy user role=`patient` và tính `last_visit`, `total_paid`, `age`, `total_appointments`, `completed_appointments` cho mỗi bệnh nhân.

#### 3.3.3 `AdminDoctorsView`
Route `admin/doctors/` trong `doccure/doccure/urls.py:53` gọi `AdminDoctorsView` trong `accounts/views/admin_views.py:137`, và trong `get_queryset` (accounts/views/admin_views.py:143) view lấy tất cả user role=`doctor`.

#### 3.3.4 `AdminAppointmentsView`
Route `admin/appointments/` trong `doccure/doccure/urls.py:58` gọi `AdminAppointmentsView` trong `accounts/views/admin_views.py:147`, và trong `get_queryset` (accounts/views/admin_views.py:153) view lấy toàn bộ booking có doctor và patient profile, sau đó sắp xếp theo ngày/giờ giảm dần.

#### 3.3.5 `AdminSpecialitiesView` và CRUD
Route `admin/specialities/` trong `doccure/doccure/urls.py:63` gọi `AdminSpecialitiesView` trong `accounts/views/admin_views.py:159`, còn route `admin/specialities/create/` gọi `SpecialityCreateView` trong `accounts/views/admin_views.py:169`, route `admin/specialities/<int:pk>/update/` gọi `SpecialityUpdateView` trong `accounts/views/admin_views.py:179`, và route `admin/specialities/<int:pk>/delete/` gọi `SpecialityDeleteView` trong `accounts/views/admin_views.py:188`, tức là phần admin quản lý danh mục chuyên môn với tạo, cập nhật và xóa chuyên khoa.

#### 3.3.6 `AdminPrescriptionsView`
Route `admin/prescriptions/` trong `doccure/doccure/urls.py:83` gọi `AdminPrescriptionsView` trong `accounts/views/admin_views.py:200`, và trong `get_queryset`/`get_context_data` (accounts/views/admin_views.py:206, 215) view lấy toàn bộ `Prescription` kèm bác sĩ, bệnh nhân và booking.

#### 3.3.7 `AdminReviewListView`
Route `admin/reviews/` trong `doccure/doccure/urls.py:88` gọi `AdminReviewListView` trong `accounts/views/admin_views.py:225`, và trong `get_queryset`/`get_context_data` (accounts/views/admin_views.py:231, 240) view lấy toàn bộ `Review` kèm bác sĩ, bệnh nhân và booking.

#### 3.3.8 `AppointmentReportView`
Route `admin/reports/appointments/` trong `doccure/doccure/urls.py:93` gọi `AppointmentReportView` trong `accounts/views/admin_views.py:249`, và trong `get_context_data` (accounts/views/admin_views.py:252) view lọc booking trong 30 ngày gần nhất, tính thống kê theo tháng, trạng thái và hiệu suất bác sĩ, rồi chuyển kết quả sang JSON cho biểu đồ.

#### 3.3.9 `RevenueReportView`
Route `admin/reports/revenue/` trong `doccure/doccure/urls.py:98` gọi `RevenueReportView` trong `accounts/views/admin_views.py:309`, và trong `get_context_data` (accounts/views/admin_views.py:312) view lọc booking `status='completed'` trong 30 ngày, tính doanh thu theo tháng và theo bác sĩ, rồi chuyển `Decimal` sang `float` để trả JSON.

---

---

## 4. Các tương tác chính giữa bác sĩ - bệnh nhân - admin

- Bệnh nhân đặt lịch: lưu `Booking` với `doctor`, `patient`, `appointment_date`, `appointment_time`.
- Bác sĩ xem lịch: luôn lọc `Booking` theo `doctor=self.request.user`.
- Bệnh nhân xem/hủy lịch: luôn lọc `Booking` theo `patient=self.request.user`.
- Bác sĩ kê đơn: tạo `Prescription` gắn `booking`, `doctor`, `patient` sau khi booking `completed`.
- Bệnh nhân đánh giá: tạo `Review` chỉ khi booking `completed` và chưa có review cho booking đó.
- Admin giám sát: xem danh sách, báo cáo và quản lý chuyên khoa.

## 5. Kết luận cho phần thuyết trình

1. Bắt đầu bằng chức năng **bác sĩ**: dashboard, quản lý lịch, quản lý cuộc hẹn, kê đơn.
2. Sang phần **bệnh nhân**: dashboard của bệnh nhân, profile, in/hủy lịch, đánh giá.
3. Kết thúc bằng phần **admin**: dashboard tổng quan, quản lý người dùng, báo cáo.
4. Nhấn mạnh các điểm:
   - quyền truy cập khác nhau (`DoctorRequiredMixin`, `PatientRequiredMixin`, `AdminRequiredMixin`),
   - tương tác dữ liệu quanh `Booking`,
   - và các quy tắc nghiệp vụ: chỉ bác sĩ mới duyệt cuộc hẹn, chỉ bệnh nhân mới huỷ lịch của mình, chỉ admin mới xem báo cáo.

---

## 6. Gợi ý học nhanh cho báo cáo
- Nói rõ mỗi view làm gì: lấy dữ liệu nào, trả dữ liệu nào, hiển thị template nào.
- Khi nói từng view, chỉ vào file và line đã ghi trong báo cáo để thầy dễ theo dõi.
- Nhấn vào `select_related`/`prefetch_related` là kỹ thuật tối ưu truy vấn.
- Nhấn vào `status` của booking: `pending`, `confirmed`, `completed`, `cancelled`.
- Nhấn vào review chỉ sau khi `completed` và không trùng.
- Nhấn vào admin là nơi tổng hợp và giám sát, không can thiệp trực tiếp vào lịch hẹn bác sĩ/bệnh nhân.
- Kết luận: bác sĩ quản lý lịch và kê đơn, bệnh nhân xem/hủy/in lịch và đánh giá, admin xem báo cáo tổng và quản lý chuyên khoa.