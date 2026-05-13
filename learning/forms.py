from unicodedata import category

from allauth.account.forms import SignupForm
from django import forms as dj_forms
from django.core.exceptions import ValidationError
from django.forms import ModelForm
from django.forms.widgets import HiddenInput
from django.utils.translation import gettext_lazy as _
from learning.models import Training


def validate_name(value):
    """Validate names without relying on unsupported Unicode regex escapes."""
    error_message = _(
        "Enter a valid name. Letters, spaces, hyphens, and apostrophes only, up to 150 characters. "
        "Must have at least 2 characters and no consecutive spaces or hyphens."
    )

    if not value or value[0] in {" ", "-"} or value[-1] in {" ", "-"}:
        raise ValidationError(error_message, code="invalid_name")

    has_letter = False
    previous_char = ""
    for char in value:
        if char == "'":
            previous_char = char
            continue
        if char in {" ", "-"}:
            if previous_char in {" ", "-"}:
                raise ValidationError(error_message, code="invalid_name")
            previous_char = char
            continue
        if category(char).startswith("L"):
            has_letter = True
            previous_char = char
            continue
        raise ValidationError(error_message, code="invalid_name")

    if not has_letter:
        raise ValidationError(error_message, code="invalid_name")


class HideFieldsMixin:
    """Mixin for hiding fields on a form."""

    hide_fields_kwarg = "hide_fields"
    hideable_fields: list[str] = []

    def __init__(self, *args, **kwargs):
        self.fields = {}
        hide_condition = kwargs.pop(self.hide_fields_kwarg, None)
        super().__init__(*args, **kwargs)

        if hide_condition:
            for field_name in self.hideable_fields:
                if field_name in self.fields:
                    self.fields[field_name].widget = HiddenInput()


class AddTrainingModelForm(HideFieldsMixin, ModelForm):
    """Model form for Add training."""

    hideable_fields = ["user"]

    class Meta:
        """Meta class for AddTrainingModelForm."""

        model = Training
        fields = ["user", "course", "completion_date"]
        widgets = {"completion_date": dj_forms.DateInput(attrs={"type": "date"})}


class ExtendTrainingModelForm(HideFieldsMixin, ModelForm):
    """Model form for Extend training."""

    hideable_fields = ["training_expiry_date"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["training_expiry_date"].required = False

    def clean_training_expiry_date(self):
        """Keep the current expiry date when the hidden field is omitted on submit."""
        training_expiry_date = self.cleaned_data.get("training_expiry_date")
        if training_expiry_date:
            return training_expiry_date
        if self.instance.pk:
            return self.instance.training_expiry_date
        return training_expiry_date

    class Meta:
        """Meta class for ExtendAccessModelForm."""

        model = Training
        fields = ["completion_date", "training_expiry_date"]
        widgets = {"completion_date": dj_forms.DateInput(attrs={"type": "date"})}


class LearningSignupForm(SignupForm):
    """Custom signup form for the Learning app."""

    first_name = dj_forms.CharField(
        required=True,
        min_length=2,
        max_length=150,
        validators=[validate_name],
    )
    last_name = dj_forms.CharField(
        required=True,
        min_length=2,
        max_length=150,
        validators=[validate_name],
    )

    def clean_email(self):
        """Restrict signup email addresses to the organisation domain."""
        email = self.cleaned_data["email"].strip().lower()
        if not email.endswith("@some.org"):
            raise ValidationError(_("Enter an email address ending in @some.org."), code="invalid_domain")
        return email

    def custom_signup(self, request, user):
        """Set the user's name from the form response and save it to their db record."""
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.save()
