from django.contrib.auth.decorators import login_required
from django.shortcuts import render,  get_object_or_404
from .models import Vehiculo, IngresoPlayon
from django.db.models import Q


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

@login_required
def lista_ingresos(request):
    grupos = set(request.user.groups.values_list("name", flat=True))

    if "ENCARGADO_PLAYON" not in grupos and "ADMIN_SISTEMA" not in grupos:
        return render(request, "cuentas/no_permiso.html")

    q = (request.GET.get("q") or "").strip()

    ingresos = (
        IngresoPlayon.objects
        .select_related("vehiculo", "recibido_por", "entregado_por")
        .order_by("-fecha_ingreso")
    )

    if q:
        ingresos = ingresos.filter(
            Q(nro_legajo_playon__icontains=q) |
            Q(vehiculo__dominio__icontains=q)
        )

    return render(request, "vehiculos/lista_ingresos.html", {
        "ingresos": ingresos,
        "titulo": "Ingresos al Playón",
        "q": q,
    })


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



