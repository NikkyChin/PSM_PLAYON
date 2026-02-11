from django.contrib import admin
from vehiculos.models import IngresoPlayon

# Registro del modelo de ingresos al playón en el admin de Django, para poder ver y editar los ingresos desde el panel de administración. 
# Se muestra el número de legajo, vehículo, fecha de ingreso, ubicación interna, quién lo recibió, y si fue retirado o no.
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