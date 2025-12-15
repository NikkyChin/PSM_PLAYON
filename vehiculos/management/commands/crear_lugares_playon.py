from django.core.management.base import BaseCommand
from vehiculos.models import LugarPlayon
import string


class Command(BaseCommand):
    help = "Crea los lugares del playón (A-Z / 1-15)"

    def handle(self, *args, **options):
        filas = list(string.ascii_uppercase)  # A-Z
        columnas = range(1, 16)  # 1 a 15

        creados = 0
        existentes = 0

        for fila in filas:
            for columna in columnas:
                lugar, created = LugarPlayon.objects.get_or_create(
                    fila=fila,
                    columna=columna,
                    defaults={
                        "estado": "LIBRE",
                        "tipo": "GENERAL",
                    },
                )

                if created:
                    creados += 1
                else:
                    existentes += 1

        self.stdout.write(self.style.SUCCESS(
            f"✔ Lugares creados: {creados}"
        ))
        self.stdout.write(self.style.WARNING(
            f"• Lugares ya existentes: {existentes}"
        ))
