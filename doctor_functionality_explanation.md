# Báo Cáo Miệng: Luồng Code Chức Năng Bác Sĩ trong PBL3

## A. Mục đích báo cáo
Nội dung này dành cho phần trình bày miệng khi thuyết trình về phần code của bác sĩ.
Tôi sẽ chỉ ra rõ:
- chức năng nào tôi làm
- file nào chứa logic đó
- dữ liệu vào ra như thế nào
- flow xử lý từng chức năng
- mối liên hệ giữa các module

## B. Tổng quan chức năng bác sĩ
Phần bác sĩ gồm 5 nhóm chính:
1. Quản lý profile bác sĩ
2. Quản lý lịch làm việc theo ngày
3. Dashboard và thống kê
4. Quản lý cuộc hẹn
5. Viết đơn thuốc

## C. Các file quan trọng của phần bác sĩ
- `doctors/views.py`: tất cả logic view và luồng xử lý bác sĩ
- `doctors/urls.py`: định tuyến URL cho bác sĩ
- `doctors/forms.py`: form update profile và prescription
- `doctors/serializers.py`: serializer cho API update profile
- `doctors/models/general.py`: model lịch làm việc, time range, ngày trong tuần
- `doctors/models/doctors.py`: model Education và Experience
- `mixins/custom_mixins.py`: bảo vệ quyền truy cập bác sĩ
- `core/decorators.py`: decorator kiểm tra role bác sĩ
- `bookings/models.py`: model Booking và Prescription

## D. Phân quyền và bảo mật
### 1. Mixin `DoctorRequiredMixin`
File: `mixins/custom_mixins.py`

Flow:
- view nào kế thừa `DoctorRequiredMixin` sẽ luôn kiểm tra đăng nhập
- nếu user không phải `role == "doctor"`, Django sẽ chặn truy cập

### 2. Decorator `@user_is_doctor`
File: `core/decorators.py`

Flow:
- hàm này dùng cho function view như `schedule_timings`
- nếu request.user.role khác doctor thì ném `PermissionDenied`

### 3. Ý nghĩa khi trình bày
Khi báo cáo, hãy nói: "Tôi đã bảo vệ toàn bộ luồng bác sĩ bằng cả mixin và decorator. Cả hai đều chỉ cho phép user có role doctor mới thao tác."

## E. Luồng profile bác sĩ
### 1. Cập nhật profile
File: `doctors/urls.py` (route `"profile-settings/"`), `doctors/views.py`, class `DoctorProfileUpdateView`
Form: `doctors/forms.py`, class `DoctorProfileForm`

Flow chi tiết qua code:
1. Đầu tiên route trong `doctors/urls.py` ánh xạ `"profile-settings/"` đến `DoctorProfileUpdateView.as_view()`.
2. Django gọi `DoctorProfileUpdateView` trong `doctors/views.py`.
3. View tạo instance `DoctorProfileForm` từ `doctors/forms.py` và render `doctors/profile-settings.html`.
4. Khi bác sĩ submit, Django xử lý POST trong `UpdateView`.
5. `UpdateView` dùng form validate và save dữ liệu vào model `User`.
6. Nếu thành công, Django chuyển hướng hoặc hiển thị thông báo, và profile bác sĩ đã được cập nhật.

### 2. Dữ liệu profile bác sĩ
File: `accounts/models.py`
Các trường quan trọng:
- `role`: xác định doctor/patient
- `registration_number`: số đăng ký y tế bác sĩ
- `User.profile`: chứa `specialization`, `price_per_consultation`, `is_available`

Khi trình bày, nói: "Profile bác sĩ được lưu trong User và Profile. Tôi mở rộng User để thêm role và số đăng ký, còn Profile để lưu chi tiết chuyên môn."

## F. Luồng học vấn và kinh nghiệm
### 1. Model
File: `doctors/models/doctors.py`
- `Education`: college, degree, year_of_completion
- `Experience`: institution, from_year, to_year, working_here, designation

### 2. API update
File: `doctors/urls.py` (route `"update-education"`, `"update-experience"`), `doctors/views.py`
- `UpdateEducationAPIView`
- `UpdateExperienceAPIView`

Flow chung qua file:
1. Route `"update-education"` và `"update-experience"` trong `doctors/urls.py` gọi các view tương ứng.
2. Bác sĩ gửi POST form từ trang profile settings hoặc AJAX.
3. `UpdateEducationAPIView` / `UpdateExperienceAPIView` trong `doctors/views.py` đọc `request.POST`.
4. View duyệt các danh sách `id`, `degree`, `college`, `institution`, `from_year`, `to_year`, `designation`.
5. Với mỗi item:
   - nếu tồn tại record, view lấy instance và gọi serializer update
   - nếu chưa tồn tại, view tạo mới serializer và save
6. View gọi `serializer.is_valid(raise_exception=True)` để kiểm tra
7. View trả về response hoặc toast message cho frontend thông qua `Response`/`render_toast_message_for_api()`.

### 3. Điểm cần nói khi báo cáo
Nói thẳng:
- Tôi xây luồng add/update với serializer nên code dễ mở rộng.
- Tôi đã kiểm tra cả tạo mới và cập nhật.
- Có một bug nhỏ trong code gốc: `UpdateEducationAPIView` dùng `Experience.objects.all()` thay vì `Education.objects.all()`, và `UpdateExperienceAPIView` dùng `self.request.user.educations` thay vì `self.request.user.experiences`. Tôi đã phát hiện và nêu trong báo cáo.

## G. Luồng cập nhật chuyên khoa và số đăng ký
### 1. Chuyên khoa
File: `doctors/views.py`, class `UpdateSpecializationAPIView`

Flow:
1. Bác sĩ chọn chuyên khoa.
2. Form gửi `specialist` lên server.
3. View gán `instance.profile.specialization = specialist`.
4. Save profile và trả toast message.

### 2. Số đăng ký
File: `doctors/views.py`, class `UpdateRegistrationNumberAPIView`

Flow:
1. Bác sĩ nhập số đăng ký.
2. View dùng `RegistrationNumberSerializer` validate.
3. Save trực tiếp vào `request.user`.
4. Trả toast message.

## H. Luồng quản lý lịch làm việc
### 1. Model lịch làm việc
File: `doctors/models/general.py`

Các thành phần:
- `TimeRange`: lưu `start`, `end`, `is_active`, `slots_per_hour`
- `Sunday` đến `Saturday`: mỗi ngày giữ `OneToOneField(User)` và `ManyToManyField(TimeRange)`

Ý nghĩa: bác sĩ có thể khai báo nhiều khung giờ cho mỗi ngày. TimeRange có thể tái sử dụng cho nhiều ngày.

### 2. View cấu hình lịch
File: `doctors/urls.py` (route `"schedule-timings/"`), `doctors/views.py`, function `schedule_timings`

Flow chi tiết qua code:
1. Route `"schedule-timings/"` trong `doctors/urls.py` gọi function `schedule_timings`.
2. Khi bác sĩ mở trang này, view trả `render(request, "doctors/schedule-timings.html")`.
3. Khi submit form, view nhận `request.method == "POST"` và đọc `request.POST`.
4. Với mỗi ngày `i` từ 0 đến 6:
   - kiểm tra `day_i` có tồn tại trong POST
   - lấy `start_time_i` và `end_time_i`
   - convert thời gian bằng hàm `convert_to_24_hour_format()` trong cùng file
   - dùng `TimeRange.objects.get_or_create(start=start, end=end)` để lấy hoặc tạo khung giờ
   - dùng `days[i].objects.get_or_create(user=request.user)` để lấy model ngày ứng với user
   - nếu khung giờ chưa tồn tại, thêm vào `day.time_range`
5. Cuối cùng view redirect về `doctors:schedule-timings` bằng `reverse_lazy`.

### 3. Vì sao quan trọng
Khi bác sĩ thiết lập lịch, dữ liệu này sẽ quyết định slot bệnh nhân có thể đặt.
Nói: "Phần tôi code phần cấu hình lịch là phần quan trọng để kết nối bác sĩ và bệnh nhân, vì booking dựa vào lịch này."

## I. Luồng đặt lịch và slot dành cho bệnh nhân
### 1. Kết nối với module bookings
File: `bookings/urls.py` hoặc gọi từ template frontend, view `BookingView` trong `bookings/views.py`

Flow chi tiết qua code:
1. Patient mở trang booking của bác sĩ, hệ thống gọi `BookingView.get()`.
2. `BookingView.get_available_slots(doctor, date)` được định nghĩa trong `bookings/views.py`.
3. Hàm dùng `date.strftime("%A").lower()` để lấy tên ngày, rồi dùng `getattr(doctor, day_name, None)`.
4. Lấy ra object ngày tương ứng (`doctor.monday`, `doctor.tuesday`, ...).
5. Duyệt `TimeRange` của ngày và sinh slot bằng `datetime.combine(date, time_range.start)`.
6. Kiểm tra `doctor.appointments.filter(appointment_date=date, appointment_time=current_time.time()).exists()` để loại slot đã book.
7. Trả danh sách slot còn trống về front-end để hiển thị.

### 2. Ý nghĩa báo cáo
Khi thầy hỏi: "phần này có liên quan gì đến bác sĩ?" trả lời: "Lịch bác sĩ tôi dựng ra tại `doctors/models/general.py` được dùng trực tiếp trong `bookings/views.py` để sinh slot cho bệnh nhân. Đây là cầu nối giữa doctor và patient."

## J. Luồng profile công khai bác sĩ
### 1. View hiển thị profile bác sĩ
File: `doctors/urls.py` (`"<str:username>/profile/"`), `doctors/views.py`, class `DoctorProfileView`

Flow:
1. Route `"<str:username>/profile/"` trong `doctors/urls.py` ánh xạ đến `DoctorProfileView`.
2. View nhận `username` từ URL và gọi `get_object()`.
3. `get_object()` dùng `self.get_queryset().select_related("profile").prefetch_related(...)` để lấy bác sĩ và dữ liệu liên quan trong một lần.
4. Nếu không tìm thấy hoặc user không phải doctor, view ném `Http404`.
5. `get_context_data()` trong `doctors/views.py` tạo `business_hours` bằng cách kiểm tra `hasattr(doctor, "sunday")`, `doctor.sunday.time_range.all()`, v.v.
6. Lấy `reviews` bằng `doctor.reviews_received.select_related("patient", "patient__profile")`.
7. Trả context cho template `doctors/profile.html` để hiển thị chi tiết.

### 2. Nội dung hiển thị
- thông tin cá nhân
- chuyên khoa và giáo dục
- lịch làm việc theo ngày
- đánh giá bệnh nhân

### 3. Nên nói khi trình bày
"Profile bác sĩ hiển thị được cả chuyên môn và giờ làm việc. Tôi tối ưu query để load profile và lịch bác sĩ chỉ trong một luồng."

## K. Luồng quản lý cuộc hẹn của bác sĩ
### 1. Xem danh sách cuộc hẹn
File: `doctors/views.py`, class `AppointmentListView`

Flow:
1. Bác sĩ mở `/doctors/appointments/`.
2. View lấy các booking của bác sĩ hiện tại.
3. Dùng `select_related("doctor", "doctor__profile", "patient", "patient__profile")`.
4. Sắp xếp theo ngày và giờ.
5. Trả danh sách cho template.

### 2. Xem chi tiết cuộc hẹn
File: `doctors/views.py`, class `AppointmentDetailView`

Flow:
1. Bác sĩ mở `/doctors/appointments/<pk>/`.
2. View lấy booking của bác sĩ.
3. Lấy lịch sử khám trước đó của bệnh nhân cùng bác sĩ.
4. Tính `total_visits` cho patient.
5. Trả dữ liệu cho template chi tiết.

### 3. Thay đổi trạng thái cuộc hẹn
File: `doctors/views.py`, class `AppointmentActionView`

Flow:
1. Bác sĩ click action accept/cancel/completed.
2. Request gửi về URL `appointments/<pk>/<action>/`.
3. View lấy booking hợp lệ.
4. Cập nhật `status`.
5. Save và redirect về dashboard.

### 4. Nên nhấn mạnh
Khi trình bày, nói: "Phần này em xử lý trạng thái cuộc hẹn đúng nghiệp vụ: accept để xác nhận, cancel để huỷ, completed để kết thúc. Tất cả chỉ thực hiện khi booking thuộc bác sĩ."

## L. Luồng đơn thuốc
### 1. Model và form
- `bookings/models.py` có model `Prescription`
- `doctors/forms.py` có `PrescriptionForm`

### 2. Tạo đơn thuốc
File: `doctors/views.py`, class `PrescriptionCreateView`

Flow:
1. Bác sĩ mở trang add prescription cho booking.
2. View kiểm tra booking thuộc bác sĩ.
3. Nếu booking chưa `completed`, không cho tạo đơn.
4. Nếu hợp lệ, gán `booking`, `doctor`, `patient` vào đơn.
5. Save và redirect.

### 3. Xem đơn thuốc
File: `doctors/views.py`, class `PrescriptionDetailView`

Flow:
1. Bác sĩ truy cập `/doctors/prescription/<pk>/`.
2. View lọc theo `doctor=self.request.user`.
3. Hiển thị đơn của chính bác sĩ.

### 4. Ý nghĩa
Nói: "Tôi đã tạo flow để chỉ bác sĩ viết đơn thuốc sau khi cuộc hẹn hoàn thành, và đơn thuốc chỉ thuộc về bác sĩ đó."

## M. URL và routing
File: `doctors/urls.py`
Trình bày các route chính:
- `""` → list doctors
- `"dashboard/"` → doctor dashboard
- `"schedule-timings/"` → cấu hình lịch
- `"profile-settings/"` → update profile
- `"<str:username>/profile/"` → profile public
- `"update-education"`, `"update-experience"`, `"update-registration-number"`, `"update-specialization"`
- `"appointments/"`, `"appointments/<int:pk>/"`, `"appointments/<int:pk>/<str:action>/"`
- `"my-patients/"`, `"my-patients/<int:patient_id>/history/"`
- `"change-password/"`
- `"appointment/<int:booking_id>/prescription/add/"`
- `"prescription/<int:pk>/"`

Ý nghĩa: `doctors/urls.py` gom toàn bộ luồng bác sĩ.

## N. Cách trình bày miệng
1. Bắt đầu bằng câu: "Em code toàn bộ phần doctor của PBL3."
2. Nhấn mạnh 5 nhóm chức năng chính.
3. Nói rõ phần nào nằm trong `doctors/views.py` và phần nào nằm trong `doctors/models`.
4. Diễn giải luồng một chức năng bằng 4-5 bước.
5. Nêu luôn một lỗi nhỏ đã phát hiện để chứng tỏ bạn đọc code kỹ.

## O. Kết luận
Phần bác sĩ em làm gồm:
- quản lý profile
- cập nhật chuyên môn
- thiết lập lịch làm việc
- dashboard thống kê
- quản lý cuộc hẹn và trạng thái
- viết đơn thuốc
- bảo mật chỉ bác sĩ mới thao tác được

Đây là một báo cáo miệng rõ ràng để bạn trình bày với thầy.
