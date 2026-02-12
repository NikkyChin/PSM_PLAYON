from django.urls import path
from . import views

urlpatterns = [
    path("admin-dashboard/", views.dashboard_admin, name="dashboard_admin"),
    path("imprimir/", views.imprimir_dashboard, name="imprimir_dashboard"),
]
