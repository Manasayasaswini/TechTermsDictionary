from flask import Flask, render_template, request, jsonify, redirect, url_for
import sqlite3
import os
from database import init_db

app = Flask(__name__)
app.json.sort_keys = False

if not os.path.exists('tech_terms.db'):
    print("Database not found. \n...Initializing database...")
    init_db()
else:
    print("Database already exists. Skipping initialization.")

def get_db_connection():
    conn=sqlite3.connect('tech_terms.db')
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/')
def home():
    conn = get_db_connection()
    terms = conn.execute('SELECT * FROM terms ORDER BY LOWER(tech_term) ASC').fetchall()
    #terms = conn.execute('SELECT * FROM terms LEFT JOIN examples ON terms.term_id = examples.term_id').fetchall()
    conn.close()

    grouped_terms = {}
    for term in terms:
        first_letter = term['tech_term'][0].upper()
        if first_letter not in grouped_terms:
            grouped_terms[first_letter] = []
        grouped_terms[first_letter].append(term)

    #return render_template('index.html', terms=terms)
    return render_template('index.html', grouped_terms=grouped_terms)

@app.route('/api/terms', methods=['GET'])
def get_terms():
    category_filter = request.args.get('category')
    query = request.args.get('q')
    conn = get_db_connection()

    if category_filter:
        terms = conn.execute('SELECT * FROM terms LEFT JOIN examples ON terms.term_id = examples.term_id WHERE category = ?',(category_filter,)).fetchall()


    elif query:

        term_name = f"%{query}%"

        terms = conn.execute('SELECT * FROM terms LEFT JOIN examples ON terms.term_id = examples.term_id WHERE tech_term LIKE ?', (term_name,)).fetchall()

    else:
        terms = conn.execute('SELECT * FROM terms LEFT JOIN examples ON terms.term_id = examples.term_id').fetchall()

    conn.close()


    terms_list = [dict(term) for term in terms]
    #return jsonify(terms_list)
    return render_template('terms.html', terms_list=terms_list)

@app.route('/api/terms/<int:term_id>/', methods=['GET'])
def get_term_details(term_id):
    conn = get_db_connection()
    term = conn.execute('SELECT * FROM terms LEFT JOIN examples ON terms.term_id = examples.term_id WHERE terms.term_id = ?',(term_id,)).fetchone()
    conn.close()

    if term is None:
        return jsonify({'error': 'Term not found'}), 404

    return render_template('term_detail.html', term=term)

@app.route('/api/admin', methods=['GET'])
def admin_page():
    conn = get_db_connection()
    terms = conn.execute("SELECT * FROM terms LEFT JOIN examples ON terms.term_id = examples.term_id ORDER BY term_id DESC LIMIT 10").fetchall()
    conn.close()
    return render_template('admin_page.html', terms=terms)

@app.route('/api/admin/addTerm', methods=['POST'])
def add_term():
    data = request.form
    conn = get_db_connection()
    required_fields = ['category', 'tech_term', 'def_in_english', 'def_in_tinglish', 'def_in_telugu', 'example1', 'example2']
    for field in required_fields:
        if field not in data:
            return jsonify({'Error': f'Missing field:{field}'}), 400

    cursor = conn.cursor()
    cursor.execute('INSERT INTO terms (category, tech_term, def_in_english, def_in_tinglish, def_in_telugu) VALUES (?,?,?,?,?)', (data['category'], data['tech_term'], data['def_in_english'], data['def_in_tinglish'], data['def_in_telugu']))
    term_id = cursor.lastrowid
    cursor.execute('INSERT INTO examples (term_id, example1, example2) VALUES (?,?,?)', (term_id, data['example1'], data['example2']))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_page'))


@app.route('/api/admin/deleteTerm/<int:term_id>', methods=['POST'])
def delete_term(term_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM terms WHERE term_id = (?)', (term_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_page'))

    #if not terms:
    #   return jsonify({'error': 'Term not found'}), 404



@app.route('/api/admin/updateTerm/<int:term_id>', methods=['GET', 'POST'])
def update_term(term_id):
  conn = get_db_connection()
  if request.method == 'GET':
    term = conn.execute('SELECT * FROM terms LEFT JOIN examples ON terms.term_id = examples.term_id WHERE terms.term_id = (?)', (term_id,)).fetchone()
    conn.commit()
    conn.close()
    return render_template('update_term.html', term = term)

  elif request.method == 'POST':
      data = request.form
      required_fields = ['category', 'tech_term', 'def_in_english', 'def_in_tinglish', 'def_in_telugu', 'example1', 'example2']
      for field in required_fields:
        if field not in data:
            return jsonify({'Error': f'Missing field:{field}'}), 400

      cursor = conn.cursor()
      cursor.execute('UPDATE terms SET category = ?, tech_term = ?, def_in_english = ?, def_in_tinglish = ?, def_in_telugu = ? WHERE term_id = ?', (data['category'], data['tech_term'], data['def_in_english'], data['def_in_tinglish'], data['def_in_telugu'], term_id))
      cursor.execute('UPDATE examples SET example1 = ?, example2 = ? WHERE term_id = ?', (data['example1'], data['example2'], term_id))
      conn.commit()
      conn.close()
      return redirect(url_for('admin_page'))


if __name__ == '__main__':
    print("----Server will run on http://localhost:8080-----")
    app.run(debug=True, host='0.0.0.0', port=8080)



