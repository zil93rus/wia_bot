import json
import os
import glob
from datetime import datetime
from typing import List, Dict, Optional


class WialonParser:
    def __init__(self, raw_data: dict):
        """Парсер данных Wialon"""
        self.raw_data = raw_data
        # Правильно извлекаем items
        if 'data' in raw_data and 'items' in raw_data['data']:
            self.items = raw_data['data']['items']
        elif 'items' in raw_data:
            self.items = raw_data['items']
        else:
            self.items = []

    def parse_all_vehicles(self) -> List[Dict]:
        """Парсинг всех ТС"""
        vehicles = []
        for item in self.items:
            vehicle = self.parse_vehicle(item)
            vehicles.append(vehicle)
        return vehicles

    def parse_vehicle(self, item: dict) -> Dict:
        """Парсинг одного ТС"""
        name = item.get('nm', 'Unknown')
        vehicle_id = item.get('id', 0)

        # Текущие показатели
        current_km = item.get('cnm_km', 0)
        current_hours = item.get('cneh', 0)

        # Парсим все сервисные интервалы
        services = self.parse_all_services(item, current_km, current_hours)

        # Определяем общий статус
        is_overdue = any(s.get('status', {}).get('is_overdue', False) for s in services)
        is_warning = any(s.get('status', {}).get('is_warning', False) for s in services) and not is_overdue

        return {
            'id': vehicle_id,
            'name': name,
            'current_km': current_km,
            'current_hours': current_hours,
            'services': services,
            'is_overdue': is_overdue,
            'is_warning': is_warning
        }

    def parse_all_services(self, item: dict, current_km: float, current_hours: float) -> List[Dict]:
        """Парсинг всех сервисных интервалов"""
        services = []

        # Получаем si из item
        si = item.get('si', {})

        if not si:
            print(f"⚠️ Нет сервисов для ТС: {item.get('nm', 'Unknown')}")
            return services

        print(f"📋 Найдено {len(si)} сервисов для ТС: {item.get('nm', 'Unknown')}")

        for key, service in si.items():
            try:
                if not isinstance(service, dict):
                    continue

                service_name = service.get('n', 'Unknown')
                description = service.get('t', '')

                # Извлекаем значения
                interval_km = int(service.get('im', 0))
                interval_days = int(service.get('it', 0))
                interval_hours = int(service.get('ie', 0))
                last_km = float(service.get('pm', 0))
                last_date = int(service.get('pt', 0))
                last_hours = float(service.get('pe', 0))

                # Пропускаем только если вообще нет данных
                has_data = (interval_km > 0 and last_km > 0) or \
                           (interval_days > 0 and last_date > 0) or \
                           (interval_hours > 0 and last_hours > 0)

                if not has_data:
                    print(f"   ⚠️ Сервис '{service_name}' не имеет активных данных")
                    continue

                print(f"   ✅ Сервис: {service_name}")
                if interval_km > 0:
                    print(f"      Пробег: интервал {interval_km} км, последний {last_km} км")
                if interval_hours > 0:
                    print(f"      Моточасы: интервал {interval_hours} ч, последний {last_hours} ч")
                if interval_days > 0 and last_date > 0:
                    last_date_str = datetime.fromtimestamp(last_date).strftime('%d.%m.%Y')
                    print(f"      Дни: интервал {interval_days} дней, последний {last_date_str}")

                # Рассчитываем статус
                status = self.calculate_service_status(
                    service_name, interval_km, interval_days, interval_hours,
                    last_km, last_date, last_hours,
                    current_km, current_hours
                )

                # Добавляем last_date_str для days_status
                if status.get('days_status') and status['days_status'].get('last_date'):
                    try:
                        status['days_status']['last_date_str'] = datetime.fromtimestamp(
                            status['days_status']['last_date']
                        ).strftime('%d.%m.%Y')
                    except:
                        status['days_status']['last_date_str'] = None

                # Преобразуем дату для отображения
                last_date_str = None
                if last_date and last_date > 0:
                    try:
                        last_date_str = datetime.fromtimestamp(last_date).strftime('%d.%m.%Y')
                    except:
                        last_date_str = None

                services.append({
                    'name': service_name,
                    'description': description,
                    'interval_km': interval_km,
                    'interval_days': interval_days,
                    'interval_hours': interval_hours,
                    'last_km': last_km,
                    'last_date': last_date,
                    'last_date_str': last_date_str,
                    'last_hours': last_hours,
                    'status': status
                })

            except Exception as e:
                print(f"   ❌ Ошибка при обработке сервиса {key}: {e}")
                continue

        # Сортируем: сначала просроченные, потом предупреждения, потом остальные
        services.sort(key=lambda x: (
            0 if x['status'].get('is_overdue') else
            1 if x['status'].get('is_warning') else 2
        ))

        return services

    def calculate_service_status(self, name: str, interval_km: int, interval_days: int, interval_hours: int,
                                 last_km: float, last_date: int, last_hours: float,
                                 current_km: float, current_hours: float) -> Dict:
        """Расчет статуса сервиса - отдельно для км, часов и дней"""
        status = {
            'km_status': None,
            'hours_status': None,
            'days_status': None,
            'is_overdue': False,
            'is_warning': False,
            'primary_type': None,
            'primary_remaining': None
        }

        # Расчет по километражу
        if interval_km > 0 and last_km > 0:
            next_km = last_km + interval_km
            remaining_km = next_km - current_km
            status['km_status'] = {
                'type': 'km',
                'last': last_km,
                'interval': interval_km,
                'next': next_km,
                'remaining': remaining_km,
                'is_overdue': remaining_km < 0,
                'is_warning': 0 <= remaining_km <= (interval_km * 0.1)
            }
            if remaining_km < 0:
                status['is_overdue'] = True
            elif remaining_km <= (interval_km * 0.1):
                status['is_warning'] = True

        # Расчет по моточасам
        if interval_hours > 0 and last_hours > 0:
            next_hours = last_hours + interval_hours
            remaining_hours = next_hours - current_hours
            status['hours_status'] = {
                'type': 'hours',
                'last': last_hours,
                'interval': interval_hours,
                'next': next_hours,
                'remaining': remaining_hours,
                'is_overdue': remaining_hours < 0,
                'is_warning': 0 <= remaining_hours <= (interval_hours * 0.1)
            }
            if remaining_hours < 0:
                status['is_overdue'] = True
                status['primary_type'] = 'hours'
                status['primary_remaining'] = remaining_hours
            elif remaining_hours <= (interval_hours * 0.1):
                status['is_warning'] = True
                if not status['primary_type']:
                    status['primary_type'] = 'hours'
                    status['primary_remaining'] = remaining_hours

        # Расчет по дням
        if interval_days > 0 and last_date > 0:
            last_date_obj = datetime.fromtimestamp(last_date)
            today = datetime.now()
            days_passed = (today - last_date_obj).days
            remaining_days = interval_days - days_passed
            status['days_status'] = {
                'type': 'days',
                'last_date': last_date,
                'interval': interval_days,
                'days_passed': days_passed,
                'remaining': remaining_days,
                'is_overdue': remaining_days < 0,
                'is_warning': 0 <= remaining_days <= (interval_days * 0.1)
            }
            if remaining_days < 0:
                status['is_overdue'] = True
            elif not status['primary_type'] and remaining_days <= (interval_days * 0.1):
                status['is_warning'] = True

        return status

    def format_service_message(self, service: Dict) -> str:
        """Форматирование сообщения для одного сервиса"""
        name = service['name']
        description = f" ({service['description']})" if service['description'] else ""
        status = service['status']

        # Определяем иконку
        if 'Пропуск' in name:
            icon = "🎫"
        elif 'Страховка' in name:
            icon = "🛡️"
        elif 'Тахограф' in name:
            icon = "📟"
        elif 'Техническое обслуживание' in name or 'ТО' in name:
            icon = "🔧"
        else:
            icon = "📋"

        message = f"{icon} <b>{name}{description}</b>\n"

        # Показываем информацию по пробегу
        if status.get('km_status'):
            km = status['km_status']
            message += f"   📍 <b>По пробегу:</b>\n"
            message += f"      Интервал: {km['interval']:,.0f} км\n"
            message += f"      Последний раз: {km['last']:,.0f} км\n"
            if km['is_overdue']:
                message += f"      ⛔ <b>ПРОСРОЧЕНО на {abs(km['remaining']):,.0f} км!</b>\n"
            else:
                message += f"      ✅ Осталось: {km['remaining']:,.0f} км\n"

        # Показываем информацию по моточасам
        if status.get('hours_status'):
            hours = status['hours_status']
            message += f"   ⏲ <b>По моточасам:</b>\n"
            message += f"      Интервал: {hours['interval']:,.0f} ч\n"
            message += f"      Последний раз: {hours['last']:,.1f} ч\n"
            if hours['is_overdue']:
                message += f"      ⛔ <b>ПРОСРОЧЕНО на {abs(hours['remaining']):,.1f} ч!</b>\n"
            else:
                message += f"      ✅ Осталось: {hours['remaining']:,.1f} ч\n"

        # Показываем информацию по дням
        if status.get('days_status'):
            days = status['days_status']
            message += f"   📆 <b>По дням:</b>\n"
            message += f"      Интервал: {days['interval']} дней\n"
            if days.get('last_date_str'):
                message += f"      Последний раз: {days['last_date_str']}\n"
            if days['is_overdue']:
                message += f"      ⛔ <b>ПРОСРОЧЕНО на {abs(days['remaining'])} дней!</b>\n"
            else:
                message += f"      ✅ Осталось: {days['remaining']} дней\n"

        return message

    def format_vehicle_message(self, vehicle: Dict, detailed: bool = False) -> str:
        """Форматирование полного сообщения о ТС со всеми сервисами"""
        status_emoji = "✅"
        if vehicle.get('is_overdue'):
            status_emoji = "🚨"
        elif vehicle.get('is_warning'):
            status_emoji = "⚠️"

        message = f"{status_emoji} <b>{vehicle['name']}</b>\n"

        # Текущие показатели
        if vehicle['current_km'] > 0:
            message += f"📊 Пробег: {vehicle['current_km']:,.0f} км\n"
        if vehicle['current_hours'] > 0:
            message += f"⏱ Моточасы: {vehicle['current_hours']:,.1f} ч\n"

        message += "\n"

        # Все сервисы
        if not vehicle['services']:
            message += "❓ Нет активных сервисов\n"
        else:
            for service in vehicle['services']:
                message += self.format_service_message(service)
                message += "\n"

        if detailed:
            message += f"\n🆔 ID: {vehicle['id']}\n"
            message += f"📅 Обновлено: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n"

        return message

    def get_statistics(self) -> Dict:
        """Получение статистики по всем ТС"""
        vehicles = self.parse_all_vehicles()

        total = len(vehicles)
        overdue = sum(1 for v in vehicles if v.get('is_overdue', False))
        warning = sum(1 for v in vehicles if v.get('is_warning', False) and not v.get('is_overdue', False))

        # Статистика по типам сервисов
        service_stats = {}
        for vehicle in vehicles:
            for service in vehicle.get('services', []):
                name = service.get('name', 'Unknown')
                if name not in service_stats:
                    service_stats[name] = {'total': 0, 'overdue': 0, 'warning': 0}
                service_stats[name]['total'] += 1
                if service.get('status', {}).get('is_overdue'):
                    service_stats[name]['overdue'] += 1
                elif service.get('status', {}).get('is_warning'):
                    service_stats[name]['warning'] += 1

        return {
            'total': total,
            'overdue': overdue,
            'warning': warning,
            'ok': total - overdue - warning,
            'service_stats': service_stats
        }


def refresh_and_load(data_folder: str = "data") -> Optional[WialonParser]:
    """Принудительное обновление данных из Wialon и загрузка нового файла"""
    print("🔄 Принудительное обновление данных из Wialon...")

    # Импортируем здесь, чтобы избежать циклических импортов
    from wialon_api import WialonAPI

    wialon_api = WialonAPI()
    filepath = wialon_api.refresh_data()

    if not filepath:
        print("❌ Не удалось обновить данные")
        return None

    # Загружаем новый файл
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"📁 Загружен обновленный файл: {filepath}")
        return WialonParser(data)
    except Exception as e:
        print(f"❌ Ошибка загрузки файла: {e}")
        return None


def get_latest_file_info(data_folder: str = "data") -> Optional[Dict]:
    """Получение подробной информации о последнем файле данных"""
    if not os.path.exists(data_folder):
        return None

    pattern = os.path.join(data_folder, "wialon_*.json")
    files = glob.glob(pattern)

    if not files:
        return None

    latest_file = max(files, key=os.path.getctime)
    file_time = datetime.fromtimestamp(os.path.getctime(latest_file))
    file_size = os.path.getsize(latest_file)

    # Проверяем содержимое файла
    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            items_count = len(data.get('data', {}).get('items', []))

            # Берем первый ТС для примера
            first_vehicle = None
            if items_count > 0:
                first_vehicle = data['data']['items'][0]
    except:
        items_count = 0
        first_vehicle = None

    return {
        'filename': os.path.basename(latest_file),
        'path': latest_file,
        'created': file_time,
        'size_kb': file_size / 1024,
        'vehicles_count': items_count,
        'first_vehicle': first_vehicle
    }


def load_and_parse_latest_json(data_folder: str = "data") -> Optional[WialonParser]:
    """Загрузка последнего JSON файла и создание парсера"""
    if not os.path.exists(data_folder):
        print(f"❌ Папка {data_folder} не существует")
        return None

    pattern = os.path.join(data_folder, "wialon_*.json")
    files = glob.glob(pattern)

    if not files:
        print(f"❌ Нет файлов с данными Wialon в папке {data_folder}")
        return None

    latest_file = max(files, key=os.path.getctime)

    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"📁 Загружен файл: {latest_file}")
        return WialonParser(data)
    except Exception as e:
        print(f"❌ Ошибка загрузки файла: {e}")
        return None


if __name__ == "__main__":
    # Тестирование
    parser = load_and_parse_latest_json()

    if parser:
        vehicles = parser.parse_all_vehicles()

        print(f"\n📊 Найдено ТС: {len(vehicles)}")

        # Показываем все ТС с сервисами
        for vehicle in vehicles:
            print("\n" + "=" * 60)
            print(parser.format_vehicle_message(vehicle))
            print("=" * 60)

        # Статистика
        stats = parser.get_statistics()
        print(f"\n📊 ОБЩАЯ СТАТИСТИКА:")
        print(f"   Всего ТС: {stats['total']}")
        print(f"   🚨 Просрочено: {stats['overdue']}")
        print(f"   ⚠️ Скоро ТО: {stats['warning']}")
        print(f"   ✅ В норме: {stats['ok']}")

        if stats['service_stats']:
            print(f"\n📊 СТАТИСТИКА ПО СЕРВИСАМ:")
            for name, stat in stats['service_stats'].items():
                print(f"\n   {name}:")
                print(f"      Всего: {stat['total']}")
                print(f"      Просрочено: {stat['overdue']}")
                print(f"      Скоро: {stat['warning']}")