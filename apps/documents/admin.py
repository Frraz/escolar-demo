from django.contrib import admin

from .models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("name", "student", "category", "mime_type", "size", "created_at")
    list_filter = ("category",)
    search_fields = ("name", "student__full_name", "google_drive_file_id")
    readonly_fields = ("google_drive_file_id", "google_drive_folder_id", "google_drive_url")
