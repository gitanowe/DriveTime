import sqlite3
from datetime import datetime, date
import os
import time
import re

LOGO = r"""
 /$$$$$$$            /$$                  /$$$$$$$$ /$$                        
| $$__  $$          |__/                 |__  $$__/|__/                        
| $$  \ $$  /$$$$$$  /$$ /$$    /$$ /$$$$$$ | $$    /$$ /$$$$$$/$$$$   /$$$$$$ 
| $$  | $$ /$$__  $$| $$|  $$  /$$//$$__  $$| $$   | $$| $$_  $$_  $$ /$$__  $$
| $$  | $$| $$  \__/| $$ \  $$/$$/| $$$$$$$$| $$   | $$| $$ \ $$ \ $$| $$$$$$$$
| $$  | $$| $$      | $$  \  $$$/ | $$_____/| $$   | $$| $$ | $$ | $$| $$_____/
| $$$$$$$/| $$      | $$   \  $/  |  $$$$$$$| $$   | $$| $$ | $$ | $$|  $$$$$$$
|_______/ |__/      |__/    \_/    \_______/|__/   |__/|__/ |__/ |__/ \_______/

"""

# Регистрация адаптеров для дат
sqlite3.register_adapter(date, lambda d: d.isoformat())
sqlite3.register_converter("DATE", lambda s: date.fromisoformat(s.decode()))


# Функция для очистки экрана
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


# Функция для создания базы данных и таблиц, если они не существуют
def create_db():
    conn = sqlite3.connect('drivetimedb.sqlite', detect_types=sqlite3.PARSE_DECLTYPES)
    c = conn.cursor()

    # Создание таблицы для клиентов
    c.execute('''CREATE TABLE IF NOT EXISTS Customer (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        full_name TEXT,
        phone TEXT,
        email TEXT,
        passport TEXT,
        driver_license TEXT
    )''')

    # Создание таблицы для администраторов
    c.execute('''CREATE TABLE IF NOT EXISTS Admin (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )''')

    # Создание таблицы для автомобилей
    c.execute('''CREATE TABLE IF NOT EXISTS Car (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        brand TEXT,
        model TEXT,
        year INTEGER,
        price_per_day REAL,
        is_busy INTEGER DEFAULT 0
    )''')

    # Создание таблицы для аренды
    c.execute('''CREATE TABLE IF NOT EXISTS Rental (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        car_id INTEGER,
        admin_id INTEGER,
        start_date DATE,
        end_date DATE,
        status TEXT,
        total_price REAL,
        FOREIGN KEY (customer_id) REFERENCES Customer(id),
        FOREIGN KEY (car_id) REFERENCES Car(id),
        FOREIGN KEY (admin_id) REFERENCES Admin(id)
    )''')

    # Создание таблицы для обслуживания
    c.execute('''CREATE TABLE IF NOT EXISTS Maintenance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        car_id INTEGER,
        service_date DATE,
        description TEXT,
        cost REAL,
        rental_id INTEGER,
        is_paid INTEGER DEFAULT 0,
        FOREIGN KEY (car_id) REFERENCES Car(id),
        FOREIGN KEY (rental_id) REFERENCES Rental(id)
    )''')

    # Создание таблицы для платежей
    c.execute('''CREATE TABLE IF NOT EXISTS Payment (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rental_id INTEGER,
        amount REAL,
        payment_date DATE,
        FOREIGN KEY (rental_id) REFERENCES Rental(id)
    )''')

    conn.commit()
    return conn


# Функция для вставки тестовых данных, если таблицы пусты
def insert_sample_data(conn):
    c = conn.cursor()

    # Проверка и вставка администраторов
    c.execute("SELECT COUNT(*) FROM Admin")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO Admin (username, password) VALUES ('admin1', 'admin')")
        c.execute("INSERT INTO Admin (username, password) VALUES ('admin2', 'admin')")

    # Проверка и вставка клиентов
    c.execute("SELECT COUNT(*) FROM Customer")
    if c.fetchone()[0] == 0:
        c.execute(
            "INSERT INTO Customer (username, password, full_name, phone, email, passport, driver_license) VALUES ('user1', 'user', 'Иван Иванов', '123456789', 'ivan@example.com', '1234-56789', '12-34-567890')")
        c.execute(
            "INSERT INTO Customer (username, password, full_name, phone, email, passport, driver_license) VALUES ('user2', 'user', 'Мария Петрова', '987654321', 'maria@example.com', '9876-54321', '98-76-543210')")

    # Проверка и вставка автомобилей
    c.execute("SELECT COUNT(*) FROM Car")
    if c.fetchone()[0] == 0:
        cars = [
            ('Porshe', '911', 2023, 8500.0),
            ('Toyota', 'Camry', 2020, 4000.0),
            ('Ford', 'Focus', 2018, 3200.0),
            ('BMW', 'X6 m', 2024, 5000.0),
            ('Audi', 'A4', 2023, 4000.0),
            ('Volkswagen', 'Golf', 2021, 2800.0),
        ]
        for car in cars:
            c.execute("INSERT INTO Car (brand, model, year, price_per_day) VALUES (?, ?, ?, ?)", car)

    conn.commit()


# Функция для симуляции оплаты
def simulate_payment(amount):
    QR = r"""                                                            

        ████████████        █   █  █    ████    ████████████    
        █          █      ███        █████  ██  █          █    
        █  █████   █  ██████     ███   ███████  █   █████  █    
        █  █████   █      ███   ███     ░███    █   █████  █    
        █  █████   █  ██      █████  ██ ██      █   █████  █    
        █          █  ██████            ██████  █          █    
        ████████████  ██  ██  █  ██  ██ ░█  ██  ████████████    
                        █▓      ███    ███  ██                  
          █    █   █  ███▓    █    █    ██    █   ███  ██       
        █     ██      ██  ██  █  ██    █   ███      ████████    
          █   █  ███████    ███  ██████     ███     ██     █    
        █  ████  █   █    █████    █   ███    █   █  █   ███    
        █      █████    ██  █   ███  █████████    █    ██  █    
              █  █   █                 ███      █   █  ███      
        █  ██      █      ███   █       ██  ██      █      █    
          ████████    ███   ███  ██  ██    █  █   █  ██         
          █   █  ████████████████    █▓    ██████   █           
        █  ██    █        ██  █████    █████      ███  ██  █    
           ██      █    ████    ████    ████      █        █    
              ████   █           ███████   ███    █████  █      
        ███   ██████  ███▒  █    ██    █    █████████    █      
                      ██████  █    █       ███      █  █████    
        ████████████    ████    █  █   █   ███  █   █    ███    
        █          █        ███    █   ███████      ███         
        █  █████   █  ████  ███         █████████████    ███    
        █  █████   █                 ██           █  █████      
        █  █████   █      ██  █      █▓    ████      ███████    
        █          █  ████    ███      █   █  █████      ███    
        ████████████            █  █████   ████     █    █      

                                                                """
    print(QR)
    print(f"Оплата по СБП - {amount} рублей")
    input("Перейдите по QR и нажмите Enter после оплаты: ")
    print("Оплата прошла успешно!")
    time.sleep(1)


# Функция для регистрации клиента
def register_customer(conn):
    clear_screen()
    print(LOGO)
    print("\n=== Регистрация клиента ===")
    try:
        username = input("Введите логин: ").strip()
        if not username:
            raise Exception("Поле не может быть пустым")
        password = input("Введите пароль: ").strip()
        if not password:
            raise Exception("Поле не может быть пустым")
        full_name = input("Введите ФИО (через пробел): ").strip()
        if not full_name or full_name.count(' ') != 2:
            raise Exception("Невеврный формат ввода", full_name.count(' '))
        phone = input("Введите телефон: ").strip()
        if not phone or all(x in phone for x in "+1234567890"):
            raise Exception("Невеврный формат ввода")
        email = input("Введите email: ").strip()
        if not email or '@' not in email:
            raise Exception("Невеврный формат ввода")
        passport = input("Введите паспорт (0000-00000): ").strip()
        if not passport:
            raise Exception("Поле не может быть пустым")
        if not re.match(r'^\d{4}-\d{5}$', passport):
            raise Exception("Некорректный формат паспорта")
        driver_license = input("Введите водительское удостоверение (00-00-000000): ").strip()
        if not driver_license:
            raise Exception("Поле не может быть пустым")
        if not re.match(r'^\d{2}-\d{2}-\d{6}$', driver_license):
            raise Exception("Некорректный формат водительского удостоверения")

        c = conn.cursor()
        c.execute(
            "INSERT INTO Customer (username, password, full_name, phone, email, passport, driver_license) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (username, password, full_name, phone, email, passport, driver_license))
        conn.commit()
        print("Регистрация успешна!")
        time.sleep(1)
    except sqlite3.IntegrityError as e:
        clear_screen()
        print(LOGO)
        print("Ошибка: Логин уже существует.")
        time.sleep(1)
    except Exception as e:
        clear_screen()
        print(LOGO)
        print(e)
        time.sleep(1)


# Функция для регистрации администратора
def register_admin(conn):
    clear_screen()
    print(LOGO)
    print("\n=== Регистрация администратора ===")
    try:
        username = input("Введите логин: ").strip()
        if not username:
            raise Exception("Поле не может быть пустым")
        password = input("Введите пароль: ").strip()
        if not password:
            raise Exception("Поле не может быть пустым")

        c = conn.cursor()
        c.execute("INSERT INTO Admin (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        print("Регистрация успешна!")
        time.sleep(1)
    except sqlite3.IntegrityError as e:
        clear_screen()
        print(LOGO)
        print("Ошибка: Логин уже существует.")
        time.sleep(1)
    except Exception as e:
        clear_screen()
        print(LOGO)
        print(f"Ошибка: {e}")
        time.sleep(1)


# Функция для входа клиента
def login_customer(conn):
    clear_screen()
    print(LOGO)
    print("\n=== Вход клиента ===")
    username = input("Введите логин: ")
    password = input("Введите пароль: ")

    try:
        c = conn.cursor()
        c.execute("SELECT id FROM Customer WHERE username = ? AND password = ?", (username, password))
        customer = c.fetchone()
        if customer:
            return customer[0]
        else:
            raise Exception("Неверный логин или пароль.")
    except Exception as e:
        clear_screen()
        print(LOGO)
        print(f"Ошибка: {e}")
        time.sleep(1)
        return None


# Функция для входа администратора
def login_admin(conn):
    clear_screen()
    print(LOGO)
    print("\n=== Вход администратора ===")
    username = input("Введите логин: ")
    password = input("Введите пароль: ")

    try:
        c = conn.cursor()
        c.execute("SELECT id FROM Admin WHERE username = ? AND password = ?", (username, password))
        admin = c.fetchone()
        if admin:
            return admin[0]
        else:
            raise Exception("Неверный логин или пароль.")
    except Exception as e:
        clear_screen()
        print(LOGO)
        print(f"Ошибка: {e}")
        time.sleep(1)
        return None


# Функция для вывода таблицы автомобилей
def print_cars(cars):
    print("\n=== Список автомобилей ===")
    print("{:<5} | {:<10} | {:<10} | {:<4} | {:<10} | {:<10}".format("ID", "Марка", "Модель", "Год", "Цена/сут",
                                                                     "Статус"))
    print("=" * 60)
    for car in cars:
        status = "Занят" if car[5] else "Свободен"
        print(
            "{:<5} | {:<10} | {:<10} | {:<4} | {:<10} | {:<10}".format(car[0], car[1], car[2], car[3], car[4], status))


# Функция для получения доступных автомобилей
def get_available_cars(conn):
    c = conn.cursor()
    c.execute("SELECT * FROM Car WHERE is_busy = 0")
    return c.fetchall()


# Функция для проверки доступности автомобиля на даты
def is_car_available(conn, car_id, start_date, end_date):
    c = conn.cursor()
    c.execute('''SELECT * FROM Rental WHERE car_id = ? AND status IN ('ожидание', 'подтверждена', 'выдана')
                 AND (start_date < ? AND end_date > ?)''', (car_id, end_date, start_date))
    return c.fetchone() is None


# Функция для создания заявки
def create_rental(conn, customer_id):
    clear_screen()
    print(LOGO)
    print("\n=== Создание заявки ===")
    available_cars = get_available_cars(conn)
    if not available_cars:
        print("Нет доступных автомобилей.")
        time.sleep(1)
        return
    print_cars(available_cars)

    try:
        car_id_input = input("Введите ID автомобиля (0 - назад): ")
        if car_id_input == '0':
            return
        car_id = int(car_id_input)
        c = conn.cursor()
        c.execute("SELECT * FROM Car WHERE id = ? AND is_busy = 0", (car_id,))
        if not c.fetchone():
            raise Exception("Автомобиль не существует или занят")

        start_str = input("Введите дату начала (YYYY-MM-DD): ")
        end_str = input("Введите дату окончания (YYYY-MM-DD): ")
        start = datetime.strptime(start_str, '%Y-%m-%d').date()
        end = datetime.strptime(end_str, '%Y-%m-%d').date()

        if end <= start or start < date.today():
            raise Exception("Некорректные даты.")

        if not is_car_available(conn, car_id, start, end):
            raise Exception("Автомобиль занят на эти даты.")

        c.execute("SELECT price_per_day FROM Car WHERE id = ?", (car_id,))
        price = c.fetchone()[0]
        total_price = (end - start).days * price

        simulate_payment(total_price)

        c.execute('''INSERT INTO Rental (customer_id, car_id, admin_id, start_date, end_date, status, total_price)
                     VALUES (?, ?, NULL, ?, ?, 'ожидание', ?)''', (customer_id, car_id, start, end, total_price))
        rental_id = c.lastrowid
        conn.commit()

        c.execute("INSERT INTO Payment (rental_id, amount, payment_date) VALUES (?, ?, ?)",
                  (rental_id, total_price, date.today()))
        conn.commit()
        print("Заявка создана!")
        time.sleep(1)
    except ValueError:
        clear_screen()
        print(LOGO)
        print("Ошибка: Некорректный ввод.")
        time.sleep(1)
    except Exception as e:
        clear_screen()
        print(LOGO)
        print(f"Ошибка: {e}")
        time.sleep(1)


# Функция для вывода таблицы заявок
def print_rentals(rentals, is_admin=False):
    if is_admin:
        print("\n=== Список заявок ===")
        print("{:<5} | {:<10} | {:<10} | {:<10} | {:<10} | {:<10} | {:<10} | {:<10} | {:<15}".format("ID", "Клиент ID",
                                                                                                     "Авто ID",
                                                                                                     "Начало", "Конец",
                                                                                                     "Статус", "Цена",
                                                                                                     "Админ ID",
                                                                                                     "Верификация"))
        print("=" * 118)
        for rental in rentals:
            admin_id = rental[3] if rental[3] else "N/A"
            status = rental[6]
            verification = "Данные подтверждены"
            print("{:<5} | {:<10} | {:<10} | {:<10} | {:<10} | {:<10} | {:<10} | {:<10} | {:<15}".format(rental[0],
                                                                                                         rental[1],
                                                                                                         rental[2],
                                                                                                         str(rental[4]),
                                                                                                         str(rental[5]),
                                                                                                         status,
                                                                                                         rental[7],
                                                                                                         admin_id,
                                                                                                         verification))
    else:
        print("\n=== Список заявок ===")
        print("{:<5} | {:<10} | {:<10} | {:<10} | {:<10} | {:<10}".format("ID", "Авто ID", "Начало", "Конец", "Статус",
                                                                          "Цена"))
        print("=" * 70)
        for rental in rentals:
            status = rental[6]
            print("{:<5} | {:<10} | {:<10} | {:<10} | {:<10} | {:<10}".format(rental[0], rental[2], str(rental[4]),
                                                                              str(rental[5]), status, rental[7]))


# Функция для просмотра своих заявок клиента
def view_my_rentals(conn, customer_id):
    clear_screen()
    print(LOGO)
    c = conn.cursor()
    c.execute("SELECT * FROM Rental WHERE customer_id = ?", (customer_id,))
    rentals = c.fetchall()
    print_rentals(rentals, is_admin=False)
    input("Нажмите Enter для продолжения...")


# Функция для отмены заявки клиента
def cancel_rental(conn, customer_id):
    clear_screen()
    print(LOGO)
    view_my_rentals(conn, customer_id)
    try:
        rental_id_input = input("Введите ID заявки для отмены (0 - назад): ")
        if rental_id_input == '0':
            return
        rental_id = int(rental_id_input)
        c = conn.cursor()
        c.execute("SELECT status FROM Rental WHERE id = ? AND customer_id = ?", (rental_id, customer_id))
        status = c.fetchone()
        if not status:
            raise Exception("Заявка не существует или не ваша")
        if status[0] == 'ожидание':
            c.execute("DELETE FROM Rental WHERE id = ?", (rental_id,))
            conn.commit()
            print("Заявка отменена!")
            time.sleep(1)
        else:
            raise Exception("Заявку нельзя отменить.")
    except Exception as e:
        clear_screen()
        print(LOGO)
        print("Введите корректный айди!")
        time.sleep(1)


# Функция для вывода таблицы штрафов
def print_fines(fines):
    print("\n=== Список штрафов ===")
    print("{:<5} | {:<10} | {:<20} | {:<10}".format("ID", "Авто ID", "Описание", "Стоимость"))
    print("=" * 50)
    for fine in fines:
        print("{:<5} | {:<10} | {:<20} | {:<10}".format(fine[0], fine[1], fine[2], fine[3]))


# Функция для подменю штрафов клиента
def customer_fines_submenu(conn, customer_id):
    while True:
        clear_screen()
        print(LOGO)
        print("\n=== Штрафы ===")
        c = conn.cursor()
        c.execute(
            """SELECT m.id, m.car_id, m.description, m.cost FROM Maintenance m JOIN Rental r ON m.rental_id = r.id WHERE r.customer_id = ? AND m.is_paid = 0""",
            (customer_id,))
        fines = c.fetchall()
        if not fines:
            print("Нет неоплаченных штрафов.")
            input("Нажмите Enter для продолжения...")
            break
        print_fines(fines)
        fine_id_input = input("Введите ID штрафа для оплаты (0 - назад): ")
        if fine_id_input == '0':
            break
        try:
            fine_id = int(fine_id_input)
            c.execute("SELECT cost, rental_id FROM Maintenance WHERE id = ? AND is_paid = 0", (fine_id,))
            selected = c.fetchone()
            if not selected:
                raise Exception("Штраф не существует или уже оплачен")
            cost, rental_id = selected
            simulate_payment(cost)
            c.execute("INSERT INTO Payment (rental_id, amount, payment_date) VALUES (?, ?, ?)",
                      (rental_id, cost, date.today()))
            c.execute("UPDATE Maintenance SET is_paid = 1 WHERE id = ?", (fine_id,))
            conn.commit()
            print("Штраф оплачен!")
            time.sleep(1)
        except Exception as e:
            clear_screen()
            print(LOGO)
            print("Введите корректный айди!")
            time.sleep(1)


# Функция для подменю управления заявками клиента
def customer_rentals_submenu(conn, customer_id):
    while True:
        clear_screen()
        print(LOGO)
        print("\n=== Управление заявками ===")
        print("1. Создать заявку")
        print("2. Отменить заявку")
        print("3. Просмотреть свои заявки")
        print("0. Назад")
        choice = input("Выберите действие: ")

        if choice == '1':
            create_rental(conn, customer_id)
        elif choice == '2':
            cancel_rental(conn, customer_id)
        elif choice == '3':
            view_my_rentals(conn, customer_id)
        elif choice == '0':
            break
        else:
            print("Неверный выбор.")
            time.sleep(1)


# Функция для меню клиента
def customer_menu(conn, customer_id):
    while True:
        clear_screen()
        print(LOGO)
        print("\n=== Меню клиента ===")
        print("1. Просмотреть доступные автомобили")
        print("2. Управление заявками")
        print("3. Штрафы")
        print("0. Выход")
        choice = input("Выберите действие: ")

        if choice == '1':
            clear_screen()
            print(LOGO)
            print_cars(get_available_cars(conn))
            input("Нажмите Enter для продолжения...")
        elif choice == '2':
            customer_rentals_submenu(conn, customer_id)
        elif choice == '3':
            customer_fines_submenu(conn, customer_id)
        elif choice == '0':
            break
        else:
            print("Неверный выбор.")
            time.sleep(1)


# Функция для добавления автомобиля
def add_car(conn):
    clear_screen()
    print(LOGO)
    print("\n=== Добавление автомобиля ===")
    brand = input("Марка: ")
    model = input("Модель: ")
    try:
        year = int(input("Год: "))
        price = float(input("Цена в сутки: "))
        c = conn.cursor()
        c.execute("INSERT INTO Car (brand, model, year, price_per_day) VALUES (?, ?, ?, ?)",
                  (brand, model, year, price))
        conn.commit()
        print("Автомобиль добавлен!")
        time.sleep(1)
    except Exception as e:
        clear_screen()
        print(LOGO)
        print("Вводите числа!")
        time.sleep(1)


# Функция для удаления автомобиля
def delete_car(conn):
    clear_screen()
    print(LOGO)
    print_cars(conn.cursor().execute("SELECT * FROM Car").fetchall())
    try:
        car_id_input = input("Введите ID для удаления (0 - назад): ")
        if car_id_input == '0':
            return
        car_id = int(car_id_input)
        c = conn.cursor()
        c.execute("SELECT * FROM Car WHERE id = ?", (car_id,))
        if not c.fetchone():
            raise Exception("Автомобиль не существует")
        c.execute("DELETE FROM Car WHERE id = ?", (car_id,))
        conn.commit()
        print("Автомобиль удален!")
        time.sleep(1)
    except Exception as e:
        clear_screen()
        print(LOGO)
        print("Введите корректный айди!")
        time.sleep(1)


# Функция для редактирования автомобиля
def edit_car(conn):
    clear_screen()
    print(LOGO)
    print_cars(conn.cursor().execute("SELECT * FROM Car").fetchall())
    try:
        car_id_input = input("Введите ID для редактирования (0 - назад): ")
        if car_id_input == '0':
            return
        car_id = int(car_id_input)
        c = conn.cursor()
        c.execute("SELECT * FROM Car WHERE id = ?", (car_id,))
        if not c.fetchone():
            raise Exception("Автомобиль не существует")
        brand = input("Новая марка (enter для пропуска): ")
        model = input("Новая модель (enter для пропуска): ")
        year_str = input("Новый год (enter для пропуска): ")
        price_str = input("Новая цена (enter для пропуска): ")

        if brand:
            c.execute("UPDATE Car SET brand = ? WHERE id = ?", (brand, car_id))
        if model:
            c.execute("UPDATE Car SET model = ? WHERE id = ?", (model, car_id))
        if year_str:
            c.execute("UPDATE Car SET year = ? WHERE id = ?", (int(year_str), car_id))
        if price_str:
            c.execute("UPDATE Car SET price_per_day = ? WHERE id = ?", (float(price_str), car_id))
        conn.commit()
        print("Автомобиль обновлен!")
        time.sleep(1)
    except Exception as e:
        clear_screen()
        print(LOGO)
        print("Введите корректный айди!")
        time.sleep(1)


# Функция для добавления обслуживания (с опциональным car_id)
def add_maintenance(conn, car_id=None, rental_id=None):
    clear_screen()
    print(LOGO)
    if not car_id:
        print_cars(conn.cursor().execute("SELECT * FROM Car").fetchall())
        try:
            car_id_input = input("Введите ID автомобиля (0 - назад): ")
            if car_id_input == '0':
                return None
            car_id = int(car_id_input)
        except Exception as e:
            clear_screen()
            print(LOGO)
            print("Введите корректный айди!")
            time.sleep(1)
            return None
    try:
        c = conn.cursor()
        c.execute("SELECT * FROM Car WHERE id = ?", (car_id,))
        if not c.fetchone():
            raise Exception("Автомобиль не существует")
        print("\n=== Добавление обслуживания ===")
        service_date = input("Дата обслуживания (YYYY-MM-DD): ")
        description = input("Описание: ")
        cost = float(input("Стоимость: "))
        c.execute("INSERT INTO Maintenance (car_id, service_date, description, cost, rental_id) VALUES (?, ?, ?, ?, ?)",
                  (car_id, datetime.strptime(service_date, '%Y-%m-%d').date(), description, cost, rental_id))
        conn.commit()
        print("Обслуживание добавлено!")
        time.sleep(1)
        return c.lastrowid
    except Exception as e:
        clear_screen()
        print(LOGO)
        print(f"Ошибка: {e}")
        time.sleep(1)
        return None


# Функция для подменю управления автопарком
def admin_cars_submenu(conn):
    while True:
        clear_screen()
        print(LOGO)
        print("\n=== Управление автопарком ===")
        print("1. Просмотреть доступные автомобили")
        print("2. Добавить автомобиль")
        print("3. Удалить автомобиль")
        print("4. Редактировать автомобиль")
        print("5. Добавить обслуживание")
        print("0. Назад")
        choice = input("Выберите действие: ")

        if choice == '1':
            clear_screen()
            print(LOGO)
            print_cars(get_available_cars(conn))
            input("Нажмите Enter для продолжения...")
        elif choice == '2':
            add_car(conn)
        elif choice == '3':
            delete_car(conn)
        elif choice == '4':
            edit_car(conn)
        elif choice == '5':
            add_maintenance(conn)
        elif choice == '0':
            break
        else:
            print("Неверный выбор.")
            time.sleep(1)


# Функция для просмотра всех заявок
def view_all_rentals(conn):
    clear_screen()
    print(LOGO)
    c = conn.cursor()
    c.execute("SELECT * FROM Rental")
    rentals = c.fetchall()
    print_rentals(rentals, is_admin=True)
    input("Нажмите Enter для продолжения...")


# Функция для подтверждения/отклонения заявки
def approve_reject_rental(conn, admin_id):
    clear_screen()
    print(LOGO)
    view_all_rentals(conn)
    try:
        rental_id_input = input("Введите ID заявки (0 - назад): ")
        if rental_id_input == '0':
            return
        rental_id = int(rental_id_input)
        c = conn.cursor()
        c.execute("SELECT status FROM Rental WHERE id = ?", (rental_id,))
        result = c.fetchone()
        if not result:
            raise Exception("Заявка не существует")
        status = result[0]
        if status != 'ожидание':
            raise Exception("Действие недоступно для текущего статуса заявки")
        action = input("Подтвердить (y) или отклонить (n)? ").lower()
        if action == 'y':
            c.execute("UPDATE Rental SET status = 'подтверждена', admin_id = ? WHERE id = ?", (admin_id, rental_id))
            print("Заявка подтверждена!")
        elif action == 'n':
            c.execute("UPDATE Rental SET status = 'отклонена', admin_id = ? WHERE id = ?", (admin_id, rental_id))
            print("Заявка отклонена!")
        else:
            raise Exception("Неверное действие")
        conn.commit()
        time.sleep(1)
    except Exception as e:
        clear_screen()
        print(LOGO)
        print(f"Ошибка: {e}")
        time.sleep(1)


# Функция для отметки issued/returned
def mark_issued_returned(conn):
    clear_screen()
    print(LOGO)
    view_all_rentals(conn)
    try:
        rental_id_input = input("Введите ID заявки (0 - назад): ")
        if rental_id_input == '0':
            return
        rental_id = int(rental_id_input)
        c = conn.cursor()
        c.execute("SELECT status, car_id FROM Rental WHERE id = ?", (rental_id,))
        result = c.fetchone()
        if not result:
            raise Exception("Заявка не существует")
        status, car_id = result
        action = input("Выдать (i) или вернуть (r)? ").lower()
        if action == 'i':
            if status != 'подтверждена':
                raise Exception("Действие недоступно для текущего статуса заявки")
            c.execute("UPDATE Rental SET status = 'выдана' WHERE id = ?", (rental_id,))
            c.execute("UPDATE Car SET is_busy = 1 WHERE id = ?", (car_id,))
            print("Автомобиль выдан!")
        elif action == 'r':
            if status != 'выдана':
                raise Exception("Действие недоступно для текущего статуса заявки")
            c.execute("UPDATE Rental SET status = 'возвращена' WHERE id = ?", (rental_id,))
            c.execute("UPDATE Car SET is_busy = 0 WHERE id = ?", (car_id,))
            print("Автомобиль возвращен!")
            damages = input("Есть повреждения? (y/n): ").lower()
            if damages == 'y':
                maintenance_id = add_maintenance(conn, car_id=car_id, rental_id=rental_id)
                if maintenance_id:
                    c.execute("SELECT cost FROM Maintenance WHERE id = ?", (maintenance_id,))
                    cost = c.fetchone()[0]
                    # Since damage payment is handled in client fines, no add_payment here
        else:
            raise Exception("Неверное действие.")
        conn.commit()
        time.sleep(1)
    except Exception as e:
        clear_screen()
        print(LOGO)
        print(f"Ошибка: {e}")
        time.sleep(1)


# Функция для подменю управления заявками админа
def admin_rentals_submenu(conn, admin_id):
    while True:
        clear_screen()
        print(LOGO)
        print("\n=== Управление заявками ===")
        print("1. Просмотреть все заявки")
        print("2. Подтвердить/отклонить заявку")
        print("3. Отметить выдачу/возврат")
        print("0. Назад")
        choice = input("Выберите действие: ")

        if choice == '1':
            view_all_rentals(conn)
        elif choice == '2':
            approve_reject_rental(conn, admin_id)
        elif choice == '3':
            mark_issued_returned(conn)
        elif choice == '0':
            break
        else:
            print("Неверный выбор.")
            time.sleep(1)


# Функция для регистрации платежа (для админа, если нужно, but removed from menu)
def add_payment(conn, rental_id, amount):
    try:
        c = conn.cursor()
        c.execute("INSERT INTO Payment (rental_id, amount, payment_date) VALUES (?, ?, ?)",
                  (rental_id, amount, date.today()))
        conn.commit()
        print("Платеж зарегистрирован!")
        time.sleep(1)
    except Exception as e:
        clear_screen()
        print(LOGO)
        print(f"Ошибка: {e}")
        time.sleep(1)


# Функция для меню администратора
def admin_menu(conn, admin_id):
    while True:
        clear_screen()
        print(LOGO)
        print("\n=== Меню администратора ===")
        print("1. Управление автопарком")
        print("2. Управление заявками")
        print("3. Добавить обслуживание")
        print("0. Выход")
        choice = input("Выберите действие: ")

        if choice == '1':
            admin_cars_submenu(conn)
        elif choice == '2':
            admin_rentals_submenu(conn, admin_id)
        elif choice == '3':
            add_maintenance(conn)
        elif choice == '0':
            break
        else:
            print("Неверный выбор.")
            time.sleep(1)


# Функция для подменю пользовательского клиента
def user_client_menu(conn):
    while True:
        clear_screen()
        print(LOGO)
        print("\n=== Пользовательский клиент ===")
        print("1. Войти")
        print("2. Зарегистрироваться")
        print("0. Выход")
        choice = input("Выберите действие: ")

        if choice == '1':
            customer_id = login_customer(conn)
            if customer_id:
                customer_menu(conn, customer_id)
        elif choice == '2':
            register_customer(conn)
        elif choice == '0':
            break
        else:
            print("Неверный выбор.")
            time.sleep(1)


# Функция для подменю администраторского клиента
def admin_client_menu(conn):
    while True:
        clear_screen()
        print(LOGO)
        print("\n=== Администраторский клиент ===")
        print("1. Войти")
        print("2. Зарегистрироваться")
        print("0. Выход")
        choice = input("Выберите действие: ")

        if choice == '1':
            admin_id = login_admin(conn)
            if admin_id:
                admin_menu(conn, admin_id)
        elif choice == '2':
            register_admin(conn)
        elif choice == '0':
            break
        else:
            print("Неверный выбор.")
            time.sleep(1)


# Главная функция
def main():
    conn = create_db()
    insert_sample_data(conn)

    while True:
        clear_screen()
        print(LOGO)
        print("\n=== DriveTime - Система учета аренды автомобилей ===")
        print("1. Пользовательский клиент")
        print("2. Администраторский клиент")
        print("0. Выход")
        choice = input("Выберите действие: ")

        if choice == '1':
            user_client_menu(conn)
        elif choice == '2':
            admin_client_menu(conn)
        elif choice == '0':
            break
        else:
            print("Неверный выбор.")
            time.sleep(1)

    conn.close()


if __name__ == "__main__":
    main()