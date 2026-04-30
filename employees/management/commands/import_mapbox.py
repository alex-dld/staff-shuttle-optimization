import openpyxl
from django.core.management.base import BaseCommand
from django.conf import settings
from employees.models import Employee
from workspaces.models import Workspace

FILE = settings.BASE_DIR / 'Docs' / 'geocode_comparison.xlsx'


class Command(BaseCommand):
    help = 'geocode_comparison.xlsx Mapbox sonuçlarını DB ye yükler, workspace e bağlar'

    def add_arguments(self, parser):
        parser.add_argument('--workspace', default='Birey Listesi (Mapbox)')

    def handle(self, *args, **options):
        ws_name = options['workspace']

        wb = openpyxl.load_workbook(FILE)
        rows = list(wb.active.iter_rows(min_row=2, values_only=True))
        total = len(rows)
        self.stdout.write(f'{total} çalışan yüklenecek...')

        ok = fail = 0
        employees = []

        for row in rows:
            # P, ADRES, Y_LAT, Y_LNG, Y_API, M_LAT, M_LNG, M_API, FARK_M, STATUS, FARKLI
            p_code = row[0]
            address = row[1]
            m_lat, m_lng, m_api = row[5], row[6], row[7]
            status = row[9]

            if not p_code:
                continue

            if status == 'ok' and m_lat and m_lng:
                emp, _ = Employee.objects.update_or_create(
                    personnel_code=p_code,
                    defaults={
                        'address': address or '',
                        'api_address': m_api or '',
                        'lat': m_lat,
                        'lng': m_lng,
                        'geocode_status': 'ok',
                    },
                )
                employees.append(emp)
                ok += 1
            else:
                emp, _ = Employee.objects.update_or_create(
                    personnel_code=p_code,
                    defaults={
                        'address': address or '',
                        'geocode_status': 'failed',
                    },
                )
                fail += 1

        workspace, created = Workspace.objects.get_or_create(
            name=ws_name,
            defaults={'description': 'Mapbox geocoding ile oluşturuldu'},
        )
        workspace.employees.set(employees)

        action = 'oluşturuldu' if created else 'güncellendi'
        self.stdout.write(self.style.SUCCESS(
            f'\nTamamlandı — Workspace "{ws_name}" {action}\n'
            f'  Yüklenen: {ok}  |  Başarısız: {fail}'
        ))
