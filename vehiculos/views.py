from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from vehiculos.models import Vehiculo

@login_required
def lista_vehiculos(request):
    # permitir solo encargados de playón
    grupos = set(request.user.groups.values_list("name", flat=True))
    
    if "ENCARGADO_PLAYON" not in grupos and "ADMIN_SISTEMA" not in grupos:
        return render(request, "vehiculos/no_permiso.html")

    vehiculos = Vehiculo.objects.all().order_by("-fecha_alta")
    return render(request, "vehiculos/lista.html", {"vehiculos": vehiculos})
