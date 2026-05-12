from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Главное меню"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="📊 Все ТС", callback_data="show_all"),
        InlineKeyboardButton(text="⚠️ Просроченные", callback_data="show_overdue")
    )
    builder.row(
        InlineKeyboardButton(text="🔍 Поиск ТС", callback_data="search_vehicle"),
        InlineKeyboardButton(text="🔄 Обновить", callback_data="refresh")
    )

    return builder.as_markup()


def get_vehicle_actions_keyboard(vehicle_id: str) -> InlineKeyboardMarkup:
    """Клавиатура действий для конкретного ТС"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="📈 Подробнее", callback_data=f"vehicle_details_{vehicle_id}"),
        InlineKeyboardButton(text="🔄 Обновить", callback_data=f"refresh_vehicle_{vehicle_id}")
    )
    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main")
    )

    return builder.as_markup()


def get_search_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для поиска"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="🔍 Поиск по номеру", callback_data="search_by_plate"),
        InlineKeyboardButton(text="🔍 Поиск по имени", callback_data="search_by_name")
    )
    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main")
    )

    return builder.as_markup()