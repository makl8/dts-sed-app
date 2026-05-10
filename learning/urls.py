"""
URL configuration for learning project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path
from django.views.generic import TemplateView
from learning import views

urlpatterns = [
    path("", TemplateView.as_view(template_name="home.html"), name="home"),
    path("health/", lambda r: HttpResponse("ok")),
    path("admin/", admin.site.urls),
    path("accounts/email/", TemplateView.as_view(template_name="change_email.html"), name="change_email"),
    path("accounts/password/reset/", TemplateView.as_view(template_name="reset_password.html"), name="reset_password"),
    path("accounts/", include("allauth.urls")),
    path("about/", TemplateView.as_view(template_name="learning/about.html"), name="about"),
    path("account/", views.AccountView.as_view(), name="account"),
    path("training/", views.training_home, name="training"),
    path("training/new/", views.add_training, name="add_training"),
    path("training/<int:pk>/renew/", views.extend_training, name="extend_training"),
    path("training/remove/", views.bulk_remove_training, name="bulk_remove_training"),
    path("training/<int:pk>/remove/", views.RemoveTrainingView.as_view(), name="remove_training"),
    path("course/<int:pk>/info/", views.CourseDetailView.as_view(), name="course"),
]
