from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('registro_asistencia', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='maestroasistencia',
            name='creado_en',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
