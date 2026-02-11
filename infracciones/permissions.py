
# Permisos para la app de infracciones. Funciones para verificar si un usuario es inspector o admin del sistema, 
# y se pueden usar en las vistas para controlar el acceso a ciertas funcionalidades.
def es_admin_sistema(user) -> bool:
    if not user.is_authenticated:
        return False
    grupos = set(user.groups.values_list("name", flat=True))
    return ("ADMIN_SISTEMA" in grupos) or user.is_superuser

def es_inspector(user) -> bool:
    if not user.is_authenticated:
        return False
    grupos = set(user.groups.values_list("name", flat=True))
    # inspector o admin
    return ("INSPECTOR" in grupos) or ("ADMIN_SISTEMA" in grupos) or user.is_superuser
