from datetime import date, timedelta

import pytest
from django.core.exceptions import ValidationError
from django.utils.timezone import now
from learning.models import Course, Training, validate_course_description


@pytest.mark.django_db
def test_course_save_normalizes_name_and_description():
    course = Course.objects.create(
        course_name="  Fire   Safety   Basics  ",
        course_description="  Mandatory fire safety training for all staff.  ",
        renewal_period=1,
    )

    assert course.course_name == "Fire Safety Basics"
    assert course.course_description == "Mandatory fire safety training for all staff."


@pytest.mark.django_db
def test_course_rejects_future_date_added():
    course = Course(
        course_name="Data Protection",
        course_description="Annual data protection training for all employees.",
        renewal_period=1,
        date_added=now().date() + timedelta(days=1),
    )

    with pytest.raises(ValidationError, match="Date added cannot be in the future"):
        course.save()


def test_validate_course_description_rejects_short_value():
    with pytest.raises(ValidationError, match="Enter a valid course description"):
        validate_course_description("Too short")


def test_validate_course_description_rejects_invalid_character():
    with pytest.raises(ValidationError, match="Enter a valid course description"):
        validate_course_description("Valid description text with a bad tab\tcharacter included.")


def test_validate_course_description_accepts_punctuation_and_newlines():
    validate_course_description("Valid description, with punctuation.\nAnd a second line too.")


@pytest.mark.django_db
def test_validate_course_description_rejects_punctuation_only():
    """Course description must contain more than punctuation and spaces."""
    course = Course(
        course_name="Invalid description, only punctuation.",
        course_description="..., --- ???",
    )
    with pytest.raises(ValidationError, match="Enter a valid course description"):
        course.full_clean()


@pytest.mark.django_db
def test_training_save_calculates_expiry_from_course_renewal(user, recurring_course):
    training = Training.objects.create(
        user=user,
        course=recurring_course,
        completion_date=date(2024, 6, 1),
    )

    assert training.training_expiry_date == date(2025, 6, 1)


@pytest.mark.django_db
def test_training_rejects_future_completion_date(user, recurring_course):
    training = Training(
        user=user,
        course=recurring_course,
        completion_date=now().date() + timedelta(days=1),
        training_expiry_date=now().date() + timedelta(days=366),
    )

    with pytest.raises(ValidationError, match="Completion date cannot be in the future"):
        training.save()


@pytest.mark.django_db
def test_training_rejects_unrealistically_old_completion_date(user, recurring_course):
    training = Training(
        user=user,
        course=recurring_course,
        completion_date=date(1999, 12, 31),
        training_expiry_date=date(2000, 12, 30),
    )

    with pytest.raises(ValidationError, match="Completion date is unrealistically old"):
        training.save()


@pytest.mark.django_db
def test_training_unique_constraint_prevents_duplicate_course_for_same_user(user, recurring_course, user_training):
    duplicate_training = Training(
        user=user,
        course=recurring_course,
        completion_date=date(2024, 7, 1),
        training_expiry_date=date(2025, 7, 1),
    )

    with pytest.raises(ValidationError, match="You already have this course"):
        duplicate_training.save()


@pytest.mark.django_db
def test_training_status_properties(user, recurring_course):
    expired_training = Training.objects.create(
        user=user,
        course=recurring_course,
        completion_date=now().date() - timedelta(days=400),
        training_expiry_date=now().date() - timedelta(days=1),
    )
    near_expiry_training = Training.objects.create(
        user=user,
        course=Course.objects.create(
            course_name="Manual Handling",
            course_description="Manual handling refresher training for operational staff.",
            renewal_period=1,
        ),
        completion_date=now().date() - timedelta(days=350),
        training_expiry_date=now().date() + timedelta(days=10),
    )
    nonrecurring_training = Training.objects.create(
        user=user,
        course=Course.objects.create(
            course_name="Local Induction",
            course_description="A one-off local induction session for joining the team.",
            renewal_period=0,
        ),
        completion_date=now().date() - timedelta(days=20),
    )

    assert expired_training.is_expired is True
    assert near_expiry_training.is_near_expired is True
    assert nonrecurring_training.is_nonrecurring is True


@pytest.mark.django_db
def test_training_str_returns_username_and_course_name(user, recurring_course):
    training = Training.objects.create(
        user=user,
        course=recurring_course,
        completion_date=date(2024, 8, 1),
        training_expiry_date=date(2025, 8, 1),
    )

    assert str(training) == f"{user.username} : {recurring_course.course_name}"
