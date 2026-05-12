# test_token_correct.py
import requests
import json

TOKEN = "2f4aeb08147209d2b5b436f334dc361d1EE59B26EE8B4AA1114528C0A72FF07234D34D95"
API_URL = "https://app.wialonlocal.online/wialon/ajax.html"

print(f"🔍 Тестируем токен через правильный метод token/login...")

params = {
    'svc': 'token/login',  # ← правильный метод
    'params': json.dumps({
        'token': TOKEN
    })
}

response = requests.get(API_URL, params=params)
data = response.json()

print(f"📦 Ответ: {data}")

if 'eid' in data:
    print(f"\n✅ Токен работает!")
    print(f"SID: {data['eid']}")
    print(f"Пользователь: {data.get('user', {}).get('nm', 'Unknown')}")

    # Пробуем получить список ТС
    sid = data['eid']
    params2 = {
        'svc': 'core/search_items',
        'params': json.dumps({
            'spec': {
                'itemsType': 'avl_unit',
                'propName': 'sys_name',
                'propValueMask': '*',
                'sortType': 'sys_name'
            },
            'force': 1,
            'flags': 1,
            'from': 0,
            'to': 100
        }),
        'sid': sid
    }

    response2 = requests.get(API_URL, params=params2)
    data2 = response2.json()

    if 'items' in data2:
        print(f"\n✅ Найдено ТС: {len(data2['items'])}")
        for item in data2['items'][:5]:
            print(f"   - {item.get('nm', 'Без имени')} (ID: {item['id']})")
    else:
        print(f"\n❌ Ошибка получения ТС: {data2}")
else:
    print(f"\n❌ Ошибка: {data}")