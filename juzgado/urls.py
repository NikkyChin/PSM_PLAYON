from django.urls import path
from . import views

app_name = "juzgado"

urlpatterns = [
    path("retiros/", views.lista_para_autorizar, name="lista_autorizaciones"),
    path("retiros/<int:ingreso_id>/", views.autorizar_retiro, name="autorizar_retiro"),
    path("retiros/<int:ingreso_id>/revocar/", views.revocar_autorizacion, name="revocar_autorizacion"),
]
