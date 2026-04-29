from rest_framework import serializers
from .models import RouteGroup, Route, Stop


class StopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stop
        fields = ['id', 'route', 'name', 'latitude', 'longitude', 'sort_order']
        read_only_fields = ['sort_order']


class RouteSerializer(serializers.ModelSerializer):
    route_group = serializers.PrimaryKeyRelatedField(read_only=True)
    route_group_id = serializers.PrimaryKeyRelatedField(
        source='route_group',
        queryset=RouteGroup.objects.all(),
        write_only=True,
        required=False,
    )
    stops = StopSerializer(many=True, read_only=True)

    class Meta:
        model = Route
        fields = [
            'id', 'route_group', 'route_group_id', 'name', 'color', 'direction',
            'waypoints', 'geojson', 'distance_km', 'duration_min', 'stops', 'created_at',
        ]
        read_only_fields = ['created_at']


class RouteGroupSerializer(serializers.ModelSerializer):
    routes = RouteSerializer(many=True, read_only=True)

    class Meta:
        model = RouteGroup
        fields = ['id', 'workspace', 'name', 'routes', 'created_at']
        read_only_fields = ['created_at']
