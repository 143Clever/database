from flask import Flask, render_template, request, send_from_directory
import sqlite3
import os

app = Flask(__name__)

# 获取数据库连接
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

if __name__ == '__main__':
    app.run(debug=True)
