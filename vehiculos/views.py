from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import Vehiculo, IngresoPlayon
from .forms import IngresoPlayonForm


@login_required
def lista_vehiculos(request):
    grupos = set(request.user.groups.values_list("name", flat=True))

    if "ENCARGADO_PLAYON" not in grupos and "ADMIN_SISTEMA" not in grupos:
        return render(request, "vehiculos/no_permiso.html")

    vehiculos = Vehiculo.objects.all().order_by("-fecha_alta")
    return render(request, "vehiculos/lista.html", {"vehiculos": vehiculos})


@login_required
def nuevo_ingreso_playon(request):
    grupos = set(request.user.groups.values_list("name", flat=True))

    if "ENCARGADO_PLAYON" not in grupos and "ADMIN_SISTEMA" not in grupos:
        return render(request, "vehiculos/no_permiso.html")

    if request.method == "POST":
        form = IngresoPlayonForm(request.POST)
        if form.is_valid():
            ingreso = form.save(commit=False)
            ingreso.recibido_por = request.user
            ingreso.save()
            return redirect("lista_vehiculos")  # después podemos ir a un detalle
    else:
        form = IngresoPlayonForm()

    return render(request, "vehiculos/ingreso_form.html", {"form": form})
