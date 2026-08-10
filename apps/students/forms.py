from django import forms

from .models import Student

INPUT_CLASSES = "field-input"
CHECKBOX_CLASSES = "h-4 w-4 rounded border-ink-300 text-brand-600 focus:ring-brand-500 cursor-pointer"


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            "full_name", "birth_date", "registration_number", "email",
            "phone", "school_class", "is_active",
        ]
        widgets = {
            "full_name": forms.TextInput(attrs={"class": INPUT_CLASSES, "placeholder": "Nome completo do aluno"}),
            "birth_date": forms.DateInput(attrs={"class": INPUT_CLASSES, "type": "date"}),
            "registration_number": forms.TextInput(attrs={"class": INPUT_CLASSES, "placeholder": "Ex: 2026001"}),
            "email": forms.EmailInput(attrs={"class": INPUT_CLASSES, "placeholder": "email@exemplo.com"}),
            "phone": forms.TextInput(attrs={"class": INPUT_CLASSES, "placeholder": "(00) 00000-0000"}),
            "school_class": forms.Select(attrs={"class": INPUT_CLASSES}),
            "is_active": forms.CheckboxInput(attrs={"class": CHECKBOX_CLASSES}),
        }
