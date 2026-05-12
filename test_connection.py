import asyncio
import requests
from config import WIALON_TOKEN, WIALON_HOST, API_URL, TELEGRAM_BOT_TOKEN, TELEGRAM_PROXY_URL


def test_wialon_connection():
    """Тестирование подключения к Wialon"""
    print("\n🔍 Тестируем подключение к Wialon API...")

    if not WIALON_TOKEN:
        print("❌ WIALON_TOKEN не указан в .env файле")
        return False

    params = {
        'svc': 'token_login',
        'params': f'{{"token":"{WIALON_TOKEN}","flags":0}}'
    }

    try:
        response = requests.get(API_URL, params=params, timeout=10)
        data = response.json()

        if 'eid' in data:
            print(f"✅ Wialon API работает! Получен SID: {data['eid'][:30]}...")
            return True
        else:
            print(f"❌ Ошибка Wialon API: {data.get('error', 'Unknown error')}")
            return False

    except Exception as e:
        print(f"❌ Ошибка подключения к Wialon: {e}")
        return False


async def test_telegram_connection():
    """Тестирование подключения к Telegram через прокси"""
    print("\n🔍 Тестируем подключение к Telegram API...")

    from aiogram import Bot
    from aiogram.client.session.aiohttp import AiohttpSession
    import aiohttp

    if not TELEGRAM_BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN не указан в .env файле")
        return False

    try:
        if TELEGRAM_PROXY_URL:
            print(
                f"Используем прокси: {TELEGRAM_PROXY_URL.split('@')[-1] if '@' in TELEGRAM_PROXY_URL else TELEGRAM_PROXY_URL}")
            timeout = aiohttp.ClientTimeout(total=30)
            session = AiohttpSession(proxy=TELEGRAM_PROXY_URL, timeout=timeout)
            bot = Bot(token=TELEGRAM_BOT_TOKEN, session=session)
        else:
            print("Работаем без прокси")
            bot = Bot(token=TELEGRAM_BOT_TOKEN)

        me = await bot.get_me()
        print(f"✅ Telegram API работает! Бот: @{me.username}")
        await bot.session.close()
        return True

    except Exception as e:
        print(f"❌ Ошибка подключения к Telegram: {e}")
        return False


if __name__ == "__main__":
    print("=" * 50)
    print("Тестирование подключений")
    print("=" * 50)

    # Тестируем Wialon (без прокси)
    wialon_ok = test_wialon_connection()

    # Тестируем Telegram (с прокси)
    telegram_ok = asyncio.run(test_telegram_connection())

    print("\n" + "=" * 50)
    print("Результаты:")
    print(f"Wialon API: {'✅ OK' if wialon_ok else '❌ FAIL'}")
    print(f"Telegram API: {'✅ OK' if telegram_ok else '❌ FAIL'}")
    print("=" * 50)