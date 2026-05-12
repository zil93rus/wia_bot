import requests
import json
from config import API_URL, WIALON_TOKEN


class WialonAuth:
    def __init__(self):
        self.token = None
        self.sid = None
        self.load_token()

    def load_token(self):
        """Загрузка токена из переменной"""
        if WIALON_TOKEN:
            self.token = WIALON_TOKEN.strip()
            print(f"✅ Токен загружен (длина: {len(self.token)} символов)")
            print(f"   Начало токена: {self.token[:50]}...")
        else:
            print("❌ Токен не найден в .env файле")
            self.token = None

    def login(self):
        """Авторизация в Wialon через токен"""
        if not self.token:
            print("❌ Токен не найден")
            return None

        params = {
            'svc': 'token/login',
            'params': json.dumps({'token': self.token})
        }

        try:
            response = requests.get(API_URL, params=params, timeout=30)
            data = response.json()

            if 'eid' in data:
                self.sid = data['eid']
                print(f"✅ Авторизация успешна!")
                return self.sid
            else:
                print(f"❌ Ошибка авторизации: {data}")
                return None

        except Exception as e:
            print(f"❌ Ошибка при авторизации: {e}")
            return None

    def get_sid(self):
        if not self.sid:
            self.login()
        return self.sid

    def is_authenticated(self):
        return self.sid is not None