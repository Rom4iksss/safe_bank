import sqlite3
from decimal import Decimal, ROUND_HALF_EVEN

DB_NAME = "bank.db"

def init_db():
    """Создает таблицы. Баланс храним как TEXT для точности Decimal."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            account_number INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            balance TEXT NOT NULL DEFAULT '0.00'
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_acc INTEGER,
            receiver_acc INTEGER,
            amount TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(sender_acc) REFERENCES users(account_number),
            FOREIGN KEY(receiver_acc) REFERENCES users(account_number)
        )
    ''')
    conn.commit()
    conn.close()

def create_user(name, initial_deposit_str):
    """Создает клиента. Принимает сумму как СТРОКУ и округляет по-банковски."""
    deposit = Decimal(initial_deposit_str).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (name, balance) VALUES (?, ?)", (name, str(deposit)))
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return new_id

def get_user_balance(account_number):
    """Возвращает имя и баланс в формате Decimal."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT name, balance FROM users WHERE account_number = ?", (account_number,))
    result = cursor.fetchone()
    conn.close()
    if result:
        name, balance_str = result
        return name, Decimal(balance_str)
    return None

def transfer_money(sender_acc, receiver_acc, amount_str):
    """Безопасный перевод денег с использованием Decimal и транзакций SQLite."""
    amount = Decimal(amount_str).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        cursor.execute("BEGIN TRANSACTION;")
        
        # 1. Проверяем баланс отправителя (берём первый элемент кортежа [0])
        cursor.execute("SELECT balance FROM users WHERE account_number = ?", (sender_acc,))
        sender_res = cursor.fetchone()
        if not sender_res:
            raise ValueError("Das Konto des Absenders wurde nicht gefunden.")
            
        sender_balance = Decimal(sender_res[0]) # <--- ИСПРАВЛЕНО: берём строку из кортежа
        if sender_balance < amount:
            raise ValueError("Das Guthaben auf dem Konto reicht nicht aus.")
            
        # 2. Проверяем существование получателя
        cursor.execute("SELECT balance FROM users WHERE account_number = ?", (receiver_acc,))
        receiver_res = cursor.fetchone()
        if not receiver_res:
            raise ValueError("Das Konto des Empfängers wurde nicht gefunden.")
            
        receiver_balance = Decimal(receiver_res[0]) # <--- ИСПРАВЛЕНО для надежности
        
        # 3. Вычисляем новые балансы
        new_sender_balance = sender_balance - amount
        new_receiver_balance = receiver_balance + amount
        
        # 4. Обновляем данные в БД
        cursor.execute(
            "UPDATE users SET balance = ? WHERE account_number = ?", 
            (str(new_sender_balance), sender_acc)
        )
        cursor.execute(
            "UPDATE users SET balance = ? WHERE account_number = ?", 
            (str(new_receiver_balance), receiver_acc)
        )
        
        # 5. Записываем транзакцию в историю
        cursor.execute(
            "INSERT INTO transactions (sender_acc, receiver_acc, amount) VALUES (?, ?, ?)",
            (sender_acc, receiver_acc, str(amount))
        )
        
        conn.commit()
        return True, "Die Überweisung wurde erfolgreich abgeschlossen."
        
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()


