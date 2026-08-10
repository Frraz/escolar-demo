from django.contrib import admin

from .models import Grade, Subject


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ("student", "subject", "school_class", "term", "value", "updated_at")
    list_filter = ("school_class", "subject", "term")
    search_fields = ("student__full_name",)
