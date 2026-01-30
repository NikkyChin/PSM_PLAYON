from django.urls import path
from . import views

urlpatterns = [
    
    path("/nuevo/", views.nuevo_ingreso_playon, name="nuevo_ingreso_playon"),

    path("", views.lista_ingresos, name="lista_ingresos"),  # todos
    path("activos/", views.ingresos_en_playon, name="ingresos_en_playon"),  # solo los que están adentro
    path("retirados/", views.retiros_playon, name="retiros_playon"),  # historial de retiros

    path("<int:ingreso_id>/egreso/", views.registrar_egreso, name="registrar_egreso"),
    path("<int:ingreso_id>/detalle/", views.detalle_ingreso, name="detalle_ingreso"),
    path("<int:ingreso_id>/retiro/imprimir/", views.imprimir_retiro, name="imprimir_retiro"),
    path("<int:ingreso_id>/editar/", views.editar_ingreso, name="editar_ingreso"), 
]