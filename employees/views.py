from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from workspaces.models import Workspace
from .models import Employee
from .serializers import EmployeeSerializer, EmployeeCreateSerializer
from .utils import geocode_address


class EmployeeViewSet(viewsets.ModelViewSet):
    serializer_class = EmployeeSerializer
    http_method_names = ['get', 'post', 'head', 'options']

    def get_queryset(self):
        qs = Employee.objects.filter(geocode_status='ok')
        workspace_id = self.request.query_params.get('workspace')
        if workspace_id:
            qs = qs.filter(workspaces__id=workspace_id)
        return qs

    def create(self, request, *args, **kwargs):
        serializer = EmployeeCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='geocode')
    def geocode(self, request):
        address = request.data.get('address', '').strip()
        if not address:
            return Response({'error': 'Adres alanı boş olamaz.'}, status=400)
        result = geocode_address(address)
        if not result['ok']:
            if result['reason'] == 'no_result':
                return Response(
                    {'error': 'Adres bulunamadı. Daha ayrıntılı bir adres deneyin.'},
                    status=422,
                )
            return Response(
                {'error': 'Yandex API hatası: ' + result.get('detail', '')},
                status=502,
            )
        return Response({'lat': result['lat'], 'lng': result['lng'], 'api_address': result['api_address']})

    @action(detail=False, methods=['post'], url_path='assign')
    def assign(self, request):
        workspace_id = request.data.get('workspace')
        employee_ids = request.data.get('employee_ids', [])
        try:
            workspace = Workspace.objects.get(id=workspace_id)
        except Workspace.DoesNotExist:
            return Response({'error': 'Workspace not found'}, status=404)
        workspace.employees.set(Employee.objects.filter(id__in=employee_ids))
        return Response({'assigned': len(employee_ids)})
