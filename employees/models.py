from django.db import models


class Employee(models.Model):
    GEOCODE_STATUS = [
        ('pending', 'Pending'),
        ('ok', 'OK'),
        ('failed', 'Failed'),
    ]

    personnel_code = models.CharField(max_length=20, unique=True)
    address = models.TextField()
    api_address = models.TextField(blank=True, default='')
    lat = models.FloatField(null=True, blank=True)
    lng = models.FloatField(null=True, blank=True)
    geocode_status = models.CharField(max_length=10, choices=GEOCODE_STATUS, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.personnel_code
