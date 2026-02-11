from django import forms
from .models import Infraccion

# Formulario para crear o editar un acta de infracción. Se usa en las vistas de creación y edición de actas.
class InfraccionForm(forms.ModelForm):
    class Meta:
        model = Infraccion
        fields = [
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
            "descripcion",
        ]
        widgets = {
            "descripcion": forms.Textarea(attrs={"rows": 4}),
        }

    def clean_dominio(self):
        dom = (self.cleaned_data.get("dominio") or "").replace(" ", "").upper()
        return dom
