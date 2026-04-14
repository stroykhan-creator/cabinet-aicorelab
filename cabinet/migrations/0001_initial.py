from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings

class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name='Company',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_active', models.BooleanField(default=True, verbose_name='Компания активна')),
                ('name', models.CharField(default='Новая компания', max_length=255, verbose_name='Название компании')),
                ('description', models.TextField(blank=True, null=True)),
                ('instance_type', models.CharField(choices=[('trial', 'Пробный'), ('pro', 'Профессиональный'), ('business', 'Бизнес')], default='trial', max_length=20)),
                ('system_prompt', models.TextField(blank=True, null=True)),
                ('openai_key', models.CharField(blank=True, max_length=255, null=True)),
                ('auto_reply_enabled', models.BooleanField(default=False, verbose_name='Автоответчик включен')),
                ('is_reanimator_enabled', models.BooleanField(default=False, verbose_name='Реаниматор включен')),
                ('is_wa_enabled', models.BooleanField(default=True, verbose_name='WhatsApp активен')),
                ('is_max_enabled', models.BooleanField(default=False, verbose_name='Макс активен')),
                ('green_api_id', models.CharField(blank=True, max_length=100, null=True)),
                ('green_api_token', models.CharField(blank=True, max_length=255, null=True)),
                ('max_api_id', models.CharField(blank=True, max_length=100, null=True)),
                ('max_api_token', models.CharField(blank=True, max_length=255, null=True)),
                ('green_api_receive_timeout', models.IntegerField(default=5)),
                ('green_api_send_timeout', models.IntegerField(default=10)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('owner', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='owned_companies', to=settings.AUTH_USER_MODEL)),
            ],            options={'verbose_name': 'Компания', 'verbose_name_plural': 'Компании'},
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(default='staff', max_length=10)),
                ('phone', models.CharField(blank=True, max_length=20, null=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Patient',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='Не указано', max_length=255)),
                ('phone', models.CharField(blank=True, max_length=20, null=True)),
                ('next_contact', models.DateField(blank=True, null=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('company', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='patients', to='cabinet.company')),
            ],
        ),
        migrations.CreateModel(
            name='Outreach',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(default='Не начат', max_length=20)),
                ('company', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='outreaches', to='cabinet.company')),
                ('patient', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='patient_outreaches', to='cabinet.patient')),
            ],
        ),
        migrations.CreateModel(
            name='MessageLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('chat_id', models.CharField(blank=True, max_length=100, null=True)),
                ('sender', models.CharField(default='system', max_length=50)),
                ('text', models.TextField(default='')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('company', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='logs', to='cabinet.company')),
            ],
        ),
        migrations.CreateModel(
            name='KnowledgeBase',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('topic', models.CharField(default='Общее', max_length=255)),
                ('information', models.TextField(blank=True, null=True)),
                ('company', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='knowledge_base', to='cabinet.company')),
            ],
        ),
    ]
