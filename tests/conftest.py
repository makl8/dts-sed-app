from datetime import date

import pytest

from learning.models import Course, Training


@pytest.fixture
def password():
    return "test-pass-123"


@pytest.fixture
def user(django_user_model, password):
    return django_user_model.objects.create_user(
        username="learner",
        email="learner@example.com",
        password=password,
    )


@pytest.fixture
def other_user(django_user_model, password):
    return django_user_model.objects.create_user(
        username="other-user",
        email="other@example.com",
        password=password,
    )


@pytest.fixture
def recurring_course():
    return Course.objects.create(
        course_name="Fire Safety",
        course_description="Mandatory fire safety training for all staff.",
        renewal_period=1,
    )


@pytest.fixture
def nonrecurring_course():
    return Course.objects.create(
        course_name="Welcome Induction",
        course_description="One-off induction training for all new joiners.",
        renewal_period=0,
    )


@pytest.fixture
def user_training(user, recurring_course):
    return Training.objects.create(
        user=user,
        course=recurring_course,
        completion_date=date(2024, 1, 15),
        training_expiry_date=date(2025, 1, 14),
    )


@pytest.fixture
def other_training(other_user, nonrecurring_course):
    return Training.objects.create(
        user=other_user,
        course=nonrecurring_course,
        completion_date=date(2024, 2, 20),
        training_expiry_date=date(2024, 2, 20),
    )