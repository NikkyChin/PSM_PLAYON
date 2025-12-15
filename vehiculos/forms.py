from django import forms
from .models import IngresoPlayon, LugarPlayon


class IngresoPlayonForm(forms.ModelForm):
    dominio = forms.CharField(label="Dominio (patente)", max_length=10)

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


class EgresoPlayonForm(forms.ModelForm):
    class Meta:
        model = IngresoPlayon
        fields = ("nombre_retira", "dni_retira", "observaciones_egreso")
