from django.urls import path
from . import views

urlpatterns = [
    path("lista/", views.lista_vehiculos, name="lista_vehiculos"),
]
