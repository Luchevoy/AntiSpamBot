from datetime import datetime, timedelta
from collections import defaultdict
import time

class AntiSpam:
    def __init__(self):
        self.user_activity = defaultdict(lambda: {'count': 0, 'last_time': 0, 'banned_until': 0})
        self.reset_time = 5  #  секунд без активности для сброса
        self.antispam_limit = 10  # Лимит сообщений
        self.antispam_interval = 5  # Интервал проверки (секунды)
        self.spam_ban_time = 10  # Время бана (секунды)

    def update_activity(self, user_id: int):
        """Обновляет статистику активности пользователя"""
        now = time.time()
        activity = self.user_activity[user_id]
        
        # Если прошло больше reset_time - полный сброс
        if now - activity['last_time'] > self.reset_time:
            activity['count'] = 0
        
        # Если прошло больше antispam_interval - частичный сброс
        if now - activity['last_time'] > self.antispam_interval:
            activity['count'] = max(0, activity['count'] - 1)
        
        activity['count'] += 1
        activity['last_time'] = now
        
        # Если превышен лимит - бан
        if activity['count'] > self.antispam_limit:
            activity['banned_until'] = now + self.spam_ban_time
            return True
        return False

    def is_spamming(self, user_id: int) -> bool:
        """Проверяет, является ли пользователь спамером"""
        activity = self.user_activity.get(user_id)
        if not activity:
            return False
            
        now = time.time()
        
        # Проверка бана
        if now < activity['banned_until']:
            return True
            
        # Проверка активности
        if now - activity['last_time'] > self.reset_time:
            activity['count'] = 0
            return False
            
        return activity['count'] > self.antispam_limit

    def has_links(self, text: str) -> bool:
        """Проверяет наличие ссылок в тексте"""
        if not text:
            return False
        #удаления ссылок
        return any(trigger in text.lower() for trigger in ["http://", "https://", "www."])