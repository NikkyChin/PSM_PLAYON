from django.urls import path
from . import views

urlpatterns = [
    path("lista/", views.lista_vehiculos, name="lista_vehiculos"),
    path("vehiculo/<int:vehiculo_id>/", views.detalle_vehiculo, name="detalle_vehiculo"),
    path("imprimir/", views.imprimir_lista_vehiculos, name="imprimir_lista_vehiculos"),
    
]
