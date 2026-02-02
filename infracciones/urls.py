from django.urls import path
from . import views

urlpatterns = [
    path("", views.lista_actas, name="infracciones_lista"),
    path("nueva/", views.nueva_acta, name="infracciones_nueva"),
    path("<int:acta_id>/", views.detalle_acta, name="infracciones_detalle"),
    path("<int:acta_id>/editar/", views.editar_acta, name="infracciones_editar"),
]

