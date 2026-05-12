from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from aiogram import Bot
from datetime import datetime
import asyncio

from wialon_api import WialonAPI
from config import TELEGRAM_CHAT_IDS, CHECK_INTERVAL_HOURS, MAINTENANCE_WARNING_KM

scheduler = AsyncIOScheduler()
wialon_api = WialonAPI()


async def check_maintenance_and_notify(bot: Bot):
    """Периодическая проверка ТО и отправка уведомлений"""
    print(f"[{datetime.now()}] 🔍 Выполняю плановую проверку ТО...")

    vehicles = wialon_api.get_all_vehicles()

    if not vehicles:
        print(f"[{datetime.now()}] ❌ Не удалось получить данные о ТС")
        return

    overdue_vehicles = []
    warning_vehicles = []

    for vehicle in vehicles:
        if vehicle.get('is_overdue'):
            overdue_vehicles.append(vehicle)
        elif vehicle.get('remaining_km') is not None and vehicle.get('remaining_km', 0) < MAINTENANCE_WARNING_KM:
            warning_vehicles.append(vehicle)

    # Отправка уведомлений во все указанные чаты
    for chat_id in TELEGRAM_CHAT_IDS:
        if not chat_id.strip():
            continue

        try:
            # Отправка срочных уведомлений
            if overdue_vehicles:
                message = "🚨 <b>СРОЧНО! Требуется техническое обслуживание!</b>\n\n"
                for vehicle in overdue_vehicles[:10]:  # Ограничиваем 10 ТС
                    message += f"🚛 <b>{vehicle['name']}</b>\n"
                    message += f"📝 {vehicle['plate']}\n"
                    message += f"⛔ Просрочено на {abs(vehicle['remaining_km']):,.0f} км\n"
                    message += "─" * 30 + "\n"

                if len(overdue_vehicles) > 10:
                    message += f"\n... и еще {len(overdue_vehicles) - 10} ТС"

                await bot.send_message(chat_id=chat_id, text=message, parse_mode="HTML")

            # Отправка предупреждений
            if warning_vehicles:
                message = "⚠️ <b>Внимание! Приближается ТО</b>\n\n"
                for vehicle in warning_vehicles[:10]:
                    message += f"🚛 <b>{vehicle['name']}</b>\n"
                    message += f"📝 {vehicle['plate']}\n"
                    message += f"⚠️ Осталось {vehicle['remaining_km']:,.0f} км\n"
                    message += "─" * 30 + "\n"

                if len(warning_vehicles) > 10:
                    message += f"\n... и еще {len(warning_vehicles) - 10} ТС"

                await bot.send_message(chat_id=chat_id, text=message, parse_mode="HTML")

            # Если всё в порядке
            if not overdue_vehicles and not warning_vehicles:
                await bot.send_message(
                    chat_id=chat_id,
                    text="✅ <b>Плановая проверка завершена.</b>\nВсе ТС в порядке!",
                    parse_mode="HTML"
                )

        except Exception as e:
            print(f"[{datetime.now()}] ❌ Ошибка отправки в чат {chat_id}: {e}")

    print(
        f"[{datetime.now()}] ✅ Проверка завершена. Просрочено: {len(overdue_vehicles)}, Предупреждений: {len(warning_vehicles)}")


def setup_scheduler(bot: Bot):
    """Настройка планировщика"""
    # Проверка каждые CHECK_INTERVAL_HOURS часов
    scheduler.add_job(
        check_maintenance_and_notify,
        trigger=IntervalTrigger(hours=CHECK_INTERVAL_HOURS),
        args=[bot],
        id="maintenance_check",
        replace_existing=True
    )

    scheduler.start()
    print(f"✅ Планировщик запущен. Проверка каждые {CHECK_INTERVAL_HOURS} часов")