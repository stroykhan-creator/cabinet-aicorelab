# /tmp/create_test_outreach.py

COMPANY_ID = 6  # ID компании для теста

from cabinet.models import Company, Patient, Outreach
from django.db import transaction

try:
    with transaction.atomic(): # Транзакция для безопасного создания
        c = Company.objects.get(id=COMPANY_ID)
        p = Patient.objects.filter(company_id=c.id, name='Тестовый Клиент').order_by('-id').first()

        if p:
            # Проверяем, есть ли уже outreach для этого пациента, чтобы не плодить
            # Важно: проверим также и на "Завершен" (Completed) или "Не удалось" (Failed), чтобы не создавать повторно
            existing_outreach = Outreach.objects.filter(
                company=c,
                patient=p,
                status__in=['Не начат', 'Отправлено', 'Обработка', 'Завершен', 'Не удалось']
            ).exists()

            if not existing_outreach:
                o = Outreach.objects.create(company=c, patient=p, status='Не начат')
                print(f"--- Created Outreach: ID={o.id} for Patient ID={p.id} ---")
            else:
                print(f"--- Outreach already exists for Patient ID={p.id} with relevant status. Skipping creation. ---")
        else:
            print(f"--- Test patient 'Тестовый Клиент' not found for Company ID={COMPANY_ID}. Cannot create Outreach. ---")

except Company.DoesNotExist:
    print(f"--- Company with ID={COMPANY_ID} not found. Cannot create Outreach. ---")
except Exception as e:
    print(f"--- Error creating test Outreach: {repr(e)} ---")

