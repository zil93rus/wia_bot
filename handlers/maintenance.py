import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime

from wialon_parser import load_and_parse_latest_json, refresh_and_load, get_latest_file_info
from keyboards.inline_keyboards import (
    get_main_menu_keyboard,
    get_vehicle_actions_keyboard,
    get_search_keyboard
)

router = Router()


class SearchStates(StatesGroup):
    waiting_for_plate = State()
    waiting_for_name = State()


@router.message(Command("start"))
async def cmd_start(message: Message):
    welcome_text = (
        "🚛 <b>Wialon Бот для мониторинга ТО</b>\n\n"
        "Я слежу за транспортными средствами и сообщаю о необходимости "
        "технического обслуживания по пробегу и моточасам.\n\n"
        "📋 <b>Команды:</b>\n"
        "/menu - Главное меню\n"
        "/check_all - Показать все ТС\n"
        "/overdue - Показать ТС с просроченным ТО\n"
        "/search - Поиск ТС\n"
        "/refresh - Обновить данные\n"
        "/fileinfo - Информация о файле данных"
    )
    await message.answer(welcome_text, parse_mode="HTML", reply_markup=get_main_menu_keyboard())


@router.message(Command("menu"))
async def cmd_menu(message: Message):
    await message.answer("📋 <b>Главное меню</b>", parse_mode="HTML", reply_markup=get_main_menu_keyboard())


@router.message(Command("check_all"))
async def cmd_check_all(message: Message):
    await message.answer("🔍 <b>Получаю информацию о всех транспортных средствах...</b>", parse_mode="HTML")

    parser = load_and_parse_latest_json()

    if not parser:
        await message.answer("❌ Не удалось получить данные о ТС. Нет сохраненных данных от Wialon.")
        return

    vehicles = parser.parse_all_vehicles()

    if not vehicles:
        await message.answer("❌ Не удалось получить данные о ТС.")
        return

    stats = parser.get_statistics()

    # Отправляем статистику
    await message.answer(
        f"📊 <b>Статистика:</b>\n"
        f"   Всего ТС: {stats['total']}\n"
        f"   🚨 Просрочено ТО: {stats['overdue']}\n"
        f"   ⚠️ Скоро ТО: {stats['warning']}\n"
        f"   ✅ В норме: {stats['ok']}",
        parse_mode="HTML"
    )

    # Отправляем все ТС с их сервисами
    await message.answer(f"📋 <b>Список всех ТС ({len(vehicles)} шт.):</b>", parse_mode="HTML")

    for vehicle in vehicles:
        msg = parser.format_vehicle_message(vehicle)
        await message.answer(msg, parse_mode="HTML")
        await asyncio.sleep(0.2)


@router.message(Command("overdue"))
async def cmd_overdue(message: Message):
    await message.answer("🔍 <b>Поиск ТС с просроченным ТО...</b>", parse_mode="HTML")

    parser = load_and_parse_latest_json()

    if not parser:
        await message.answer("❌ Нет данных о ТС")
        return

    vehicles = parser.parse_all_vehicles()
    overdue = [v for v in vehicles if v.get('is_overdue')]

    if not overdue:
        await message.answer("✅ <b>Нет ТС с просроченным ТО!</b>", parse_mode="HTML")
        return

    await message.answer(f"🚨 <b>Найдено {len(overdue)} ТС с просроченным ТО:</b>", parse_mode="HTML")

    for vehicle in overdue:
        msg = parser.format_vehicle_message(vehicle)
        await message.answer(msg, parse_mode="HTML")
        await asyncio.sleep(0.3)


@router.message(Command("search"))
async def cmd_search(message: Message):
    await message.answer("🔍 <b>Введите название или номер ТС для поиска:</b>", parse_mode="HTML")


@router.message(Command("refresh"))
async def cmd_refresh(message: Message):
    msg = await message.answer("🔄 <b>Обновляю данные с сервера Wialon...</b>\n\n"
                               "⏳ Это может занять несколько секунд...",
                               parse_mode="HTML")

    try:
        parser = refresh_and_load()

        if not parser:
            await msg.edit_text("❌ <b>Не удалось обновить данные!</b>\n\n"
                                "Проверьте:\n"
                                "1. Подключение к Wialon\n"
                                "2. Токен авторизации\n"
                                "3. Статус сервера",
                                parse_mode="HTML")
            return

        vehicles = parser.parse_all_vehicles()

        if not vehicles:
            await msg.edit_text("❌ <b>Данные получены, но нет транспортных средств!</b>", parse_mode="HTML")
            return

        first_vehicle = vehicles[0]

        response_text = (
            f"✅ <b>Данные успешно обновлены!</b>\n\n"
            f"📊 <b>Статистика:</b>\n"
            f"   📦 Всего ТС: {len(vehicles)}\n\n"
            f"🔍 <b>Пример (первое ТС):</b>\n"
            f"   🚛 {first_vehicle['name']}\n"
            f"   📊 Пробег: {first_vehicle['current_km']:,.0f} км\n"
            f"   ⏱ Моточасы: {first_vehicle['current_hours']:,.1f} ч\n"
            f"   📋 Сервисов: {len(first_vehicle['services'])}\n\n"
            f"💡 Используйте /check_all для просмотра всех ТС"
        )

        await msg.edit_text(response_text, parse_mode="HTML")

    except Exception as e:
        await msg.edit_text(f"❌ <b>Ошибка при обновлении:</b>\n<code>{str(e)}</code>", parse_mode="HTML")


@router.message(Command("fileinfo"))
async def cmd_fileinfo(message: Message):
    """Показать информацию о текущем файле данных"""
    info = get_latest_file_info()

    if not info:
        await message.answer("❌ Нет файлов с данными")
        return

    response = (
        f"📁 <b>Информация о файле данных:</b>\n\n"
        f"📄 Имя: {info['filename']}\n"
        f"🕐 Создан: {info['created'].strftime('%d.%m.%Y %H:%M:%S')}\n"
        f"💾 Размер: {info['size_kb']:.1f} KB\n"
        f"🚛 ТС в файле: {info['vehicles_count']}\n"
    )

    if info.get('first_vehicle'):
        response += (
            f"\n🔍 <b>Пример (первое ТС):</b>\n"
            f"   Имя: {info['first_vehicle'].get('nm', 'Unknown')}\n"
            f"   Пробег: {info['first_vehicle'].get('cnm_km', 0):,.0f} км\n"
            f"   Моточасы: {info['first_vehicle'].get('cneh', 0):,.1f} ч\n"
        )

    await message.answer(response, parse_mode="HTML")


# Обработка текстовых сообщений для поиска
@router.message(F.text & ~F.text.startswith('/'))
async def handle_search(message: Message):
    query = message.text.strip()

    if len(query) < 2:
        return

    await message.answer(f"🔍 <b>Поиск: {query}</b>", parse_mode="HTML")

    parser = load_and_parse_latest_json()

    if not parser:
        await message.answer("❌ Нет данных для поиска")
        return

    vehicles = parser.parse_all_vehicles()

    # Поиск по имени
    results = []
    query_lower = query.lower()
    for v in vehicles:
        if query_lower in v['name'].lower():
            results.append(v)

    if not results:
        await message.answer("❌ ТС не найдены")
        return

    await message.answer(f"✅ <b>Найдено {len(results)} ТС:</b>", parse_mode="HTML")

    for vehicle in results[:10]:
        msg = parser.format_vehicle_message(vehicle)
        await message.answer(msg, parse_mode="HTML")
        await asyncio.sleep(0.2)

    if len(results) > 10:
        await message.answer(f"... и еще {len(results) - 10} ТС")


# Callback handlers
@router.callback_query(F.data == "show_all")
async def callback_show_all(callback: CallbackQuery):
    await callback.answer()
    await cmd_check_all(callback.message)


@router.callback_query(F.data == "show_overdue")
async def callback_show_overdue(callback: CallbackQuery):
    await callback.answer()
    await cmd_overdue(callback.message)


@router.callback_query(F.data == "refresh")
async def callback_refresh(callback: CallbackQuery):
    await callback.answer("Обновление...")
    await cmd_refresh(callback.message)


@router.callback_query(F.data == "back_to_main")
async def callback_back_to_main(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text("📋 <b>Главное меню</b>", parse_mode="HTML", reply_markup=get_main_menu_keyboard())


@router.callback_query(F.data == "search_vehicle")
async def callback_search_vehicle(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text("🔍 <b>Введите название или номер ТС для поиска:</b>", parse_mode="HTML")