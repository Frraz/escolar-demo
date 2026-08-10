from django.contrib import admin

from .models import Class


@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ("name", "school_year", "shift", "is_active")
    list_filter = ("is_active", "shift", "school_year")
    search_fields = ("name",)
