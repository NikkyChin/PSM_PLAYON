from django import forms
from .models import IngresoPlayon


class IngresoPlayonForm(forms.ModelForm):
    dominio = forms.CharField(label="Dominio (patente)", max_length=10)

    class Meta:
        model = IngresoPlayon
        # sacamos vehiculo, fecha_ingreso y recibido_por (se completan por código)
        exclude = ("fecha_ingreso", "recibido_por", "vehiculo")
