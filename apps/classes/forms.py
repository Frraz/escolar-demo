from django import forms

from .models import Class

INPUT_CLASSES = "field-input"
CHECKBOX_CLASSES = "h-4 w-4 rounded border-ink-300 text-brand-600 focus:ring-brand-500 cursor-pointer"


class ClassForm(forms.ModelForm):
    class Meta:
        model = Class
        fields = ["name", "school_year", "shift", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={"class": INPUT_CLASSES, "placeholder": "Ex: 1º Ano A"}),
            "school_year": forms.NumberInput(attrs={"class": INPUT_CLASSES}),
            "shift": forms.Select(attrs={"class": INPUT_CLASSES}),
            "is_active": forms.CheckboxInput(attrs={"class": CHECKBOX_CLASSES}),
        }
