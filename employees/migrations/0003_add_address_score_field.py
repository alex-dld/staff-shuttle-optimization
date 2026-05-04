from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('employees', '0002_importjob'),
    ]

    operations = [
        migrations.AddField(
            model_name='employee',
            name='address_score',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
