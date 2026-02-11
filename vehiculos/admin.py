from django.contrib import admin
from .models import Vehiculo, IngresoPlayon, LugarPlayon

# Registro de los modelos de vehículos, ingresos al playón y lugares del playón en el admin de Django, para poder ver y editar estos datos desde el panel de administración.
@admin.register(Vehiculo)
class VehiculoAdmin(admin.ModelAdmin):
    list_display = ("dominio", "marca", "modelo", "color", "anio", "fecha_alta")
    list_filter = ("marca", "color", "anio")
    search_fields = ("dominio", "marca", "modelo", "nro_chasis", "nro_motor")
