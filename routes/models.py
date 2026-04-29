import uuid
from django.db import models
from workspaces.models import Workspace


class RouteGroup(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='route_groups')
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Route(models.Model):
    DIRECTION_CHOICES = [
        ('inbound', 'İş Yerine Geliş'),
        ('outbound', 'İş Yerinden Çıkış'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    route_group = models.ForeignKey(RouteGroup, on_delete=models.CASCADE, related_name='routes')
    name = models.CharField(max_length=255)
    color = models.CharField(max_length=7, default='#3498DB')
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES)
    waypoints = models.JSONField(default=list)
    geojson = models.JSONField(null=True, blank=True)
    distance_km = models.FloatField(null=True, blank=True)
    duration_min = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.route_group.name} — {self.get_direction_display()}"


class Stop(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='stops')
    name = models.CharField(max_length=255)
    latitude = models.FloatField()
    longitude = models.FloatField()
    radius = models.IntegerField(default=1000)
    isochrone = models.JSONField(null=True, blank=True)
    sort_order = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sort_order']

    def __str__(self):
        return f"{self.route} - {self.name}"
