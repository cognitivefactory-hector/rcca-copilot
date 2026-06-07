from django.urls import path

from . import views

app_name = "rcca"

urlpatterns = [
    path("", views.home, name="home"),
    path("healthz", views.healthz, name="healthz"),
    path("samples/<slug:nc_id>/start", views.start_sample, name="start_sample"),
    path("investigations/<int:pk>/", views.workspace, name="workspace"),
    path("investigations/<int:pk>/export", views.export, name="export"),
    path("sections/<int:pk>/edit", views.edit_section, name="edit_section"),
    path("sections/<int:pk>/approve", views.approve_section, name="approve_section"),
]
