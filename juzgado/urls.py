from django.urls import path
from . import views

app_name = "juzgado"

urlpatterns = [
    path("", views.lista_para_autorizar, name="lista_autorizaciones"),
    path("<int:ingreso_id>/", views.autorizar_retiro, name="autorizar_retiro"),
    path("<int:ingreso_id>/revocar/", views.revocar_autorizacion, name="revocar_autorizacion"),

    path("historial/autorizaciones/", views.historial_autorizaciones, name="historial_autorizaciones"),

    # 🚧 comentar o activar según definas con tu jefe:
    # path("historial/retiros/", views.historial_retiros, name="historial_retiros"),
]