import string
from django.core.management.base import BaseCommand
from django.db import transaction
from playon.models import LugarPlayon
from ingresos.models import IngresoPlayon


class Command(BaseCommand):
    help = "Crea los lugares del playón A-Z y 1-15 si faltan y recalcula estados OCUPADO/LIBRE según ingresos activos."

    def add_arguments(self, parser):
        parser.add_argument(
            "--filas",
            default="A-Z",
            help="Rango de filas. Ej: A-Z (default) o A-N",
        )
        parser.add_argument(
            "--columnas",
            type=int,
            default=15,
            help="Cantidad de columnas (default 15)",
        )

    def _parse_filas(self, spec: str):
        spec = (spec or "").strip().upper()
        if spec == "A-Z":
            return list(string.ascii_uppercase)

        # Permite "A-N"
        if len(spec) == 3 and spec[1] == "-" and spec[0].isalpha() and spec[2].isalpha():
            start = spec[0]
            end = spec[2]
            a = ord(start)
            b = ord(end)
            if a > b:
                a, b = b, a
            return [chr(x) for x in range(a, b + 1)]

        raise ValueError("Formato de --filas inválido. Usá A-Z o A-N.")

    @transaction.atomic
    def handle(self, *args, **options):
        filas = self._parse_filas(options["filas"])
        columnas = range(1, options["columnas"] + 1)

        # 1) Crear los que falten
        creados = 0
        for fila in filas:
            for col in columnas:
                _, was_created = LugarPlayon.objects.get_or_create(
                    fila=fila,
                    columna=col,
                    defaults={"estado": "LIBRE", "tipo": "GENERAL"},
                )
                if was_created:
                    creados += 1

        # 2) Recalcular estados: mantener FUERA, resetear resto a LIBRE
        LugarPlayon.objects.exclude(estado="FUERA").update(estado="LIBRE")

        # 3) Marcar OCUPADO según ingresos activos con lugar asignado
        lugares_ocupados_ids = (
            IngresoPlayon.objects.filter(retirado=False, lugar__isnull=False)
            .values_list("lugar_id", flat=True)
            .distinct()
        )
        LugarPlayon.objects.filter(id__in=lugares_ocupados_ids).update(estado="OCUPADO")

        self.stdout.write(self.style.SUCCESS("Seed del playón OK"))
        self.stdout.write(f"- Lugares creados nuevos: {creados}")
        self.stdout.write(f"- Lugares ocupados recalculados: {len(set(lugares_ocupados_ids))}")
        self.stdout.write("- Nota: lugares en estado 'FUERA' se respetaron.")
