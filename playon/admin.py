from django.contrib import admin
from .models import LugarPlayon

# Registro del modelo de lugares del playón en el admin de Django, para poder ver y editar los lugares desde el panel de administración.
# Se muestra el código del lugar, su estado (libre, ocupado, fuera), y su tipo (auto, moto, camión). Se pueden filtrar por estado, tipo y fila, y se ordenan por fila y columna.
@admin.register(LugarPlayon)
class LugarPlayonAdmin(admin.ModelAdmin):
    list_display = ("codigo", "estado", "tipo")
    list_filter = ("estado", "tipo", "fila")
    ordering = ("fila", "columna")

