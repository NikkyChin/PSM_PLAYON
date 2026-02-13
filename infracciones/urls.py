from django.urls import path
from . import views

app_name = "infracciones"

urlpatterns = [
    path("", views.lista_actas, name="lista"),
    path("nueva/", views.nueva_acta, name="nueva"),
    path("<int:acta_id>/", views.detalle_acta, name="detalle"),
    path("<int:acta_id>/editar/", views.editar_acta, name="editar"),
    path("infractores/", views.lista_infractores, name="infractores"),
]