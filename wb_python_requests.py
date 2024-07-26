import requests
import json
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

python_API = "[Your Wildberries API-key]"


def get_info(token):
    """
    Получает информацию о товарах с Wildberries API.
    """
    headers = {
        "Authorization": f"{token}"
    }
    data = {
        "settings": {
            "cursor": {
                "limit": 100
            },
            "filter": {
                "withPhoto": -1
            }
        }
    }
    url = 'https://content-api.wildberries.ru/content/v2/get/cards/list'
    try:
        res = requests.post(url, headers=headers, json=data)
        res.raise_for_status()  # Проверка успешности запроса
        res_info = res.json()
        return res_info
    except requests.RequestException as e:
        logging.error(f"Ошибка при запросе информации о товарах: {e}")
        return {}


def get_tasks(token):
    """
    Получает информацию о сборочных заданиях с Wildberries API.
    """
    headers = {
        "Authorization": f"{token}"
    }
    url = 'https://marketplace-api.wildberries.ru/api/v3/orders/new'
    try:
        res = requests.get(url, headers=headers)
        res.raise_for_status()  # Проверка успешности запроса
        res_tasks = res.json()
        return res_tasks
    except requests.RequestException as e:
        logging.error(f"Ошибка при запросе информации о сборочных заданиях: {e}")
        return {}


def get_item(token, nmID):
    """
    Получает информацию о конкретном товаре по nmID.
    """
    try:
        res_info = get_info(token).get('cards', [])
        for item in res_info:
            if item['nmID'] == nmID:
                return item['title']
    except Exception as e:
        logging.error(f"Ошибка при получении информации о товаре {nmID}: {e}")
    return None


def order_maker(order):
    """
    Формирует список значений для заказа.
    """
    return [
        order.get('rid'),        # Идентификатор заказа
        order.get('orderUid'),   # Уникальный идентификатор заказа
        order.get('price', 0) / 100,  # Цена заказа (в рублях)
        order.get('createdAt', '')[:10],  # Дата создания заказа
        order.get('nmId')        # Идентификатор товара
    ]


def get_pass(token, driver):
    """
    Запрашивает пропуск для водителя.
    """
    headers = {
        "Authorization": f"{token}"
    }
    data = {
        "firstName": driver[0],
        "lastName": driver[1],
        "carModel": driver[2],
        "carNumber": driver[3],
        "officeId": 338
    }
    url = 'https://marketplace-api.wildberries.ru/api/v3/passes'
    try:
        res = requests.post(url, headers=headers, json=data)
        res.raise_for_status()  # Проверка успешности запроса
        res_info = res.json()
        return res_info
    except requests.RequestException as e:
        logging.error(f"Ошибка при запросе пропуска: {e}")
        return {}
