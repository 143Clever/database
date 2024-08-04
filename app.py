from flask import Flask, render_template, request
import sqlite3

app = Flask(__name__)

# Function to query the database
def get_album_details(album_name):
    conn = sqlite3.connect('music.db')  # Update to the correct database file name
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM album WHERE album_name=?", (album_name,))
    album = cursor.fetchone()
    conn.close()
    return album

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/albums', methods=['GET', 'POST'])
def albums():
    search_query = request.args.get('search')
    if search_query:
        album = get_album_details(search_query)
        if album:
            return render_template('album_details.html', album=album)
        else:
            return render_template('albums.html', error="No album found with that name")
    return render_template('albums.html')

if __name__ == '__main__':
    app.run(debug=True)
