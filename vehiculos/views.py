from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .models import Vehiculo, IngresoPlayon
from .forms import IngresoPlayonForm, EgresoPlayonForm
from .models import MovimientoLugar



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
                },
            )

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
