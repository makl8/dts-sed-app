import pytest
from django.http import Http404
from django.urls import reverse
from learning import views
from learning.models import Training


def assert_non_owner_cannot_extend_training(client, acting_user, training):
    client.force_login(acting_user)

    response = client.get(reverse("extend_training", args=[training.pk]))

    assert response.status_code == 404


def assert_bulk_remove_only_deletes_owned_records(client, owner, owned_training, foreign_training):
    client.force_login(owner)

    response = client.post(
        reverse("bulk_remove_training"),
        {
            "selected_training_ids": [owned_training.pk, foreign_training.pk],
            "confirm_removal": "1",
        },
    )

    assert response.status_code == 302
    assert response.url == reverse("training")
    assert not Training.objects.filter(pk=owned_training.pk).exists()
    assert Training.objects.filter(pk=foreign_training.pk).exists()


def assert_view_raises_user_not_found_http404(
    rf, user, path, monkeypatch, request_method, view_callable, *view_args, **view_kwargs
):
    request_factory = getattr(rf, request_method)
    request = request_factory(path)
    request.user = user

    def raise_user_not_found(*args, **kwargs):
        raise views.User.DoesNotExist()

    monkeypatch.setattr(views.User.objects, "get", raise_user_not_found)

    try:
        callable_under_test = view_callable.__wrapped__
    except AttributeError:
        callable_under_test = view_callable

    with pytest.raises(Http404):
        callable_under_test(request, *view_args, **view_kwargs)


def assert_extend_training_updates_completion_and_expiry(
    client, user, training, new_completion_date, submitted_expiry_date
):
    client.force_login(user)

    response = client.post(
        reverse("extend_training", args=[training.pk]),
        {
            "completion_date": new_completion_date.isoformat(),
            "training_expiry_date": submitted_expiry_date,
        },
    )

    training.refresh_from_db()
    return response
