def es_admin_sistema(user) -> bool:
    return (
        user.is_authenticated
        and (user.is_superuser or user.groups.filter(name="ADMIN_SISTEMA").exists())
    )

def es_inspector(user) -> bool:
    return (
        user.is_authenticated
        and (user.is_superuser or user.groups.filter(name="INSPECTOR").exists())
    )
