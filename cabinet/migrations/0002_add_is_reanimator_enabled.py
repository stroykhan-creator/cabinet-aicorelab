from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('cabinet', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='company',
            name='is_reanimator_enabled',
            field=models.BooleanField(default=False, verbose_name='Реаниматор включен'),
        ),
    ]
