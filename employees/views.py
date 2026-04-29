from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from workspaces.models import Workspace
from .models import Employee
from .serializers import EmployeeSerializer


class EmployeeViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = EmployeeSerializer

    def get_queryset(self):
        qs = Employee.objects.filter(geocode_status='ok')
        workspace_id = self.request.query_params.get('workspace')
        if workspace_id:
            qs = qs.filter(workspaces__id=workspace_id)
        return qs

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
