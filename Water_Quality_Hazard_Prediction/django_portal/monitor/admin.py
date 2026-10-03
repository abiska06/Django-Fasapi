from django.contrib import admin

from .models import PredictionRecord


@admin.register(PredictionRecord)
class PredictionRecordAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "site_label",
        "predicted_ph",
        "hazard_probability",
        "is_hazard",
    )
    list_filter = ("is_hazard",)
    ordering = ("-created_at",)
