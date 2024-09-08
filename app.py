from flask import Flask, render_template, request, send_from_directory, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

def get_db_connection():
    conn = sqlite3.connect('music.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/genre')
def genre():
    conn = get_db_connection()
    genre = conn.execute('SELECT * FROM genre').fetchall()
    conn.close()
    return render_template('genre.html', genre=genre)

@app.route('/genre/<int:genre_id>')
def genre_bands(genre_id):
    conn = get_db_connection()
    bands = conn.execute('SELECT * FROM band WHERE genre_id = ?', (genre_id,)).fetchall()
    conn.close()
    return render_template('genre_bands.html', bands=bands)

@app.route('/bands')
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

@app.route('/albums')
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
def timeline():
    return render_template('timeline.html')

@app.route('/images/<filename>')
def image(filename):
    return send_from_directory('static/images', filename)
@app.route('/login', methods=['GET', 'POST'])
def login():
    message = None  # 默认消息为空
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        try:
            # 连接数据库
            conn = sqlite3.connect('music.db')
            cursor = conn.cursor()

            # 检查数据库中是否有这个用户
            cursor.execute('SELECT password FROM users WHERE username = ?', (username,))
            user = cursor.fetchone()

            if user is None:
                message = 'Username does not exist'
            else:
                # 数据库中的加密密码
                hashed_password = user[0]

                # 使用 check_password_hash 验证密码
                if check_password_hash(hashed_password, password):
                    message = 'Login successful!'
                else:
                    message = 'Incorrect password'

        except sqlite3.Error as e:
            print("Error occurred:", e)
            message = 'Login failed, please try again later'

        finally:
            # 关闭连接
            conn.close()

    return render_template('login.html', message=message)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # 检查用户名和密码是否为空
        if not username or not password:
            return 'Username and password cannot be empty'

        # 使用 werkzeug 的默认密码加密算法
        hashed_password = generate_password_hash(password)

        try:
            # 连接数据库
            conn = sqlite3.connect('music.db')
            cursor = conn.cursor()

            # 插入用户数据
            cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
            
            # 提交更改
            conn.commit()

            # 确认用户添加成功
            print("User added successfully:", username)

        except sqlite3.Error as e:
            print("Error occurred:", e)
            return 'Failed to sign up, please try again later'

        finally:
            # 关闭连接
            conn.close()

        return redirect(url_for('login'))

    return render_template('signup.html')



if __name__ == '__main__':
    app.run(debug=True)
