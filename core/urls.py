from django.contrib import admin
from django.urls import path, include

from workspaces.views import workspace_select
from routes.views import map_view
from employees.views import manage_view, sample_excel

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('routes.urls')),
    path('api/', include('workspaces.urls')),
    path('api/', include('employees.urls')),
    path('map/<uuid:workspace_id>/', map_view),
    path('employees/', manage_view),
    path('employees/sample-excel/', sample_excel),
    path('', workspace_select),
]
