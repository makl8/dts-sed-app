import inspect
from datetime import date
from types import SimpleNamespace

import pytest
from django import forms as django_forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.http import Http404, HttpResponse
from django.urls import reverse
from learning import forms, models, views
from learning.forms import ExtendTrainingModelForm, LearningSignupForm
from learning.models import Training
from tests.helpers import (
    assert_bulk_remove_only_deletes_owned_records,
    assert_extend_training_updates_completion_and_expiry,
    assert_non_owner_cannot_extend_training,
    assert_view_raises_user_not_found_http404,
)


@pytest.mark.owasp_a1
@pytest.mark.django_db
def test_add_training_rejects_sql_like_course_identifier(client, user):
    client.force_login(user)

    response = client.post(
        reverse("add_training"),
        {
            "course": "1 OR 1=1",
            "completion_date": "2024-04-10",
        },
    )

    assert response.status_code == 200
    assert response.context["success"] is False
    assert "course" in response.context["form"].errors
    assert Training.objects.filter(user=user).count() == 0


@pytest.mark.owasp_a1
@pytest.mark.django_db
def test_add_training_rejects_sql_like_completion_date(client, user, recurring_course):
    client.force_login(user)

    response = client.post(
        reverse("add_training"),
        {
            "course": recurring_course.pk,
            "completion_date": "2024-04-10' OR '1'='1",
        },
    )

    assert response.status_code == 200
    assert response.context["success"] is False
    assert "completion_date" in response.context["form"].errors
    assert Training.objects.filter(user=user, course=recurring_course).count() == 0


@pytest.mark.owasp_a1
@pytest.mark.django_db
def test_signup_form_rejects_header_injection_email_payload():
    form = LearningSignupForm(
        data={
            "first_name": "Alice",
            "last_name": "Tester",
            "email": "alice@some.org\r\nbcc:attacker@example.com",
            "username": "alice-tester",
            "password1": "S3curePassw0rd!234",
            "password2": "S3curePassw0rd!234",
        }
    )

    assert form.is_valid() is False
    assert "email" in form.errors


@pytest.mark.owasp_a1
def test_signup_form_normalizes_allowed_org_email():
    form = LearningSignupForm()
    form.cleaned_data = {"email": "  PERSON@SOME.ORG  "}

    assert form.clean_email() == "person@some.org"


@pytest.mark.owasp_a1
def test_signup_form_rejects_script_like_name_payload():
    form = LearningSignupForm()

    with pytest.raises(ValidationError):
        form.fields["first_name"].clean("<script>alert(1)</script>")


@pytest.mark.owasp_a1
@pytest.mark.parametrize(
    "payload",
    [
        "Robert'); DROP TABLE training;--",
        "Anne--Marie",
        "123456",
    ],
)
def test_validate_name_rejects_hostile_or_invalid_payloads(payload):
    with pytest.raises(ValidationError):
        forms.validate_name(payload)


@pytest.mark.owasp_a1
def test_validate_name_rejects_consecutive_spaces():
    with pytest.raises(ValidationError):
        forms.validate_name("Anne  Marie")


@pytest.mark.owasp_a1
@pytest.mark.django_db
def test_extend_training_form_omitted_expiry_remains_none_for_unsaved_instance(user, recurring_course):
    form = ExtendTrainingModelForm(
        data={
            "completion_date": date(2025, 1, 10).isoformat(),
            "training_expiry_date": "",
        },
        instance=Training(user=user, course=recurring_course),
    )

    assert form.is_valid() is True
    assert form.cleaned_data["training_expiry_date"] is None


@pytest.mark.owasp_a1
def test_hide_fields_mixin_ignores_unknown_hideable_fields():
    class DummyForm(forms.HideFieldsMixin, django_forms.Form):
        hideable_fields = ["missing_field"]
        present_field = django_forms.CharField()

    form = DummyForm(hide_fields=True)

    assert "present_field" in form.fields
    assert form.fields["present_field"].widget.__class__ is not forms.HiddenInput


@pytest.mark.owasp_a1
def test_learning_modules_do_not_use_raw_sql_apis():
    source = "\n".join(
        [
            inspect.getsource(forms),
            inspect.getsource(models),
            inspect.getsource(views),
        ]
    )

    for pattern in (".raw(", ".extra(", "cursor.execute(", "RawSQL("):
        assert pattern not in source


@pytest.mark.owasp_a2
@pytest.mark.django_db
@pytest.mark.parametrize("url_name", ["account", "add_training"])
def test_anonymous_users_are_redirected_from_protected_endpoints(client, url_name):
    response = client.get(reverse(url_name))

    assert response.status_code == 302
    assert reverse("account_login") in response.url


@pytest.mark.owasp_a2
@pytest.mark.django_db
def test_anonymous_users_cannot_access_training_mutation_endpoints(client, user_training):
    get_response = client.get(reverse("extend_training", args=[user_training.pk]))
    remove_response = client.post(reverse("remove_training", args=[user_training.pk]))
    bulk_response = client.post(reverse("bulk_remove_training"), {"selected_training_ids": [user_training.pk]})

    for response in (get_response, remove_response, bulk_response):
        assert response.status_code == 302
        assert reverse("account_login") in response.url


@pytest.mark.owasp_a2
@pytest.mark.django_db
def test_email_login_sets_hardened_session_cookie(client, user, password, settings):
    settings.SESSION_COOKIE_SECURE = True
    settings.SESSION_COOKIE_HTTPONLY = True

    response = client.post(
        reverse("account_login"),
        {
            "login": user.email,
            "password": password,
        },
        secure=True,
    )

    assert response.status_code == 302
    cookie = response.cookies.get(settings.SESSION_COOKIE_NAME)
    assert cookie is not None
    assert cookie["secure"] is True
    assert cookie["httponly"] is True
    assert "_auth_user_id" in client.session


@pytest.mark.owasp_a2
@pytest.mark.django_db
def test_invalid_password_does_not_create_authenticated_session(client, user):
    response = client.post(
        reverse("account_login"),
        {
            "login": user.email,
            "password": "wrong-password",
        },
        secure=True,
    )

    assert response.status_code == 200
    assert "_auth_user_id" not in client.session
    assert response.context["form"].errors


@pytest.mark.owasp_a2
@pytest.mark.django_db
def test_username_cannot_be_used_when_login_is_email_only(client, user, password):
    response = client.post(
        reverse("account_login"),
        {
            "login": user.username,
            "password": password,
        },
        secure=True,
    )

    assert response.status_code == 200
    assert "_auth_user_id" not in client.session
    assert response.context["form"].errors


@pytest.mark.owasp_a2
def test_authentication_security_configuration_is_enabled(settings):
    validator_names = {validator["NAME"].rsplit(".", maxsplit=1)[-1] for validator in settings.AUTH_PASSWORD_VALIDATORS}

    assert settings.ACCOUNT_LOGIN_METHODS == {"email"}
    assert {"CommonPasswordValidator", "NumericPasswordValidator"}.issubset(validator_names)


@pytest.mark.owasp_a2
@pytest.mark.django_db
def test_common_password_is_rejected_by_configured_validators(user):
    with pytest.raises(ValidationError):
        validate_password("password", user=user)


@pytest.mark.owasp_a5
@pytest.mark.django_db
def test_add_training_ignores_forged_user_identifier_in_post_data(client, user, other_user, nonrecurring_course):
    client.force_login(user)

    response = client.post(
        reverse("add_training"),
        {
            "user": other_user.pk,
            "course": nonrecurring_course.pk,
            "completion_date": date(2024, 4, 10).isoformat(),
        },
    )

    training = Training.objects.get(course=nonrecurring_course)
    assert response.status_code == 200
    assert response.context["success"] is True
    assert training.user == user
    assert not Training.objects.filter(user=other_user, course=nonrecurring_course).exists()


@pytest.mark.owasp_a5
@pytest.mark.django_db
def test_training_home_does_not_expose_data_when_authenticated_user_record_cannot_be_resolved(
    rf, user, other_training, monkeypatch
):
    request = rf.get(reverse("training"))
    request.user = user
    captured = {}

    def raise_user_not_found(*args, **kwargs):
        raise views.User.DoesNotExist()

    def fake_render(request, template_name, context=None):
        captured["template_name"] = template_name
        captured["context"] = context
        return HttpResponse("ok")

    monkeypatch.setattr(views.User.objects, "get", raise_user_not_found)
    monkeypatch.setattr(views, "render", fake_render)

    response = views.training_home(request)

    assert response.status_code == 200
    assert captured["template_name"] == "learning/index.html"
    assert captured["context"]["training_list"] == []
    assert captured["context"]["course_dict"] == {}
    assert other_training.course.course_name not in response.content.decode()


@pytest.mark.owasp_a5
@pytest.mark.django_db
def test_add_training_returns_404_when_authenticated_user_record_no_longer_exists(
    rf, user, recurring_course, monkeypatch
):
    request = rf.post(
        reverse("add_training"),
        {
            "course": recurring_course.pk,
            "completion_date": date(2024, 4, 10).isoformat(),
        },
    )
    request.user = user

    def raise_user_not_found(*args, **kwargs):
        raise views.User.DoesNotExist()

    monkeypatch.setattr(views.User.objects, "get", raise_user_not_found)

    with pytest.raises(Http404):
        views.add_training.__wrapped__(request)

    assert Training.objects.filter(user=user, course=recurring_course).count() == 0


@pytest.mark.owasp_a5
@pytest.mark.django_db
def test_non_owner_cannot_extend_another_users_training(client, other_user, user_training):
    assert_non_owner_cannot_extend_training(client, other_user, user_training)


@pytest.mark.owasp_a5
@pytest.mark.django_db
def test_extend_training_returns_404_when_authenticated_user_record_no_longer_exists(
    rf, user, user_training, monkeypatch
):
    assert_view_raises_user_not_found_http404(
        rf,
        user,
        reverse("extend_training", args=[user_training.pk]),
        monkeypatch,
        "get",
        views.extend_training,
        user_training.pk,
    )


@pytest.mark.owasp_a5
@pytest.mark.django_db
def test_extend_training_rejects_malformed_completion_date_without_updating_record(client, user, user_training):
    client.force_login(user)
    original_completion_date = user_training.completion_date
    original_expiry_date = user_training.training_expiry_date

    response = client.post(
        reverse("extend_training", args=[user_training.pk]),
        {
            "completion_date": "2025-03-01' OR '1'='1",
            "training_expiry_date": "",
        },
    )

    user_training.refresh_from_db()
    assert response.status_code == 200
    assert response.context["success"] is False
    assert "completion_date" in response.context["form"].errors
    assert user_training.completion_date == original_completion_date
    assert user_training.training_expiry_date == original_expiry_date


@pytest.mark.owasp_a5
@pytest.mark.django_db
def test_non_owner_cannot_post_updates_to_another_users_training(client, other_user, user_training):
    client.force_login(other_user)
    original_completion_date = user_training.completion_date
    original_expiry_date = user_training.training_expiry_date

    response = client.post(
        reverse("extend_training", args=[user_training.pk]),
        {
            "completion_date": date(2025, 3, 1).isoformat(),
            "training_expiry_date": "",
        },
    )

    user_training.refresh_from_db()
    assert response.status_code == 404
    assert user_training.completion_date == original_completion_date
    assert user_training.training_expiry_date == original_expiry_date


@pytest.mark.owasp_a5
@pytest.mark.django_db
def test_extend_training_recalculates_expiry_even_when_hidden_field_is_tampered(client, user, user_training):
    new_completion_date = date(2025, 3, 1)

    response = assert_extend_training_updates_completion_and_expiry(
        client, user, user_training, new_completion_date, date(2099, 1, 1).isoformat()
    )

    assert response.status_code == 200
    assert response.context["success"] is True
    assert user_training.completion_date == new_completion_date
    assert user_training.training_expiry_date == date(2026, 3, 1)


@pytest.mark.owasp_a5
@pytest.mark.django_db
def test_non_owner_cannot_delete_another_users_training(client, other_user, user_training):
    client.force_login(other_user)

    response = client.post(reverse("remove_training", args=[user_training.pk]))

    assert response.status_code == 404
    assert Training.objects.filter(pk=user_training.pk).exists()


@pytest.mark.owasp_a5
@pytest.mark.django_db
def test_remove_training_returns_404_when_authenticated_user_record_no_longer_exists(
    rf, user, user_training, monkeypatch
):
    assert_view_raises_user_not_found_http404(
        rf,
        user,
        reverse("remove_training", args=[user_training.pk]),
        monkeypatch,
        "get",
        views.RemoveTrainingView.as_view(),
        pk=user_training.pk,
    )

    assert Training.objects.filter(pk=user_training.pk).exists()


@pytest.mark.owasp_a5
@pytest.mark.django_db
def test_bulk_remove_returns_404_when_authenticated_user_record_no_longer_exists(rf, user, user_training, monkeypatch):
    request = rf.post(reverse("bulk_remove_training"), {"selected_training_ids": [user_training.pk]})
    request.user = user

    def raise_user_not_found(*args, **kwargs):
        raise views.User.DoesNotExist()

    monkeypatch.setattr(views.User.objects, "get", raise_user_not_found)

    with pytest.raises(Http404):
        views.bulk_remove_training.__wrapped__(request)


@pytest.mark.owasp_a5
def test_account_view_returns_no_user_context_when_authenticated_user_record_cannot_be_resolved(monkeypatch):
    view = views.AccountView()
    view.request = SimpleNamespace(user=SimpleNamespace(is_authenticated=True))

    class FilterResult:
        def first(self):
            return None

    monkeypatch.setattr(views.User.objects, "filter", lambda **kwargs: FilterResult())

    context = view.get_context_data()

    assert context["user"] is None


@pytest.mark.owasp_a5
@pytest.mark.django_db
def test_training_home_does_not_expose_other_users_training_records(client, user, user_training, other_training):
    client.force_login(user)

    response = client.get(reverse("training"))

    assert response.status_code == 200
    assert list(response.context["training_list"]) == [user_training]
    assert other_training not in response.context["training_list"]
    assert other_training.course.course_name not in response.content.decode()


@pytest.mark.owasp_a5
@pytest.mark.django_db
def test_bulk_remove_confirmation_only_lists_owned_records(client, user, user_training, other_training):
    client.force_login(user)

    response = client.post(
        reverse("bulk_remove_training"),
        {
            "selected_training_ids": [user_training.pk, other_training.pk],
        },
    )

    assert response.status_code == 200
    assert response.context["bulk_remove"] is True
    assert response.context["selected_training_list"] == [user_training]
    assert response.context["selected_training_ids"] == [str(user_training.pk)]
    assert other_training.course.course_name not in response.content.decode()


@pytest.mark.owasp_a5
@pytest.mark.django_db
def test_bulk_remove_only_deletes_owned_training_records(client, user, user_training, other_training):
    assert_bulk_remove_only_deletes_owned_records(client, user, user_training, other_training)


@pytest.mark.owasp_a5
@pytest.mark.django_db
def test_bulk_remove_with_only_foreign_record_ids_deletes_nothing(client, user, user_training, other_training):
    client.force_login(user)

    response = client.post(
        reverse("bulk_remove_training"),
        {
            "selected_training_ids": [other_training.pk],
            "confirm_removal": "1",
        },
    )

    assert response.status_code == 302
    assert response.url == reverse("training")
    assert Training.objects.filter(pk=user_training.pk).exists()
    assert Training.objects.filter(pk=other_training.pk).exists()
