from django import forms
from vehiculos.models import IngresoPlayon, LugarPlayon

# Formulario para registrar el ingreso de un vehículo al playón. Se usa en la vista de registro de ingresos.
class IngresoPlayonForm(forms.ModelForm):
    dominio = forms.CharField(label="Dominio (patente)", max_length=10)
    nro_chasis = forms.CharField(label="N° de chasis", max_length=50, required=False)
    nro_motor = forms.CharField(label="N° de motor", max_length=50, required=False)


    class Meta:
        model = IngresoPlayon
        exclude = (
            "fecha_ingreso",
            "recibido_por",
            "vehiculo",
            "retirado",
            "fecha_retiro",
            "entregado_por",
            "nombre_retira",
            "dni_retira",
            "observaciones_egreso",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 1) Por defecto: solo lugares LIBRES
        qs = LugarPlayon.objects.filter(estado="LIBRE").order_by("fila", "columna")

        # 2) Si el usuario eligió tipo_vehiculo=MOTO (POST), filtramos a lugares tipo MOTO
        tipo = None
        if self.data:
            tipo = self.data.get("tipo_vehiculo")
        elif self.instance and getattr(self.instance, "tipo_vehiculo", None):
            tipo = self.instance.tipo_vehiculo

        if tipo == "MOTO":
            qs = qs.filter(tipo="MOTO")
        else:
            # si NO es moto, evitamos lugares exclusivos de moto
            qs = qs.exclude(tipo="MOTO")

        self.fields["lugar"].queryset = qs
        self.fields["lugar"].required = False  # por ahora opcional (hasta que tu jefe diga si es obligatorio)

    def clean_lugar(self):
        lugar = self.cleaned_data.get("lugar")
        if not lugar:
            return lugar

        if lugar.estado != "LIBRE":
            raise forms.ValidationError("Ese lugar ya no está libre. Elegí otro.")

        return lugar

# Formulario para registrar el egreso de un vehículo del playón. Se usa en la vista de registro de egresos.
class EgresoPlayonForm(forms.ModelForm):
    class Meta:
        model = IngresoPlayon
        fields = ("nombre_retira", "dni_retira", "observaciones_egreso")

# Formulario para editar los datos de un ingreso al playón, incluyendo detalles del vehículo, lugar de infracción, actas recibidas, estado de la alcoholemia, etc. 
# Se usa en la vista de edición de ingresos.
class EditarIngresoPlayonForm(forms.ModelForm):
    class Meta:
        model = IngresoPlayon
        fields = (
            "tipo_vehiculo",
            "lugar_infraccion",
            "nro_legajo_playon",
            "acta_infraccion_recibida",
            "acta_secuestro_recibida",
            "inventario_objetos_visibles_recibido",
            "registro_fotografico_recibido",
            "prueba_alcoholemia_estado",
            "coincide_inventario",
            "coinciden_danios_registrados",
            "detalle_danios_no_coincidentes",
            "bateria_desconectada",
            "observaciones_generales",
        )
