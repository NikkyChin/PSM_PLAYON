from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import OuterRef, Subquery
from django.utils import timezone

from ingresos.models import IngresoPlayon
from infracciones.models import Infraccion

def es_juez(user) -> bool:
    if not user.is_authenticated:
        return False
    grupos = set(user.groups.values_list("name", flat=True))
    return ("JUEZ" in grupos) or ("ADMIN_SISTEMA" in grupos) or user.is_superuser


@login_required
def lista_para_autorizar(request):
    if not es_juez(request.user):
        return render(request, "cuentas/no_permiso.html")

    # Subquery: última acta por dominio
    ultima_acta_sq = Infraccion.objects.filter(
        dominio=OuterRef("vehiculo__dominio")
    ).order_by("-creada_en").values("nro_acta")[:1]

    ingresos = (
        IngresoPlayon.objects
        .select_related("vehiculo", "lugar")
        .filter(retirado=False)  # están en playón
        .annotate(nro_acta=Subquery(ultima_acta_sq))
        .order_by("-fecha_ingreso")
    )

    return render(request, "juzgado/lista_autorizaciones.html", {"ingresos": ingresos})


@login_required
def autorizar_retiro(request, ingreso_id):
    if not es_juez(request.user):
        return render(request, "cuentas/no_permiso.html")

    ingreso = get_object_or_404(
        IngresoPlayon.objects.select_related("vehiculo", "lugar"),
        id=ingreso_id,
        retirado=False
    )

    # Actas asociadas a esa patente (dominio)
    actas = (
        Infraccion.objects
        .filter(dominio=ingreso.vehiculo.dominio)
        .select_related("inspector")
        .order_by("-creada_en")
    )

    if request.method == "POST":
        ingreso.retiro_autorizado = True
        ingreso.retiro_autorizado_en = timezone.now()
        ingreso.retiro_autorizado_por = request.user
        ingreso.save(update_fields=["retiro_autorizado", "retiro_autorizado_en", "retiro_autorizado_por"])
        return redirect("juzgado_lista")

    return render(request, "juzgado/autorizar_retiro.html", {
        "ingreso": ingreso,
        "actas": actas,
        "acta_principal": actas.first(),  # por si querés mostrar “la última” bien destacada
    })



@login_required
def revocar_autorizacion(request, ingreso_id):
    if not es_juez(request.user):
        return render(request, "cuentas/no_permiso.html")

    ingreso = get_object_or_404(
        IngresoPlayon,
        id=ingreso_id,
        retirado=False,
    )

    if request.method == "POST":
        ingreso.retiro_autorizado = False
        ingreso.retiro_autorizado_en = None
        ingreso.retiro_autorizado_por = None
        ingreso.save(update_fields=["retiro_autorizado", "retiro_autorizado_en", "retiro_autorizado_por"])
        return redirect("juzgado:lista_autorizaciones")

    return redirect("juzgado:autorizar_retiro", ingreso_id=ingreso.id)
