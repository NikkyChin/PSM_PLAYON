from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
import string
from django.db.models import Q
from django.db import transaction
from vehiculos.models import IngresoPlayon, LugarPlayon, MovimientoLugar, AuditoriaIngreso, Vehiculo
from vehiculos.forms import EditarVehiculoForm, EditarIngresoPlayonForm



def _diff_instance_form(original_obj, form):
    """
    Devuelve dict {campo: {"antes": x, "despues": y}} solo para fields que cambiaron.
    Funciona con ModelForm. CAMBIAR EN EL FUTURO
    """
    cambios = {}
    for field in form.changed_data:
        antes = getattr(original_obj, field)
        despues = form.cleaned_data.get(field)

        # normalizar datetimes a str si querés evitar problemas JSON
        if hasattr(antes, "isoformat"):
            antes = antes.isoformat()
        if hasattr(despues, "isoformat"):
            despues = despues.isoformat()

        cambios[field] = {"antes": antes, "despues": despues}
    return cambios

@login_required
def tablero_playon(request):
    # lugares ordenados A1..Z15
    lugares = list(LugarPlayon.objects.all().order_by("fila", "columna"))

    # ingresos activos (no retirados) con lugar asignado
    ingresos_activos = (
        IngresoPlayon.objects
        .filter(retirado=False, lugar__isnull=False)
        .select_related("vehiculo", "lugar")
    )

    # mapa: lugar_id -> ingreso activo
    ocupacion = {ing.lugar_id: ing for ing in ingresos_activos}

    # armamos matriz A-Z / 1-15
    filas = list(string.ascii_uppercase)  # A..Z
    columnas = list(range(1, 16))         # 1..15

    # mapa rápido: (fila, col) -> LugarPlayon
    lugares_map = {(l.fila, l.columna): l for l in lugares}

    tablero = []
    for f in filas:
        fila_celdas = []
        for c in columnas:
            lugar = lugares_map.get((f, c))
            ingreso = ocupacion.get(lugar.id) if lugar else None
            fila_celdas.append({"lugar": lugar, "ingreso": ingreso})

        tablero.append({"fila": f, "celdas": fila_celdas})

    # contadores
    total_lugares = len(lugares)
    lugares_libres = sum(1 for l in lugares if l.estado == "LIBRE")
    lugares_ocupados = sum(1 for l in lugares if l.estado == "OCUPADO")
    lugares_fuera = sum(1 for l in lugares if l.estado == "FUERA")
    ocupacion_pct = round((lugares_ocupados / total_lugares) * 100, 1) if total_lugares else 0

    return render(
        request,
        "playon/tablero_playon.html",
        {
            "tablero": tablero,
            "columnas": columnas,
            "total_lugares": total_lugares,
            "lugares_libres": lugares_libres,
            "lugares_ocupados": lugares_ocupados,
            "lugares_fuera": lugares_fuera,
            "ocupacion_pct": ocupacion_pct,
        },
    )

@login_required
def detalle_lugar(request, lugar_id):
    lugar = get_object_or_404(LugarPlayon, id=lugar_id)

    # ingreso activo (si lo hay)
    ingreso_activo = (
        IngresoPlayon.objects
        .filter(lugar=lugar, retirado=False)
        .select_related("vehiculo", "recibido_por", "entregado_por")
        .first()
    )

    # historial de ingresos (últimos 20) en ese lugar
    historial_ingresos = (
        IngresoPlayon.objects
        .filter(lugar=lugar)
        .select_related("vehiculo")
        .order_by("-fecha_ingreso")[:20]
    )

    movimientos = []
    if ingreso_activo:
        movimientos = (
            MovimientoLugar.objects
            .filter(ingreso=ingreso_activo)
            .select_related("movido_por", "lugar_anterior", "lugar_nuevo")
            .order_by("-fecha")[:50]
        )

    return render(
        request,
        "playon/detalle_lugar.html",
        {
            "lugar": lugar,
            "ingreso_activo": ingreso_activo,
            "historial_ingresos": historial_ingresos,
            "movimientos": movimientos,
        },
    )



@require_POST
@login_required
def reactivar_lugar(request, lugar_id):
    grupos = set(request.user.groups.values_list("name", flat=True))
    if "ENCARGADO_PLAYON" not in grupos and "ADMIN_SISTEMA" not in grupos:
        return render(request, "cuentas/no_permiso.html")

    lugar = get_object_or_404(LugarPlayon, id=lugar_id)

    ocupado = IngresoPlayon.objects.filter(lugar=lugar, retirado=False).exists()
    if ocupado:
        return redirect("detalle_lugar", lugar_id=lugar.id)

    lugar.estado = "LIBRE"
    lugar.save()
    return redirect("detalle_lugar", lugar_id=lugar.id)



@login_required
def editar_ingreso(request, ingreso_id):
    grupos = set(request.user.groups.values_list("name", flat=True))
    if "ENCARGADO_PLAYON" not in grupos and "ADMIN_SISTEMA" not in grupos:
        return render(request, "cuentas/no_permiso.html")

    ingreso = get_object_or_404(IngresoPlayon.objects.select_related("vehiculo"), id=ingreso_id)
    vehiculo = ingreso.vehiculo

    
    ingreso_antes = IngresoPlayon.objects.get(id=ingreso.id)
    vehiculo_antes = Vehiculo.objects.get(id=vehiculo.id)

    if request.method == "POST":
        form_ingreso = EditarIngresoPlayonForm(request.POST, instance=ingreso)
        form_vehiculo = EditarVehiculoForm(request.POST, instance=vehiculo)

        if form_ingreso.is_valid() and form_vehiculo.is_valid():
            cambios_ingreso = _diff_instance_form(ingreso_antes, form_ingreso)
            cambios_vehiculo = _diff_instance_form(vehiculo_antes, form_vehiculo)

            cambios = {}
            if cambios_ingreso:
                cambios["ingreso"] = cambios_ingreso
            if cambios_vehiculo:
                cambios["vehiculo"] = cambios_vehiculo

            with transaction.atomic():
                form_vehiculo.save()
                form_ingreso.save()

                # Guardar auditoría SOLO si hubo cambios reales
                if cambios:
                    AuditoriaIngreso.objects.create(
                        ingreso=ingreso,
                        usuario=request.user,
                        accion="EDICION",
                        cambios=cambios,
                    )

            return redirect("detalle_ingreso", ingreso_id=ingreso.id)

    else:
        form_ingreso = EditarIngresoPlayonForm(instance=ingreso)
        form_vehiculo = EditarVehiculoForm(instance=vehiculo)

    return render(
        request,
        "vehiculos/editar_ingreso.html",
        {
            "ingreso": ingreso,
            "form_ingreso": form_ingreso,
            "form_vehiculo": form_vehiculo,
        },
    )

@require_POST
@login_required
def marcar_lugar_fuera(request, lugar_id):
    grupos = set(request.user.groups.values_list("name", flat=True))
    if "ENCARGADO_PLAYON" not in grupos and "ADMIN_SISTEMA" not in grupos:
        return render(request, "cuentas/no_permiso.html")

    lugar = get_object_or_404(LugarPlayon, id=lugar_id)

    # No permitir si hay ingreso activo ocupando ese lugar
    ocupado = IngresoPlayon.objects.filter(lugar=lugar, retirado=False).exists()
    if ocupado:
        return redirect("detalle_lugar", lugar_id=lugar.id)

    lugar.estado = "FUERA"
    lugar.save()
    return redirect("detalle_lugar", lugar_id=lugar.id)
