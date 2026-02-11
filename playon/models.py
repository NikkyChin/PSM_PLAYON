from django.db import models
from ingresos.models import IngresoPlayon
from django.contrib.auth.models import User


# Modelo para representar los lugares del playón, con su estado (libre, ocupado, fuera de servicio) y tipo (general o exclusivo para motos).
class LugarPlayon(models.Model):
    ESTADO_CHOICES = [
        ("LIBRE", "Libre"),
        ("OCUPADO", "Ocupado"),
        ("FUERA", "Fuera de servicio"),
    ]

    TIPO_CHOICES = [
        ("GENERAL", "General"),
        ("MOTO", "Exclusivo motos"),
    ]

    fila = models.CharField(max_length=1)  # A-Z
    columna = models.PositiveSmallIntegerField()  # 1-15
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default="LIBRE")
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, default="GENERAL")

    class Meta:
        unique_together = ("fila", "columna")
        ordering = ["fila", "columna"]

    @property
    def codigo(self):
        return f"{self.fila}{self.columna}"

    def __str__(self):
        return self.codigo
    
# Modelo para registrar los movimientos de un vehículo dentro del playón, como cambios de lugar. 
# Se relaciona con el ingreso al playón, el lugar anterior y el nuevo lugar, el usuario que realizó el movimiento, la fecha y el motivo.
# Actualmente no se usa en ningún formulario ni vista, pero queda preparado para cuando quieras implementar la funcionalidad de mover vehículos dentro del playón.
class MovimientoLugar(models.Model):
    ingreso = models.ForeignKey(IngresoPlayon, on_delete=models.CASCADE, related_name="movimientos")
    lugar_anterior = models.ForeignKey(LugarPlayon, on_delete=models.PROTECT, null=True, blank=True, related_name="+")
    lugar_nuevo = models.ForeignKey(LugarPlayon, on_delete=models.PROTECT, related_name="+")
    movido_por = models.ForeignKey(User, on_delete=models.PROTECT)
    fecha = models.DateTimeField(auto_now_add=True)
    motivo = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.ingreso.nro_legajo_playon}: {self.lugar_anterior} -> {self.lugar_nuevo}"
    
