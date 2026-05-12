from datetime import date, timedelta

import pytest
from django.urls import reverse
from learning.models import Training


@pytest.mark.django_db
def test_home_page_regular_user_message(client, user):
    client.force_login(user)

    response = client.get(reverse("home"))

    assert response.status_code == 200
    assert "your own" in response.content.decode()
    assert "signed in as an administrator" not in response.content.decode()


@pytest.mark.django_db
def test_home_page_admin_user_message(client, django_user_model, password):
    admin_user = django_user_model.objects.create_user(
        username="admin-user",
        email="admin@example.com",
        password=password,
        is_staff=True,
        is_superuser=True,
    )
    client.force_login(admin_user)

    response = client.get(reverse("home"))

    assert response.status_code == 200
    assert "administrator" in response.content.decode()
    assert reverse("admin:index") in response.content.decode()
    assert "manage all application data" in response.content.decode()


@pytest.mark.django_db
def test_training_home_anonymous_renders_page(client):
    response = client.get(reverse("training"))

    assert response.status_code == 200
    assert "learning/index.html" in [template.name for template in response.templates]
    assert "training_list" not in response.context


@pytest.mark.django_db
def test_training_home_lists_only_current_user_training(client, user, user_training, recurring_course):
    client.force_login(user)

    response = client.get(reverse("training"))

    assert response.status_code == 200
    assert list(response.context["training_list"]) == [user_training]
    assert response.context["course_dict"] == {recurring_course.id: recurring_course.course_name}


@pytest.mark.django_db
def test_course_detail_requires_login(client, recurring_course):
    response = client.get(reverse("course", args=[recurring_course.pk]))

    assert response.status_code == 302
    assert reverse("account_login") in response.url


@pytest.mark.django_db
def test_course_detail_sets_xframe_header_for_authenticated_user(client, user, recurring_course):
    client.force_login(user)

    response = client.get(reverse("course", args=[recurring_course.pk]))

    assert response.status_code == 200
    assert response.context["course"] == recurring_course
    assert response.headers["X-Frame-Options"] == "SAMEORIGIN"


@pytest.mark.django_db
def test_add_training_requires_login(client):
    response = client.get(reverse("add_training"))

    assert response.status_code == 302
    assert reverse("account_login") in response.url


@pytest.mark.django_db
def test_add_training_get_populates_context(client, user):
    client.force_login(user)

    response = client.get(reverse("add_training"))

    assert response.status_code == 200
    assert "learning/add_training.html" in [template.name for template in response.templates]
    assert response.context["success"] is False
    assert response.context["confirmation_message"] is None
    assert "Add training" in response.content.decode()


@pytest.mark.django_db
def test_add_training_post_creates_training_and_sets_expiry(client, user, nonrecurring_course):
    client.force_login(user)
    completion_date = date(2024, 4, 10)

    response = client.post(
        reverse("add_training"),
        {
            "course": nonrecurring_course.pk,
            "completion_date": completion_date.isoformat(),
        },
    )

    training = Training.objects.get(user=user, course=nonrecurring_course)
    assert response.status_code == 200
    assert response.context["success"] is True
    assert response.context["confirmation_message"] == "Training added successfully."
    assert training.completion_date == completion_date
    assert training.training_expiry_date == completion_date


@pytest.mark.django_db
def test_add_training_post_with_invalid_data_returns_errors(client, user, recurring_course, user_training):
    client.force_login(user)

    response = client.post(
        reverse("add_training"),
        {
            "course": recurring_course.pk,
            "completion_date": (date.today() + timedelta(days=30)).isoformat(),
        },
    )

    assert response.status_code == 200
    assert response.context["success"] is False
    assert response.context["confirmation_message"] is None
    assert response.context["form"].errors
    assert Training.objects.filter(user=user, course=recurring_course).count() == 1


@pytest.mark.django_db
def test_extend_training_requires_login(client, user_training):
    response = client.get(reverse("extend_training", args=[user_training.pk]))

    assert response.status_code == 302
    assert reverse("account_login") in response.url


@pytest.mark.django_db
def test_extend_training_denies_non_owner(client, other_user, user_training):
    client.force_login(other_user)

    response = client.get(reverse("extend_training", args=[user_training.pk]))

    assert response.status_code == 404


@pytest.mark.django_db
def test_extend_training_get_shows_existing_training_details(client, user, user_training, recurring_course):
    client.force_login(user)

    response = client.get(reverse("extend_training", args=[user_training.pk]))

    assert response.status_code == 200
    assert response.context["training_instance"] == user_training
    assert response.context["previous_completion_date"] == user_training.completion_date
    assert response.context["training_expiry_date"] == user_training.completion_date + timedelta(
        days=365 * recurring_course.renewal_period
    )


@pytest.mark.django_db
def test_extend_training_post_updates_completion_and_expiry(client, user, user_training):
    client.force_login(user)
    new_completion_date = date(2025, 3, 1)

    response = client.post(
        reverse("extend_training", args=[user_training.pk]),
        {
            "completion_date": new_completion_date.isoformat(),
            "training_expiry_date": "",
        },
    )

    user_training.refresh_from_db()
    assert response.status_code == 200
    assert response.context["success"] is True
    assert user_training.completion_date == new_completion_date
    assert user_training.training_expiry_date == date(2026, 3, 1)
    assert "Training expiry date updated successfully" in response.content.decode()


@pytest.mark.django_db
def test_extend_training_post_with_invalid_data_keeps_existing_record(client, user, user_training):
    client.force_login(user)
    original_completion_date = user_training.completion_date
    original_expiry_date = user_training.training_expiry_date

    response = client.post(
        reverse("extend_training", args=[user_training.pk]),
        {
            "completion_date": (date.today() + timedelta(days=30)).isoformat(),
            "training_expiry_date": "",
        },
    )

    user_training.refresh_from_db()
    assert response.status_code == 200
    assert response.context["success"] is False
    assert response.context["confirmation_message"] is None
    assert response.context["form"].errors
    assert user_training.completion_date == original_completion_date
    assert user_training.training_expiry_date == original_expiry_date


@pytest.mark.django_db
def test_extend_training_missing_record_returns_404(client, user):
    client.force_login(user)

    response = client.get(reverse("extend_training", args=[99999]))

    assert response.status_code == 404


@pytest.mark.django_db
def test_bulk_remove_training_requires_login(client):
    response = client.post(reverse("bulk_remove_training"))

    assert response.status_code == 302
    assert reverse("account_login") in response.url


@pytest.mark.django_db
def test_bulk_remove_training_without_selection_redirects_home(client, user, user_training):
    client.force_login(user)

    response = client.post(reverse("bulk_remove_training"))

    assert response.status_code == 302
    assert response.url == reverse("training")
    assert Training.objects.filter(pk=user_training.pk).exists()


@pytest.mark.django_db
def test_bulk_remove_training_confirmation_shows_only_owned_selected_records(
    client, user, user_training, other_training
):
    client.force_login(user)

    response = client.post(
        reverse("bulk_remove_training"),
        {"selected_training_ids": [user_training.pk, other_training.pk]},
    )

    assert response.status_code == 200
    assert "learning/remove_training.html" in [template.name for template in response.templates]
    assert response.context["bulk_remove"] is True
    assert response.context["selected_training_list"] == [user_training]
    assert response.context["selected_training_ids"] == [str(user_training.pk)]


@pytest.mark.django_db
def test_bulk_remove_training_confirm_deletes_owned_selected_records(client, user, user_training, other_training):
    client.force_login(user)

    response = client.post(
        reverse("bulk_remove_training"),
        {
            "selected_training_ids": [user_training.pk, other_training.pk],
            "confirm_removal": "1",
        },
    )

    assert response.status_code == 302
    assert response.url == reverse("training")
    assert not Training.objects.filter(pk=user_training.pk).exists()
    assert Training.objects.filter(pk=other_training.pk).exists()


@pytest.mark.django_db
def test_remove_training_get_allows_owner(client, user, user_training):
    client.force_login(user)

    response = client.get(reverse("remove_training", args=[user_training.pk]))

    assert response.status_code == 200
    assert response.context["training_list"] == user_training


@pytest.mark.django_db
def test_remove_training_get_blocks_non_owner(client, other_user, user_training):
    client.force_login(other_user)

    response = client.get(reverse("remove_training", args=[user_training.pk]))

    assert response.status_code == 404


@pytest.mark.django_db
def test_remove_training_post_deletes_owned_training(client, user, user_training):
    client.force_login(user)

    response = client.post(reverse("remove_training", args=[user_training.pk]))

    assert response.status_code == 302
    assert response.url == reverse("training")
    assert not Training.objects.filter(pk=user_training.pk).exists()


@pytest.mark.django_db
def test_account_view_requires_login(client):
    response = client.get(reverse("account"))

    assert response.status_code == 302
    assert reverse("account_login") in response.url


@pytest.mark.django_db
def test_account_view_includes_current_user(client, user):
    client.force_login(user)

    response = client.get(reverse("account"))

    assert response.status_code == 200
    assert response.context["user"] == user
