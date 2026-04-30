from django.contrib import admin
from django.urls import path, include

from workspaces.views import workspace_select
from routes.views import map_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('routes.urls')),
    path('api/', include('workspaces.urls')),
    path('api/', include('employees.urls')),
    path('map/<uuid:workspace_id>/', map_view),
    path('', workspace_select),
]
