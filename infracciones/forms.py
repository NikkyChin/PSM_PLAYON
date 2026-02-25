from django import forms
from django.contrib.auth.models import User
from .models import Infraccion


class InfraccionForm(forms.ModelForm):

    class Meta:
        model = Infraccion
        fields = [
            "fecha_acta",
            "autor_acta",

            "nro_acta",
            "dni_infractor",
            "nombre_infractor",
            "apellido_infractor",

            "dominio",
            "marca",
            "modelo",

            "es_titular",
            "nro_cedula",

            "retenido_playon",
            "prueba_alcoholemia_estado",
            "descripcion",

            "archivo_adjunto",
        ]

        widgets = {
            "fecha_acta": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "descripcion": forms.Textarea(attrs={"rows": 4}),
        }

def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

    if self.instance and self.instance.fecha_acta:
        self.fields["fecha_acta"].initial = self.instance.fecha_acta.strftime("%Y-%m-%dT%H:%M")

    def clean_dominio(self):
        return (self.cleaned_data.get("dominio") or "").replace(" ", "").upper()