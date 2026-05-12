#!/usr/bin/env python
# -*- coding: utf-8 -*-

from wialon_collector import WialonCollector
from data_manager import DataManager
from config import WIALON_TOKEN, WIALON_HOST


def main():
    print("=" * 60)
    print("Сбор данных из Wialon")
    print("=" * 60)

    # Создаем коллектор
    collector = WialonCollector(
        token=WIALON_TOKEN,
        host=WIALON_HOST
    )

    # Собираем данные
    vehicles = collector.collect_all_vehicles()

    if not vehicles:
        print("❌ Не удалось собрать данные")
        return

    # Сохраняем в JSON
    manager = DataManager()
    manager.save_data(vehicles)

    print("\n📊 Статистика:")
    print(f"   Всего ТС: {len(vehicles)}")

    # Показываем первые 5
    print("\n📋 Первые 5 ТС:")
    for v in vehicles[:5]:
        print(f"   - {v['name']}: {v['mileage']:.0f} км, {v['engine_hours']:.1f} ч")


if __name__ == "__main__":
    main()