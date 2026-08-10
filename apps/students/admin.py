from django.contrib import admin

from .models import Student


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("full_name", "registration_number", "school_class", "is_active", "created_at")
    list_filter = ("is_active", "school_class")
    search_fields = ("full_name", "registration_number", "email")
