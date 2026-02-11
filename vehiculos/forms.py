from django import forms
from .models import Vehiculo

# Formulario para editar los datos de un vehículo registrado en el playón, como dominio, marca, modelo, color, año, número de chasis y número de motor. 
# Se usa en la vista de edición de vehículos.
class EditarVehiculoForm(forms.ModelForm):
    class Meta:
        model = Vehiculo
        fields = (
            "dominio",
            "marca",
            "modelo",
            "color",
            "anio",
            "nro_chasis",
            "nro_motor",
        )