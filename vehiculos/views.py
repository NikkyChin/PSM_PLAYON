from django.contrib.auth.decorators import login_required
from django.shortcuts import render,  get_object_or_404
from .models import Vehiculo
from django.db.models import Q

# Lista de vehículos con búsqueda
@login_required
def lista_vehiculos(request):
    grupos = set(request.user.groups.values_list("name", flat=True))

    if "ENCARGADO_PLAYON" not in grupos and "ADMIN_SISTEMA" not in grupos:
        return render(request, "cuentas/no_permiso.html")

    q = (request.GET.get("q") or "").strip()

    vehiculos = Vehiculo.objects.all().order_by("-fecha_alta")
    if q:
        vehiculos = vehiculos.filter(
            Q(dominio__icontains=q) |
            Q(marca__icontains=q) |
            Q(modelo__icontains=q)
        )

    return render(request, "vehiculos/lista.html", {"vehiculos": vehiculos, "q": q})

# Muestra detalle de un vehículo, con su historial de ingresos al playón
@login_required
def detalle_vehiculo(request, vehiculo_id):
    grupos = set(request.user.groups.values_list("name", flat=True))
    if "ENCARGADO_PLAYON" not in grupos and "ADMIN_SISTEMA" not in grupos:
        return render(request, "cuentas/no_permiso.html")

    vehiculo = get_object_or_404(Vehiculo, id=vehiculo_id)


    # historial de ingresos de ese vehículo (últimos 20)
    ingresos = (
        vehiculo.ingresos
        .select_related("lugar", "recibido_por", "entregado_por")
        .order_by("-fecha_ingreso")[:20]
    )

    return render(
        request,
        "vehiculos/detalle_vehiculo.html",
        {"vehiculo": vehiculo, "ingresos": ingresos},
    )


@login_required
def imprimir_lista_vehiculos(request):
    q = (request.GET.get("q") or "").strip()

    vehiculos = Vehiculo.objects.all().order_by("-fecha_alta")

    if q:
        vehiculos = vehiculos.filter(
            Q(dominio__icontains=q) |
            Q(marca__icontains=q) |
            Q(modelo__icontains=q)
        )

    return render(request, "vehiculos/imprimir_lista.html", {"vehiculos": vehiculos, "q": q})