# Generated migration for RouteHistory model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('safety', '0003_emergencycontact_sosalert_sosdeliverylog'),
    ]

    operations = [
        migrations.CreateModel(
            name='RouteHistory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source_name', models.CharField(max_length=255)),
                ('source_latitude', models.FloatField()),
                ('source_longitude', models.FloatField()),
                ('destination_name', models.CharField(max_length=255)),
                ('destination_latitude', models.FloatField()),
                ('destination_longitude', models.FloatField()),
                ('distance_km', models.FloatField()),
                ('estimated_time_minutes', models.IntegerField()),
                ('safety_score', models.IntegerField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='route_history', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
