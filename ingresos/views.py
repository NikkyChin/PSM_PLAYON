from django.shortcuts import render
from vehiculos.forms import EgresoPlayonForm, EditarIngresoPlayonForm, EditarVehiculoForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.http import HttpResponseForbidden
from django.db.models import Q, Count
from django.db import transaction
from vehiculos.forms import IngresoPlayonForm
from vehiculos.models import IngresoPlayon, MovimientoLugar, AuditoriaIngreso
from vehiculos.models import Vehiculo

# Auditoría: función para comparar un objeto original con los datos de un form y detectar cambios
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

# Vistas para gestión de ingresos y egresos al playón, y su auditoría
def _qs_ingresos_base():
    return (
        IngresoPlayon.objects
        .select_related("vehiculo", "recibido_por", "entregado_por", "lugar")
        .annotate(
            reincidencias=Count("vehiculo__ingresos", distinct=True),
            reincidencias_alcoholemia=Count(
                "vehiculo__ingresos",
                filter=Q(vehiculo__ingresos__prueba_alcoholemia_estado="SI"),
                distinct=True
            ),
        )
        .order_by("-fecha_ingreso")
    )
    
# Lista de ingresos al playón con búsqueda
@login_required
def nuevo_ingreso_playon(request):
    grupos = set(request.user.groups.values_list("name", flat=True))

    if "ENCARGADO_PLAYON" not in grupos and "ADMIN_SISTEMA" not in grupos:
        return render(request, "cuentas/no_permiso.html")

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

            if ingreso.lugar:
                ingreso.lugar.estado = "OCUPADO"
                ingreso.lugar.save()

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

    return render(request, "ingresos/ingreso_form.html", {"form": form})

# Resgistra el egreso de un vehículo del playón, con formulario para cargar datos de retiro y generar auditoría de cambios.
@login_required
def registrar_egreso(request, ingreso_id):
    grupos = set(request.user.groups.values_list("name", flat=True))

    if "ENCARGADO_PLAYON" not in grupos and "ADMIN_SISTEMA" not in grupos:
        return render(request, "cuentas/no_permiso.html")

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

    return render(request, "ingresos/egreso_form.html", {"form": form, "ingreso": ingreso})

# Imprime el comprobante de retiro del playón, con datos del ingreso y egreso, para entregar 
# al usuario que retira el vehículo. Solo se puede imprimir si el ingreso ya fue retirado, para evitar confusiones.
@login_required
def imprimir_retiro(request, ingreso_id):
    grupos = set(request.user.groups.values_list("name", flat=True))
    if "ENCARGADO_PLAYON" not in grupos and "ADMIN_SISTEMA" not in grupos:
        return render(request, "cuentas/no_permiso.html")

    ingreso = get_object_or_404(
        IngresoPlayon.objects.select_related("vehiculo", "recibido_por", "entregado_por", "lugar"),
        id=ingreso_id
    )

    # Solo se imprime si ya fue retirado
    if not ingreso.retirado:
        return HttpResponseForbidden("Este ingreso todavía no fue retirado.")

    return render(request, "ingresos/imprimir_retiro.html", {"ingreso": ingreso})

# Detalle de un ingreso al playón, con su auditoría de cambios
@login_required
def detalle_ingreso(request, ingreso_id):
    grupos = set(request.user.groups.values_list("name", flat=True))

    if "ENCARGADO_PLAYON" not in grupos and "ADMIN_SISTEMA" not in grupos:
        return render(request, "cuentas/no_permiso.html")

    ingreso = get_object_or_404(IngresoPlayon, id=ingreso_id)
    auditorias = ingreso.auditorias.select_related("usuario").all()[:20]

    return render(request, "ingresos/detalle_ingreso.html", {"ingreso": ingreso, "auditorias": auditorias})

# Lista de ingresos al playón con búsqueda
@login_required
def lista_ingresos(request):
    grupos = set(request.user.groups.values_list("name", flat=True))
    if "ENCARGADO_PLAYON" not in grupos and "ADMIN_SISTEMA" not in grupos:
        return render(request, "cuentas/no_permiso.html")

    q = (request.GET.get("q") or "").strip()

    ingresos = _qs_ingresos_base()

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

    
# Lista de ingresos actualmente en el playón (no retirados) con búsqueda
@login_required
def ingresos_en_playon(request):
    grupos = set(request.user.groups.values_list("name", flat=True))
    if "ENCARGADO_PLAYON" not in grupos and "ADMIN_SISTEMA" not in grupos:
        return render(request, "cuentas/no_permiso.html")

    q = (request.GET.get("q") or "").strip()

    ingresos = _qs_ingresos_base().filter(retirado=False)

    if q:
        ingresos = ingresos.filter(
            Q(nro_legajo_playon__icontains=q) |
            Q(vehiculo__dominio__icontains=q)
        )

    return render(request, "ingresos/lista_ingresos.html", {
        "ingresos": ingresos,
        "titulo": "En el playón",
        "q": q,
    })

# Lista de ingresos retirados del playón con búsqueda
@login_required
def retiros_playon(request):
    grupos = set(request.user.groups.values_list("name", flat=True))
    if "ENCARGADO_PLAYON" not in grupos and "ADMIN_SISTEMA" not in grupos:
        return render(request, "cuentas/no_permiso.html")

    q = (request.GET.get("q") or "").strip()

    ingresos = _qs_ingresos_base().filter(retirado=True)

    if q:
        ingresos = ingresos.filter(
            Q(nro_legajo_playon__icontains=q) |
            Q(vehiculo__dominio__icontains=q)
        )

    return render(request, "ingresos/lista_ingresos.html", {
        "ingresos": ingresos,
        "titulo": "Retirados",
        "q": q,
    })

# Editar un ingreso al playón, con formulario para modificar datos del ingreso y del vehículo, y generar auditoría de cambios.
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
        "ingresos/editar_ingreso.html",
        {
            "ingreso": ingreso,
            "form_ingreso": form_ingreso,
            "form_vehiculo": form_vehiculo,
        },
    )