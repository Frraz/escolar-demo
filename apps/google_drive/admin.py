from django.contrib import admin

from .models import GoogleCredential, GoogleDriveFolder, GoogleSheet


@admin.register(GoogleDriveFolder)
class GoogleDriveFolderAdmin(admin.ModelAdmin):
    list_display = ("name", "kind", "google_drive_folder_id", "student", "school_class", "created_at")
    list_filter = ("kind",)
    search_fields = ("name", "google_drive_folder_id")


@admin.register(GoogleSheet)
class GoogleSheetAdmin(admin.ModelAdmin):
    list_display = ("school_class", "google_sheet_id", "last_synced_at")


@admin.register(GoogleCredential)
class GoogleCredentialAdmin(admin.ModelAdmin):
    list_display = ("account_email", "connected_by", "connected_at", "token_expiry")
    readonly_fields = ("access_token", "refresh_token")
