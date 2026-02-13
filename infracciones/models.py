from django.db import models
from django.contrib.auth.models import User

# Modelo para registrar las infracciones. Se usa en la app de infracciones 
class Infraccion(models.Model):
    inspector = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="actas_infraccion",
    )

    nro_acta = models.CharField("N° de acta", max_length=30, unique=True)

    dni_infractor = models.CharField("DNI", max_length=20)
    nombre_infractor = models.CharField("Nombre", max_length=80)
    apellido_infractor = models.CharField("Apellido", max_length=80)

    dominio = models.CharField("Dominio (patente)", max_length=10)
    marca = models.CharField("Marca", max_length=50, blank=True)
    modelo = models.CharField("Modelo", max_length=50, blank=True)

    es_titular = models.BooleanField("¿Es titular?", default=False)
    nro_cedula = models.CharField("N° de cédula", max_length=50, blank=True)

    retenido_playon = models.BooleanField("¿Retenido para playón de secuestro?", default=False)

    PRUEBA_ALCOHOLEMIA_CHOICES = [
        ("SI", "Sí"),
        ("NO", "No"),
        ("NC", "No corresponde"),
    ]
    prueba_alcoholemia_estado = models.CharField(
        "Prueba de alcoholemia/test",
        max_length=2,
        choices=PRUEBA_ALCOHOLEMIA_CHOICES,
        default="NC",
    )

    descripcion = models.TextField("Descripción / tipo de infracción")

    creada_en = models.DateTimeField(auto_now_add=True)
    actualizada_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-creada_en"]

    def __str__(self):
        return f"Acta {self.nro_acta} - {self.dominio}"


# El modelo AuditoriaInfraccion registra los cambios realizados a un acta, con el usuario que hizo el cambio, la fecha y un texto con los cambios realizados.
class AuditoriaInfraccion(models.Model):
    infraccion = models.ForeignKey(
        "Infraccion",
        on_delete=models.CASCADE,
        related_name="auditorias",
    )
    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    fecha = models.DateTimeField(auto_now_add=True)

    accion = models.CharField(max_length=30, default="EDICION")
    cambios_txt = models.TextField(blank=True)  # <-- texto legible, no JSON

    class Meta:
        ordering = ["-fecha"]

    def __str__(self):
        return f"Acta {self.infraccion.nro_acta} - {self.accion} - {self.fecha:%Y-%m-%d %H:%M}"