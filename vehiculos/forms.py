from django import forms
from .models import IngresoPlayon


class IngresoPlayonForm(forms.ModelForm):
    dominio = forms.CharField(label="Dominio (patente)", max_length=10)

    class Meta:
        model = IngresoPlayon
        # campos que NO se muestran en el form (los manejamos a mano)
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


class EgresoPlayonForm(forms.ModelForm):
    class Meta:
        model = IngresoPlayon
        fields = ("nombre_retira", "dni_retira", "observaciones_egreso")
