from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('personal', '0015_empleado_ubicacion'),
    ]

    operations = [
        migrations.AddField(
            model_name='empleado',
            name='cuadrilla',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
