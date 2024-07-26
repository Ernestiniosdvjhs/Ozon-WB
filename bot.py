import logging
import telebot
import threading
import schedule
from time import sleep
from telebot import types

import wb_python_requests
import wb_database
import wb_table
import ozon_requests
import ozon_database
import ozon_table

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Токен Telegram
token = "[Your Telegram token]"
bot = telebot.TeleBot(token)


def format_user_choices(user_choices):
    # Форматирует выборы пользователя для отображения.
    # :param user_choices: Словарь с выбором пользователя
    # :return: Список строк с форматированным текстом
    formatted_list = []
    for choice, details in user_choices.items():
        formatted_str = f"{choice}\n"
        for key, value in details.items():
            formatted_str += f"{key}: {value}\n"
        formatted_list.append(formatted_str)
    return formatted_list


def format_wb_choices(user_choices):
    # Форматирует выборы пользователя для Wildberries.
    # :param user_choices: Словарь с выбором пользователя
    # :return: Список строк с форматированным текстом
    formatted_list = []
    for choice, detail in user_choices.items():
        formatted_list.append(f"{choice}: {detail}\n")
    return formatted_list


def send_wb_tasks():
    # Отправляет задачи Wildberries в Telegram.
    try:
        tasks = wb_python_requests.get_tasks(wb_python_requests.python_API)
        formatted_tasks = format_wb_choices(wb_database.orders_insert(tasks)[1])
        if formatted_tasks:
            bot.send_message("[Your chatID]", 'Новые сборочные задания Wildberries:\n')
            for task in formatted_tasks:
                bot.send_message("[Your chatID]", task)
    except Exception as e:
        logging.error("Ошибка при отправке задач Wildberries: %s", e)


def schedule_tasks():
    # Планирует регулярные задачи.
    schedule.every(1).minutes.do(send_wb_tasks)
    schedule.every().day.at("15:00").do(send_wb_tasks)
    schedule.every().day.at("18:00").do(send_wb_tasks)
    while True:
        schedule.run_pending()
        sleep(1)


@bot.message_handler(commands=['start'])
def start(message):
    # Обрабатывает команду /start.
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("/start"))
    markup.add(types.KeyboardButton("🛒Заказы"))
    markup.add(types.KeyboardButton("🔄Обновить артикулы"))
    markup.add(types.KeyboardButton("📋Обновить таблицу"))
    markup.add(types.KeyboardButton("🆆Создать пропуск WB"))
    bot.send_message(message.chat.id, 'Здравствуйте! Нажав на соответствующие кнопки ниже, Вы можете:\n'
                                      '• увидеть доступные на данный момент заказы;\n'
                                      '• обновить артикулы товаров в базе данных;\n'
                                      '• обновить данные о товарах в электронной таблице;\n'
                                      '• оформить пропуск на склад Wildberries.', reply_markup=markup)


@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    # Обрабатывает все сообщения.
    if message.text == "🛒Заказы":
        show_orders(message)
    elif message.text == "🔄Обновить артикулы":
        update_offer_id(message)
    elif message.text == "📋Обновить таблицу":
        update_table(message)
    elif message.text == "🆆Создать пропуск WB":
        create_wb_pass(message)
    elif message.text == "/start":
        start(message)


@bot.message_handler(commands=['wb_pass'])
def process_wb_pass_details(message):
    # Обрабатывает детали для создания пропуска WB.
    answer_choice = message.text.strip().split('\n')
    try:
        wb_python_requests.get_pass(wb_python_requests.python_API, answer_choice)
        bot.send_message(message.chat.id, 'Пропуск успешно оформлен')
    except Exception as e:
        logging.error("Ошибка при оформлении пропуска: %s", e)
        bot.send_message(message.chat.id, 'Не удалось оформить пропуск. Попробуйте повторить запрос позже или проверьте'
                                          ' введенные данные.')


def handle_wb_pass(message):
    # Обрабатывает создание пропуска WB.
    pass_choice = message.text
    if pass_choice == '1':
        try:
            wb_python_requests.get_pass(wb_python_requests.python_API, ['Имя', 'Фамилия', 'Марка машины', 'Номер'])
            bot.send_message(message.chat.id, 'Пропуск успешно оформлен')
        except Exception as e:
            logging.error("Ошибка при оформлении пропуска: %s", e)
            bot.send_message(message.chat.id, 'Не удалось оформить пропуск. Попробуйте повторить запрос позже.')
    elif pass_choice == '2':
        answer = bot.send_message(message.chat.id, 'Введите данные водителя (Имя, Фамилия, Модель машины, Номер машины)'
                                                   ' в следующем формате:\nАлександр\nПетров\nLamborghini\nA456BC123')
        bot.register_next_step_handler(answer, process_wb_pass_details)
    elif pass_choice == '3':
        bot.send_message(message.chat.id, '❌ Действие отменено.')
    else:
        bot.send_message(message.chat.id, 'Некорректный ввод. Введите "1" или "2"')
        create_wb_pass(message)


def create_wb_pass(message):
    # Инициирует процесс создания пропуска WB.
    msg = bot.send_message(message.chat.id, 'Оформить пропуск на:\n1️⃣ Chery Tiggo "Н973ОХ702"\n2️⃣ Другую машину\n3'
                                            '️⃣ Отмена\n(В ответе введите цифру)')
    bot.register_next_step_handler(msg, handle_wb_pass)


@bot.message_handler(commands=['offer_id'])
def process_offer_id_details(message):
    # Обрабатывает обновление артикулов.
    answer_choice = message.text
    if answer_choice == '1':
        try:
            wb_database.products_update(wb_python_requests.get_info(wb_python_requests.python_API))
            bot.send_message(message.chat.id, 'Артикулы успешно обновлены')
        except Exception as e:
            logging.error("Ошибка при обновлении артикулов Wildberries: %s", e)
            bot.send_message(message.chat.id, 'Произошла ошибка при обновлении артикулов.')
    elif answer_choice == '2':
        try:
            ozon_database.products_update(ozon_requests.get_ids())
            bot.send_message(message.chat.id, 'Артикулы успешно обновлены')
        except Exception as e:
            logging.error("Ошибка при обновлении артикулов Ozon: %s", e)
            bot.send_message(message.chat.id, 'Произошла ошибка при обновлении артикулов.')
    elif answer_choice == '3':
        bot.send_message(message.chat.id, '❌ Действие отменено.')
    else:
        bot.send_message(message.chat.id, 'Некорректный ввод. Введите "1" или "2"')
        update_offer_id(message)


def update_offer_id(message):
    # Инициирует процесс обновления артикулов.
    msg = bot.send_message(message.chat.id, 'Обновить артикулы для:\n1️⃣ Wildberries\n2️⃣ Ozon\n3️⃣ Отмена\n'
                                            '(В ответе введите цифру)')
    bot.register_next_step_handler(msg, process_offer_id_details)


@bot.message_handler(commands=['table_up'])
def process_table_update(message):
    # Обрабатывает обновление таблиц.
    answer_choice = message.text
    if answer_choice == '1':
        try:
            sheet_url = wb_table.orders_table()
            bot.send_message(message.chat.id, f'Данные в таблице успешно обновлены: {sheet_url}')
        except Exception as e:
            logging.error("Ошибка при обновлении таблицы Wildberries: %s", e)
            bot.send_message(message.chat.id, 'Произошла ошибка при обновлении данных в таблице.')
    elif answer_choice == '2':
        try:
            sheet_url = ozon_table.orders_table()
            bot.send_message(message.chat.id, f'Данные в таблице успешно обновлены: {sheet_url}')
        except Exception as e:
            logging.error("Ошибка при обновлении таблицы Ozon: %s", e)
            bot.send_message(message.chat.id, 'Произошла ошибка при обновлении данных в таблице.')
    elif answer_choice == '3':
        bot.send_message(message.chat.id, '❌ Действие отменено.')
    else:
        bot.send_message(message.chat.id, 'Некорректный ввод. Введите "1" или "2"')
        update_table(message)


def update_table(message):
    # Инициирует процесс обновления таблиц.
    msg = bot.send_message(message.chat.id, 'Обновить таблицу для:\n1️⃣ Wildberries\n2️⃣ Ozon\n3️⃣ Отмена\n'
                                            '(В ответе введите цифру)')
    bot.register_next_step_handler(msg, process_table_update)


@bot.message_handler(commands=['orders'])
def process_orders_details(message):
    # Обрабатывает запрос заказов.
    answer_choice = message.text
    if answer_choice == '1':
        try:
            user_choices = wb_database.orders_insert(wb_python_requests.get_tasks(wb_python_requests.python_API))[0]
            formatted_choices = format_user_choices(user_choices)
            if formatted_choices:
                bot.send_message(message.chat.id, 'Сборочные задания на данный момент:')
                for choice in formatted_choices:
                    bot.send_message(message.chat.id, choice)
            else:
                bot.send_message(message.chat.id, 'На данный момент заказов нет')
        except Exception as e:
            logging.error("Ошибка при формировании заказов Wildberries: %s", e)
            bot.send_message(message.chat.id, 'Произошла ошибка при формировании заказов.')
    elif answer_choice == '2':
        try:
            user_choices = ozon_database.orders_insert(ozon_requests.get_ids(), ozon_requests.get_fbs())
            formatted_choices = format_user_choices(user_choices)
            if formatted_choices:
                bot.send_message(message.chat.id, 'Заказы на данный момент:')
                for choice in formatted_choices:
                    bot.send_message(message.chat.id, choice)
            else:
                bot.send_message(message.chat.id, 'На данный момент заказов нет')
        except Exception as e:
            logging.error("Ошибка при формировании заказов Ozon: %s", e)
            bot.send_message(message.chat.id, 'Произошла ошибка при формировании заказов.')
    elif answer_choice == '3':
        bot.send_message(message.chat.id, '❌ Действие отменено.')
    else:
        bot.send_message(message.chat.id, 'Некорректный ввод. Введите "1" или "2"')
        show_orders(message)


def show_orders(message):
    # Инициирует процесс отображения заказов.
    msg = bot.send_message(message.chat.id,
                           'Вывести заказы для:\n1️⃣ Wildberries\n2️⃣ Ozon\n3️⃣ Отмена\n(В ответе введите цифру)')
    bot.register_next_step_handler(msg, process_orders_details)


if __name__ == '__main__':
    thread = threading.Thread(target=schedule_tasks)
    thread.start()
    bot.polling(none_stop=True)
