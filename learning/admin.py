from django.contrib import admin
from learning.models import Course, Training

admin.site.register(Course)


@admin.register(Training)
class TrainingAdmin(admin.ModelAdmin):
    """Make training expiry date and date added visible in the admin as read-only."""

    readonly_fields = (
        "date_added",
        "training_expiry_date",
    )
