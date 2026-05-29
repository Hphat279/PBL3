from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.forms import PasswordResetForm
from django.utils.translation import gettext_lazy as _

from .models import User


class DoctorRegistrationForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super(DoctorRegistrationForm, self).__init__(*args, **kwargs)
        self.fields["first_name"].label = "Tên"
        self.fields["last_name"].label = "Họ"
        self.fields["password1"].label = "Mật khẩu"
        self.fields["password2"].label = "Xác nhận mật khẩu"

        self.fields["first_name"].widget.attrs.update(
            {
                "placeholder": "Nhập tên",
            }
        )
        self.fields["last_name"].widget.attrs.update(
            {
                "placeholder": "Nhập họ",
            }
        )
        self.fields["email"].widget.attrs.update(
            {
                "placeholder": "Nhập email",
            }
        )
        self.fields["password1"].widget.attrs.update(
            {
                "placeholder": "Nhập mật khẩu",
            }
        )
        self.fields["password2"].widget.attrs.update(
            {
                "placeholder": "Xác nhận mật khẩu",
            }
        )

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "username",
            "email",
            "password1",
            "password2",
        ]
        error_messages = {
            "first_name": {
                "required": "Tên là bắt buộc",
                "max_length": "Họ tên quá dài",
            },
            "last_name": {
                "required": "Họ là bắt buộc",
                "max_length": "Họ tên quá dài",
            },
        }

    def save(self, commit=True):
        user = super(UserCreationForm, self).save(commit=False)
        user.role = "doctor"
        if commit:
            user.save()
        return user


class PatientRegistrationForm(UserCreationForm):
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "username",
            "password1",
            "password2",
        ]

    def save(self, commit=True):
        user = super(UserCreationForm, self).save(commit=False)
        user.role = "patient"
        if commit:
            user.save()
        return user


class UserLoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(
        label="Mật khẩu",
        strip=False,
        widget=forms.PasswordInput,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None
        self.fields["username"].widget.attrs.update(
            {"placeholder": "Nhập tên đăng nhập"}
        )
        self.fields["password"].widget.attrs.update(
            {"placeholder": "Nhập mật khẩu"}
        )

    def clean(self, *args, **kwargs):
        username = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")

        if password and password:
            self.user = authenticate(username=username, password=password)

            if self.user is None:
                raise forms.ValidationError("Tên đăng nhập hoặc mật khẩu không chính xác.")
            if not self.user.check_password(password):
                raise forms.ValidationError("Tên đăng nhập hoặc mật khẩu không chính xác.")
            if not self.user.is_active:
                raise forms.ValidationError("Người dùng chưa kích hoạt.")

        return super(UserLoginForm, self).clean(*args, **kwargs)

    def get_user(self):
        return self.user


class GoogleStartForm(forms.Form):
    email = forms.EmailField(label="Gmail", widget=forms.EmailInput(attrs={"placeholder": "Email Gmail của bạn"}))


class GoogleVerifyForm(forms.Form):
    code = forms.CharField(max_length=8, label="Mã xác thực", widget=forms.TextInput(attrs={"placeholder": "Nhập mã xác thực"}))
    first_name = forms.CharField(required=True, label="Tên", widget=forms.TextInput(attrs={"placeholder": "Tên"}))
    last_name = forms.CharField(required=False, label="Họ", widget=forms.TextInput(attrs={"placeholder": "Họ"}))
    username = forms.CharField(required=True, label="Tên đăng nhập", widget=forms.TextInput(attrs={"placeholder": "Tên đăng nhập"}))
    password1 = forms.CharField(required=True, label="Mật khẩu", widget=forms.PasswordInput(attrs={"placeholder": "Mật khẩu"}))
    password2 = forms.CharField(required=True, label="Xác nhận mật khẩu", widget=forms.PasswordInput(attrs={"placeholder": "Xác nhận mật khẩu"}))

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password1")
        p2 = cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Mật khẩu và xác nhận mật khẩu không khớp.")
        return cleaned


class ProfileCompletionForm(forms.Form):
    """Form used to complete required profile information after initial login."""
    email = forms.EmailField(required=True, label="Email", widget=forms.EmailInput(attrs={"placeholder": "Email của bạn"}))
    first_name = forms.CharField(required=True, label="Tên", widget=forms.TextInput(attrs={"placeholder": "Tên"}))
    last_name = forms.CharField(required=True, label="Họ", widget=forms.TextInput(attrs={"placeholder": "Họ"}))
    phone = forms.CharField(required=False, label="Số điện thoại", widget=forms.TextInput(attrs={"placeholder": "Số điện thoại"}))
    dob = forms.DateField(required=False, label="Ngày sinh", widget=forms.DateInput(attrs={"type": "date"}))
    gender = forms.ChoiceField(required=False, label="Giới tính", choices=[('', 'Chọn'), ('male', 'Nam'), ('female', 'Nữ'), ('other', 'Khác')])
    address = forms.CharField(required=False, label="Địa chỉ", widget=forms.TextInput(attrs={"placeholder": "Địa chỉ nơi ở"}))
    city = forms.CharField(required=False, label="Thành phố / Tỉnh", widget=forms.TextInput(attrs={"placeholder": "Thành phố"}))
    state = forms.CharField(required=False, label="Quận / Huyện", widget=forms.TextInput(attrs={"placeholder": "Tỉnh/Quận"}))
    country = forms.CharField(required=False, label="Quốc gia", widget=forms.TextInput(attrs={"placeholder": "Quốc gia"}))
    blood_group = forms.ChoiceField(required=False, label="Nhóm máu", choices=[('', 'Chọn'), ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'), ('O+', 'O+'), ('O-', 'O-'), ('AB+', 'AB+'), ('AB-', 'AB-')])
    allergies = forms.CharField(required=False, label="Dị ứng", widget=forms.Textarea(attrs={"placeholder": "Các dị ứng (nếu có)", "rows": 2}))
    medical_conditions = forms.CharField(required=False, label="Tiền sử bệnh", widget=forms.Textarea(attrs={"placeholder": "Các bệnh mãn tính / tiền sử (nếu có)", "rows": 2}))

    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Allow current user to keep their email; uniqueness will be validated in the view
        return email


class CustomPasswordResetForm(PasswordResetForm):
    """Require that the submitted email exists in the user database and show
    a friendly validation error if not. Note: this reveals whether an email
    is registered.
    """

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise forms.ValidationError(_('Vui lòng nhập địa chỉ email.'), code='required')
        # check existence
        from .models import User

        if not User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(_('Email không đúng với tài khoản của bạn.'), code='invalid')
        return email
