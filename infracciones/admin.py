from django.contrib import admin
from .models import Infraccion

@admin.register(Infraccion)
class InfraccionAdmin(admin.ModelAdmin):
    list_display = ("nro_acta", "dominio", "dni_infractor", "inspector", "retenido_playon", "creada_en")
    search_fields = ("nro_acta", "dominio", "dni_infractor", "apellido_infractor")
    list_filter = ("retenido_playon", "inspector")
