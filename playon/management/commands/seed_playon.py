# Comando de Django para poblar la base de datos con los lugares del playón, y recalcular su estado en base a los ingresos activos. 
# Se puede ejecutar con "python manage.py seed_playon".
from playon.models import LugarPlayon
from ingresos.models import IngresoPlayon
import string

filas = list(string.ascii_uppercase)  # A-Z
columnas = range(1, 16)  # 1-15

# 1) Crear los que falten (SIN borrar)
creados = 0
for fila in filas:
    for col in columnas:
        obj, was_created = LugarPlayon.objects.get_or_create(
            fila=fila,
            columna=col,
            defaults={"estado": "LIBRE", "tipo": "GENERAL"},
        )
        if was_created:
            creados += 1

# 2) Recalcular estado en base a ingresos activos
# Primero: poner LIBRE a todos los que NO estén FUERA
LugarPlayon.objects.exclude(estado="FUERA").update(estado="LIBRE")

# Luego: marcar OCUPADO a lugares que están siendo usados por ingresos no retirados
lugares_ocupados_ids = (
    IngresoPlayon.objects.filter(retirado=False, lugar__isnull=False)
    .values_list("lugar_id", flat=True)
    .distinct()
)

LugarPlayon.objects.filter(id__in=lugares_ocupados_ids).update(estado="OCUPADO")

print(f"Listo. Lugares creados nuevos: {creados}. Ocupados recalculados: {len(set(lugares_ocupados_ids))}.")
