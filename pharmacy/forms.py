from django import forms
from .models import Medicine


class MedicineForm(forms.ModelForm):
    """
    tạo mới hoặc cập nhật thông tin thuốc trong kho 
    """
    class Meta:
        model = Medicine
        fields = ["sku", "name", "description", "unit", "quantity", "price", "is_active"]
        widgets = {
            "sku": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nhập mã thuốc (SKU)"}),
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nhập tên thuốc"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Nhập mô tả thuốc"}),
            "unit": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ví dụ: viên, chai, vỉ, hộp"}),
            "quantity": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
            "price": forms.NumberInput(attrs={"class": "form-control", "min": 0, "step": "100"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean_sku(self):
        """
        Hàm kiểm tra  trường mã thuốc (sku).
        Đảm bảo mã SKU là duy nhất và không bị trùng lặp trong cơ sở dữ liệu.
        """
        sku = self.cleaned_data.get("sku")
        if self.instance.pk:
            # Trường hợp cập nhật (Update): Loại trừ chính ID của thuốc hiện tại ra khỏi tầm quét trùng lặp
            if Medicine.objects.filter(sku=sku).exclude(pk=self.instance.pk).exists():
                raise forms.ValidationError("Mã thuốc (SKU) này đã tồn tại.")
        else:
            # Trường hợp tạo mới (Create): Kiểm tra xem mã SKU đã tồn tại chưa
            if Medicine.objects.filter(sku=sku).exists():
                raise forms.ValidationError("Mã thuốc (SKU) này đã tồn tại.")
        return sku
