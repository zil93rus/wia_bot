import requests
import json
from datetime import datetime
from typing import List, Dict, Optional


class WialonCollector:
    def __init__(self, token: str, host: str = "https://app.wialonlocal.online"):
        self.token = token
        self.host = host
        self.sid = None
        self.api_url = f"{self.host}/wialon/ajax.html"

    def login(self) -> bool:
        """Авторизация и получение SID"""
        params = {
            'svc': 'token/login',
            'params': json.dumps({'token': self.token})
        }

        try:
            response = requests.get(self.api_url, params=params, timeout=30)
            data = response.json()

            if 'eid' in data:
                self.sid = data['eid']
                print(f"✅ Авторизация успешна! SID: {self.sid[:30]}...")
                return True
            else:
                print(f"❌ Ошибка авторизации: {data}")
                return False
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            return False

    def get_all_units(self) -> Optional[List[Dict]]:
        """Получение всех ТС"""
        if not self.sid and not self.login():
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
                'flags': 1,
                'from': 0,
                'to': 10000
            }),
            'sid': self.sid
        }

        try:
            response = requests.get(self.api_url, params=params, timeout=30)
            data = response.json()

            if 'items' in data:
                return data['items']
            else:
                print(f"❌ Ошибка получения ТС: {data}")
                return None
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            return None

    def get_unit_data(self, unit_id: int) -> Dict:
        """Получение данных конкретного ТС (пробег, моточасы)"""
        if not self.sid:
            return {'mileage': 0, 'engine_hours': 0}

        result = {'mileage': 0, 'engine_hours': 0}

        # Получаем пробег
        params = {
            'svc': 'unit/get_data',
            'params': json.dumps({
                'id': unit_id,
                'type': 'L',  # L = пробег
                'time': {'from': 0, 'to': int(datetime.now().timestamp())}
            }),
            'sid': self.sid
        }

        try:
            response = requests.get(self.api_url, params=params, timeout=30)
            data = response.json()
            if 'data' in data and data['data'] and 'value' in data['data']:
                result['mileage'] = float(data['data']['value'])
        except:
            pass

        # Получаем моточасы
        params['params'] = json.dumps({
            'id': unit_id,
            'type': 'M',  # M = моточасы
            'time': {'from': 0, 'to': int(datetime.now().timestamp())}
        })

        try:
            response = requests.get(self.api_url, params=params, timeout=30)
            data = response.json()
            if 'data' in data and data['data'] and 'value' in data['data']:
                result['engine_hours'] = float(data['data']['value'])
        except:
            pass

        return result

    def get_license_plate(self, unit_id: int) -> str:
        """Получение госномера ТС"""
        if not self.sid:
            return "Н/Д"

        params = {
            'svc': 'core/get_item_data',
            'params': json.dumps({'id': unit_id, 'flags': 1}),
            'sid': self.sid
        }

        try:
            response = requests.get(self.api_url, params=params, timeout=30)
            data = response.json()

            if 'props' in data:
                for prop in data['props']:
                    prop_name = prop.get('n', '').lower()
                    if any(k in prop_name for k in ['номер', 'plate', 'number', 'госномер']):
                        return prop.get('v', 'Не указан')
            return "Не указан"
        except:
            return "Ошибка"

    def collect_all_vehicles(self) -> List[Dict]:
        """Сбор всех данных о ТС"""
        print("🔍 Начинаем сбор данных о всех ТС...")

        units = self.get_all_units()
        if not units:
            return []

        vehicles = []
        total = len(units)

        for i, unit in enumerate(units, 1):
            print(f"   Обработка {i}/{total}: {unit.get('nm', 'Unknown')}")

            unit_data = self.get_unit_data(unit['id'])
            plate = self.get_license_plate(unit['id'])

            vehicle = {
                'id': unit['id'],
                'name': unit.get('nm', 'Без названия'),
                'plate': plate,
                'mileage': unit_data['mileage'],
                'engine_hours': unit_data['engine_hours'],
                'last_maintenance_km': None,
                'last_maintenance_hours': None
            }

            vehicles.append(vehicle)

        print(f"✅ Собрано данных о {len(vehicles)} ТС")
        return vehicles