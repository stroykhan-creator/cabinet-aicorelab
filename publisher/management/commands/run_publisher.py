import time
import requests
import os
from django.core.management.base import BaseCommand
from django.utils import timezone
from publisher.models import AutoPost, PostLog

class Command(BaseCommand):
    help = 'Запуск рассылки рекламных постов (Вещатель с поддержкой медиа и дат)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Вещатель запущен и готов к медиа-постингу!'))
        
        while True:
            now = timezone.localtime(timezone.now())
            current_time = now.strftime('%H:%M')
            current_date = now.date()
            current_weekday_int = now.weekday() # 0=Пн, 1=Вт...

            # Маппинг номера дня недели
            day_field_map = {
                0: 'monday', 1: 'tuesday', 2: 'wednesday',
                3: 'thursday', 4: 'friday', 5: 'saturday', 6: 'sunday'
            }
            current_day_field_name = day_field_map.get(current_weekday_int)

            # Базовая фильтрация (время, активность, день недели)
            posts_filter = {
                'is_active': True,
                'post_time__icontains': current_time,
            }
            if current_day_field_name:
                posts_filter[current_day_field_name] = True

            posts = AutoPost.objects.filter(**posts_filter)

            for post in posts:
                # ПРОВЕРКА ДИАПАЗОНА ДАТ
                # Если даты установлены, проверяем, входит ли текущий день в диапазон
                if post.start_date and current_date < post.start_date:
                    continue
                if post.end_date and current_date > post.end_date:
                    continue

                self.process_post(post)

            time.sleep(30) # Проверка каждые 30 секунд

    def process_post(self, post):
        company = post.company
        base_url = company.green_api_url.rstrip('/')
        
        # Определяем метод и URL в зависимости от наличия медиафайла
        if post.media_file:
            method = "sendFileByUpload"
        else:
            method = "sendMessage"
            
        url = f"{base_url}/waInstance{company.green_api_id}/{method}/{company.green_api_token}"

        for target_list in post.targets.all():
            chat_ids = target_list.get_id_list()
            for chat_id in chat_ids:
                chat_id = chat_id.strip()
                if not chat_id: continue
                
                # Проверка дублей (в ту же минуту)
                now = timezone.now()
                already_sent = PostLog.objects.filter(
                    autopost=post,
                    group_id=chat_id,
                    created_at__date=now.date(),
                    created_at__hour=now.hour,
                    created_at__minute=now.minute
                ).exists()

                if not already_sent:
                    self.stdout.write(f"  -> Отправка в {chat_id} (Метод: {method})...")
                    self.send_to_green_api(url, chat_id, post)

    def send_to_green_api(self, url, chat_id, post):
        try:
            if post.media_file:
                # ОТПРАВКА С ФАЙЛОМ (multipart/form-data)
                file_path = post.media_file.path
                file_name = os.path.basename(post.media_file.name)
                
                with open(file_path, 'rb') as f:
                    files = {'file': (file_name, f)}
                    payload = {
                        'chatId': chat_id,
                        'caption': post.text # Текст становится подписью к фото
                    }
                    # При отправке файлов используем аргумент 'files' и 'data'
                    resp = requests.post(url, data=payload, files=files, timeout=60)
            else:
                # ОТПРАВКА ПРОСТО ТЕКСТА (json)
                payload = {
                    "chatId": chat_id,
                    "message": post.text
                }
                resp = requests.post(url, json=payload, timeout=30)

            status = 'success' if resp.status_code == 200 else 'error'
            
            PostLog.objects.create(
                autopost=post,
                group_id=chat_id,
                status=status,
                response=resp.text
            )
            
            if status == 'success':
                self.stdout.write(self.style.SUCCESS(f"   [+] УСПЕХ: {chat_id}"))
            else:
                self.stdout.write(self.style.ERROR(f"   [-] ОШИБКА {chat_id}: {resp.text}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   [!] СИСТЕМНАЯ ОШИБКА: {e}"))