from django.shortcuts import render, redirect
from django.contrib import auth
from django.urls import resolve, reverse
from django.conf import settings
import time


# Meddleware que verifica que el usuario autenticado tenga al menos un rol (grupo) asignado.
class UsuarioConRolMiddleware:
    # Se pueden configurar rutas excluidas, como las de login/logout, para que no se aplique esta verificación en esas rutas.
    EXCLUIDAS = [
        "login",
        "logout",
        "admin",
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            ruta = resolve(request.path_info).url_name or ""

            # excluir rutas permitidas
            if not any(ruta.startswith(x) for x in self.EXCLUIDAS):
                if not request.user.groups.exists() and not request.user.is_superuser:
                    return render(request, "cuentas/sin_rol.html")

        return self.get_response(request)

# Middleware que verifica que el usuario autenticado no este inactivo por mas de X segundos. y si es asi, lo desloguea y lo redirige al login.
class IdleTimeoutMiddleware:
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.timeout = getattr(settings, "SESSION_IDLE_TIMEOUT_SECONDS", 20 * 60)

    def __call__(self, request):
        # Dejá pasar recursos estáticos/media sin tocar sesión
        path = request.path or ""
        if path.startswith("/static/") or path.startswith("/media/"):
            return self.get_response(request)

        user = getattr(request, "user", None)
        if user and user.is_authenticated:
            now = int(time.time())
            last_activity = request.session.get("last_activity")

            # Si existe last_activity y superó el timeout → logout
            if last_activity and (now - int(last_activity) > self.timeout):
                auth.logout(request)
                request.session.flush()

                login_url = reverse("login") if "login" else "/login/"
                # next para volver adonde estaba
                return redirect(f"{login_url}?next={request.path}")

            # Actualizar actividad
            request.session["last_activity"] = now

        return self.get_response(request)
