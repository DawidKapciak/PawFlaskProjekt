import sqlite3

# Utwórz połączenie z bazą danych
conn = sqlite3.connect('instance/paw.db')
cursor = conn.cursor()

# Utwórz tabelę 'Note' z wymaganymi kolumnami, jeśli nie istnieje
cursor.execute('''CREATE TABLE IF NOT EXISTS note
                  (id INTEGER PRIMARY KEY,
                   user TEXT,
                   title TEXT,
                   text TEXT,
                   date_added datetime)''')
print("Stworzono tabelę 'note'")
# Przykładowe dane
data = [
    (1, "dawidkapciak@gmail.com", 'Tytuł notatki 1', 'Treść notatki 1', '2023-01-01'),
    (2, "FlaskPaw@gmail.com", 'Tytuł notatki 2', 'Treść notatki 2', '2023-02-01'),
    (3, "FlaskPaw@gmail.com", 'Tytuł notatki 3', 'Treść notatki 3', '2023-03-01')
]

# Wstaw dane do tabeli 'Note'
cursor.executemany('INSERT INTO note VALUES (?,?,?,?,?)', data)

# Zatwierdź zmiany
conn.commit()

# Wyświetl potwierdzenie wykonania operacji
print("Operacja wstawiania danych do tabeli 'note' została wykonana.")

# Zamknij połączenie z bazą danych
conn.close()

# Wyświetl potwierdzenie zamknięcia połączenia
print("Połączenie z bazą danych zostało zamknięte.")