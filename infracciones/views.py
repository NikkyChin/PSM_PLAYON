from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from .models import Infraccion, AuditoriaInfraccion
from .forms import InfraccionForm
from .permissions import es_inspector


def _diff_to_text(original_obj, form):
    """
    Devuelve un string con cambios tipo:
    - campo: 'antes' -> 'después'
    Solo para campos que cambiaron.
    """
    lineas = []
    for field in form.changed_data:
        antes = getattr(original_obj, field, "")
        despues = form.cleaned_data.get(field, "")

        # Normalizar None y strings
        if antes is None:
            antes = ""
        if despues is None:
            despues = ""

        lineas.append(f"- {field}: '{antes}' -> '{despues}'")

    return "\n".join(lineas)


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
    auditorias = acta.auditorias.select_related("usuario").all()[:30]
    return render(request, "infracciones/detalle_acta.html", {"acta": acta, "auditorias": auditorias})



@login_required
def editar_acta(request, acta_id):
    if not es_inspector(request.user):
        return render(request, "cuentas/no_permiso.html")

    acta = get_object_or_404(Infraccion, id=acta_id, inspector=request.user)

    # snapshot antes
    acta_antes = Infraccion.objects.get(id=acta.id)

    if request.method == "POST":
        form = InfraccionForm(request.POST, instance=acta)
        if form.is_valid():
            cambios_txt = _diff_to_text(acta_antes, form)

            form.save()

            # guardar auditoría solo si hubo cambios reales
            if cambios_txt.strip():
                AuditoriaInfraccion.objects.create(
                    infraccion=acta,
                    usuario=request.user,
                    accion="EDICION",
                    cambios_txt=cambios_txt,
                )

            return redirect("infracciones:detalle", acta_id=acta.id)
    else:
        form = InfraccionForm(instance=acta)

    return render(request, "infracciones/acta_form.html", {
        "form": form,
        "modo": "editar",
        "acta": acta
    })
