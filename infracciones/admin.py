from django.contrib import admin
from .models import Infraccion
# Registra del modelo de infracciones en el admin de Django, para poder ver y editar las actas de infraccion desde el panel de administracion. 
# Se muestra el numero de acta, dominio, dni del infractor, inspector que la cargo, si esta retenida para playon, y la fecha de creacion.
@admin.register(Infraccion)
class InfraccionAdmin(admin.ModelAdmin):
    list_display = ("nro_acta", "dominio", "dni_infractor", "inspector", "retenido_playon", "creada_en")
    search_fields = ("nro_acta", "dominio", "dni_infractor", "apellido_infractor")
    list_filter = ("retenido_playon", "inspector")
