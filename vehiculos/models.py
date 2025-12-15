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

    fecha_alta = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.dominio


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


class IngresoPlayon(models.Model):
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.PROTECT, related_name="ingresos")
    fecha_ingreso = models.DateTimeField(auto_now_add=True)

    tipo_vehiculo = models.CharField(
        max_length=20,
        choices=[
            ("AUTO", "Auto"),
            ("MOTO", "Moto"),
            ("CAMIONETA", "Camioneta"),
            ("CAMION", "Camión"),
            ("OTRO", "Otro"),
        ],
        blank=True,
    )

    nro_legajo_playon = models.CharField(max_length=30, unique=True)

    # (opcional) texto libre, lo mantenemos porque tu admin lo usa
    ubicacion_interna = models.CharField("Ubicación interna en playa", max_length=100, blank=True)

    # Lugar estructurado del tablero (recomendado)
    lugar = models.ForeignKey(
        LugarPlayon,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="ingresos",
    )

    recibido_por = models.ForeignKey(User, on_delete=models.PROTECT, related_name="ingresos_recibidos")

    # Datos de egreso (retiro)
    retirado = models.BooleanField("¿Retirado?", default=False)
    fecha_retiro = models.DateTimeField("Fecha de retiro", null=True, blank=True)

    entregado_por = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="egresos_entregados",
        null=True,
        blank=True,
    )

    nombre_retira = models.CharField("Nombre de quien retira", max_length=100, blank=True)
    dni_retira = models.CharField("DNI de quien retira", max_length=20, blank=True)
    observaciones_egreso = models.TextField("Observaciones de egreso", blank=True)

    class Meta:
        ordering = ["-fecha_ingreso"]

    def __str__(self):
        return f"{self.nro_legajo_playon} - {self.vehiculo.dominio}"


class MovimientoLugar(models.Model):
    ingreso = models.ForeignKey(IngresoPlayon, on_delete=models.CASCADE, related_name="movimientos")
    lugar_anterior = models.ForeignKey(
        LugarPlayon,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
    )
    lugar_nuevo = models.ForeignKey(LugarPlayon, on_delete=models.PROTECT, related_name="+")
    movido_por = models.ForeignKey(User, on_delete=models.PROTECT)
    fecha = models.DateTimeField(auto_now_add=True)
    motivo = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.ingreso} → {self.lugar_nuevo}"
