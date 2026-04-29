from rest_framework import serializers
from .models import Employee


class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ['id', 'personnel_code', 'address', 'api_address', 'lat', 'lng', 'geocode_status', 'created_at']
        read_only_fields = ['created_at']


class EmployeeCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ['id', 'personnel_code', 'address', 'api_address', 'lat', 'lng', 'geocode_status', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_personnel_code(self, value):
        if Employee.objects.filter(personnel_code=value).exists():
            raise serializers.ValidationError('Bu personel kodu zaten kayıtlı.')
        return value
