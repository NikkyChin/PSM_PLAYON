from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .models import Vehiculo, IngresoPlayon, MovimientoLugar, LugarPlayon, AuditoriaIngreso 
from .forms import IngresoPlayonForm, EgresoPlayonForm, EditarIngresoPlayonForm, EditarVehiculoForm
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponseForbidden
import string

def _diff_instance_form(original_obj, form):
    """
    Devuelve dict {campo: {"antes": x, "despues": y}} solo para fields que cambiaron.
    Funciona con ModelForm.
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
def lista_vehiculos(request):
    grupos = set(request.user.groups.values_list("name", flat=True))

    if "ENCARGADO_PLAYON" not in grupos and "ADMIN_SISTEMA" not in grupos:
        return render(request, "vehiculos/no_permiso.html")

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

            # marcar lugar como ocupado
            if ingreso.lugar:
                ingreso.lugar.estado = "OCUPADO"
                ingreso.lugar.save()

                # registrar movimiento
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

            # registrar movimiento de salida
            if egreso.lugar:
                MovimientoLugar.objects.create(
                    ingreso=egreso,
                    lugar_anterior=egreso.lugar,
                    lugar_nuevo=egreso.lugar,
                    movido_por=request.user,
                    motivo="Egreso (retiro del playón)",
                )

                # liberar el lugar
                egreso.lugar.estado = "LIBRE"
                egreso.lugar.save()

            return redirect("imprimir_retiro", ingreso_id=egreso.id)
    else:
        form = EgresoPlayonForm(instance=ingreso)

    return render(request, "vehiculos/egreso_form.html", {"form": form, "ingreso": ingreso})

@login_required
def ingresos_en_playon(request):
    grupos = set(request.user.groups.values_list("name", flat=True))

    if "ENCARGADO_PLAYON" not in grupos and "ADMIN_SISTEMA" not in grupos:
        return render(request, "vehiculos/no_permiso.html")

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
def retiros_playon(request):
    grupos = set(request.user.groups.values_list("name", flat=True))

    if "ENCARGADO_PLAYON" not in grupos and "ADMIN_SISTEMA" not in grupos:
        return render(request, "vehiculos/no_permiso.html")

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
def detalle_ingreso(request, ingreso_id):
    grupos = set(request.user.groups.values_list("name", flat=True))

    if "ENCARGADO_PLAYON" not in grupos and "ADMIN_SISTEMA" not in grupos:
        return render(request, "vehiculos/no_permiso.html")

    ingreso = get_object_or_404(IngresoPlayon, id=ingreso_id)
    auditorias = ingreso.auditorias.select_related("usuario").all()[:20]

    return render(request, "vehiculos/detalle_ingreso.html", {"ingreso": ingreso, "auditorias": auditorias})

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
        "vehiculos/tablero_playon.html",
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



@login_required
def imprimir_retiro(request, ingreso_id):
    grupos = set(request.user.groups.values_list("name", flat=True))
    if "ENCARGADO_PLAYON" not in grupos and "ADMIN_SISTEMA" not in grupos:
        return render(request, "vehiculos/no_permiso.html")

    ingreso = get_object_or_404(
        IngresoPlayon.objects.select_related("vehiculo", "recibido_por", "entregado_por", "lugar"),
        id=ingreso_id
    )

    # Solo se imprime si ya fue retirado
    if not ingreso.retirado:
        return HttpResponseForbidden("Este ingreso todavía no fue retirado.")

    return render(request, "vehiculos/imprimir_retiro.html", {"ingreso": ingreso})


@login_required
def editar_ingreso(request, ingreso_id):
    grupos = set(request.user.groups.values_list("name", flat=True))
    if "ENCARGADO_PLAYON" not in grupos and "ADMIN_SISTEMA" not in grupos:
        return render(request, "vehiculos/no_permiso.html")

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
