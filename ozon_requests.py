import requests
import json
import datetime
import os
from pypdf import PdfReader
import logging


# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Возвращает offer_id товаров
def get_ids():
    """
    Получает список товаров с Ozon API.

    :return: Словарь с информацией о товарах
    """
    headers = {
        "Client-Id": "[Your Client-ID]",
        "Api-Key": "[Your Api-Key]",
        "last_id": "",
        "limit": '100'
    }
    url = 'https://api-seller.ozon.ru/v2/product/list'
    try:
        res = requests.post(url, headers=headers)
        res.raise_for_status()  # Проверка успешности запроса
        res_t = res.json()
        return res_t
    except requests.RequestException as e:
        logging.error(f"Ошибка при запросе списка товаров: {e}")
        return {}


# Возвращает информацию о товарах
def get_info(i):
    """
    Получает информацию о товаре по offer_id и product_id.

    :param i: Словарь с offer_id и product_id товара
    :return: Словарь с информацией о товаре
    """
    offer = i['offer_id'].encode('utf-8')
    product = i['product_id']
    headers = {
        "Client-Id": "[Your Client-ID]",
        "Api-Key": "[Your Api-Key]"
    }
    data = {
        "offer_id": f"{offer.decode('utf-8')}",
        "product_id": f"{product}",
        "filter": '',
        "sku": "0"
    }
    url = 'https://api-seller.ozon.ru/v2/product/info'
    try:
        res = requests.post(url, headers=headers, json=data)
        res.raise_for_status()  # Проверка успешности запроса
        res_info = res.json()
        return res_info
    except requests.RequestException as e:
        logging.error(f"Ошибка при запросе информации о товаре: {e}")
        return {}


# Возвращает информацию о заказах
def get_fbs():
    """
    Получает информацию о незавершенных заказах с Ozon API.

    :return: Словарь с информацией о заказах
    """
    time = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
    headers = {
        "Client-Id": "[Your Client-ID]",
        "Api-Key": "[Your Api-Key]"
    }
    data = {
        "dir": "ASC",
        "filter": {
            "status": "awaiting_deliver",
            "cutoff_from": f"{time}T14:15:22Z",
            "cutoff_to": "2205-08-31T14:15:22Z"
        },
        "with": {
            "analytics_data": True,
            "barcodes": True,
            "financial_data": True,
            "translit": True
        },
        "limit": '100',
        "offset": '0'
    }
    url = 'https://api-seller.ozon.ru/v3/posting/fbs/unfulfilled/list'
    try:
        res = requests.post(url, headers=headers, json=data)
        res.raise_for_status()  # Проверка успешности запроса
        res_fbs = res.json()
        return res_fbs
    except requests.RequestException as e:
        logging.error(f"Ошибка при запросе информации о заказах: {e}")
        return {}


# Возвращает комиссию по номеру заказа
def commis(posting_number):
    """
    Получает информацию о комиссии по номеру заказа.

    :param posting_number: Номер заказа
    :return: Словарь с информацией о комиссии
    """
    headers = {
        "Client-Id": "[Your Client-ID]",
        "Api-Key": "[Your Api-Key]"
    }
    data = {
        "posting_number": f"{posting_number}",
        "transaction_type": "all"
    }
    url = 'https://api-seller.ozon.ru/v3/finance/transaction/totals'
    try:
        res = requests.post(url, headers=headers, json=data)
        res.raise_for_status()  # Проверка успешности запроса
        res_com = res.json()
        return res_com
    except requests.RequestException as e:
        logging.error(f"Ошибка при запросе информации о комиссии: {e}")
        return {}


# Получает адрес и id заказчика с этикетки
def address_maker(posting_number):
    """
    Получает адрес и ID заказчика по номеру заказа.

    :param posting_number: Номер заказа
    :return: Строка с адресом и ID заказчика
    """
    headers = {
        "Client-Id": "[Your Client-ID]",
        "Api-Key": "[Your Api-Key]"
    }
    data = {
        "posting_number": [f"{posting_number}"]
    }
    url = 'https://api-seller.ozon.ru/v2/posting/fbs/package-label'
    try:
        res = requests.post(url, headers=headers, json=data)
        res.raise_for_status()  # Проверка успешности запроса
        with open('metadata.pdf', 'wb') as fd:
            for chunk in res.iter_content(2000):
                fd.write(chunk)
        reader = PdfReader('metadata.pdf')
        page = reader.pages[0]
        address = page.extract_text().replace('\n', ' ')
        os.remove("metadata.pdf")
        return address
    except requests.RequestException as e:
        logging.error(f"Ошибка при запросе этикетки: {e}")
        return ""
    except Exception as e:
        logging.error(f"Ошибка при обработке PDF: {e}")
        return ""


# Формирует массив с заказами для БД
def order_maker(order, res_t):
    """
    Формирует массив с заказами для сохранения в базе данных.

    :param order: Словарь с информацией о заказе
    :param res_t: Словарь с информацией о товарах
    :return: Список заказов в формате массива
    """
    products = order.get('products', [])
    order_arr = []

    for product in products:
        arr = [
            order.get('order_id'),
            order.get('posting_number'),
            order.get('shipment_date', '')[:10],
            product.get('price', 0),
            product.get('quantity', 0),
            product.get('quantity', 0) * float(product.get('price', 0))
        ]

        # Найти product_id по offer_id
        offer_id = product.get('offer_id')
        product_id = None
        for item in res_t.get('result', {}).get('items', []):
            if item.get('offer_id') == offer_id:
                product_id = item.get('product_id')
                break
        arr.append(product_id)

        # Получить адрес и идентифицировать его
        address = address_maker(order.get('posting_number', ''))
        ind = address.find('|') + 1

        for idx in range(len(address) - 10):
            if address[idx] == ' ' and address[idx + 5] == ' ' and address[idx + 1:idx + 5].isdigit() and \
                    address[idx + 6].isdigit():
                ind = idx
                break

        arr.append(address[ind + 1:ind + 5])

        ind = address.find('|') - 2

        for idx in range(ind, 0, -1):
            if address[idx] == ' ':
                ind = idx
                break

        if 'ПВЗ' in address:
            arr.append(address[address.index('ПВЗ') + 4: ind])
        elif 'КУР' in address:
            arr.append(address[address.index('КУР') + 4: ind])
        else:
            arr.append('')

        order_arr.append(arr)

    return order_arr
