from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from functools import wraps
import os
from database import init_db

app = Flask(__name__)
app.json.sort_keys = False
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-this-in-production')

# Admin credentials from environment variables
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')

# Detect environment: use PostgreSQL on Vercel/Render, SQLite locally
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    # Production: PostgreSQL
    import psycopg2
    from psycopg2.extras import RealDictCursor
    DB_TYPE = 'postgresql'
else:
    # Local: SQLite
    import sqlite3
    DB_TYPE = 'sqlite'
    
    if not os.path.exists('tech_terms.db'):
        print("Database not found. \n...Initializing database...")
        init_db()
    else:
        print("Database already exists. Skipping initialization.")

# Decorator for admin authentication
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def get_db_connection():
    if DB_TYPE == 'postgresql':
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    else:
        conn = sqlite3.connect('tech_terms.db')
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        return conn


@app.route('/')
def home():
    conn = get_db_connection()
    
    if DB_TYPE == 'postgresql':
        cursor = conn.cursor(cursor_factory=RealDictCursor)
    else:
        cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM terms ORDER BY LOWER(tech_term) ASC')
    terms = cursor.fetchall()
    cursor.close()
    conn.close()

    grouped_terms = {}
    for term in terms:
        first_letter = term['tech_term'][0].upper()
        if first_letter not in grouped_terms:
            grouped_terms[first_letter] = []
        grouped_terms[first_letter].append(term)

    return render_template('index.html', grouped_terms=grouped_terms)

@app.route('/api/terms', methods=['GET'])
def get_terms():
    category_filter = request.args.get('category')
    query = request.args.get('q')
    conn = get_db_connection()
    
    if DB_TYPE == 'postgresql':
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        placeholder = '%s'
        like_op = 'ILIKE'
    else:
        cursor = conn.cursor()
        placeholder = '?'
        like_op = 'LIKE'

    if category_filter:
        cursor.execute(f'SELECT * FROM terms LEFT JOIN examples ON terms.term_id = examples.term_id WHERE category = {placeholder}', (category_filter,))
        terms = cursor.fetchall()

    elif query:
        term_name = f"%{query}%"
        cursor.execute(f'SELECT * FROM terms LEFT JOIN examples ON terms.term_id = examples.term_id WHERE tech_term {like_op} {placeholder}', (term_name,))
        terms = cursor.fetchall()

    else:
        cursor.execute('SELECT * FROM terms LEFT JOIN examples ON terms.term_id = examples.term_id')
        terms = cursor.fetchall()

    cursor.close()
    conn.close()

    terms_list = [dict(term) for term in terms]
    return render_template('terms.html', terms_list=terms_list)

@app.route('/api/terms/<int:term_id>/', methods=['GET'])
def get_term_details(term_id):
    conn = get_db_connection()
    
    if DB_TYPE == 'postgresql':
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('SELECT * FROM terms LEFT JOIN examples ON terms.term_id = examples.term_id WHERE terms.term_id = %s', (term_id,))
    else:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM terms LEFT JOIN examples ON terms.term_id = examples.term_id WHERE terms.term_id = ?', (term_id,))
    
    term = cursor.fetchone()
    cursor.close()
    conn.close()

    if term is None:
        return jsonify({'error': 'Term not found'}), 404

    return render_template('term_detail.html', term=term)

@app.route('/api/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_page'))
        else:
            return render_template('admin_login.html', error='Invalid credentials')
    
    return render_template('admin_login.html')

@app.route('/api/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('home'))

@app.route('/api/admin', methods=['GET'])
@login_required
def admin_page():
    conn = get_db_connection()
    
    if DB_TYPE == 'postgresql':
        cursor = conn.cursor(cursor_factory=RealDictCursor)
    else:
        cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM terms LEFT JOIN examples ON terms.term_id = examples.term_id ORDER BY terms.term_id DESC LIMIT 10")
    terms = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('admin_page.html', terms=terms)

@app.route('/api/admin/addTerm', methods=['POST'])
@login_required
def add_term():
    data = request.form
    conn = get_db_connection()
    cursor = conn.cursor()
    
    required_fields = ['category', 'tech_term', 'def_in_english', 'def_in_tinglish', 'def_in_telugu', 'example1', 'example2']
    for field in required_fields:
        if field not in data:
            return jsonify({'Error': f'Missing field:{field}'}), 400

    if DB_TYPE == 'postgresql':
        cursor.execute('INSERT INTO terms (category, tech_term, def_in_english, def_in_tinglish, def_in_telugu) VALUES (%s,%s,%s,%s,%s) RETURNING term_id', 
                       (data['category'], data['tech_term'], data['def_in_english'], data['def_in_tinglish'], data['def_in_telugu']))
        term_id = cursor.fetchone()[0]
        cursor.execute('INSERT INTO examples (term_id, example1, example2) VALUES (%s,%s,%s)', 
                       (term_id, data['example1'], data['example2']))
    else:
        cursor.execute('INSERT INTO terms (category, tech_term, def_in_english, def_in_tinglish, def_in_telugu) VALUES (?,?,?,?,?)', 
                       (data['category'], data['tech_term'], data['def_in_english'], data['def_in_tinglish'], data['def_in_telugu']))
        term_id = cursor.lastrowid
        cursor.execute('INSERT INTO examples (term_id, example1, example2) VALUES (?,?,?)', 
                       (term_id, data['example1'], data['example2']))
    
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('admin_page'))


@app.route('/api/admin/deleteTerm/<int:term_id>', methods=['POST'])
@login_required
def delete_term(term_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if DB_TYPE == 'postgresql':
        cursor.execute('DELETE FROM terms WHERE term_id = %s', (term_id,))
    else:
        cursor.execute('DELETE FROM terms WHERE term_id = ?', (term_id,))
    
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('admin_page'))


@app.route('/api/admin/updateTerm/<int:term_id>', methods=['GET', 'POST'])
@login_required
def update_term(term_id):
    conn = get_db_connection()
    
    if request.method == 'GET':
        if DB_TYPE == 'postgresql':
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute('SELECT * FROM terms LEFT JOIN examples ON terms.term_id = examples.term_id WHERE terms.term_id = %s', (term_id,))
        else:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM terms LEFT JOIN examples ON terms.term_id = examples.term_id WHERE terms.term_id = ?', (term_id,))
        
        term = cursor.fetchone()
        cursor.close()
        conn.close()
        return render_template('update_term.html', term=term)

    elif request.method == 'POST':
        data = request.form
        required_fields = ['category', 'tech_term', 'def_in_english', 'def_in_tinglish', 'def_in_telugu', 'example1', 'example2']
        for field in required_fields:
            if field not in data:
                return jsonify({'Error': f'Missing field:{field}'}), 400

        cursor = conn.cursor()
        
        if DB_TYPE == 'postgresql':
            cursor.execute('UPDATE terms SET category = %s, tech_term = %s, def_in_english = %s, def_in_tinglish = %s, def_in_telugu = %s WHERE term_id = %s', 
                           (data['category'], data['tech_term'], data['def_in_english'], data['def_in_tinglish'], data['def_in_telugu'], term_id))
            cursor.execute('UPDATE examples SET example1 = %s, example2 = %s WHERE term_id = %s', 
                           (data['example1'], data['example2'], term_id))
        else:
            cursor.execute('UPDATE terms SET category = ?, tech_term = ?, def_in_english = ?, def_in_tinglish = ?, def_in_telugu = ? WHERE term_id = ?', 
                           (data['category'], data['tech_term'], data['def_in_english'], data['def_in_tinglish'], data['def_in_telugu'], term_id))
            cursor.execute('UPDATE examples SET example1 = ?, example2 = ? WHERE term_id = ?', 
                           (data['example1'], data['example2'], term_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('admin_page'))


if __name__ == '__main__':
    print(f"----Server will run on http://localhost:8080 using {DB_TYPE.upper()}-----")
    app.run(debug=True, host='0.0.0.0', port=8080)
