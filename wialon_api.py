import requests
import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from wialon_auth import WialonAuth
from config import API_URL, DATA_FOLDER, WIALON_TOKEN


class WialonAPI:
    def __init__(self):
        self.auth = WialonAuth()
        self.sid = None

    def ensure_auth(self) -> bool:
        """Авторизация и получение SID"""
        if not self.sid:
            # Пробуем получить SID через токен
            params = {
                'svc': 'token/login',
                'params': json.dumps({'token': WIALON_TOKEN})
            }

            try:
                response = requests.get(API_URL, params=params, timeout=30)
                data = response.json()

                if 'eid' in data:
                    self.sid = data['eid']
                    print(f"✅ Авторизация успешна! SID: {self.sid[:30]}...")
                    return True
                else:
                    print(f"❌ Ошибка авторизации: {data}")
                    return False
            except Exception as e:
                print(f"❌ Ошибка авторизации: {e}")
                return False

        return True

    def get_all_vehicles_raw(self, flag: int = 4611686018427387903) -> Optional[Dict]:
        """Получение сырых данных от Wialon"""
        if not self.ensure_auth():
            return None

        params = {
            'svc': 'core/search_items',
            'params': json.dumps({
                'spec': {
                    'itemsType': 'avl_unit',
                    'propName': 'sys_name',
                    'propValueMask': '*',
                    'sortType': 'sys_name'
                },
                'force': 1,
                'flags': flag,
                'from': 0,
                'to': 10000
            }),
            'sid': self.sid
        }

        try:
            print("📡 Отправляю запрос к Wialon API...")
            response = requests.get(API_URL, params=params, timeout=60)
            data = response.json()

            if 'items' in data:
                print(f"✅ Получено {len(data['items'])} транспортных средств")
                return data
            else:
                print(f"❌ Ошибка получения ТС: {data.get('error', 'Unknown error')}")
                return None
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            return None

    def save_raw_data(self, data: dict) -> str:
        """Сохраняет сырые данные в JSON файл с датой и временем"""
        # Создаем папку если нет
        if not os.path.exists(DATA_FOLDER):
            os.makedirs(DATA_FOLDER)
            print(f"📁 Создана папка: {DATA_FOLDER}")

        # Формируем имя файла: wialon_20260430_165226.json
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"wialon_{timestamp}.json"
        filepath = os.path.join(DATA_FOLDER, filename)

        # Сохраняем с метаданными
        full_data = {
            'timestamp': datetime.now().isoformat(),
            'data': data
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(full_data, f, ensure_ascii=False, indent=2)

        print(f"💾 Данные сохранены: {filepath}")
        return filepath

    def refresh_data(self) -> Optional[str]:
        """Принудительное обновление данных из Wialon"""
        print("🔄 Обновляем данные из Wialon...")

        raw_data = self.get_all_vehicles_raw()
        if raw_data:
            filepath = self.save_raw_data(raw_data)
            print(f"✅ Данные успешно обновлены! Файл: {filepath}")
            return filepath

        print("❌ Не удалось обновить данные")
        return None