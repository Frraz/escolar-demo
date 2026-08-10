from django import forms

from .models import DocumentCategory
from .validators import validate_upload

INPUT_CLASSES = "field-input"
FILE_INPUT_CLASSES = (
    "field-input cursor-pointer file:mr-3 file:cursor-pointer file:rounded-md file:border-0 "
    "file:bg-brand-50 file:px-3 file:py-1.5 file:text-sm file:font-medium file:text-brand-700 "
    "hover:file:bg-brand-100"
)


class DocumentUploadForm(forms.Form):
    file = forms.FileField(
        label="Arquivo",
        widget=forms.ClearableFileInput(attrs={"class": FILE_INPUT_CLASSES}),
    )
    category = forms.ChoiceField(
        label="Categoria",
        choices=DocumentCategory.choices,
        initial=DocumentCategory.OUTROS,
        widget=forms.Select(attrs={"class": INPUT_CLASSES}),
    )

    def clean_file(self):
        uploaded_file = self.cleaned_data["file"]
        detected_mime = validate_upload(uploaded_file)
        self.detected_mime_type = detected_mime
        return uploaded_file
