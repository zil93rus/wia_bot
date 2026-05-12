import requests
import json

# Конфигурация
WIALON_HOST = "https://app.wialonlocal.online"
API_URL = f"{WIALON_HOST}/wialon/ajax.html"

# Введите свои данные
LOGIN = "Groskranadm"
PASSWORD = "112233Qwerty!@#"


def test_login():
    print("=" * 60)
    print("Тестирование авторизации Wialon")
    print("=" * 60)

    # Шаг 1: Логин
    print(f"\n1️⃣ Логин с пользователем: {LOGIN}")
    params = {
        'svc': 'core/login',
        'params': json.dumps({
            'user': LOGIN,
            'password': PASSWORD,
            'lang': 'ru'
        })
    }

    try:
        response = requests.get(API_URL, params=params, timeout=30)
        data = response.json()

        if 'eid' in data:
            sid = data['eid']
            print(f"   ✅ SID получен: {sid[:30]}...")

            # Шаг 2: Получение токена
            print("\n2️⃣ Получение токена...")
            params2 = {
                'svc': 'core/get_token',
                'params': json.dumps({}),
                'sid': sid
            }

            response2 = requests.get(API_URL, params=params2, timeout=30)
            data2 = response2.json()

            if 'token' in data2:
                token = data2['token']
                print(f"   ✅ Токен получен: {token[:50]}...")
                print(f"\n📝 Сохраните этот токен в .env:")
                print(f"WIALON_TOKEN={token}")
                return token
            else:
                print(f"   ❌ Ошибка получения токена: {data2}")
                return None
        else:
            print(f"   ❌ Ошибка логина: {data}")
            return None

    except Exception as e:
        print(f"   ❌ Исключение: {e}")
        return None


def test_token(token):
    """Тестирование полученного токена"""
    print("\n3️⃣ Тестирование токена...")

    params = {
        'svc': 'token_login',
        'params': json.dumps({
            'token': token,
            'flags': 0
        })
    }

    try:
        response = requests.get(API_URL, params=params, timeout=30)
        data = response.json()

        if 'eid' in data:
            print("   ✅ Токен работает!")
            return True
        else:
            print(f"   ❌ Токен не работает: {data}")
            return False
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return False


if __name__ == "__main__":
    token = test_login()
    if token:
        test_token(token)