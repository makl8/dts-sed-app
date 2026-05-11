import json
import logging
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.timezone import now
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.decorators.http import require_POST
from django.views.generic import DeleteView, DetailView, TemplateView
from learning.forms import AddTrainingModelForm, ExtendTrainingModelForm
from learning.models import Course, Training

User = get_user_model()
logger = logging.getLogger(__name__)


# xframe_options_sameorigin required to allow embedding
@method_decorator(xframe_options_sameorigin, name="dispatch")
class CourseDetailView(LoginRequiredMixin, DetailView):
    """Render the Course info page."""

    model = Course
    template_name = "learning/course_info.html"
    context_object_name = "course"


def training_home(request):
    """Render the training page of the Learning app."""
    logger.info("Training home")
    if request.user.is_authenticated:  # pylint: disable=R1705
        try:
            current_user = User.objects.get(username=request.user)
            logger.debug(current_user)
        except User.DoesNotExist:
            current_user = None
        user_training_list = Training.objects.filter(user=current_user).select_related("course") if current_user else []
        course_dict = {item.course.id: item.course.course_name for item in user_training_list}
        context = {
            "training_list": user_training_list,
            "course_dict": course_dict,
        }
        return render(request, template_name="learning/index.html", context=context)
    else:
        return render(request, template_name="learning/index.html")


@login_required
def add_training(request):
    """Render the Add training page of the Learning app."""
    logger.info("Add training")
    success = False
    training_instance = Training()
    nonrecurring_course_ids_json = list(Course.objects.filter(renewal_period="0").values_list("pk", flat=True))
    renewal_period = {course.pk: course.renewal_period for course in Course.objects.all()}
    date_added = now().date()
    calculated_training_expiry_date = None
    confirmation_message = None

    if request.method == "POST":
        post_data = request.POST.copy()
        # get the related User instance for the current user
        try:
            current_user = User.objects.get(username=request.user)
        except User.DoesNotExist as exc:
            raise Http404("User not found.") from exc
        post_data["user"] = current_user
        form = AddTrainingModelForm(post_data, hide_fields=True)
        if form.is_valid():
            training_instance.user = current_user
            training_instance.course = form.cleaned_data["course"]
            training_instance.completion_date = form.cleaned_data["completion_date"]
            delta = timedelta(days=365 * training_instance.course.renewal_period)
            calculated_training_expiry_date = training_instance.completion_date + delta
            training_instance.training_expiry_date = calculated_training_expiry_date
            training_instance.save()
            success = True
            confirmation_message = "Training added successfully."
    else:
        form = AddTrainingModelForm(hide_fields=True)

    context = {
        "form": form,
        "training_instance": training_instance,
        "date_added": date_added,
        "calculated_training_expiry_date": calculated_training_expiry_date,
        "confirmation_message": confirmation_message,
        "renewal_period_json": json.dumps(renewal_period),
        "nonrecurring_course_ids_json": json.dumps(nonrecurring_course_ids_json),
        "success": success,
    }

    return render(request, "learning/add_training.html", context)


@login_required
def extend_training(request, pk):
    """Render the Extend training page of the Learning app."""
    logger.info("Extend training")
    # ownership check: only the owner can extend their training
    try:
        current_user = User.objects.get(username=request.user)
    except User.DoesNotExist as exc:
        raise Http404("User not found.") from exc
    try:
        training_instance = Training.objects.get(pk=pk)
    except Training.DoesNotExist as exc:
        raise Http404("Training record does not exist.") from exc
    if training_instance.user != current_user:
        raise Http404("You do not have permission to extend this training.")

    success = False
    renewal_period = training_instance.course.renewal_period
    prev_completion_date = training_instance.completion_date
    # default expiry calculation based on current renewal period
    calculated_training_expiry_date = prev_completion_date + timedelta(
        days=365 * training_instance.course.renewal_period
    )

    confirmation_message = None
    if request.method == "POST":
        form = ExtendTrainingModelForm(request.POST, hide_fields=True, instance=training_instance)
        if form.is_valid():
            # recalculate expiry date based on renewal period
            training_instance.completion_date = form.cleaned_data["completion_date"]
            delta = timedelta(days=365 * training_instance.course.renewal_period)
            calculated_training_expiry_date = training_instance.completion_date + delta
            training_instance.training_expiry_date = calculated_training_expiry_date
            training_instance.save()
            success = True
            # calculated_training_expiry_date = training_instance.training_expiry_date
            confirmation_message = f"Training expiry date updated successfully to {calculated_training_expiry_date}."
    else:
        form = ExtendTrainingModelForm(
            hide_fields=True,
            initial={
                "training_instance": training_instance.course,
                "renewal_period": renewal_period,
                "training_expiry_date": calculated_training_expiry_date,
                "success": success,
            },
        )

    context = {
        "form": form,
        "training_instance": training_instance,
        "previous_completion_date": prev_completion_date,
        "training_expiry_date": calculated_training_expiry_date,
        "renewal_period": renewal_period,
        "confirmation_message": confirmation_message,
        "success": success,
    }

    return render(request, "learning/extend_training.html", context)


@login_required
@require_POST
def bulk_remove_training(request):
    """Confirm or remove multiple training records owned by the current user."""
    try:
        current_user = User.objects.get(username=request.user)
    except User.DoesNotExist as exc:
        raise Http404("User not found.") from exc

    selected_training_ids = request.POST.getlist("selected_training_ids")
    selected_training_list = list(
        Training.objects.filter(user=current_user, pk__in=selected_training_ids).select_related("course")
    )
    if not selected_training_list:
        return HttpResponseRedirect(reverse("training"))

    if request.POST.get("confirm_removal") == "1":
        with transaction.atomic():
            Training.objects.filter(
                user=current_user, pk__in=[training.pk for training in selected_training_list]
            ).delete()

        return HttpResponseRedirect(reverse("training"))

    context = {
        "bulk_remove": True,
        "selected_training_ids": [str(training.pk) for training in selected_training_list],
        "selected_training_list": selected_training_list,
    }
    return render(request, "learning/remove_training.html", context)


class RemoveTrainingView(LoginRequiredMixin, DeleteView):
    """Render the Remove training page."""

    model = Training
    template_name = "learning/remove_training.html"
    success_url = reverse_lazy("training")
    context_object_name = "training_list"

    def get_queryset(self):
        """Allow deletion of Training objects owned by the current user only."""
        try:
            current_user = User.objects.get(username=self.request.user)
        except User.DoesNotExist:
            return Training.objects.none()
        return Training.objects.filter(user=current_user)


class AccountView(LoginRequiredMixin, TemplateView):
    """Render the account page."""

    template_name = "learning/account.html"

    def get_context_data(self, **kwargs):
        """Populate account details for the current user."""
        context = super().get_context_data(**kwargs)
        current_user = None
        if self.request.user.is_authenticated:
            current_user = User.objects.filter(username=self.request.user).first()
        context["user"] = current_user
        return context
