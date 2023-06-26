import sqlite3

# Utwórz połączenie z bazą danych
conn = sqlite3.connect('instance/paw.db')
cursor = conn.cursor()

# Utwórz tabelę 'Note' z wymaganymi kolumnami, jeśli nie istnieje
cursor.execute('''CREATE TABLE IF NOT EXISTS note
                  (id INTEGER PRIMARY KEY,
                   user_id INTEGER,
                   title TEXT,
                   text TEXT,
                   category_id INTEGER,
                   date_added datetime,
                   date_updated datetime,
                   date_ending datetime,
                   sharing_id INTEGER)''')
print("Stworzono tabelę 'note'")
# Przykładowe dane
data = [
    (1, 1, 'Tytuł notatki 1', 'Treść notatki 1', 1, '2023-01-01', '2023-01-02', '2023-01-05', 1),
    (2, 1, 'Tytuł notatki 2', 'Treść notatki 2', 2, '2023-02-01', '2023-02-02', '2023-02-05', 0),
    (3, 2, 'Tytuł notatki 3', 'Treść notatki 3', 1, '2023-03-01', '2023-03-02', '2023-03-05', 1)
]

# Wstaw dane do tabeli 'Note'
cursor.executemany('INSERT INTO note VALUES (?,?,?,?,?,?,?,?,?)', data)

# Zatwierdź zmiany
conn.commit()

# Wyświetl potwierdzenie wykonania operacji
print("Operacja wstawiania danych do tabeli 'note' została wykonana.")

# Zamknij połączenie z bazą danych
conn.close()

# Wyświetl potwierdzenie zamknięcia połączenia
print("Połączenie z bazą danych zostało zamknięte.")