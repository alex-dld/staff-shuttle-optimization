from django.shortcuts import render, redirect
from rest_framework import viewsets

from .models import Workspace
from .serializers import WorkspaceSerializer


def workspace_select(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            name = request.POST.get('name', '').strip()
            description = request.POST.get('description', '').strip()
            if name:
                ws = Workspace.objects.create(name=name, description=description)
                return redirect(f'/map/{ws.id}/')
        elif action == 'select':
            workspace_id = request.POST.get('workspace_id')
            if workspace_id:
                return redirect(f'/map/{workspace_id}/')

    workspaces = Workspace.objects.filter(is_active=True).order_by('-created_at')
    return render(request, 'workspaces/select.html', {'workspaces': workspaces})


class WorkspaceViewSet(viewsets.ModelViewSet):
    queryset = Workspace.objects.all()
    serializer_class = WorkspaceSerializer
