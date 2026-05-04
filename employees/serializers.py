from rest_framework import serializers
from .models import Employee
from .utils import address_match_score


class EmployeeSerializer(serializers.ModelSerializer):
    workspace_names = serializers.SerializerMethodField()

    def get_workspace_names(self, obj):
        return [w.name for w in obj.workspaces.all()]

    class Meta:
        model = Employee
        fields = ['id', 'personnel_code', 'address', 'api_address', 'lat', 'lng', 'geocode_status', 'created_at', 'workspace_names', 'address_score']
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
