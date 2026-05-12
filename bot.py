import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from aiogram.enums import ParseMode
from aiogram.client.session.aiohttp import AiohttpSession
import aiohttp

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_PROXY_URL
from handlers import maintenance
from utils.scheduler import setup_scheduler

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def set_bot_commands(bot: Bot):
    """Установка команд бота"""
    commands = [
        BotCommand(command="start", description="🚀 Запустить бота"),
        BotCommand(command="menu", description="📋 Главное меню"),
        BotCommand(command="check_all", description="📊 Показать все ТС"),
        BotCommand(command="overdue", description="⚠️ Показать просроченные ТО"),
        BotCommand(command="search", description="🔍 Поиск ТС"),
        BotCommand(command="refresh", description="🔄 Обновить данные"),
    ]
    await bot.set_my_commands(commands)


async def main():
    """Запуск бота"""
    # Проверка наличия токена
    if not TELEGRAM_BOT_TOKEN:
        logger.error("❌ TELEGRAM_BOT_TOKEN не найден в .env файле")
        return

    # Настройка сессии с прокси (только для Telegram)
    if TELEGRAM_PROXY_URL:
        logger.info(
            f"✅ Использую прокси для Telegram: {TELEGRAM_PROXY_URL.split('@')[-1] if '@' in TELEGRAM_PROXY_URL else TELEGRAM_PROXY_URL}")

        # Простой вариант - только прокси
        session = AiohttpSession(proxy=TELEGRAM_PROXY_URL)
        bot = Bot(token=TELEGRAM_BOT_TOKEN, session=session, parse_mode=ParseMode.HTML)
    else:
        logger.info("⚠️ Прокси не настроен, работаем напрямую")
        bot = Bot(token=TELEGRAM_BOT_TOKEN, parse_mode=ParseMode.HTML)

    dp = Dispatcher()

    # Регистрация роутеров
    dp.include_router(maintenance.router)

    try:
        # Установка команд
        await set_bot_commands(bot)

        # Запуск планировщика
        setup_scheduler(bot)

        logger.info("✅ Бот запущен и готов к работе!")

        # Запуск поллинга
        await dp.start_polling(bot)

    except Exception as e:
        logger.error(f"❌ Ошибка при запуске бота: {e}")
        raise
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())