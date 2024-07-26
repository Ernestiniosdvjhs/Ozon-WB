import pygsheets
import pandas as pd
import sqlite3
import openpyxl

# Авторизация в Google Sheets
client = pygsheets.authorize(service_account_file="[Your Json file]")


def orders_table():
    # Извлечение данных из базы данных SQLite
    new_df = pd.read_sql(
        """
        SELECT orders.shipment_date AS 'Дата', 
               products.product_name AS 'Изделие', 
               products.characteristic AS 'Характеристика', 
               orders.price AS 'Цена', 
               orders.quantity AS 'Количество', 
               total_price AS 'Общая цена', 
               commission AS 'Комиссия',
               orders.posting_number AS 'Номер заказа', 
               client_id AS 'ID заказчика', 
               address AS 'Адрес'
        FROM orders 
        LEFT JOIN products ON orders.product_id = products.product_id
        """,
        sqlite3.connect("database/stoliarnaja_masterskaja.db")
    )

    # Преобразование даты в формат datetime и удаление времени
    new_df['Дата'] = pd.to_datetime(new_df['Дата'], format='%Y-%m-%d').dt.strftime('%Y-%m-%d')

    # Добавление "ID:" перед номером ID заказчика
    new_df['ID заказчика'] = 'ID:' + new_df['ID заказчика'].astype(str)

    # Группировка данных по месяцам
    new_df['Месяц'] = pd.to_datetime(new_df['Дата']).dt.to_period('M')
    grouped = new_df.groupby('Месяц')

    # Создание нового DataFrame для хранения результатов
    result_df = pd.DataFrame()

    for month, group in grouped:
        # Добавление названия месяца перед данными
        month_name = month.strftime("%B %Y")
        result_df = pd.concat([result_df, pd.DataFrame({
            'Дата': [f'{month_name}'],
            'Цена': [''],
            'Количество': [''],
            'Общая цена': [''],
            'Комиссия': [''],
            'Изделие': [''],
            'Характеристика': [''],
            'Номер заказа': [''],
            'ID заказчика': [''],
            'Адрес': ['']
        })])

        result_df = pd.concat([result_df, group])

        # Создание строки с количеством для каждого типа изделий
        quantity_summary = ''
        for product_name, quantity in group.groupby('Изделие')['Количество'].sum().items():
            quantity_summary += f"{product_name} - {quantity} шт\n"

        total_price = group['Общая цена'].sum()
        total_commission = group['Комиссия'].sum()
        price_commission_diff = total_price - total_commission
        price_commission_diff_percentage = (price_commission_diff / total_price) * 100 if total_price != 0 else 0

        result_df = pd.concat([result_df, pd.DataFrame({
            'Дата': [f'Итого за {month_name}'],
            'Цена': [''],
            'Количество': [quantity_summary.strip()],
            'Общая цена': [total_price],
            'Комиссия': [total_commission],
            'Изделие': [''],
            'Характеристика': [''],
            'Номер заказа': [''],
            'ID заказчика': [''],
            'Адрес': ['']
        })])

        result_df = pd.concat([result_df, pd.DataFrame({
            'Дата': [''],
            'Цена': [''],
            'Количество': [''],
            'Общая цена': [''],
            'Комиссия': [f'Процент комиссии: {price_commission_diff_percentage:.2f}%'],
            'Изделие': [''],
            'Характеристика': [''],
            'Номер заказа': [''],
            'ID заказчика': [''],
            'Адрес': ['']
        })])

        # Добавление пустой строки для отступа
        result_df = pd.concat([result_df, pd.DataFrame({col: [''] for col in result_df.columns})])

    # Удаление временного столбца 'Месяц'
    result_df = result_df.drop(columns=['Месяц'])

    # Сохранение данных в Excel-файл на диск
    result_df.to_excel("tables/Заказы_OZON.xlsx", index=False)

    # Открытие Google Sheet
    sheet = client.open("Заказы_OZON")  # Укажите название вашей таблицы Google Sheets
    worksheet = sheet[0]  # Выбор первого листа в таблице

    # Обновление данных в Google Sheet
    worksheet.clear()  # Очистка существующих данных
    worksheet.set_dataframe(result_df, (1, 1))  # Запись новых данных начиная с ячейки A1

    return sheet.url
