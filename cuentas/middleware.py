from django.shortcuts import render
from django.urls import resolve

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
