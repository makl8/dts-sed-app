from allauth.account.forms import SignupForm
from django.forms import ModelForm
from django.forms.widgets import HiddenInput
from django import forms as dj_forms
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

from learning.models import Training

name_validator = RegexValidator(
    regex=r"^[\p{L}']+(?:[ -][\p{L}']+)*$",
    message=_("Enter a valid name. Letters, spaces, hyphens, and apostrophes only, up to 100 characters. "
            "Must have at least 2 characters and no consecutive spaces or hyphens."),
    code="invalid_name",
)


class AddTrainingModelForm(ModelForm):
    """Model form for Add training."""

    class Meta:
        """Meta class for AddTrainingModelForm."""

        model = Training
        fields = ["user", "course", "completion_date"]
        widgets = {
            "completion_date": dj_forms.DateInput(
                attrs={"type": "date"}
            )
        }

    def __init__(self, *args, **kwargs):
        hide_condition = kwargs.pop("hide_fields", None)
        super(AddTrainingModelForm, self).__init__(*args, **kwargs)
        if hide_condition:
            self.fields["user"].widget = HiddenInput()


class ExtendTrainingModelForm(ModelForm):
    """Model form for Extend training."""

    class Meta:
        """Meta class for ExtendAccessModelForm."""

        model = Training
        fields = ["completion_date", "training_expiry_date"]
        widgets = {
            "completion_date": dj_forms.DateInput(
                attrs={"type": "date"}
            )
        }

    def __init__(self, *args, **kwargs):
        hide_condition = kwargs.pop("hide_fields", None)
        super().__init__(*args, **kwargs)
        if hide_condition:
            self.fields["training_expiry_date"].widget = HiddenInput()


class LearningSignupForm(SignupForm):
    """Custom signup form for the Learning app."""

    first_name = dj_forms.CharField(
        required=True,
        min_length=2,
        max_length=100,
        validators=[name_validator],
    )
    last_name = dj_forms.CharField(
        required=True,
        min_length=2,
        max_length=100,
        validators=[name_validator],
    )

    def custom_signup(self, request, user):
        """Set the user's name from the form response and save it to their db record."""
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.save()
