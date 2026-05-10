from datetime import date, timedelta

from django.contrib.auth.models import User
from django.core.validators import RegexValidator, ValidationError
from django.db import models
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _


class Course(models.Model):
    """Model representing a course."""

    course_name = models.CharField(
        _("Course name:"),
        unique=True,
        max_length=200,
        validators=[
            RegexValidator(
                regex=r"^(?![^\w]*$)(?!.*[.,:!?'()&/\-]{2,})[\w.,:!?'()&/\- ]*[A-Za-z0-9][\w.,:!?'()&/\- ]*$",
                message=_(
                    "Enter a valid course name. Must have at least one word. "
                    "Letters, numbers, underscores, spaces and basic punctuation allowed up to 200 characters."
                ),
                code="invalid_course_name",
            ),
        ],
    )
    course_description = models.TextField(
        _("Course description:"),
        max_length=4000,
        validators=[
            RegexValidator(
                regex=r"^[\p{L}\p{N}\p{P}\p{Zs}\n\r]{20,4000}$",
                message=_(
                    "Enter a valid course description. Descriptions may include letters, "
                    "numbers, spaces and punctuation, and must be between 20 and 4000 characters."
                ),
                code="invalid_course_description",
            ),
        ],
    )

    class RenewalPeriodChoices(models.IntegerChoices):  # noqa: E301,D106
        TIER0 = 0, _("no renewal")
        TIER1 = 1, _("1 year")
        TIER3 = 3, _("3 years")

    renewal_period = models.IntegerField(
        _("Renewal period:"),
        choices=RenewalPeriodChoices,
        default=RenewalPeriodChoices.TIER1,
        db_default=RenewalPeriodChoices.TIER1,
    )
    is_mandatory = models.BooleanField(_("Select if this is a mandatory course."), default=False)
    date_added = models.DateField(
        _("Date added to training set:"),
        null=True,
        blank=True,
    )
    timestamp = models.DateTimeField(auto_now=True)

    def clean(self):
        """Raise validation error to disallow future dates and normalize whitespace for string."""
        super().clean()
        if self.course_name:
            # Normalize whitespace: strip leading/trailing and collapse internal whitespace
            self.course_name = " ".join(self.course_name.split())
        if self.course_description:
            self.course_description = self.course_description.strip()
        if self.date_added and self.date_added > now().date():
            raise ValidationError(_("Date added cannot be in the future."))

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):  # noqa: D105
        return self.course_name


class Training(models.Model):
    """Model representing a completed training."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="trainings")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="trainings")
    date_added = models.DateField(auto_now_add=True)
    completion_date = models.DateField(
        _("Course completion date:"), error_messages={"invalid": "Please enter a valid date (DD/MM/YYYY)."}
    )
    training_expiry_date = models.DateField()
    timestamp = models.DateTimeField(auto_now=True)

    class Meta:  # noqa: D106
        constraints = [
            models.UniqueConstraint(
                fields=["user", "course"],
                name="unique_course",
                violation_error_message=_("You already have this course. Please update it rather than adding new."),
            ),
        ]

    @property
    def is_expired(self):
        """Set to True if the training has expired."""
        return self.training_expiry_date < now().date()

    @property
    def is_near_expired(self):
        """Set to True if the training is nearly expired."""
        return now().date() + timedelta(days=15) > self.training_expiry_date >= now().date()

    @property
    def is_nonrecurring(self):
        """Set to True if the training does not need to be renewed."""
        return self.training_expiry_date == self.completion_date

    def clean(self):
        """Raise validation error to disallow future dates and unrealistically old dates."""
        if self.completion_date > now().date():
            raise ValidationError(_("Completion date cannot be in the future."))
        if self.completion_date < date(2000, 1, 1):
            raise ValidationError(_("Completion date is unrealistically old."))

    def save(self, *args, **kwargs):
        """Override save method to set training expiry date and enforce model validation."""
        if not self.training_expiry_date:
            self.training_expiry_date = self.completion_date + timedelta(days=365 * self.course.renewal_period)
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):  # noqa: D105
        return self.user.username + " : " + self.course.course_name
