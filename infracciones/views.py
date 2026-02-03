from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from .models import Infraccion
from .forms import InfraccionForm
from .permissions import es_inspector


@login_required
def lista_actas(request):
    if not es_inspector(request.user):
        return render(request, "cuentas/no_permiso.html")

    q = (request.GET.get("q") or "").strip()

    actas = Infraccion.objects.filter(inspector=request.user).order_by("-creada_en")

    if q:
        # Búsqueda simple por nro_acta, dni o dominio
        actas = actas.filter(
            Q(nro_acta__icontains=q) |
            Q(dni_infractor__icontains=q) |
            Q(dominio__icontains=q)
        )

    return render(request, "infracciones/lista_actas.html", {"actas": actas, "q": q})


@login_required
def nueva_acta(request):
    if not es_inspector(request.user):
        return render(request, "cuentas/no_permiso.html")

    if request.method == "POST":
        form = InfraccionForm(request.POST)
        if form.is_valid():
            acta = form.save(commit=False)
            acta.inspector = request.user
            acta.save()
            return redirect("infracciones:lista")
    else:
        form = InfraccionForm()

    return render(request, "infracciones/acta_form.html", {"form": form, "modo": "nueva"})


@login_required
def detalle_acta(request, acta_id):
    if not es_inspector(request.user):
        return render(request, "cuentas/no_permiso.html")

    acta = get_object_or_404(Infraccion, id=acta_id, inspector=request.user)
    return render(request, "infracciones/detalle_acta.html", {"acta": acta})


@login_required
def editar_acta(request, acta_id):
    if not es_inspector(request.user):
        return render(request, "cuentas/no_permiso.html")

    acta = get_object_or_404(Infraccion, id=acta_id, inspector=request.user)

    if request.method == "POST":
        form = InfraccionForm(request.POST, instance=acta)
        if form.is_valid():
            form.save()
            return redirect("infracciones:detalle", acta_id=acta.id)
    else:
        form = InfraccionForm(instance=acta)

    return render(request, "infracciones/acta_form.html", {"form": form, "modo": "editar", "acta": acta})
