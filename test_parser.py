from wialon_parser import get_all_vehicles, get_overdue_vehicles, get_statistics, format_vehicle_message


def main():
    print("=" * 60)
    print("Тестирование парсера Wialon")
    print("=" * 60)

    # Получаем все ТС
    vehicles = get_all_vehicles()

    if not vehicles:
        print("❌ Не удалось получить данные")
        return

    print(f"\n✅ Получено {len(vehicles)} ТС")

    # Статистика
    stats = get_statistics()
    print(f"\n📊 Статистика:")
    print(f"   Всего ТС: {stats['total']}")
    print(f"   Просрочено ТО: {stats['overdue']}")
    print(f"   Нет данных о ТО по пробегу: {stats['no_data_km']}")
    print(f"   Нет данных о ТО по моточасам: {stats['no_data_hr']}")

    # Показываем просроченные
    overdue = get_overdue_vehicles()
    if overdue:
        print(f"\n🚨 Просроченные ТС ({len(overdue)}):")
        for v in overdue[:5]:
            print(f"   - {v['name']}: км: {v['still_km']:.0f}, ч: {v['still_hr']:.1f}")

    # Показываем первые 5 ТС с полной информацией
    print("\n📋 Примеры ТС:")
    for v in vehicles[:3]:
        print("\n" + "=" * 40)
        print(format_vehicle_message(v))


if __name__ == "__main__":
    main()