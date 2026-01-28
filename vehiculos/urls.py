from django.urls import path
from . import views

urlpatterns = [
    path("lista/", views.lista_vehiculos, name="lista_vehiculos"),
    path("ingreso/nuevo/", views.nuevo_ingreso_playon, name="nuevo_ingreso_playon"),

    path("ingresos/", views.lista_ingresos, name="lista_ingresos"),  # todos
    path("ingresos/activos/", views.ingresos_en_playon, name="ingresos_en_playon"),  # solo los que están adentro
    path("ingresos/retirados/", views.retiros_playon, name="retiros_playon"),  # historial de retiros

    path("ingresos/<int:ingreso_id>/egreso/", views.registrar_egreso, name="registrar_egreso"),
    path("ingresos/<int:ingreso_id>/detalle/", views.detalle_ingreso, name="detalle_ingreso"),
    path("ingresos/<int:ingreso_id>/retiro/imprimir/", views.imprimir_retiro, name="imprimir_retiro"),
    #path("ingresos/<int:ingreso_id>/editar/", views.editar_ingreso, name="editar_ingreso"), 

    path("playon/tablero/", views.tablero_playon, name="tablero_playon"),
    path("playon/lugar/<int:lugar_id>/", views.detalle_lugar, name="detalle_lugar"),

    path("playon/lugar/<int:lugar_id>/fuera/", views.marcar_lugar_fuera, name="marcar_lugar_fuera"),
    path("playon/lugar/<int:lugar_id>/reactivar/", views.reactivar_lugar, name="reactivar_lugar"),

    path("vehiculo/<int:vehiculo_id>/", views.detalle_vehiculo, name="detalle_vehiculo"),
    

]
