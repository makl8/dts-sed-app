import pytest
from django.urls import resolve, reverse
from learning import views


def test_home_route_resolves():
    match = resolve(reverse("home"))

    assert match.route == ""
    assert match.func.view_class.__name__ == "TemplateView"


def test_health_route_resolves():
    match = resolve("/health/")

    assert match.route == "health/"


def test_about_route_resolves():
    match = resolve(reverse("about"))

    assert match.route == "about/"
    assert match.func.view_class.__name__ == "TemplateView"


def test_change_email_route_resolves():
    match = resolve(reverse("change_email"))

    assert match.route == "accounts/email/"
    assert match.func.view_class.__name__ == "TemplateView"


def test_reset_password_route_resolves():
    match = resolve(reverse("reset_password"))

    assert match.route == "accounts/password/reset/"
    assert match.func.view_class.__name__ == "TemplateView"


def test_training_route_resolves_to_function_view():
    match = resolve(reverse("training"))

    assert match.func == views.training_home


def test_add_training_route_resolves_to_function_view():
    match = resolve(reverse("add_training"))

    assert match.func == views.add_training


def test_extend_training_route_resolves_to_function_view():
    match = resolve(reverse("extend_training", args=[123]))

    assert match.func == views.extend_training
    assert match.kwargs == {"pk": 123}


def test_bulk_remove_training_route_resolves_to_function_view():
    match = resolve(reverse("bulk_remove_training"))

    assert match.func == views.bulk_remove_training


def test_remove_training_route_resolves_to_class_view():
    match = resolve(reverse("remove_training", args=[123]))

    assert match.func.view_class == views.RemoveTrainingView
    assert match.kwargs == {"pk": 123}


def test_account_route_resolves_to_class_view():
    match = resolve(reverse("account"))

    assert match.func.view_class == views.AccountView


def test_course_route_resolves_to_class_view():
    match = resolve(reverse("course", args=[123]))

    assert match.func.view_class == views.CourseDetailView
    assert match.kwargs == {"pk": 123}


@pytest.mark.parametrize(
    ("path", "expected_text"),
    [
        ("/", None),
        ("/health/", "ok"),
        ("/about/", None),
        ("/accounts/email/", None),
        ("/accounts/password/reset/", None),
    ],
)
def test_public_routes_return_success(client, path, expected_text):
    response = client.get(path)

    assert response.status_code == 200
    if expected_text is not None:
        assert response.content.decode() == expected_text