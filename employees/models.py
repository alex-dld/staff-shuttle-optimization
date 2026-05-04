import uuid
from django.db import models
from .utils import address_match_score


class ImportJob(models.Model):
    STATUS_CHOICES = [('running', 'Running'), ('done', 'Done'), ('stopped', 'Stopped')]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='running')
    total = models.IntegerField(default=0)
    done = models.IntegerField(default=0)
    ok = models.IntegerField(default=0)
    failed = models.IntegerField(default=0)
    skipped = models.IntegerField(default=0)
    stop_requested = models.BooleanField(default=False)
    log = models.JSONField(default=list)
    errors = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'ImportJob {self.id} [{self.status}]'


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
    address_score = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.address_score = address_match_score(self.address, self.api_address)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.personnel_code
