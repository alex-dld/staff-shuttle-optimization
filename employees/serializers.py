from rest_framework import serializers
from .models import Employee


class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ['id', 'personnel_code', 'address', 'api_address', 'lat', 'lng', 'geocode_status', 'created_at']
        read_only_fields = ['created_at']
