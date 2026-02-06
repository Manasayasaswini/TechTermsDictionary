import csv
import os

# Detect environment
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    # Production: PostgreSQL
    import psycopg2
    DB_TYPE = 'postgresql'
else:
    # Local: SQLite
    import sqlite3
    DB_TYPE = 'sqlite'

def init_db():
    print(f"Initializing database using {DB_TYPE.upper()}......")
    
    if DB_TYPE == 'postgresql':
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS terms (
            term_id SERIAL PRIMARY KEY,
            category TEXT NOT NULL,
            tech_term TEXT NOT NULL,
            def_in_english TEXT,
            def_in_tinglish TEXT,
            def_in_telugu TEXT
        )''')

        cursor.execute('CREATE INDEX IF NOT EXISTS idx_term_name ON terms (tech_term)')

        cursor.execute('''CREATE TABLE IF NOT EXISTS examples (
            term_id INTEGER NOT NULL,
            example1 TEXT,
            example2 TEXT,
            FOREIGN KEY (term_id) REFERENCES terms(term_id) ON DELETE CASCADE
        )''')

        cursor.execute('CREATE INDEX IF NOT EXISTS idx_example_term_id ON examples (term_id)')
        
        # Check if terms.csv exists
        if os.path.exists('terms.csv'):
            with open('terms.csv', 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                count = 0
                for row in reader:
                    print("Inserting in terms........")
                    cursor.execute('''INSERT INTO terms (category, tech_term, def_in_english, def_in_tinglish, def_in_telugu) VALUES (%s,%s,%s,%s,%s) RETURNING term_id''', 
                                   (row['category'], row['tech_term'], row['def_in_english'], row['def_in_tinglish'], row['def_in_telugu']))

                    term_id = cursor.fetchone()[0]

                    print("Inserting examples........")

                    cursor.execute('''INSERT INTO examples (term_id, example1, example2) VALUES (%s,%s,%s)''', 
                                   (term_id, row['example1'], row['example2']))

                    count = count + 1
            print(f"Inserted {count} terms")
        else:
            print("terms.csv not found. Skipping data import.")

    else:
        # SQLite
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

        cursor.execute('CREATE INDEX IF NOT EXISTS idx_term_name ON terms (tech_term)')

        cursor.execute('''CREATE TABLE IF NOT EXISTS examples (
            term_id INTEGER NOT NULL,
            example1 TEXT,
            example2 TEXT,
            FOREIGN KEY (term_id) REFERENCES terms(term_id) ON DELETE CASCADE
        )''')

        cursor.execute('CREATE INDEX IF NOT EXISTS idx_example_term_id ON examples (term_id)')

        if os.path.exists('terms.csv'):
            with open('terms.csv', 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                count = 0
                for row in reader:
                    print("Inserting in terms........")
                    cursor.execute('''INSERT INTO terms (category, tech_term, def_in_english, def_in_tinglish, def_in_telugu) VALUES (?,?,?,?,?)''', 
                                   (row['category'], row['tech_term'], row['def_in_english'], row['def_in_tinglish'], row['def_in_telugu']))

                    term_id = cursor.lastrowid

                    print("Inserting examples........")

                    cursor.execute('''INSERT INTO examples (term_id, example1, example2) VALUES (?,?,?)''', 
                                   (term_id, row['example1'], row['example2']))

                    count = count + 1
            print(f"Inserted {count} terms")
        else:
            print("terms.csv not found. Skipping data import.")

    conn.commit()
    cursor.close()
    conn.close()
    print("Database initialization complete")

if __name__ == '__main__':
    init_db()
