import requests
import json

API_URL = "https://app.wialonlocal.online/wialon/ajax.html"


def test_login(login, password):
    """Тестирование логина с разными вариантами"""
    print(f"\n🔍 Тестируем логин: '{login}'")

    params = {
        'svc': 'core/login',
        'params': json.dumps({
            'user': login,
            'password': password,
            'lang': 'ru'
        })
    }

    try:
        response = requests.get(API_URL, params=params, timeout=30)
        data = response.json()

        if 'eid' in data:
            print(f"   ✅ УСПЕХ! SID получен: {data['eid'][:30]}...")
            return True, data['eid']
        else:
            error_msg = {
                1: "Неверный токен",
                2: "Неверный формат",
                3: "Доступ запрещен",
                4: "Сессия не найдена",
                5: "Недостаточно прав",
                6: "Внутренняя ошибка",
                7: "Неверный логин или пароль"
            }
            error_code = data.get('error', 0)
            print(f"   ❌ Ошибка {error_code}: {error_msg.get(error_code, 'Неизвестная ошибка')}")
            return False, None

    except Exception as e:
        print(f"   ❌ Исключение: {e}")
        return False, None


def test_login_with_domain(login, password, domain=""):
    """Тестирование логина с доменом"""
    if domain:
        full_login = f"{domain}\\{login}"
        print(f"\n🔍 Тестируем логин с доменом: '{full_login}'")
        return test_login(full_login, password)
    return False, None


if __name__ == "__main__":
    print("=" * 60)
    print("Диагностика авторизации Wialon")
    print("=" * 60)
    print("\nВНИМАНИЕ: Сначала проверьте вход через браузер!")
    print("URL: https://app.wialonlocal.online/login.html")
    print("=" * 60)

    # Введите данные
    login = input("\nВведите логин от Wialon: ").strip()
    password = input("Введите пароль от Wialon: ").strip()

    # Проверяем разные варианты
    print("\n" + "=" * 60)
    print("Тестирование различных вариантов входа")
    print("=" * 60)

    # Вариант 1: Как есть
    success, sid = test_login(login, password)

    # Вариант 2: Если есть домен (например, для Active Directory)
    if not success:
        domain = input(
            "\nЛогин не подошел. Есть ли домен? (например: domain\\user)\nВведите домен или оставьте пустым: ").strip()
        if domain:
            success, sid = test_login_with_domain(login, password, domain)

    # Вариант 3: Может быть email вместо логина
    if not success:
        print("\n❓ Возможно, используется email в качестве логина?")
        email = input("Введите email (если отличается): ").strip()
        if email:
            success, sid = test_login(email, password)

    if success:
        print("\n" + "=" * 60)
        print("✅ Авторизация успешна!")
        print("=" * 60)

        # Получаем токен
        print("\n🔑 Получаем токен...")
        params = {
            'svc': 'core/get_token',
            'params': json.dumps({}),
            'sid': sid
        }

        try:
            response = requests.get(API_URL, params=params, timeout=30)
            data = response.json()

            if 'token' in data:
                token = data['token']
                print(f"\n✅ Токен получен!")
                print(f"📝 Добавьте в .env файл:")
                print(f"WIALON_TOKEN={token}")
                print(f"\nИли используйте логин/пароль в .env:")
                print(f"WIALON_LOGIN={login}")
                print(f"WIALON_PASSWORD={password}")

                # Сохраняем токен в файл
                with open('token.txt', 'w') as f:
                    f.write(token)
                print(f"\n✅ Токен сохранен в token.txt")
            else:
                print(f"❌ Ошибка получения токена: {data}")
        except Exception as e:
            print(f"❌ Ошибка: {e}")
    else:
        print("\n" + "=" * 60)
        print("❌ Не удалось авторизоваться")
        print("=" * 60)
        print("\nВозможные причины:")
        print("1. Неверный логин или пароль")
        print("2. Для Wialon используется другой логин (возможно email)")
        print("3. Требуется двухфакторная авторизация")
        print("4. Доступ ограничен IP-адресами")
        print("5. Учетная запись заблокирована")
        print("\nРекомендации:")
        print("- Проверьте вход через браузер: https://app.wialonlocal.online/login.html")
        print("- Убедитесь, что у вас есть права доступа к API")
        print("- Обратитесь к администратору Wialon для проверки учетной записи")