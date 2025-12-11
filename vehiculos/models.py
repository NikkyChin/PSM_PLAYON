from django.db import models

class Vehiculo(models.Model):
    dominio = models.CharField("Dominio (Patente)", max_length=10, unique=True)
    marca = models.CharField(max_length=50, blank=True)
    modelo = models.CharField(max_length=50, blank=True)
    color = models.CharField(max_length=30, blank=True)
    nro_chasis = models.CharField("N° de chasis", max_length=50, blank=True)
    nro_motor = models.CharField("N° de motor", max_length=50, blank=True)
    anio = models.PositiveIntegerField("Año", null=True, blank=True)

    fecha_alta = models.DateTimeField("Fecha de alta en sistema", auto_now_add=True)

    def __str__(self):
        return f"{self.dominio} - {self.marca} {self.modelo}".strip()
