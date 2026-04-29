from django.contrib import admin
from .models import Employee


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('personnel_code', 'address', 'geocode_status', 'lat', 'lng')
    list_filter = ('geocode_status',)
    search_fields = ('personnel_code', 'address')
    readonly_fields = ('created_at',)
