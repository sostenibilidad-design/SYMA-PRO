from decimal import Decimal

from django.db import migrations, models


def cargar_jornadas(apps, schema_editor):
    """Jornada inicial: 8,5 h de lunes a jueves y 8 h el viernes (42 h semanales)."""
    JornadaDia = apps.get_model('registro_asistencia', 'JornadaDia')
    for dia, horas in ((0, '8.50'), (1, '8.50'), (2, '8.50'), (3, '8.50'), (4, '8.00')):
        JornadaDia.objects.get_or_create(dia_semana=dia, defaults={'horas': Decimal(horas)})


class Migration(migrations.Migration):

    dependencies = [
        ('registro_asistencia', '0004_horahistorica_accion'),
    ]

    operations = [
        migrations.CreateModel(
            name='JornadaDia',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dia_semana', models.PositiveSmallIntegerField(choices=[(0, 'Lunes'), (1, 'Martes'), (2, 'Miércoles'), (3, 'Jueves'), (4, 'Viernes')], unique=True)),
                ('horas', models.DecimalField(decimal_places=2, max_digits=4)),
            ],
            options={
                'verbose_name': 'Jornada del día',
                'verbose_name_plural': 'Jornadas por día de la semana',
                'db_table': 'asistencia_jornada_dia',
                'ordering': ['dia_semana'],
            },
        ),
        migrations.RunPython(cargar_jornadas, migrations.RunPython.noop),
    ]
