from django.shortcuts import render
from django.urls import resolve

class UsuarioConRolMiddleware:
    """
    Verifica que el usuario autenticado tenga al menos un grupo asignado.
    """

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
                if not request.user.groups.exists():
                    return render(request, "cuentas/sin_rol.html")

        return self.get_response(request)
