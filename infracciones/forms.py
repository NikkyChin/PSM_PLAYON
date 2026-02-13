from django import forms
from .models import Infraccion

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
            "prueba_alcoholemia_estado", 
            "descripcion",
        ]
        widgets = {
            "descripcion": forms.Textarea(attrs={"rows": 4}),
        }

    def clean_dominio(self):
        dom = (self.cleaned_data.get("dominio") or "").replace(" ", "").upper()
        return dom
