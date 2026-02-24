from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import OuterRef, Subquery, Q
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
        return render(request, "cuentas/no_permisos.html")

    q = (request.GET.get("q") or "").strip()

    # Subquery: última acta por dominio
    ultima_acta_sq = Infraccion.objects.filter(
        dominio=OuterRef("vehiculo__dominio")
    ).order_by("-creada_en").values("nro_acta")[:1]

    ingresos = (
        IngresoPlayon.objects
        .select_related("vehiculo", "lugar")
        .filter(retirado=False)                 # están en playón
        .annotate(nro_acta=Subquery(ultima_acta_sq))
        .order_by("-fecha_ingreso")
    )

    if q:
        ingresos = ingresos.filter(
            Q(vehiculo__dominio__icontains=q) |
            Q(nro_legajo_playon__icontains=q) |
            Q(lugar_infraccion__icontains=q)
        )

    return render(request, "juzgado/lista_autorizaciones.html", {"ingresos": ingresos, "q": q})


@login_required
def autorizar_retiro(request, ingreso_id):
    if not es_juez(request.user):
        return render(request, "cuentas/no_permisos.html")

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
        motivo = (request.POST.get("retiro_autorizacion_motivo") or "").strip()
        archivo = request.FILES.get("retiro_autorizacion_archivo")

        # Si querés obligar motivo sí o sí:
        if not motivo:
            return render(request, "juzgado/autorizar_retiro.html", {
                "ingreso": ingreso,
                "actas": actas,
                "acta_principal": actas.first(),
                "error": "Tenés que escribir un motivo / descripción de la autorización.",
            })

        ingreso.retiro_autorizado = True
        ingreso.retiro_autorizado_en = timezone.now()
        ingreso.retiro_autorizado_por = request.user
        ingreso.retiro_autorizacion_motivo = motivo

        # Archivo opcional pero recomendado
        if archivo:
            ingreso.retiro_autorizacion_archivo = archivo

        ingreso.save()

        # ✅ Historial de AUTORIZACIONES (recomendado para control judicial)
        return redirect("juzgado:historial_autorizaciones")

        # 🚧 Alternativa: si tu jefe quiere historial de RETIROS reales, redirigí a ese:
        # return redirect("juzgado:historial_retiros")

    return render(request, "juzgado/autorizar_retiro.html", {
        "ingreso": ingreso,
        "actas": actas,
        "acta_principal": actas.first(),
    })


@login_required
def revocar_autorizacion(request, ingreso_id):
    if not es_juez(request.user):
        return render(request, "cuentas/no_permisos.html")

    ingreso = get_object_or_404(IngresoPlayon, id=ingreso_id, retirado=False)

    if request.method == "POST":
        ingreso.retiro_autorizado = False
        ingreso.retiro_autorizado_en = None
        ingreso.retiro_autorizado_por = None
        ingreso.retiro_autorizacion_motivo = ""
        ingreso.retiro_autorizacion_archivo = None
        ingreso.save()
        return redirect("juzgado:lista_autorizaciones")

    return redirect("juzgado:autorizar_retiro", ingreso_id=ingreso.id)


# ==========================
# ✅ Historial de AUTORIZACIONES (recomendado)
# (muestra todo lo que el juez ya autorizó, aunque aún no se retiró)
# ==========================
@login_required
def historial_autorizaciones(request):
    if not es_juez(request.user):
        return render(request, "cuentas/no_permisos.html")

    q = (request.GET.get("q") or "").strip()

    ultima_acta_sq = Infraccion.objects.filter(
        dominio=OuterRef("vehiculo__dominio")
    ).order_by("-creada_en").values("nro_acta")[:1]

    autorizaciones = (
        IngresoPlayon.objects
        .select_related("vehiculo", "lugar", "retiro_autorizado_por")
        .filter(retiro_autorizado=True)
        .annotate(nro_acta=Subquery(ultima_acta_sq))
        .order_by("-retiro_autorizado_en")
    )

    if q:
        autorizaciones = autorizaciones.filter(
            Q(vehiculo__dominio__icontains=q) |
            Q(nro_legajo_playon__icontains=q) |
            Q(retiro_autorizacion_motivo__icontains=q)
        )

    return render(request, "juzgado/historial_autorizaciones.html", {
        "items": autorizaciones,
        "q": q,
        "titulo": "Historial de Autorizaciones",
    })


# ==========================
# 🚧 Historial de RETIROS (comentado)
# (muestra solo los que efectivamente ya salieron del playón)
# ==========================
"""
@login_required
def historial_retiros(request):
    if not es_juez(request.user):
        return render(request, "cuentas/no_permisos.html")

    q = (request.GET.get("q") or "").strip()

    ultima_acta_sq = Infraccion.objects.filter(
        dominio=OuterRef("vehiculo__dominio")
    ).order_by("-creada_en").values("nro_acta")[:1]

    retiros = (
        IngresoPlayon.objects
        .select_related("vehiculo", "lugar", "retiro_autorizado_por", "entregado_por")
        .filter(retirado=True)
        .annotate(nro_acta=Subquery(ultima_acta_sq))
        .order_by("-fecha_retiro")
    )

    if q:
        retiros = retiros.filter(
            Q(vehiculo__dominio__icontains=q) |
            Q(nro_legajo_playon__icontains=q)
        )

    return render(request, "juzgado/historial_retiros.html", {
        "items": retiros,
        "q": q,
        "titulo": "Historial de Retiros",
    })
"""