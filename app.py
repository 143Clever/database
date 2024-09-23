from flask import Flask, render_template, request, send_from_directory, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
from passlib.hash import scrypt
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your_secret_key'

def get_db_connection():
    conn = sqlite3.connect('music.db', timeout=5)
    conn.row_factory = sqlite3.Row
    return conn

@app.before_request
def require_login():
    # 需要登录的页面列表
    protected_routes = ['bands', 'albums', 'timeline', 'genre', 'genre_bands']
    
    if request.endpoint in protected_routes and 'username' not in session:
        return redirect(url_for('login'))


@app.route('/')

def index():
    if 'username' in session:
        return render_template('index.html', username=session['username'])
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    message = ""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            message = "Please provide both username and password."
            return render_template('login.html', message=message)

        try:
            BASE_DIR = os.path.dirname(os.path.abspath(__file__))
            conn = sqlite3.connect('music.db')
            cursor = conn.cursor()

            cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
            result = cursor.fetchone()
            conn.close()

            if result:
                stored_hashed_password = result[0]
                if scrypt.verify(password, stored_hashed_password):
                    session['logged_in'] = True
                    session['username'] = username
                    message = "Login successful!"
                    return redirect(url_for('index')) 
                else:
                    message = "Incorrect password."
            else:
                message = "Username does not exist."

        except Exception as e:
            message = f"An error occurred: {e}"

    return render_template('login.html', message=message)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session or not session['logged_in']:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/account')
def account():
    if 'username' not in session:
        return redirect(url_for('login'))  
    username = session['username']
    return render_template('account.html', username=username)




@app.route('/delete_account', methods=['POST'])
def delete_account():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    
    try:
       
        conn = sqlite3.connect('music.db')
        cursor = conn.cursor()

       
        cursor.execute("DELETE FROM users WHERE username = ?", (username,))
        conn.commit()

       
        cursor.close()
        conn.close()

        
        session.pop('username', None)

        
        return redirect(url_for('index'))
    except sqlite3.Error as e:
        
        return f"An error occurred: {e}"


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    message = ""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

       
        if not username or not password:
            message = "Please provide both username and password."
            return render_template('signup.html', message=message)

     
        encrypted_password = scrypt.hash(password)

        try:
           
            BASE_DIR = os.path.dirname(os.path.abspath(__file__))
            conn = sqlite3.connect('music.db')
           
            cursor = conn.cursor()

           
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, encrypted_password))
            conn.commit()
            conn.close()

            message = "Signup successful!"
        except sqlite3.IntegrityError:
            message = "Username already exists."
        except Exception as e:
            message = f"An error occurred: {e}"
    
    return render_template('signup.html', message=message)


def enable_wal_mode():
    conn = get_db_connection()
    conn.execute('PRAGMA journal_mode=WAL;')
    conn.close()

@app.route('/genre')
@login_required
def genre():
    conn = get_db_connection()
    genre = conn.execute('SELECT * FROM genre').fetchall()
    conn.close()
    return render_template('genre.html', genre=genre)

@app.route('/genre/<int:genre_id>')
@login_required
def genre_bands(genre_id):
    conn = get_db_connection()
    bands = conn.execute('SELECT * FROM band WHERE genre_id = ?', (genre_id,)).fetchall()
    conn.close()
    return render_template('genre_bands.html', bands=bands)

@app.route('/bands')
@login_required
def bands():
    search_query = request.args.get('search', '').strip().lower()
    conn = get_db_connection()
    bands = conn.execute('SELECT * FROM band').fetchall()
    if search_query:
        bands = conn.execute('SELECT * FROM band WHERE LOWER(band_name) LIKE ?', ('%' + search_query + '%',)).fetchall()
    else:
        bands = conn.execute('SELECT * FROM band').fetchall()
    conn.close()
    return render_template('bands.html', bands=bands)

@app.route('/band_albums/<int:band_id>')
def band_albums(band_id):
    conn = sqlite3.connect('music.db')
    cursor = conn.cursor()
    
    # 获取该乐队的专辑
    cursor.execute("SELECT album_name, released_year, image FROM album WHERE band_id = ?", (band_id,))
    albums = cursor.fetchall()
    
    # 获取乐队名称
    cursor.execute("SELECT band_name FROM band WHERE band_id = ?", (band_id,))
    band_name = cursor.fetchone()[0]
    
    conn.close()
    
    return render_template('band_albums.html', albums=albums, band_name=band_name)


@app.route('/albums')
@login_required
def albums():
    search_query = request.args.get('search', '').strip().lower()
    conn = get_db_connection()

    if search_query:
        albums = conn.execute('SELECT * FROM album WHERE LOWER(album_name) LIKE ?', ('%' + search_query + '%',)).fetchall()
    else:
        albums = conn.execute('SELECT * FROM album').fetchall()
    
    conn.close()
    return render_template('albums.html', albums=albums)

@app.route('/timeline')
@login_required
def timeline():
    return render_template('timeline.html')
if __name__ == '__main__':
    app.run(debug=True)

