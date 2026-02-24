from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("login/", auth_views.LoginView.as_view(template_name="cuentas/login.html"), name="login"),
    path("salir/",views.logout_view,name="logout"),
    path("cambiar-password/",auth_views.PasswordChangeView.as_view(template_name="cuentas/cambiar_password.html", success_url=reverse_lazy("cambiar_password_exito")), name="cambiar_password",),
    path("cambiar-password/exito/",auth_views.PasswordChangeDoneView.as_view(template_name="cuentas/cambiar_password_exito.html"),name="cambiar_password_exito",),
    path("no-permiso/", views.no_permisos, name="no_permisos"),
]
