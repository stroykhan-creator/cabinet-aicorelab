
import time
import requests
from openai import OpenAI
from django.core.management.base import BaseCommand
from datetime import datetime, timedelta
from cabinet.models import Company, Patient, Outreach, MessageLog, KnowledgeBase

class Command(BaseCommand):
    help = 'Запуск SaaS ИИ-агента с поддержкой автоответчика'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("--- Мотор Запущен ---"))
        while True:
            active_companies = Company.objects.filter(is_active=True, is_reanimator_enabled=True)
            
            for company in active_companies:
                # Добавлено логирование начала обработки компании
                self.stdout.write(self.style.NOTICE(f"--- Processing company: {company.id} {company.name} ---"))
                self.run_initial_outreach(company)
                self.check_scheduler(company)
                self.process_incoming(company)
                self.stdout.write(self.style.NOTICE(f"--- Finished processing company: {company.id} ---"))
            time.sleep(5)

    def get_client(self, company):
        # Удаляем base_url, чтобы использовать официальный API OpenAI по умолчанию
        # или явно указываем: base_url="https://api.openai.com/v1"
        return OpenAI(api_key=company.openai_key)
        # ИЛИ так:
        # return OpenAI(api_key=company.openai_key, base_url="https://api.openai.com/v1")
    
    def analyze_sentiment(self, company, text):
        client = self.get_client(company)
        try:
            res = client.chat.completions.create(
                model="gpt-3.5-turbo", # ИСПРАВЛЕНО имя модели
                messages=[
                    {"role": "system", "content": "Классифицируй ответ. Только ОДНО слово: 'ОТКАЗ', 'ИНТЕРЕС', 'ЗАПИСЬ', 'ДИАЛОГ'."},
                    {"role": "user", "content": text}
                ],
                temperature=0
            )
            return res.choices[0].message.content.strip().upper()
        except Exception as e: # ДОБАВЛЕНО ЛОГИРОВАНИЕ
            self.stdout.write(self.style.ERROR(f"--- analyze_sentiment: Error calling OpenAI for company {company.id}: {repr(e)} ---"))
            return "ДИАЛОГ" # Возвращаем заглушку, чтобы не прерывать процесс

    def extract_date(self, company, text):
        client = self.get_client(company)
        today = datetime.now().strftime("%Y-%m-%d")
        try:
            res = client.chat.completions.create(
                model="gpt-3.5-turbo", # ИСПРАВЛЕНО имя модели
                messages=[
                    {"role": "system", "content": f"Сегодня {today}. Выведи дату в формате YYYY-MM-DD или слово NONE."},
                    {"role": "user", "content": text}
                ],
                temperature=0
            )
            date_str = res.choices[0].message.content.strip()
            if "NONE" in date_str.upper():
                return None
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except Exception as e: # ДОБАВЛЕНО ЛОГИРОВАНИЕ
            self.stdout.write(self.style.ERROR(f"--- extract_date: Error calling OpenAI for company {company.id}: {repr(e)} ---"))
            return None

    def process_incoming(self, company):
        url = f"https://api.green-api.com/waInstance{company.green_api_id}/receiveNotification/{company.green_api_token}"
        del_url = f"https://api.green-api.com/waInstance{company.green_api_id}/deleteNotification/{company.green_api_token}/"
        
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
                        target_client = Patient.objects.filter(company=company, phone=phone_raw).first()

                        if target_client:
                            MessageLog.objects.create(company=company, chat_id=chat_id, sender="Клиент", text=text)
                            
                            sentiment = self.analyze_sentiment(company, text)
                            outreach = Outreach.objects.filter(company=company, patient=target_client).first()

                            if sentiment == "ОТКАЗ":
                                if outreach:
                                    outreach.status = 'ОТКАЗ'
                                    outreach.save()
                                self.send_wa(company, chat_id, "Хорошо, больше не беспокоим.")
                            else:
                                if outreach:
                                    status_map = {"ЗАПИСЬ": "Записан", "ИНТЕРЕС": "ИНТЕРЕС"}
                                    outreach.status = status_map.get(sentiment, "Диалог")
                                    outreach.save()

                                new_date = self.extract_date(company, text)
                                if new_date:
                                    target_client.next_contact = new_date
                                    target_client.save()

                                if company.auto_reply_enabled:
                                    reply = self.generate_ai_reply(company, chat_id, text)
                                    if reply: # Проверяем, что ИИ дал ответ
                                        self.send_wa(company, chat_id, reply)
                                    else:
                                        self.stdout.write(self.style.WARNING(f"--- process_incoming: No AI reply generated for incoming message from {chat_id}. ---"))
                                else:
                                    MessageLog.objects.create(company=company, chat_id=chat_id, sender="system", text="Автоответ отключен в настройках компании.")

                if receipt_id:
                    requests.delete(f"{del_url}{receipt_id}", timeout=company.green_api_send_timeout)
        except Exception as e: # ДОБАВЛЕНО ЛОГИРОВАНИЕ ОШИБОК ПОЛУЧЕНИЯ
            self.stdout.write(self.style.ERROR(f"--- process_incoming: Error receiving from Green API ({company.name}): {repr(e)} ---"))

    def generate_ai_reply(self, company, chat_id, user_text, task="dialog"):
        client = self.get_client(company)
        kb = KnowledgeBase.objects.filter(company=company)
        knowledge = "\nБАЗА ЗНАНИЙ:\n" + "\n".join([f"{k.topic}: {k.information}" for k in kb])
        
        logs = MessageLog.objects.filter(company=company, chat_id=chat_id).order_by('-created_at')[:10]
        history = [{"role": ("assistant" if l.sender == "ИИ Администратор" else "user"), "content": l.text} for l in reversed(logs)]

        instruction = (company.system_prompt or "") + "\n" + knowledge
        messages = [{"role": "system", "content": instruction}] + history + [{"role": "user", "content": user_text}]
        
        try:
            res = client.chat.completions.create(model="gpt-3.5-turbo", messages=messages, temperature=0.7) # ИСПРАВЛЕНО имя модели
            return res.choices[0].message.content
        except Exception as e: # ДОБАВЛЕНО ЛОГИРОВАНИЕ
            self.stdout.write(self.style.ERROR(f"--- generate_ai_reply: Error calling OpenAI for company {company.id} ({chat_id}): {repr(e)} ---"))
            return None # Возвращаем None, если была ошибка

    def send_wa(self, company, chat_id, text):
        if not chat_id.endswith('@c.us'):
            chat_id = f"{chat_id}@c.us"
        url = f"https://api.green-api.com/waInstance{company.green_api_id}/sendMessage/{company.green_api_token}"
        try:
            response = requests.post(url, json={"chatId": chat_id, "message": text}, timeout=company.green_api_send_timeout)
            if response.status_code == 200:
                response_data = response.json()
                if response_data.get("idMessage"):
                    MessageLog.objects.create(company=company, chat_id=chat_id, sender="ИИ Администратор", text=text)
                    self.stdout.write(self.style.SUCCESS(f"--- send_wa: Sent message to {chat_id}. MessageLog created. ---"))
                    return True
                else:
                    self.stdout.write(self.style.ERROR(f"--- send_wa: Green API returned 200 OK, but no idMessage. Response: {response_data} ---"))
                    return False
            else:
                self.stdout.write(self.style.ERROR(f"--- send_wa: HTTP Error {response.status_code} - {response.text} for {chat_id} ---"))
                return False
        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f"--- send_wa: Request Exception to {chat_id} - {repr(e)} ---"))
            return False
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"--- send_wa: General Exception to {chat_id} - {repr(e)} ---"))
            return False

    def run_initial_outreach(self, company):
       items = Outreach.objects.filter(company=company, status='Не начат')[:3]
       self.stdout.write(self.style.NOTICE(f"--- run_initial_outreach: Found {len(items)} outreaches with status 'Не начат'. ---"))
       for i in items:
           reply = self.generate_ai_reply(company, i.patient.phone, f"Поприветствуй клиента {i.patient.name}", task="initial")
           
           if reply:
               if self.send_wa(company, i.patient.phone, reply):
                   i.status = 'Отправлено'
                   self.stdout.write(self.style.SUCCESS(f"--- run_initial_outreach: Message sent to {i.patient.phone}. Status updated to 'Отправлено'. ---"))
               else:
                   i.status = 'Ошибка отправки'
                   self.stdout.write(self.style.ERROR(f"--- run_initial_outreach: Failed to send message to {i.patient.phone}. Status updated to 'Ошибка отправки'. ---"))
           else:
               i.status = 'Ошибка генерации ответа'
               self.stdout.write(self.style.ERROR(f"--- run_initial_outreach: Failed to generate AI reply for {i.patient.phone}. Status updated to 'Ошибка генерации ответа'. ---"))
           
           i.save()

    def check_scheduler(self, company):
        today = datetime.now().date()
        due = Patient.objects.filter(company=company, next_contact=today)
        self.stdout.write(self.style.NOTICE(f"--- check_scheduler: Found {len(due)} patients with next_contact due today. ---"))
        for p in due:
            reply = self.generate_ai_reply(company, p.phone, "Напомни о нас вежливо", task="reanimation")
            if reply: # Проверяем, что ИИ дал ответ
                if self.send_wa(company, p.phone, reply):
                    p.next_contact = today + timedelta(days=365)
                    p.save()
                    self.stdout.write(self.style.SUCCESS(f"--- check_scheduler: Reminder sent to {p.phone}. next_contact updated. ---"))
                else:
                    self.stdout.write(self.style.ERROR(f"--- check_scheduler: Failed to send reminder to {p.phone}. ---"))
            else:
                self.stdout.write(self.style.ERROR(f"--- check_scheduler: Failed to generate AI reply for reminder to {p.phone}. ---"))

