from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .models import Vehiculo, IngresoPlayon, MovimientoLugar, LugarPlayon
from .forms import IngresoPlayonForm, EgresoPlayonForm
import string



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
            dominio = form.cleaned_data["dominio"]
            dominio = dominio.replace(" ", "").upper()

            vehiculo, creado = Vehiculo.objects.get_or_create(
                dominio=dominio,
                defaults={
                    "marca": form.cleaned_data.get("marca", ""),
                    "modelo": form.cleaned_data.get("modelo", ""),
                    "color": form.cleaned_data.get("color", ""),
                    "anio": form.cleaned_data.get("anio"),
                    "nro_chasis": form.cleaned_data.get("nro_chasis", ""),
                    "nro_motor": form.cleaned_data.get("nro_motor", ""),
                },
            )
            
            # si ya existía, actualizamos si nos mandaron valores
            nro_chasis = (form.cleaned_data.get("nro_chasis") or "").strip()
            nro_motor = (form.cleaned_data.get("nro_motor") or "").strip()

            cambios = False
            if nro_chasis and not vehiculo.nro_chasis:
                vehiculo.nro_chasis = nro_chasis
                cambios = True

            if nro_motor and not vehiculo.nro_motor:
                vehiculo.nro_motor = nro_motor
                cambios = True

            if cambios:
                vehiculo.save()


            ingreso = form.save(commit=False)
            ingreso.vehiculo = vehiculo
            ingreso.recibido_por = request.user
            ingreso.save()

            # 👉 1️⃣ marcar lugar como ocupado
            if ingreso.lugar:
                ingreso.lugar.estado = "OCUPADO"
                ingreso.lugar.save()

                # 👉 2️⃣ registrar movimiento
                MovimientoLugar.objects.create(
                    ingreso=ingreso,
                    lugar_anterior=None,
                    lugar_nuevo=ingreso.lugar,
                    movido_por=request.user,
                    motivo="Ingreso al playón",
                )
            return redirect("lista_vehiculos")

        else:
            print("❌ FORMULARIO NO VÁLIDO:", form.errors)
    else:
        form = IngresoPlayonForm()

    return render(request, "vehiculos/ingreso_form.html", {"form": form})


@login_required
def lista_ingresos(request):
    grupos = set(request.user.groups.values_list("name", flat=True))

    if "ENCARGADO_PLAYON" not in grupos and "ADMIN_SISTEMA" not in grupos:
        return render(request, "vehiculos/no_permiso.html")

    ingresos = IngresoPlayon.objects.select_related("vehiculo", "recibido_por", "entregado_por").order_by("-fecha_ingreso")
    return render(request, "vehiculos/lista_ingresos.html", {"ingresos": ingresos})

@login_required
def registrar_egreso(request, ingreso_id):
    grupos = set(request.user.groups.values_list("name", flat=True))

    if "ENCARGADO_PLAYON" not in grupos and "ADMIN_SISTEMA" not in grupos:
        return render(request, "vehiculos/no_permiso.html")

    ingreso = get_object_or_404(IngresoPlayon, id=ingreso_id)

    # si ya está retirado, no tiene sentido cargarlo de nuevo
    if ingreso.retirado:
        return redirect("lista_ingresos")

    if request.method == "POST":
        form = EgresoPlayonForm(request.POST, instance=ingreso)
        if form.is_valid():
            egreso = form.save(commit=False)
            egreso.retirado = True
            egreso.fecha_retiro = timezone.now()
            egreso.entregado_por = request.user
            egreso.save()

            # 👉 1️⃣ registrar movimiento de salida
            if egreso.lugar:
                MovimientoLugar.objects.create(
                    ingreso=egreso,
                    lugar_anterior=egreso.lugar,
                    lugar_nuevo=egreso.lugar,
                    movido_por=request.user,
                    motivo="Egreso (retiro del playón)",
                )

                # 👉 2️⃣ liberar el lugar
                egreso.lugar.estado = "LIBRE"
                egreso.lugar.save()

            return redirect("lista_ingresos")
    else:
        form = EgresoPlayonForm(instance=ingreso)

    return render(request, "vehiculos/egreso_form.html", {"form": form, "ingreso": ingreso})

@login_required
def ingresos_en_playon(request):
    grupos = set(request.user.groups.values_list("name", flat=True))

    if "ENCARGADO_PLAYON" not in grupos and "ADMIN_SISTEMA" not in grupos:
        return render(request, "vehiculos/no_permiso.html")

    ingresos = IngresoPlayon.objects.select_related("vehiculo").filter(retirado=False).order_by("-fecha_ingreso")
    return render(request, "vehiculos/lista_ingresos.html", {
        "ingresos": ingresos,
        "titulo": "Vehículos actualmente en el playón",
        "solo_en_playon": True,
    })


@login_required
def retiros_playon(request):
    grupos = set(request.user.groups.values_list("name", flat=True))

    if "ENCARGADO_PLAYON" not in grupos and "ADMIN_SISTEMA" not in grupos:
        return render(request, "vehiculos/no_permiso.html")

    ingresos = IngresoPlayon.objects.select_related("vehiculo", "entregado_por").filter(retirado=True).order_by("-fecha_retiro")
    return render(request, "vehiculos/lista_ingresos.html", {
        "ingresos": ingresos,
        "titulo": "Historial de retiros del playón",
        "solo_en_playon": False,
    })


@login_required
def detalle_ingreso(request, ingreso_id):
    grupos = set(request.user.groups.values_list("name", flat=True))

    if "ENCARGADO_PLAYON" not in grupos and "ADMIN_SISTEMA" not in grupos:
        return render(request, "vehiculos/no_permiso.html")

    ingreso = get_object_or_404(IngresoPlayon, id=ingreso_id)

    return render(request, "vehiculos/detalle_ingreso.html", {"ingreso": ingreso})

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

    return render(
        request,
        "vehiculos/tablero_playon.html",
        {"tablero": tablero, "columnas": columnas},
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
        "vehiculos/detalle_lugar.html",
        {
            "lugar": lugar,
            "ingreso_activo": ingreso_activo,
            "historial_ingresos": historial_ingresos,
            "movimientos": movimientos,
        },
    )

@require_POST
@login_required
def marcar_lugar_fuera(request, lugar_id):
    grupos = set(request.user.groups.values_list("name", flat=True))
    if "ENCARGADO_PLAYON" not in grupos and "ADMIN_SISTEMA" not in grupos:
        return render(request, "vehiculos/no_permiso.html")

    lugar = get_object_or_404(LugarPlayon, id=lugar_id)

    # No permitir si hay ingreso activo ocupando ese lugar
    ocupado = IngresoPlayon.objects.filter(lugar=lugar, retirado=False).exists()
    if ocupado:
        # Si querés, más adelante lo mostramos bonito con messages framework
        return redirect("detalle_lugar", lugar_id=lugar.id)

    lugar.estado = "FUERA"
    lugar.save()
    return redirect("detalle_lugar", lugar_id=lugar.id)


@require_POST
@login_required
def reactivar_lugar(request, lugar_id):
    grupos = set(request.user.groups.values_list("name", flat=True))
    if "ENCARGADO_PLAYON" not in grupos and "ADMIN_SISTEMA" not in grupos:
        return render(request, "vehiculos/no_permiso.html")

    lugar = get_object_or_404(LugarPlayon, id=lugar_id)

    ocupado = IngresoPlayon.objects.filter(lugar=lugar, retirado=False).exists()
    if ocupado:
        return redirect("detalle_lugar", lugar_id=lugar.id)

    lugar.estado = "LIBRE"
    lugar.save()
    return redirect("detalle_lugar", lugar_id=lugar.id)


@login_required
def detalle_vehiculo(request, vehiculo_id):
    grupos = set(request.user.groups.values_list("name", flat=True))
    if "ENCARGADO_PLAYON" not in grupos and "ADMIN_SISTEMA" not in grupos:
        return render(request, "vehiculos/no_permiso.html")

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
