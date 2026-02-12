from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Count
from ingresos.models import IngresoPlayon
from infracciones.models import Infraccion

# Vista para el dashboard de administración, accesible solo por usuarios con rol ADMIN_SISTEMA o superusuarios.
def es_admin_sistema(user) -> bool:
    if not user.is_authenticated:
        return False
    grupos = set(user.groups.values_list("name", flat=True))
    return ("ADMIN_SISTEMA" in grupos) or user.is_superuser

# Decorador para requerir login en la vista del dashboard.
@login_required
def dashboard_admin(request):
    if not es_admin_sistema(request.user):
        return render(request, "cuentas/no_permiso.html")

    total = IngresoPlayon.objects.count()
    en_playon = IngresoPlayon.objects.filter(retirado=False).count()
    retirados = IngresoPlayon.objects.filter(retirado=True).count()
    alcoholemia_si = IngresoPlayon.objects.filter(prueba_alcoholemia_estado="SI").count()

    # Torta: estados (en playón vs retirados)
    estados_labels = ["En playón", "Retirados"]
    estados_values = [en_playon, retirados]

    # Barras: por tipo de vehículo
    por_tipo = (
        IngresoPlayon.objects.values("tipo_vehiculo")
        .annotate(c=Count("id"))
        .order_by("-c")
    )
    tipo_labels = [x["tipo_vehiculo"] for x in por_tipo]
    tipo_values = [x["c"] for x in por_tipo]

    # Barras: alcoholemia (SI/NO/NC)
    por_alco = (
        IngresoPlayon.objects.values("prueba_alcoholemia_estado")
        .annotate(c=Count("id"))
        .order_by("-c")
    )
    alco_labels = [x["prueba_alcoholemia_estado"] for x in por_alco]
    alco_values = [x["c"] for x in por_alco]

    # “Motivos”: lo más cercano sin tocar modelos hoy:
    # usamos Infraccion.descripcion como "motivo" (Top 10)
    motivos = (
        Infraccion.objects.values("descripcion")
        .annotate(c=Count("id"))
        .order_by("-c")[:10]
    )
    motivos_labels = [x["descripcion"][:40] + ("…" if len(x["descripcion"]) > 40 else "") for x in motivos]
    motivos_values = [x["c"] for x in motivos]

    context = {
        "total": total,
        "en_playon": en_playon,
        "retirados": retirados,
        "alcoholemia_si": alcoholemia_si,
        "estados_labels": estados_labels,
        "estados_values": estados_values,
        "tipo_labels": tipo_labels,
        "tipo_values": tipo_values,
        "alco_labels": alco_labels,
        "alco_values": alco_values,
        "motivos_labels": motivos_labels,
        "motivos_values": motivos_values,
    }
    return render(request, "estadisticas/dashboard_admin.html", context)

# Vista para imprimir el dashboard, con un diseño más simple y optimizado para impresión.
@login_required
def imprimir_dashboard(request):
    if not request.user.groups.filter(name="ADMIN_SISTEMA").exists():
        return render(request, "cuentas/no_permiso.html")

    ingresos = IngresoPlayon.objects.all()

    total = ingresos.count()
    retirados = ingresos.filter(retirado=True).count()
    en_playon = ingresos.filter(retirado=False).count()

    alco_si = ingresos.filter(prueba_alcoholemia_estado="SI").count()
    alco_no = ingresos.filter(prueba_alcoholemia_estado="NO").count()
    alco_nc = ingresos.filter(prueba_alcoholemia_estado="NC").count()

    # Si quisieras agregar más estadísticas a esta vista de impresión, podrías calcularlas aquí y pasarlas al contexto.
    # por_tipo = ingresos.values("tipo_vehiculo").annotate(total=Count("id")).order_by("-total")

    return render(request, "estadisticas/imprimir_dashboard.html", {
        "total": total,
        "retirados": retirados,
        "en_playon": en_playon,
        "alco_si": alco_si,
        "alco_no": alco_no,
        "alco_nc": alco_nc,
        # "por_tipo": por_tipo,
    })
