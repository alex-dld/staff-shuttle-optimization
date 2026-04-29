import uuid
from django.db import models


class Workspace(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    employees = models.ManyToManyField(
        'employees.Employee',
        blank=True,
        related_name='workspaces',
    )

    def __str__(self):
        return self.name
