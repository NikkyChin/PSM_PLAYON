from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from .models import Infraccion, AuditoriaInfraccion
from .forms import InfraccionForm
from .permissions import es_inspector, es_admin_sistema

# Auditoría de cambios: función para comparar un objeto original con los datos de un formulario, y generar un texto con los cambios realizados, 
# solo para los campos que cambiaron. Se usa para registrar auditorías de edición de actas de infracción.
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

# Lista de actas de infracción, con búsqueda por número de acta, DNI del infractor, dominio del vehículo o nombre del inspector.
@login_required
def lista_actas(request):
    if not es_inspector(request.user):
        return render(request, "cuentas/no_permisos.html")

    q = (request.GET.get("q") or "").strip()

    actas = Infraccion.objects.all()

    # si NO es admin, solo sus actas
    if not es_admin_sistema(request.user):
        actas = actas.filter(inspector=request.user)

    if q:
        actas = actas.filter(
            Q(nro_acta__icontains=q) |
            Q(dni_infractor__icontains=q) |
            Q(dominio__icontains=q)|
            Q(inspector__username__icontains=q)
        )

    actas = actas.order_by("-creada_en")

    return render(request, "infracciones/lista_actas.html", {"actas": actas, "q": q})

# Crear una nueva acta de infracción, con formulario para cargar datos del acta, y asignar automáticamente el inspector que la crea. 
# Solo pueden crear actas los usuarios con rol de inspector.
# Revisar si esto funciona bien, porque el form no tiene el campo inspector, y se asigna en la vista antes de guardar. Si el form no es válido, se pierde el inspector asignado.
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

# Detalle de un acta de infracción, con su auditoría de cambios. Solo pueden ver el detalle los inspectores que la crearon, o los admins del sistema.
@login_required
def detalle_acta(request, acta_id):
    if not es_inspector(request.user):
        return render(request, "cuentas/no_permiso.html")

    qs = Infraccion.objects.all()
    if not es_admin_sistema(request.user):
        qs = qs.filter(inspector=request.user)

    acta = get_object_or_404(qs, id=acta_id)
    auditorias = acta.auditorias.select_related("usuario").all()[:30]

    return render(request, "infracciones/detalle_acta.html", {"acta": acta, "auditorias": auditorias})

# Editar un acta de infracción, con formulario para modificar datos del acta, y generar auditoría de cambios. 
# Solo pueden editar los inspectores que la crearon, o los admins del sistema.
@login_required
def editar_acta(request, acta_id):
    if not es_inspector(request.user):
        return render(request, "cuentas/no_permiso.html")

    qs = Infraccion.objects.all()
    if not es_admin_sistema(request.user):
        qs = qs.filter(inspector=request.user)

    acta = get_object_or_404(qs, id=acta_id)

    acta_antes = Infraccion.objects.get(id=acta.id)

    if request.method == "POST":
        form = InfraccionForm(request.POST, instance=acta)
        if form.is_valid():
            cambios_txt = _diff_to_text(acta_antes, form)

            form.save()

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

    return render(request, "infracciones/acta_form.html", {"form": form, "modo": "editar", "acta": acta})
