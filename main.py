import sys
import logging
from decimal import Decimal, InvalidOperation
from database import init_db, create_user, get_user_balance, transfer_money

# Полностью очищаем старые настройки логов, чтобы избежать конфликтов
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

# Создаем новый чистый логгер
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Создаем обработчик для записи в файл и СТРОГО задаем ему кодировку UTF-8
file_handler = logging.FileHandler('bank.log', encoding='utf-8')

# Задаем красивый формат вывода (дата - уровень - сообщение)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Добавляем этот обработчик к нашему логгеру
logger.addHandler(file_handler)


def main():
    # Инициализируем таблицы базы данных при старте
    init_db()
    logging.info("Das Bankensystem Decimal wurde erfolgreich in Betrieb genommen.")
    
    while True:
        print("\n=== NATIONAL LINUX BANK (DECIMAL PRO) ===")
        print("1. Ein neues Konto eröffnen")
        print("2. Kontostand prüfen")
        print("3. Geld überweisen")
        print("4. Beenden")
        
        choice = input("Wählen Sie eine Aktion (1–4): ").strip()
        
        if choice == "1":
            name = input("Geben Sie den Namen des Kunden ein: ").strip()
            if not name:
                print("Fehler: Der Name darf nicht leer sein.")
                continue
                
            deposit_input = input("Geben Sie den Betrag der ersten Rate ein (z. B. 500,00): ").strip()
            try:
                # Проверяем, что введено корректное число
                deposit = Decimal(deposit_input)
                if deposit < 0:
                    print("Fehler: Der Betrag darf nicht negativ sein.")
                    continue
                    
                # Создаем пользователя в БД
                acc_num = create_user(name, deposit_input)
                print(f" Erfolg! Das Konto Nr. {acc_num} für den Kunden {name} wurde angelegt.")
                logging.info(f"Das Konto Nr. {acc_num} ({name}) mit einem Guthaben von {deposit} EUR wurde eingerichtet")
            except InvalidOperation:
                print("Fehler: Falsches Format für den Betrag. Verwenden Sie einen Punkt als Trennzeichen (z. B. 100,50).")
                
        elif choice == "2":
            try:
                acc_num = int(input("Geben Sie die Kontonummer ein: "))
                user_data = get_user_balance(acc_num)
                if user_data:
                    name, balance = user_data
                    print(f"Kunde: {name} | Aktueller Kontostand: {balance} EUR")
                else:
                    print("Fehler: Das Konto wurde nicht gefunden.")
            except ValueError:
                print("Fehler: Die Kontonummer muss eine ganze Zahl sein.")
                
        elif choice == "3":
            try:
                sender = int(input("Geben Sie Ihre Kontonummer ein: "))
                receiver = int(input("Geben Sie die Kontonummer des Empfängers ein: "))
                
                if sender == receiver:
                    print("Fehler: Sie können kein Geld an sich selbst überweisen.")
                    continue
                    
                amount_input = input("Geben Sie den Überweisungsbetrag ein: ").strip()
                
                # Валидация суммы перевода
                amount = Decimal(amount_input)
                if amount <= 0:
                    print("Fehler: Der Überweisungsbetrag muss größer als null sein.")
                    continue
                    
                # Запуск безопасной транзакции перевода денег
                success, message = transfer_money(sender, receiver, amount_input)
                if success:
                    print(f" {message}")
                    logging.info(f"Erfolgreiche Überweisung: Konto {sender} -> Konto {receiver} | Betrag: {amount} EUR")
                else:
                    print(f" Transaktionsfehler: {message}")
                    logging.warning(f"Überweisungsfehler: {sender} -> {receiver} | Grund: {message}")
            except InvalidOperation:
                print("Fehler: Das Format des Überweisungsbetrags ist falsch.")
            except ValueError:
                print("Fehler: Kontonummern müssen aus ganzen Zahlen bestehen.")
                
        elif choice == "4":
            print("Das System wird heruntergefahren. Auf Wiedersehen!")
            logging.info("Der Vorgang wurde vom Benutzer abgeschlossen.")
            sys.exit()
        else:
            print("Fehler: Falscher Menüpunkt. Wählen Sie eine Zahl zwischen 1 und 4.")

if __name__ == "__main__":
    main()

