import secrets
import sqlite3

# Utwórz połączenie z bazą danych
conn = sqlite3.connect('instance/paw.db')
cursor = conn.cursor()

# Utwórz tabelę 'user_info' z wymaganymi kolumnami, jeśli nie istnieje
cursor.execute('''CREATE TABLE IF NOT EXISTS user_info
                  (user_id INTEGER PRIMARY KEY,
                   email TEXT UNIQUE,
                   api_key VARCHAR(16),
                   total_requests INTEGER,
                   last_request_timestamp datetime)''')
print("Stworzono tabelę 'user_info'")


# Utwórz tabelę 'Note' z wymaganymi kolumnami, jeśli nie istnieje
cursor.execute('''CREATE TABLE IF NOT EXISTS note
                  (id INTEGER PRIMARY KEY,
                   user_id INTEGER,
                   title TEXT,
                   text TEXT,
                   date_added datetime,
                   FOREIGN KEY (user_id) REFERENCES user_info(user_id))''')
print("Stworzono tabelę 'note'")

# Przykładowe dane
note_data = [
    (1, 1, 'Tytuł notatki 1', 'Treść notatki 1', '2023-01-01'),
    (2, 2, 'Tytuł notatki 2', 'Treść notatki 2', '2023-02-27'),
    (3, 2, 'Tytuł notatki 3', 'Treść notatki 3', '2023-03-27')
]

user_info_data = [
    (1, 'dawidkapciak@gmail.com', secrets.token_hex(16), 0, '2023-06-27'),
    (2, 'flaskpaw@gmail.com', secrets.token_hex(16), 0, '2023-06-27')
]

# Wstaw dane do tabeli 'Note'
cursor.executemany('INSERT INTO note VALUES (?,?,?,?,?)', note_data)

# Wstaw dane do tabeli 'user_info'
cursor.executemany('INSERT INTO user_info VALUES (?,?,?,?,?)', user_info_data)

# Zatwierdź zmiany
conn.commit()

# Wyświetl potwierdzenie wykonania operacji
print("Operacja wstawiania danych została wykonana.")

# Zamknij połączenie z bazą danych
conn.close()

# Wyświetl potwierdzenie zamknięcia połączenia
print("Połączenie z bazą danych zostało zamknięte.")