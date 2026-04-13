
import time
import requests
from openai import OpenAI
from django.core.management.base import BaseCommand
from datetime import datetime, timedelta
from cabinet.models import Company, Patient, Outreach, MessageLog, KnowledgeBase

class Command(BaseCommand):
    help = 'Запуск SaaS ИИ-агента (WhatsApp + МАКС)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("--- Мотор Запущен (WA + MAX) ---"))
        while True:
            active_companies = Company.objects.filter(is_active=True)
            for company in active_companies:
                # 1. Рассылка (Outreach)
                self.run_initial_outreach(company)
                
                # 2. Планировщик
                self.check_scheduler(company)

                # 3. Проверка WhatsApp (если включен)
                if company.is_wa_enabled and company.green_api_id:
                    self.process_incoming(company, company.green_api_id, company.green_api_token, "WA")

                # 4. Проверка МАКС (если включен)
                if company.is_max_enabled and company.max_api_id:
                    self.process_incoming(company, company.max_api_id, company.max_api_token, "MAX")

            time.sleep(5)

    def get_client(self, company):
        return OpenAI(api_key=company.openai_key, base_url="https://api.proxyapi.ru/openai/v1")

    def analyze_sentiment(self, company, text):
        client = self.get_client(company)
        try:
            res = client.chat.completions.create(
                model="-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Классифицируй ответ. Только ОДНО слово: 'ОТКАЗ', 'ИНТЕРЕС', 'ЗАПИСЬ', 'ДИАЛОГ'."},
                    {"role": "user", "content": text}
                ],
                temperature=0
            )
            return res.choices[0].message.content.strip().upper()
        except:
            return "ДИАЛОГ"

    def extract_date(self, company, text):
        client = self.get_client(company)
        today = datetime.now().strftime("%Y-%m-%d")
        try:
            res = client.chat.completions.create(
                model="-3.5-turbo",
                messages=[
                    {"role": "system", "content": f"Сегодня {today}. Выведи дату YYYY-MM-DD или NONE."},
                    {"role": "user", "content": text}
                ],
                temperature=0
            )
            date_str = res.choices[0].message.content.strip()
            return datetime.strptime(date_str, '%Y-%m-%d').date() if "NONE" not in date_str else None
        except:
            return None

    def process_incoming(self, company, instance_id, token, channel_label):
        url = f"https://api.green-api.com/waInstance{instance_id}/receiveNotification/{token}"
        del_url = f"https://api.green-api.com/waInstance{instance_id}/deleteNotification/{token}/"
        try:
            resp = requests.get(url, timeout=company.green_api_receive_timeout)
            if resp.status_code == 200 and resp.json():
                data = resp.json()
                receipt_id = data.get('receiptId')
                body = data.get('body')

                if body and body.get('typeWebhook') == 'incomingMessageReceived':
                    chat_id = body.get('senderData', {}).get('chatId')
                    text = body.get('messageData', {}).get('textMessageData', {}).get('textMessage') or \
                           body.get('messageData', {}).get('extendedTextMessageData', {}).get('textMessage')

                    if chat_id and text:
                        phone_raw = chat_id.split('@')[0]
                        # Поиск пациента по номеру (из очищенного chatId)
                        target_client = Patient.objects.filter(company=company, phone__contains=phone_raw).first()

                        if target_client:
                            MessageLog.objects.create(company=company, patient=target_client, chat_id=chat_id, sender="Клиент", text=text)
                            
                            sentiment = self.analyze_sentiment(company, text)
                            outreach = Outreach.objects.filter(company=company, patient=target_client).first()

                            if sentiment == "ОТКАЗ":
                                if outreach: outreach.status = 'ОТКАЗ'; outreach.save()
                                self.send_wa(company, instance_id, token, chat_id, "Хорошо, больше не беспокоим.", channel_label, target_client)
                            else:
                                if outreach:
                                    if sentiment == "ЗАПИСЬ": outreach.status = 'Записан'
                                    elif sentiment == "ИНТЕРЕС": outreach.status = 'ИНТЕРЕС'
                                    else: outreach.status = 'Диалог'
                                    outreach.save()

                                new_date = self.extract_date(company, text)
                                if new_date:
                                    target_client.next_contact = new_date
                                    target_client.save()

                                reply = self.generate_ai_reply(company, chat_id, text)
                                self.send_wa(company, instance_id, token, chat_id, reply, channel_label, target_client)

                if receipt_id:
                    requests.delete(del_url + str(receipt_id), timeout=company.green_api_send_timeout)
        except Exception as e:
            self.stdout.write(f"Ошибка получения ({channel_label}): {e}")

    def generate_ai_reply(self, company, chat_id, user_text, task="dialog"):
        client = self.get_client(company)
        kb = KnowledgeBase.objects.filter(company=company)
        knowledge = "\nБАЗА ЗНАНИЙ:\n" + "\n".join([f"{k.topic}: {k.information}" for k in kb])
        
        # Берем последние 10 сообщений именно по этому chatId для контекста
        logs = MessageLog.objects.filter(company=company, chat_id=chat_id).order_by('-created_at')[:10]
        history = [{"role": ("assistant" if "ИИ" in l.sender else "user"), "content": l.text} for l in reversed(logs)]

        instruction = (company.system_prompt or "") + "\n" + knowledge
        messages = [{"role": "system", "content": instruction}] + history + [{"role": "user", "content": user_text}]
        
        try:
            res = client.chat.completions.create(model="-3.5-turbo", messages=messages, temperature=0.7)
            return res.choices[0].message.content
        except:
            return "Минутку, уточняю информацию..."

    def send_wa(self, company, instance_id, token, chat_id, text, label, patient=None):
        if not chat_id.endswith('@c.us'): chat_id = f"{chat_id}@c.us"
        url = f"https://api.green-api.com/waInstance{instance_id}/sendMessage/{token}"
        try:
            requests.post(url, json={"chatId": chat_id, "message": text}, timeout=company.green_api_send_timeout)
            MessageLog.objects.create(
                company=company, 
                patient=patient, 
                chat_id=chat_id, 
                sender=f"ИИ Администратор ({label})", 
                text=text
            )
            return True
        except:
            return False

    def run_initial_outreach(self, company):
        # Выбираем, через какой канал слать (WA в приоритете, если включен)
        if company.is_wa_enabled and company.green_api_id:
            inst, tok, lbl = company.green_api_id, company.green_api_token, "WA"
        elif company.is_max_enabled and company.max_api_id:
            inst, tok, lbl = company.max_api_id, company.max_api_token, "MAX"
        else: return

        items = Outreach.objects.filter(company=company, status='Не начат')[:3]
        for i in items:
            reply = self.generate_ai_reply(company, i.patient.phone, f"Поприветствуй клиента {i.patient.name}", task="initial")
            if self.send_wa(company, inst, tok, i.patient.phone, reply, lbl, i.patient):
                i.status = 'Отправлено'
                i.save()

    def check_scheduler(self, company):
        if company.is_wa_enabled and company.green_api_id:
            inst, tok, lbl = company.green_api_id, company.green_api_token, "WA"
        elif company.is_max_enabled and company.max_api_id:
            inst, tok, lbl = company.max_api_id, company.max_api_token, "MAX"
        else: return

        today = datetime.now().date()
        due = Patient.objects.filter(company=company, next_contact=today)
        for p in due:
            reply = self.generate_ai_reply(company, p.phone, "Напомни о нас", task="reanimation")
            if self.send_wa(company, inst, tok, p.phone, reply, lbl, p):
                p.next_contact = today + timedelta(days=365)
                p.save()
