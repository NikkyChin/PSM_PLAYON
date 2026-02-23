
# Permisos personalizados para el módulo de juzgado de faltas. Funciones para verificar si un usuario es juez o admin del sistema, 
# y se pueden usar en las vistas para controlar el acceso a ciertas funcionalidades.
def es_admin_sistema(user) -> bool:
    if not user.is_authenticated:
        return False
    grupos = set(user.groups.values_list("name", flat=True))
    return ("ADMIN_SISTEMA" in grupos) or user.is_superuser
def es_juez(user) -> bool:
    if not user.is_authenticated:
        return False
    grupos = set(user.groups.values_list("name", flat=True))
    return ("JUEZ" in grupos) or ("ADMIN_SISTEMA" in grupos) or user.is_superuser
