from django.contrib import admin
from .models import Vehiculo, IngresoPlayon, LugarPlayon


@admin.register(Vehiculo)
class VehiculoAdmin(admin.ModelAdmin):
    list_display = ("dominio", "marca", "modelo", "color", "anio", "fecha_alta")
    list_filter = ("marca", "color", "anio")
    search_fields = ("dominio", "marca", "modelo", "nro_chasis", "nro_motor")


@admin.register(IngresoPlayon)
class IngresoPlayonAdmin(admin.ModelAdmin):
    list_display = (
        "nro_legajo_playon",
        "vehiculo",
        "fecha_ingreso",
        "ubicacion_interna",
        "recibido_por",
        "retirado",
    )
    search_fields = ("nro_legajo_playon", "vehiculo__dominio")
    list_filter = ("tipo_vehiculo", "fecha_ingreso", "retirado")


@admin.register(LugarPlayon)
class LugarPlayonAdmin(admin.ModelAdmin):
    list_display = ("codigo", "estado", "tipo")
    list_filter = ("estado", "tipo", "fila")
    ordering = ("fila", "columna")
