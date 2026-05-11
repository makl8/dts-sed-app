from datetime import date

import pytest
from django.core.exceptions import ValidationError
from django.forms.widgets import HiddenInput
from learning.forms import AddTrainingModelForm, ExtendTrainingModelForm, LearningSignupForm, validate_name


@pytest.mark.django_db
def test_add_training_form_hides_user_field_when_requested():
    form = AddTrainingModelForm(hide_fields=True)

    assert isinstance(form.fields["user"].widget, HiddenInput)


@pytest.mark.django_db
def test_add_training_form_uses_date_widget_by_default():
    form = AddTrainingModelForm()

    assert form.fields["completion_date"].widget.input_type == "date"
    assert not isinstance(form.fields["user"].widget, HiddenInput)


@pytest.mark.django_db
def test_add_training_form_accepts_valid_data(user, recurring_course):
    form = AddTrainingModelForm(
        data={
            "user": user.pk,
            "course": recurring_course.pk,
            "completion_date": date(2024, 5, 20).isoformat(),
        }
    )

    assert form.is_valid() is True


@pytest.mark.django_db
def test_extend_training_form_hides_expiry_field_when_requested(user_training):
    form = ExtendTrainingModelForm(instance=user_training, hide_fields=True)

    assert isinstance(form.fields["training_expiry_date"].widget, HiddenInput)


@pytest.mark.django_db
def test_extend_training_form_accepts_valid_data(user_training):
    form = ExtendTrainingModelForm(
        data={
            "completion_date": date(2025, 1, 10).isoformat(),
            "training_expiry_date": date(2026, 1, 10).isoformat(),
        },
        instance=user_training,
    )

    assert form.is_valid() is True


@pytest.mark.django_db
def test_extend_training_form_keeps_submitted_expiry_date(user_training):
    submitted_expiry_date = date(2026, 6, 1)
    form = ExtendTrainingModelForm(
        data={
            "completion_date": date(2025, 6, 1).isoformat(),
            "training_expiry_date": submitted_expiry_date.isoformat(),
        },
        instance=user_training,
    )

    assert form.is_valid() is True
    assert form.cleaned_data["training_expiry_date"] == submitted_expiry_date


@pytest.mark.parametrize(
    "invalid_name",
    [
        " Anne",
        "Anne ",
        "-Anne",
        "Anne-",
        "Anne--Marie",
        "Anne  Marie",
        "Anne1",
    ],
)
def test_validate_name_rejects_invalid_values(invalid_name):
    with pytest.raises(ValidationError):
        validate_name(invalid_name)


def test_validate_name_accepts_unicode_letters_and_apostrophes():
    validate_name("Eimear O'Connor")
    validate_name("Jose Alvarez")


def test_learning_signup_form_first_name_rejects_invalid_value():
    form = LearningSignupForm()

    with pytest.raises(ValidationError):
        form.fields["first_name"].clean("A1")


@pytest.mark.django_db
def test_learning_signup_form_custom_signup_sets_names(django_user_model):
    form = LearningSignupForm()
    user = django_user_model.objects.create_user(
        username="new-learner",
        email="new-learner@example.com",
        password="test-pass-123",
    )
    form.cleaned_data = {
        "first_name": "Anne-Marie",
        "last_name": "O'Neill",
    }

    form.custom_signup(request=None, user=user)
    user.refresh_from_db()

    assert user.first_name == "Anne-Marie"
    assert user.last_name == "O'Neill"