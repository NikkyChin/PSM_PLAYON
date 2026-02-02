def es_inspector(user) -> bool:
    if not user.is_authenticated:
        return False
    grupos = set(user.groups.values_list("name", flat=True))
    return ("INSPECTOR" in grupos) or user.is_superuser
