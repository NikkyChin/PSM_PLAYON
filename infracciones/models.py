from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User


class Infraccion(models.Model):
    # Quién cargó (inspector)
    inspector = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="actas_infraccion",
    )

    # Acta
    nro_acta = models.CharField("N° de acta", max_length=30, unique=True)

    # Persona a la que se labra el acta
    dni_infractor = models.CharField("DNI", max_length=20)
    nombre_infractor = models.CharField("Nombre", max_length=80)
    apellido_infractor = models.CharField("Apellido", max_length=80)

    # Datos del vehículo (snapshot del acta)
    dominio = models.CharField("Dominio (patente)", max_length=10)
    marca = models.CharField("Marca", max_length=50, blank=True)
    modelo = models.CharField("Modelo", max_length=50, blank=True)

    # Titularidad / documentación
    es_titular = models.BooleanField("¿Es titular?", default=False)
    nro_cedula = models.CharField("N° de cédula", max_length=50, blank=True)

    # Secuestro
    retenido_playon = models.BooleanField("¿Retenido para playón de secuestro?", default=False)

    # Tipo / descripción de infracción
    descripcion = models.TextField("Descripción / tipo de infracción")

    # Auditoría simple
    creada_en = models.DateTimeField(auto_now_add=True)
    actualizada_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-creada_en"]

    def __str__(self):
        return f"Acta {self.nro_acta} - {self.dominio}"
