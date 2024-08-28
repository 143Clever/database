from flask import Flask, render_template, request
import sqlite3

app = Flask(__name__)


def get_db_connection():
    conn = sqlite3.connect('music.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/bands')
def bands():
    conn = get_db_connection()
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
@app.route('/bands', methods=['GET'])
def bands():
    search_query = request.args.get('search')
    conn = get_db_connection()

    if search_query:
        query = "SELECT * FROM band WHERE band_name LIKE ?"
        bands = conn.execute(query, ('%' + search_query + '%',)).fetchall()
    else:
        bands = conn.execute("SELECT * FROM band").fetchall()

    conn.close()
    return render_template('bands.html', bands=bands)


if __name__ == '__main__':
    app.run(debug=True)
