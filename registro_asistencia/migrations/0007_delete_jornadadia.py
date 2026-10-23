from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('registro_asistencia', '0006_aniofestivos_festivo'),
    ]

    operations = [
        migrations.DeleteModel(
            name='JornadaDia',
        ),
    ]
