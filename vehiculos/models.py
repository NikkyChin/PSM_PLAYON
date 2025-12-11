from django.db import models
from django.contrib.auth.models import User


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


class IngresoPlayon(models.Model):
    TIPO_VEHICULO_CHOICES = [
        ("AUTO", "Auto"),
        ("MOTO", "Moto"),
        ("CAMIONETA", "Camioneta"),
        ("CAMION", "Camión"),
        ("OTRO", "Otro"),
    ]

    vehiculo = models.ForeignKey(
        Vehiculo,
        on_delete=models.PROTECT,
        related_name="ingresos",
    )
    fecha_ingreso = models.DateTimeField("Fecha de ingreso", auto_now_add=True)

    tipo_vehiculo = models.CharField(
        "Tipo de vehículo",
        max_length=20,
        choices=TIPO_VEHICULO_CHOICES,
        blank=True,
    )
    marca = models.CharField(max_length=50, blank=True)
    modelo = models.CharField(max_length=50, blank=True)
    anio = models.PositiveIntegerField("Año", null=True, blank=True)
    color = models.CharField(max_length=30, blank=True)

    nro_legajo_playon = models.CharField(
        "N° de legajo en playón",
        max_length=30,
        unique=True,
    )
    lugar_infraccion = models.CharField(
        "Lugar de la infracción",
        max_length=255,
        blank=True,
    )

    # Documentación anexada
    acta_infraccion_recibida = models.BooleanField(
        "Acta de infracción recibida",
        default=False,
    )
    acta_secuestro_recibida = models.BooleanField(
        "Acta de secuestro recibida",
        default=False,
    )
    inventario_objetos_visibles_recibido = models.BooleanField(
        "Inventario de objetos visibles recibido",
        default=False,
    )
    registro_fotografico_recibido = models.BooleanField(
        "Registro fotográfico recibido",
        default=False,
    )

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

    # Observaciones de ingreso
    coincide_inventario = models.BooleanField(
        "¿Coincide el inventario?",
        default=True,
    )
    coinciden_danios_registrados = models.BooleanField(
        "¿Coinciden los daños registrados?",
        default=True,
    )
    detalle_danios_no_coincidentes = models.TextField(
        "Detalle de daños no coincidentes",
        blank=True,
    )
    bateria_desconectada = models.BooleanField(
        "Batería desconectada",
        default=False,
    )
    ubicacion_interna = models.CharField(
        "Ubicación interna en playa",
        max_length=100,
        blank=True,
    )

    recibido_por = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="ingresos_recibidos",
    )
    observaciones_generales = models.TextField(
        "Observaciones generales",
        blank=True,
    )

    # Datos de egreso
    retirado = models.BooleanField("¿Retirado?", default=False)
    fecha_retiro = models.DateTimeField(
        "Fecha de retiro",
        null=True,
        blank=True,
    )
    entregado_por = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="egresos_entregados",
        null=True,
        blank=True,
    )
    nombre_retira = models.CharField(
        "Nombre de quien retira",
        max_length=100,
        blank=True,
    )
    dni_retira = models.CharField(
        "DNI de quien retira",
        max_length=20,
        blank=True,
    )
    observaciones_egreso = models.TextField(
        "Observaciones de egreso",
        blank=True,
    )

    class Meta:
        verbose_name = "Ingreso al playón"
        verbose_name_plural = "Ingresos al playón"
        ordering = ["-fecha_ingreso"]

    def __str__(self):
        return f"Ingreso {self.nro_legajo_playon} - {self.vehiculo.dominio}"
