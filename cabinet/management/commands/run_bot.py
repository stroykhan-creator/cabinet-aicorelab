
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
            # Берем только те компании, которые отмечены как активные И у которых включен Реаниматор
            # is_reanimator_enabled = True  # <-- Основное изменение здесь
            active_companies = Company.objects.filter(is_active=True, is_reanimator_enabled=True)
            
            for company in active_companies:
                self.run_initial_outreach(company) # Эти функции теперь будут вызываться только для активных и с включенным реаниматором
                self.check_scheduler(company)    #
                self.process_incoming(company)  # process_incoming уже имеет свою логику проверки auto_reply_enabled
            # Пауза 5 секунд перед следующим циклом проверки всех компаний
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
        except Exception:
            return "ДИАЛОГ"

    def extract_date(self, company, text):
        client = self.get_client(company)
        today = datetime.now().strftime("%Y-%m-%d")
        try:
            res = client.chat.completions.create(
                model="-3.5-turbo",
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
        except Exception:
            return None

    def process_incoming(self, company):
        # Эта функция обрабатывает ВХОДЯЩИЕ сообщения.
        # Здесь автоответчик (AI Reply) включается только если company.auto_reply_enabled == True.
        # Реаниматор (check_scheduler) и начальная рассылка (run_initial_outreach)
        # теперь управляются флагом is_reanimator_enabled в handle().
        url = f"https://api.green-api.com/waInstance{company.green_api_id}/receiveNotification/{company.green_api_token}"
        del_url = f"https://api.green-api.com/waInstance{company.green_api_id}/deleteNotification/{company.green_api_token}/"
        
        try:
            # Получаем уведомление с таймаутом из настроек компании
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
                            # 1. Всегда логируем входящее сообщение
                            MessageLog.objects.create(company=company, chat_id=chat_id, sender="Клиент", text=text)
                            
                            # 2. Анализируем намерения
                            sentiment = self.analyze_sentiment(company, text)
                            outreach = Outreach.objects.filter(company=company, patient=target_client).first()

                            if sentiment == "ОТКАЗ":
                                if outreach:
                                    outreach.status = 'ОТКАЗ'
                                    outreach.save()
                                self.send_wa(company, chat_id, "Хорошо, больше не беспокоим.")
                            else:
                                # Обновляем статус в воронке
                                if outreach:
                                    status_map = {"ЗАПИСЬ": "Записан", "ИНТЕРЕС": "ИНТЕРЕС"}
                                    outreach.status = status_map.get(sentiment, "Диалог")
                                    outreach.save()

                                # Пытаемся вытащить дату
                                new_date = self.extract_date(company, text)
                                if new_date:
                                    target_client.next_contact = new_date
                                    target_client.save()

                                # 3. Отвечаем, ТОЛЬКО если вкл. автоответчик (это ИИ-ответ на входящий, не реаниматор)
                                if company.auto_reply_enabled:
                                    reply = self.generate_ai_reply(company, chat_id, text)
                                    self.send_wa(company, chat_id, reply)
                                else:
                                    # Просто логируем, что ИИ промолчал из-за настроек
                                    MessageLog.objects.create(company=company, chat_id=chat_id, sender="system", text="Автоответ отключен в настройках компании.")

                # Удаляем уведомление из очереди Green API
                if receipt_id:
                    requests.delete(f"{del_url}{receipt_id}", timeout=company.green_api_send_timeout)
        except Exception as e:
            self.stdout.write(f"Ошибка получения ({company.name}): {e}")

    def generate_ai_reply(self, company, chat_id, user_text, task="dialog"):
        client = self.get_client(company)
        kb = KnowledgeBase.objects.filter(company=company)
        knowledge = "\nБАЗА ЗНАНИЙ:\n" + "\n".join([f"{k.topic}: {k.information}" for k in kb])
        
        # Берем историю последних 10 сообщений
        logs = MessageLog.objects.filter(company=company, chat_id=chat_id).order_by('-created_at')[:10]
        history = [{"role": ("assistant" if l.sender == "ИИ Администратор" else "user"), "content": l.text} for l in reversed(logs)]

        instruction = (company.system_prompt or "") + "\n" + knowledge
        messages = [{"role": "system", "content": instruction}] + history + [{"role": "user", "content": user_text}]
        
        try:
            res = client.chat.completions.create(model="-3.5-turbo", messages=messages, temperature=0.7)
            return res.choices[0].message.content
        except Exception:
            return "Минутку, уточняю информацию..."

    def send_wa(self, company, chat_id, text):
        if not chat_id.endswith('@c.us'):
            chat_id = f"{chat_id}@c.us"
        url = f"https://api.green-api.com/waInstance{company.green_api_id}/sendMessage/{company.green_api_token}"
        try:
            requests.post(url, json={"chatId": chat_id, "message": text}, timeout=company.green_api_send_timeout)
            MessageLog.objects.create(company=company, chat_id=chat_id, sender="ИИ Администратор", text=text)
            return True
        except Exception:
            return False

    def run_initial_outreach(self, company):
        # Эта функция теперь вызывается только если is_reanimator_enabled = True для company
        # Автоответчик (auto_reply_enabled) может быть отключен, но реаниматор (initial outreach) включен
        # Если вы хотите, чтобы initial outreach работал только если auto_reply_enabled=True,
        # то верните проверку `if not company.auto_reply_enabled: return`
        
        items = Outreach.objects.filter(company=company, status='Не начат')[:3]
        for i in items:
            reply = self.generate_ai_reply(company, i.patient.phone, f"Поприветствуй клиента {i.patient.name}", task="initial")
            if self.send_wa(company, i.patient.phone, reply):
                i.status = 'Отправлено'
                i.save()

    def check_scheduler(self, company):
        # Эта функция теперь вызывается только если is_reanimator_enabled = True для company
        # Если вы хотите, чтобы check_scheduler работал только если auto_reply_enabled=True,
        # то верните проверку `if not company.auto_reply_enabled: return`
        
        today = datetime.now().date()
        due = Patient.objects.filter(company=company, next_contact=today)
        for p in due:
            reply = self.generate_ai_reply(company, p.phone, "Напомни о нас вежливо", task="reanimation")
            if self.send_wa(company, p.phone, reply):
                # Откладываем следующее касание на год (или пока клиент не ответит)
                p.next_contact = today + timedelta(days=365)
                p.save()
