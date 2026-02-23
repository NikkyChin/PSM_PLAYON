from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone as djtz

class IngresoPlayon(models.Model):
    TIPO_VEHICULO_CHOICES = [
        ("AUTO", "Auto"),
        ("MOTO", "Moto"),
        ("CAMIONETA", "Camioneta"),
        ("CAMION", "Camión"),
        ("OTRO", "Otro"),
    ]

    vehiculo = models.ForeignKey("vehiculos.Vehiculo", on_delete=models.PROTECT, related_name="ingresos")
    fecha_ingreso = models.DateTimeField("Fecha de ingreso", auto_now_add=True)

    tipo_vehiculo = models.CharField("Tipo de vehículo", max_length=20, choices=TIPO_VEHICULO_CHOICES, blank=False)
    marca = models.CharField(max_length=50, blank=False)
    modelo = models.CharField(max_length=50, blank=False)
    anio = models.PositiveIntegerField("Año", null=True, blank=False)
    color = models.CharField(max_length=30, blank=False)

    nro_legajo_playon = models.CharField("N° de legajo en playón", max_length=30, unique=True)
    lugar_infraccion = models.CharField("Lugar de la infracción", max_length=255, blank=False)

    acta_infraccion_recibida = models.BooleanField("Acta de infracción recibida", default=False)
    acta_secuestro_recibida = models.BooleanField("Acta de secuestro recibida", default=False)
    inventario_objetos_visibles_recibido = models.BooleanField("Inventario de objetos visibles recibido", default=False)
    registro_fotografico_recibido = models.BooleanField("Registro fotográfico recibido", default=False)

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

    coincide_inventario = models.BooleanField("¿Coincide el inventario?", default=False)
    coinciden_danios_registrados = models.BooleanField("¿Coinciden daños registrados?", default=False)
    detalle_danios_no_coincidentes = models.TextField("Detalle de daños no coincidentes", blank=True)
    bateria_desconectada = models.BooleanField("Batería desconectada", default=False)

    ubicacion_interna = models.CharField("Ubicación interna en playón", max_length=100, blank=False)
    lugar = models.ForeignKey(
        "playon.LugarPlayon",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="ingresos",
    )
    operador_grua = models.TextField("Operador de grúa y detalles del traslado", blank=False, default="")
    recibido_por = models.ForeignKey(User, on_delete=models.PROTECT, related_name="ingresos_recibidos")
    observaciones_generales = models.TextField("Observaciones generales", blank=True, default="")

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

    retiro_autorizado = models.BooleanField("Retiro autorizado por Juzgado", default=False)
    retiro_autorizado_en = models.DateTimeField("Fecha autorización", null=True, blank=True)
    retiro_autorizado_por = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="retiros_autorizados",
        verbose_name="Autorizado por",
    )

    class Meta:
        verbose_name = "Ingreso al playón"
        verbose_name_plural = "Ingresos al playón"
        ordering = ["-fecha_ingreso"]

    def __str__(self):
        return f"Ingreso {self.nro_legajo_playon} - {self.vehiculo.dominio}"

    @property
    def dias_en_playon(self):
        inicio = djtz.localtime(self.fecha_ingreso).date()
        fin_dt = self.fecha_retiro if (self.retirado and self.fecha_retiro) else djtz.now()
        fin = djtz.localtime(fin_dt).date()
        return (fin - inicio).days + 1

# Modelo para auditoría de cambios en IngresoPlayon. Cada vez que se edite un ingreso, se puede crear una instancia de este modelo con los cambios realizados.
class AuditoriaIngreso(models.Model):
    ingreso = models.ForeignKey("ingresos.IngresoPlayon", on_delete=models.CASCADE, related_name="auditorias",)
    usuario = models.ForeignKey(User,on_delete=models.PROTECT,related_name="auditorias_ingresos",)  # este sí está bien que sea único)
    fecha = models.DateTimeField(auto_now_add=True)

    accion = models.CharField(max_length=30, default="EDICION")
    cambios = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.ingreso.nro_legajo_playon} - {self.accion} - {self.fecha:%Y-%m-%d %H:%M}"
