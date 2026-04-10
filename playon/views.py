from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.core.management import call_command
import string
from django.db.models import Q
from .models import LugarPlayon, IngresoPlayon, MovimientoLugar
from ingresos.models import IngresoPlayon

# Vistas para el tablero del playón y gestión de lugares
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
            "es_admin_sistema": es_admin_sistema(request.user),
        },
    )

# Detalle de lugar: muestra ingreso activo (si hay), historial de ingresos y movimientos
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

# vistas para cambiar tipo de lugar (general <-> moto)
@require_POST
@login_required
def toggle_tipo_lugar(request, lugar_id):
    grupos = set(request.user.groups.values_list("name", flat=True))
    if "ENCARGADO_PLAYON" not in grupos and "ADMIN_SISTEMA" not in grupos:
        return render(request, "cuentas/no_permisos.html")

    lugar = get_object_or_404(LugarPlayon, id=lugar_id)

    # ❌ No permitir si está ocupado
    ocupado = IngresoPlayon.objects.filter(lugar=lugar, retirado=False).exists()
    if ocupado:
        return redirect("detalle_lugar", lugar_id=lugar.id)

    # 🔄 Alternar tipo
    if lugar.tipo == "GENERAL":
        lugar.tipo = "MOTO"
    else:
        lugar.tipo = "GENERAL"

    lugar.save()

    return redirect("detalle_lugar", lugar_id=lugar.id)

# vistas para cambiar estado de lugar (libre <-> fuera)
@require_POST
@login_required
def reactivar_lugar(request, lugar_id):
    grupos = set(request.user.groups.values_list("name", flat=True))
    if "ENCARGADO_PLAYON" not in grupos and "ADMIN_SISTEMA" not in grupos:
        return render(request, "cuentas/no_permisos.html")

    lugar = get_object_or_404(LugarPlayon, id=lugar_id)

    ocupado = IngresoPlayon.objects.filter(lugar=lugar, retirado=False).exists()
    if ocupado:
        return redirect("detalle_lugar", lugar_id=lugar.id)

    lugar.estado = "LIBRE"
    lugar.save()
    return redirect("detalle_lugar", lugar_id=lugar.id)




# marcar lugar fuera de servicio (no se puede usar hasta reactivar)
@require_POST
@login_required
def marcar_lugar_fuera(request, lugar_id):
    grupos = set(request.user.groups.values_list("name", flat=True))
    if "ENCARGADO_PLAYON" not in grupos and "ADMIN_SISTEMA" not in grupos:
        return render(request, "cuentas/no_permisos.html")

    lugar = get_object_or_404(LugarPlayon, id=lugar_id)

    # No permitir si hay ingreso activo ocupando ese lugar
    ocupado = IngresoPlayon.objects.filter(lugar=lugar, retirado=False).exists()
    if ocupado:
        return redirect("detalle_lugar", lugar_id=lugar.id)

    lugar.estado = "FUERA"
    lugar.save()
    return redirect("detalle_lugar", lugar_id=lugar.id)

# Lista de ingresos al playón con búsqueda
@login_required
def lista_ingresos(request):
    grupos = set(request.user.groups.values_list("name", flat=True))

    if "ENCARGADO_PLAYON" not in grupos and "ADMIN_SISTEMA" not in grupos:
        return render(request, "cuentas/no_permisos.html")

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

    return render(request, "ingresos/lista_ingresos.html", {
        "ingresos": ingresos,
        "titulo": "Ingresos al Playón",
        "q": q,
    })

# Solo admins pueden ejecutar esta vista que repara el tablero (crea lugares faltantes y recalcula estados)
def es_admin_sistema(user) -> bool:
    if not user.is_authenticated:
        return False
    grupos = set(user.groups.values_list("name", flat=True))
    return ("ADMIN_SISTEMA" in grupos) or user.is_superuser


@login_required
def reparar_tablero(request):
    if not es_admin_sistema(request.user):
        return render(request, "cuentas/no_permisos.html")

    # corre el command
    call_command("seed_playon")

    # volvemos al tablero
    return redirect("tablero_playon")
