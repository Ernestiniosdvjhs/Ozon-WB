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
        SELECT orders.create_date AS 'Дата', 
               products.product_name AS 'Изделие', 
               products.characteristic AS 'Характеристика', 
               orders.quantity AS 'Количество', 
               orders.price AS 'Цена', 
               orders.order_id AS 'Номер заказа', 
               orders.orderUid AS 'Номер сборки'
        FROM orders 
        LEFT JOIN products ON orders.nmID = products.nmID
        """,
        sqlite3.connect("database/wb_stoliarnaja_masterskaja.db")
    )

    # Преобразование даты в формат datetime и удаление времени
    new_df['Дата'] = pd.to_datetime(new_df['Дата'], format='%Y-%m-%d').dt.strftime('%Y-%m-%d')

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
            'Дата отправки': [''],
            'Цена': [''],
            'Количество': [''],
            'Изделие': [''],
            'Характеристика': [''],
            'Номер заказа': [''],
            'Номер сборки': ['']
        })])

        result_df = pd.concat([result_df, group])

        # Создание строки с количеством для каждого типа изделий
        quantity_summary = ''
        for product_name, quantity in group.groupby('Изделие')['Количество'].sum().items():
            quantity_summary += f"{product_name} - {quantity} шт\n"

        total_price = group['Цена'].sum()

        result_df = pd.concat([result_df, pd.DataFrame({
            'Дата': [f'Итого за {month_name}'],
            'Дата отправки': [''],
            'Цена': [total_price],
            'Количество': [quantity_summary.strip()],
            'Изделие': [''],
            'Характеристика': [''],
            'Номер заказа': [''],
            'Номер сборки': ['']
        })])

        # Добавление пустой строки для отступа
        result_df = pd.concat([result_df, pd.DataFrame({col: [''] for col in result_df.columns})])

    # Удаление временного столбца 'Месяц'
    result_df = result_df.drop(columns=['Месяц'])

    # Сохранение данных в Excel-файл на диск
    result_df.to_excel("tables/Заказы_WB.xlsx", index=False)

    # Открытие Google Sheet
    sheet = client.open("Заказы_WB")  # Укажите название вашей таблицы Google Sheets
    worksheet = sheet[0]  # Выбор первого листа в таблице

    # Обновление данных в Google Sheet
    worksheet.clear()  # Очистка существующих данных
    worksheet.set_dataframe(result_df, (1, 1))  # Запись новых данных начиная с ячейки A1

    # Получение ссылки на Google Sheets
    sheet_url = sheet.url
    return sheet.url
