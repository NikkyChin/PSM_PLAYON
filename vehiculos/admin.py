from django.contrib import admin
from .models import Vehiculo, IngresoPlayon, LugarPlayon

# Registro de los modelos de vehículos, ingresos al playón y lugares del playón en el admin de Django, para poder ver y editar estos datos desde el panel de administración.
@admin.register(Vehiculo)
class VehiculoAdmin(admin.ModelAdmin):
    list_display = ("dominio", "marca", "modelo", "color", "anio", "fecha_alta")
    list_filter = ("marca", "color", "anio")
    search_fields = ("dominio", "marca", "modelo", "nro_chasis", "nro_motor")

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

# Registro del modelo de lugares del playón en el admin de Django, para poder ver y editar los lugares desde el panel de administración.
# Se muestra el código del lugar, su estado (libre, ocupado, fuera), y su tipo (auto, moto, camión). Se pueden filtrar por estado, tipo y fila, y se ordenan por fila y columna.
@admin.register(LugarPlayon)
class LugarPlayonAdmin(admin.ModelAdmin):
    list_display = ("codigo", "estado", "tipo")
    list_filter = ("estado", "tipo", "fila")
    ordering = ("fila", "columna")

