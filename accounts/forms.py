from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm

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
