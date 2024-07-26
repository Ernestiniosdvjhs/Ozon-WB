import sqlite3
import ozon_requests


def products_creator():
    # Создает таблицу products, если она не существует.
    conn = sqlite3.connect('database/[database name].db')
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS products(
        product_id INT PRIMARY KEY,
        offer_id VARCHAR(255),
        product_name VARCHAR(255)
    );
    """)
    conn.commit()
    cur.close()
    conn.close()


def products_insert(res_t):
    # Вставляет данные о продуктах в таблицу products.
    conn = sqlite3.connect('database/[database name].db')
    cur = conn.cursor()
    if not cur.execute("""SELECT name FROM sqlite_master 
                    WHERE type = 'table' AND name = 'products'; """).fetchall():
        products_creator()
    for i in res_t['result']['items']:
        values = [i['product_id'], i['offer_id'], ozon_requests.get_info(i)['result']['name']]
        cur.execute("""SELECT EXISTS(SELECT 1 FROM products WHERE product_id = ?)""", [i['product_id']])
        product = cur.fetchone()
        if not product[0]:
            cur.execute("""INSERT INTO products (product_id, offer_id, product_name) VALUES
                (?, ?, ?)
            """, values)
    conn.commit()
    cur.close()
    conn.close()


def products_update(res_t):
    # Обновляет данные о продуктах в таблице products.
    conn = sqlite3.connect('database/[database name].db')
    cur = conn.cursor()
    for i in res_t['result']['items']:
        values = [i['offer_id'], i['product_id']]
        cur.execute("""UPDATE products 
            SET offer_id = ?
            WHERE product_id = ?
        """, values)
    conn.commit()
    cur.close()
    conn.close()


def orders_creator():
    # Создает таблицу orders, если она не существует.
    conn = sqlite3.connect('database/[database name].db')
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS orders(
        order_ind INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id BIGINT,
        posting_number VARCHAR(255),
        shipment_date DATE,
        price DECIMAL(11, 4),
        quantity INT,
        total_price DECIMAL(11, 4),
        commission DECIMAL(11, 4),
        product_id BIGINT,
        client_id VARCHAR(4),
        address VARCHAR(500)
    );
    """)
    conn.commit()
    cur.close()
    conn.close()


def orders_insert(res_t, res_fbs):
    # Вставляет данные о заказах в таблицу orders.
    conn = sqlite3.connect('database/[database name].db')
    cur = conn.cursor()
    if not cur.execute("""SELECT name FROM sqlite_master 
                    WHERE type = 'table' AND name = 'orders'; """).fetchall():
        orders_creator()
    if not cur.execute("""SELECT name FROM sqlite_master 
                    WHERE type = 'table' AND name = 'products'; """).fetchall():
        products_creator()
    nuc = {}
    for i in res_fbs['result']['postings']:
        values_gen = ozon_requests.order_maker(i, res_t)
        for values in values_gen:

            cur.execute("""SELECT EXISTS(SELECT 1 FROM products WHERE product_id = ?)""", [values[6]])
            product = cur.fetchone()
            if not product[0]:
                products_insert(res_t)
            date = values[2][8:10] + '-' + values[2][5:7] + '-' + values[2][:4]

            if date not in nuc:
                nuc[date] = {}
                index = 1

            cur.execute("""SELECT product_name
                FROM products WHERE product_id = ?""", [values[6]])
            name = cur.fetchone()
            cur.execute("""SELECT EXISTS(SELECT 1 FROM orders WHERE order_id = ?)""", [values[0]])
            orders = cur.fetchone()
            if not orders[0]:
                key_name = f"{index} - НОВОЕ - {name[0]} - "
            else:
                key_name = f"{index} - {name[0]} - "
            nuc[date][key_name] = f'Количество: {values[4]}; Номер заказа:  {values[1]}'
            index += 1
            cur.execute("""SELECT * FROM orders WHERE product_id = ? AND order_id = ?""", [values[6], values[0]])
            checker = cur.fetchone()
            if not checker:
                cur.execute("""INSERT INTO orders (order_id, posting_number, shipment_date, price, quantity, 
                total_price, commission, product_id, client_id, address) VALUES (?,?,?,?,?,?,0,?,?,?)""", values)

    conn.commit()
    cur.close()
    conn.close()

    set_commission()
    return nuc


def dropper(table):
    # Удаляет указанную таблицу.
    conn = sqlite3.connect('database/[database name].db')
    cur = conn.cursor()
    cur.execute(f"""DROP TABLE IF EXISTS {table}""")
    conn.commit()
    cur.close()
    conn.close()


def set_commission():
    # Устанавливает комиссию для заказов.
    conn = sqlite3.connect('database/[database name].db')
    cur = conn.cursor()
    num = cur.execute("""SELECT posting_number
        FROM orders WHERE commission = 0""").fetchall()
    for i in num:
        res = ozon_requests.commis(i[0])['result']
        res_2 = res['accruals_for_sale'] + res['sale_commission'] + res['processing_and_delivery'] + \
                res['refunds_and_cancellations'] + res['services_amount'] + res['compensation_amount'] + \
                res['money_transfer'] + res['others_amount']
        cur.execute("""UPDATE orders SET commission = ? WHERE posting_number = ?""", [res_2, i[0]])
    conn.commit()
    cur.close()
    conn.close()
