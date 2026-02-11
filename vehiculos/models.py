from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone as djtz

# Modelo para representar un vehículo registrado en el sistema. Se relaciona con los ingresos al playón.
class Vehiculo(models.Model):
    dominio = models.CharField("Dominio (Patente)", max_length=10, unique=True)
    marca = models.CharField(max_length=50, blank=False)
    modelo = models.CharField(max_length=50, blank=False)
    color = models.CharField(max_length=30, blank=False)
    nro_chasis = models.CharField("N° de chasis", max_length=50, blank=False)
    nro_motor = models.CharField("N° de motor", max_length=50, blank=False)
    anio = models.PositiveIntegerField("Año", null=True, blank=False)

    fecha_alta = models.DateTimeField("Fecha de alta en sistema", auto_now_add=True)

    def __str__(self):
        return f"{self.dominio} - {self.marca} {self.modelo}".strip()

    def reincidencias_total(self):
        return self.ingresos.count()
    
    def reincidencias_alcoholemia(self):
        return self.ingresos.filter(prueba_alcoholemia_estado="SI").count()

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

# Modelo para representar el ingreso de un vehículo al playón, con sus datos, documentación recibida, ubicación, y datos de egreso (retiro). 
# Se relaciona con el vehículo y el lugar del playón.
class IngresoPlayon(models.Model):
    TIPO_VEHICULO_CHOICES = [
        ("AUTO", "Auto"),
        ("MOTO", "Moto"),
        ("CAMIONETA", "Camioneta"),
        ("CAMION", "Camión"),
        ("OTRO", "Otro"),
    ]

    # Relación al vehículo
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.PROTECT, related_name="ingresos")
    fecha_ingreso = models.DateTimeField("Fecha de ingreso", auto_now_add=True)

    # Datos del vehículo (captura en el momento del ingreso; puede diferir del Vehiculo base)
    tipo_vehiculo = models.CharField("Tipo de vehículo", max_length=20, choices=TIPO_VEHICULO_CHOICES, blank=False)
    marca = models.CharField(max_length=50, blank=False)
    modelo = models.CharField(max_length=50, blank=False)
    anio = models.PositiveIntegerField("Año", null=True, blank=False)
    color = models.CharField(max_length=30, blank=False)

    nro_legajo_playon = models.CharField("N° de legajo en playón", max_length=30, unique=True)
    lugar_infraccion = models.CharField("Lugar de la infracción", max_length=255, blank=False)

    # Documentación anexada (checklist)
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

    # Observaciones de ingreso
    coincide_inventario = models.BooleanField("¿Coincide el inventario?", default=False)
    coinciden_danios_registrados = models.BooleanField("¿Coinciden los daños registrados?", default=False)
    detalle_danios_no_coincidentes = models.TextField("Detalle de daños no coincidentes", blank=True)
    bateria_desconectada = models.BooleanField("Batería desconectada", default=False)

    # Ubicación (texto libre) + lugar estructurado del tablero
    ubicacion_interna = models.CharField("Ubicación interna en playa", max_length=100, blank=False)
    lugar = models.ForeignKey(
        LugarPlayon,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="ingresos",
    )

    recibido_por = models.ForeignKey(User, on_delete=models.PROTECT, related_name="ingresos_recibidos")
    observaciones_generales = models.TextField("Observaciones generales", blank=True)

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
        verbose_name = "Ingreso al playón"
        verbose_name_plural = "Ingresos al playón"
        ordering = ["-fecha_ingreso"]

    def __str__(self):
        return f"Ingreso {self.nro_legajo_playon} - {self.vehiculo.dominio}"
    
    @property
    def dias_en_playon(self):
    # Día 1 cuenta desde el día que ingresó
        inicio = djtz.localtime(self.fecha_ingreso).date()

        fin_dt = self.fecha_retiro if (self.retirado and self.fecha_retiro) else djtz.now()
        fin = djtz.localtime(fin_dt).date()

        return (fin - inicio).days + 1


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

# Modelo para auditar los cambios realizados en los ingresos al playón.
# Cada vez que se edite un ingreso, se puede crear una instancia de AuditoriaIngreso con los datos del ingreso antes de la edición, 
# el usuario que hizo el cambio, la fecha y los cambios realizados (en formato JSON).
class AuditoriaIngreso(models.Model):
    ingreso = models.ForeignKey("IngresoPlayon", on_delete=models.CASCADE, related_name="auditorias")
    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    fecha = models.DateTimeField(auto_now_add=True)

    accion = models.CharField(max_length=30, default="EDICION")  # por si en el futuro se agregan otras acciones
    cambios = models.JSONField(default=dict, blank=True)  # Django 6 + Postgres/SQLite ok

    class Meta:
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.ingreso.nro_legajo_playon} - {self.accion} - {self.fecha:%Y-%m-%d %H:%M}"