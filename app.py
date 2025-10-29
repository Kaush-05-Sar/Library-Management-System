from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime
import sqlite3, os

app = Flask(__name__)

# Ensure database path is correct
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(BASE_DIR, 'library.db')


# --- Initialize database ---
def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            year INTEGER,
            borrow_date TEXT,
            return_date TEXT,
            fine REAL DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()


# --- Fine Calculation ---
def calculate_fine(borrow_date, return_date, rate_per_day=2):
    if not borrow_date or not return_date:
        return 0
    try:
        b_date = datetime.strptime(borrow_date, "%Y-%m-%d")
        r_date = datetime.strptime(return_date, "%Y-%m-%d")
        days_late = (r_date - b_date).days - 14  # 14 days allowed
        return max(0, days_late * rate_per_day)
    except Exception as e:
        print("Fine calculation error:", e)
        return 0


# --- Routes ---

@app.route('/')
def index():
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute('SELECT * FROM books')
    books = cur.fetchall()
    conn.close()
    return render_template('index.html', books=books)


@app.route('/add', methods=['GET', 'POST'])
def add_book():
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        year = request.form['year']

        conn = sqlite3.connect(DATABASE)
        cur = conn.cursor()
        cur.execute('INSERT INTO books (title, author, year) VALUES (?, ?, ?)',
                    (title, author, year))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))

    return render_template('add_book.html')


@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_book(id):
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()

    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        year = request.form['year']
        cur.execute('UPDATE books SET title=?, author=?, year=? WHERE id=?',
                    (title, author, year, id))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))

    cur.execute('SELECT * FROM books WHERE id=?', (id,))
    book = cur.fetchone()
    conn.close()
    return render_template('edit_book.html', book=book)


@app.route('/delete/<int:id>')
def delete_book(id):
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute('DELETE FROM books WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))


@app.route('/borrow/<int:id>', methods=['GET', 'POST'])
def borrow_book(id):
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()

    if request.method == 'POST':
        borrow_date = request.form['borrow_date']
        cur.execute("UPDATE books SET borrow_date=?, fine=0 WHERE id=?", (borrow_date, id))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))

    cur.execute("SELECT * FROM books WHERE id=?", (id,))
    book = cur.fetchone()
    conn.close()
    return render_template('borrow_book.html', book=book)


@app.route('/return/<int:id>', methods=['GET', 'POST'])
def return_book(id):
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()

    if request.method == 'POST':
        return_date = request.form['return_date']
        cur.execute("SELECT borrow_date FROM books WHERE id=?", (id,))
        result = cur.fetchone()
        borrow_date = result[0] if result and result[0] else None
        fine = calculate_fine(borrow_date, return_date)
        cur.execute("UPDATE books SET return_date=?, fine=? WHERE id=?", (return_date, fine, id))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))

    cur.execute("SELECT * FROM books WHERE id=?", (id,))
    book = cur.fetchone()
    conn.close()
    return render_template('return_book.html', book=book)


@app.route('/pay/<int:id>', methods=['GET', 'POST'])
def pay_fine(id):
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()

    if request.method == 'POST':
        cur.execute("UPDATE books SET fine=0 WHERE id=?", (id,))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))

    cur.execute("SELECT * FROM books WHERE id=?", (id,))
    book = cur.fetchone()
    conn.close()
    return render_template('pay_fine.html', book=book)


# --- Main entry ---
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
