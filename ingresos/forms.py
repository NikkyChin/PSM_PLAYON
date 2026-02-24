from django import forms
from .models import IngresoPlayon
from playon.models import LugarPlayon


# ==========================
# 1) FORM: NUEVO INGRESO
# ==========================
class IngresoPlayonForm(forms.ModelForm):
    # Campos extra (no están en IngresoPlayon)
    dominio = forms.CharField(label="Dominio (patente)", max_length=10)
    nro_chasis = forms.CharField(label="N° de chasis", max_length=50, required=False)
    nro_motor = forms.CharField(label="N° de motor", max_length=50, required=False)

    class Meta:
        model = IngresoPlayon

        # ✅ LISTA BLANCA: SOLO lo que se carga al ingresar
        fields = (
            # snapshot del ingreso (vehículo)
            "tipo_vehiculo",
            "marca",
            "modelo",
            "anio",
            "color",

            # datos del ingreso
            "nro_legajo_playon",
            "lugar_infraccion",
            "ubicacion_interna",
            "lugar",

            # documentación
            "acta_infraccion_recibida",
            "acta_secuestro_recibida",
            "inventario_objetos_visibles_recibido",
            "registro_fotografico_recibido",

            # alcoholemia
            "prueba_alcoholemia_estado",

            # observaciones / checklist
            "coincide_inventario",
            "coinciden_danios_registrados",
            "detalle_danios_no_coincidentes",
            "bateria_desconectada",

            # traslado
            "operador_grua",

            # observaciones generales
            "observaciones_generales",
        )

        widgets = {
            "detalle_danios_no_coincidentes": forms.Textarea(attrs={"rows": 3}),
            "observaciones_generales": forms.Textarea(attrs={"rows": 3}),
            "operador_grua": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 1) Por defecto: solo lugares LIBRES
        qs = LugarPlayon.objects.filter(estado="LIBRE").order_by("fila", "columna")

        # 2) Si el usuario eligió tipo_vehiculo=MOTO, filtramos a lugares tipo MOTO
        tipo = None
        if self.data:
            tipo = self.data.get("tipo_vehiculo")
        elif self.instance and getattr(self.instance, "tipo_vehiculo", None):
            tipo = self.instance.tipo_vehiculo

        if tipo == "MOTO":
            qs = qs.filter(tipo="MOTO")
        else:
            qs = qs.exclude(tipo="MOTO")

        # Lugar opcional
        self.fields["lugar"].queryset = qs
        self.fields["lugar"].required = False

    def clean_dominio(self):
        dom = (self.cleaned_data.get("dominio") or "").replace(" ", "").upper()
        return dom

    def clean_lugar(self):
        lugar = self.cleaned_data.get("lugar")
        if not lugar:
            return lugar

        if lugar.estado != "LIBRE":
            raise forms.ValidationError("Ese lugar ya no está libre. Elegí otro.")

        return lugar


# ==========================
# 2) FORM: EGRESO / RETIRO
# ==========================
class EgresoPlayonForm(forms.ModelForm):
    class Meta:
        model = IngresoPlayon
        fields = ("nombre_retira", "dni_retira", "observaciones_egreso")

        widgets = {
            "observaciones_egreso": forms.Textarea(attrs={"rows": 3}),
        }


# ==========================
# 3) FORM: EDITAR INGRESO
# ==========================
class EditarIngresoPlayonForm(forms.ModelForm):
    class Meta:
        model = IngresoPlayon

        # ✅ LISTA BLANCA: SOLO lo que permitís editar
        # (y NUNCA aparecen los campos del juez ni campos nuevos)
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

            "operador_grua",
            "observaciones_generales",

            # si querés permitir cambiar la ubicación/lugar, descomentá:
            # "ubicacion_interna",
            # "lugar",
        )

        widgets = {
            "detalle_danios_no_coincidentes": forms.Textarea(attrs={"rows": 3}),
            "observaciones_generales": forms.Textarea(attrs={"rows": 3}),
            "operador_grua": forms.Textarea(attrs={"rows": 2}),
        }