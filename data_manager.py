import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional


class DataManager:
    def __init__(self, cache_file="wialon_cache.json", cache_ttl=300):  # TTL = 5 минут
        self.cache_file = cache_file
        self.cache_ttl = cache_ttl
        self.data = None
        self.last_update = None

    def save_data(self, vehicles_data: List[Dict]):
        """Сохраняет данные ТС в JSON файл"""
        cache = {
            'timestamp': datetime.now().isoformat(),
            'vehicles': vehicles_data
        }
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
        self.data = vehicles_data
        self.last_update = datetime.now()
        print(f"✅ Данные сохранены в {self.cache_file} ({len(vehicles_data)} ТС)")

    def load_data(self) -> Optional[List[Dict]]:
        """Загружает данные из JSON файла"""
        if not os.path.exists(self.cache_file):
            return None

        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                cache = json.load(f)

            timestamp = datetime.fromisoformat(cache['timestamp'])
            age = (datetime.now() - timestamp).total_seconds()

            if age > self.cache_ttl:
                print(f"⚠️ Кэш устарел (возраст: {age:.0f} сек), нужно обновить")
                return None

            self.data = cache['vehicles']
            self.last_update = timestamp
            print(f"✅ Загружено из кэша: {len(self.data)} ТС (возраст: {age:.0f} сек)")
            return self.data
        except Exception as e:
            print(f"❌ Ошибка загрузки кэша: {e}")
            return None

    def get_vehicles(self, force_update=False) -> List[Dict]:
        """Получает данные ТС (из кэша или требует обновления)"""
        if not force_update and self.data is not None:
            return self.data

        cached = self.load_data()
        if cached and not force_update:
            return cached

        return None

    def search_by_text(self, query: str) -> List[Dict]:
        """Поиск ТС по номеру или названию"""
        if not self.data:
            return []

        query_lower = query.lower()
        results = []

        for vehicle in self.data:
            if (query_lower in vehicle['name'].lower() or
                    query_lower in vehicle['plate'].lower() or
                    query_lower in str(vehicle['id'])):
                results.append(vehicle)

        return results

    def get_by_id(self, vehicle_id: str) -> Optional[Dict]:
        """Получение ТС по ID"""
        if not self.data:
            return None

        for vehicle in self.data:
            if str(vehicle['id']) == str(vehicle_id):
                return vehicle
        return None

    def get_statistics(self) -> Dict:
        """Получение статистики по ТС"""
        if not self.data:
            return {}

        total = len(self.data)
        overdue = sum(1 for v in self.data if v.get('is_overdue', False))
        no_data = sum(
            1 for v in self.data if v['km_status'].get('last') is None and v['hours_status'].get('last') is None)

        return {
            'total': total,
            'overdue': overdue,
            'no_data': no_data,
            'last_update': self.last_update
        }