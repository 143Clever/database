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
    return render_template('bands.html')

@app.route('/albums', methods=['GET'])
def albums():
    search_query = request.args.get('search')
    conn = get_db_connection()
    if search_query:
        albums = conn.execute("SELECT * FROM album WHERE album_name LIKE ?", ('%' + search_query + '%',)).fetchall()
    else:
        albums = conn.execute("SELECT * FROM album").fetchall()
    conn.close()
    return render_template('albums.html', albums=albums)

@app.route('/timeline')
def timeline():
    return render_template('timeline.html')

if __name__ == '__main__':
    app.run(debug=True)
