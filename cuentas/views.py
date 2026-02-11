from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

# Vista para la página de inicio, que muestra diferentes opciones según el rol del usuario (inspector, encargado de playón, admin del sistema, juez).
@login_required
def home(request):
    grupos_usuario = set(request.user.groups.values_list("name", flat=True))

    context = {
        "es_admin_sistema": "ADMIN_SISTEMA" in grupos_usuario,
        "es_encargado_playon": "ENCARGADO_PLAYON" in grupos_usuario,
        "es_inspector": "INSPECTOR" in grupos_usuario,
        "es_juez": "JUEZ" in grupos_usuario,
    }

    return render(request, "cuentas/home.html", context)

# Vista para cerrar sesion, que simplemente llama al logout de django y redirige a la pagina de login.
def logout_view(request):
    logout(request)
    return redirect("login")
