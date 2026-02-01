import sqlite3
import csv

def init_db():
    print("Intitializing database......")
    
    conn = sqlite3.connect('tech_terms.db')
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS terms (
        term_id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT NOT NULL,
        tech_term TEXT NOT NULL,
        def_in_english TEXT,
        def_in_tinglish TEXT,
        def_in_telugu TEXT
    )''')

    cursor.execute('CREATE INDEX IF NOT EXISTS idx_term_name ON terms (tech_term)');

    cursor.execute('''CREATE TABLE IF NOT EXISTS examples (
        term_id INTEGER NOT NULL,
        example1 TEXT NOT NULL,
        example2 TEXT NOT NULL,
        FOREIGN KEY (term_id) REFERENCES terms(term_id) ON DELETE CASCADE
    )''')

    cursor.execute('CREATE INDEX IF NOT EXISTS idx_example_term_id ON examples (term_id)');

    with open('terms.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            print("Inserting in terms........")
            cursor.execute('''INSERT INTO terms (category, tech_term, def_in_english, def_in_tinglish, def_in_telugu) VALUES (?,?,?,?,?)''', (row['category'], row['tech_term'], row['def_in_english'], row['def_in_tinglish'], row['def_in_telugu']))

            term_id = cursor.lastrowid

            print("Inserting examples........")

            cursor.execute('''INSERT INTO examples (term_id, example1, example2) VALUES (?,?,?)''', (term_id, row['example1'], row['example2']))
            
            count = count + 1

    conn.commit()
    conn.close()
    print("Database intialization complete")

if __name__ == '__main__':
    init_db()
