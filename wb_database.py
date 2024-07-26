import sqlite3
import wb_python_requests


def products_creator():
    # Создает таблицу 'products', если она не существует.
    conn = sqlite3.connect('database/[other database name].db')
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS products(
        nmId BIGINT PRIMARY KEY,
        vendorCode VARCHAR(255),
        product_name VARCHAR(255)
    );
    """)
    conn.commit()
    cur.close()
    conn.close()


def products_insert(res_t):
    # Вставляет данные о продуктах в таблицу 'products'.
    conn = sqlite3.connect('database/[other database name].db')
    cur = conn.cursor()
    if not cur.execute("""SELECT name FROM sqlite_master 
                    WHERE type = 'table' AND name = 'products'; """).fetchall():
        products_creator()
    for i in res_t['cards']:
        values = [i['nmID'], i['vendorCode'], i['title']]
        # Убедимся, что запись не существует, перед вставкой
        cur.execute("""INSERT OR IGNORE INTO products (nmId, vendorCode, product_name) VALUES
            (?, ?, ?)
        """, values)
    conn.commit()
    cur.close()
    conn.close()


def products_update(res_t):
    # Обновляет данные о продуктах в таблице 'products'.
    conn = sqlite3.connect('database/[other database name].db')
    cur = conn.cursor()
    for i in res_t['cards']:
        values = [i['vendorCode'], i['nmID']]
        cur.execute("""UPDATE products 
            SET vendorCode = ?
            WHERE nmId = ?
        """, values)
    conn.commit()
    cur.close()
    conn.close()


def orders_creator():
    # Создает таблицу 'orders', если она не существует.
    conn = sqlite3.connect('database/[other database name].db')
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS orders(
        order_id VARCHAR(255),
        orderUid VARCHAR(255),
        price DECIMAL(11, 4),
        quantity INT,
        create_date DATE,
        nmId BIGINT,
        PRIMARY KEY (order_id, orderUid) -- Добавляем PRIMARY KEY, чтобы предотвратить дублирование записей
    );
    """)
    conn.commit()
    cur.close()
    conn.close()


def orders_insert(res_tasks):
    # Вставляет данные о заказах в таблицу 'orders'.
    conn = sqlite3.connect('database/[other database name].db')
    cur = conn.cursor()
    if not cur.execute("""SELECT name FROM sqlite_master 
                    WHERE type = 'table' AND name = 'orders'; """).fetchall():
        orders_creator()
    if not cur.execute("""SELECT name FROM sqlite_master 
                    WHERE type = 'table' AND name = 'products'; """).fetchall():
        products_creator()
    nuc = {}
    nuc_push = {}
    index = 1
    for i in res_tasks['orders']:
        values = wb_python_requests.order_maker(i)

        date = values[3][8:10] + '-' + values[3][5:7] + '-' + values[3][:4]
        if date not in nuc:
            nuc[date] = {}

        cur.execute("""SELECT product_name
            FROM products WHERE nmId = ?""", [values[4]])
        name = cur.fetchone()

        cur.execute("""SELECT EXISTS(SELECT 1 FROM orders WHERE order_id = ? AND orderUid = ?)""",
                    [values[0], values[1]])
        orders = cur.fetchone()
        if not orders[0]:
            key_name = f"{index} - НОВОЕ - {name[0]} - "
            nuc_push[name[0]] = name[1] + '; Количество: 1' + f'; Номер сборочного задания: {values[1]}'
        else:
            key_name = f"{index} - {name[0]} - "

        nuc[date][key_name] = name[1] + '; Количество: 1' + f'; Номер сборочного задания: {values[1]}'
        index += 1

        if not orders[0]:
            cur.execute("""INSERT INTO orders (order_id, orderUid, price, quantity, create_date, nmId) 
            VALUES (?, ?, ?, 1, ?, ?)""", values)
    conn.commit()
    cur.close()
    conn.close()
    return nuc, nuc_push


def dropper(table):
    # Удаляет указанную таблицу.
    conn = sqlite3.connect('database/[other database name].db')
    cur = conn.cursor()
    cur.execute(f"""DROP TABLE IF EXISTS {table}""")
    conn.commit()
    cur.close()
    conn.close()
