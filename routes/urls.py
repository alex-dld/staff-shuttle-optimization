from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import RouteGroupViewSet, RouteViewSet, StopViewSet

router = DefaultRouter()
router.register('route-groups', RouteGroupViewSet, basename='route-group')
router.register('routes', RouteViewSet)
router.register('stops', StopViewSet, basename='stop')

urlpatterns = [
    path('', include(router.urls)),
]
