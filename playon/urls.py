from django.urls import path
from . import views

urlpatterns = [
    path("tablero/", views.tablero_playon, name="tablero_playon"),
    path("reparar/", views.reparar_tablero, name="reparar_tablero"),
    path("lugar/<int:lugar_id>/", views.detalle_lugar, name="detalle_lugar"),
    path("lugar/<int:lugar_id>/fuera/", views.marcar_lugar_fuera, name="marcar_lugar_fuera"),
    path("lugar/<int:lugar_id>/reactivar/", views.reactivar_lugar, name="reactivar_lugar"),

]