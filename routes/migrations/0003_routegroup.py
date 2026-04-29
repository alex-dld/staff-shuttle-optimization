import uuid
import django.db.models.deletion
from django.db import migrations, models


def create_groups_from_routes(apps, schema_editor):
    Route = apps.get_model('routes', 'Route')
    RouteGroup = apps.get_model('routes', 'RouteGroup')
    for route in Route.objects.select_related('workspace').all():
        group = RouteGroup.objects.create(
            workspace=route.workspace,
            name=route.name,
        )
        route.route_group = group
        route.direction = 'outbound'
        route.save(update_fields=['route_group', 'direction'])


def reverse_groups(apps, schema_editor):
    RouteGroup = apps.get_model('routes', 'RouteGroup')
    Route = apps.get_model('routes', 'Route')
    for route in Route.objects.select_related('route_group').all():
        route.workspace = route.route_group.workspace
        route.save(update_fields=['workspace'])
    RouteGroup.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('routes', '0002_route_distance_km_route_duration_min_route_geojson'),
        ('workspaces', '0001_initial'),
    ]

    operations = [
        # 1. Create RouteGroup table
        migrations.CreateModel(
            name='RouteGroup',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('workspace', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='route_groups',
                    to='workspaces.workspace',
                )),
            ],
        ),
        # 2. Add nullable route_group FK to Route
        migrations.AddField(
            model_name='route',
            name='route_group',
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='routes',
                to='routes.routegroup',
            ),
        ),
        # 3. Populate route_group for every existing Route
        migrations.RunPython(create_groups_from_routes, reverse_code=reverse_groups),
        # 4. Make route_group non-nullable
        migrations.AlterField(
            model_name='route',
            name='route_group',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='routes',
                to='routes.routegroup',
            ),
        ),
        # 5. Drop workspace FK from Route
        migrations.RemoveField(
            model_name='route',
            name='workspace',
        ),
    ]
