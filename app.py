from flask import Flask, render_template, request, redirect, url_for, session
from functools import wraps
import sqlite3
import os
from passlib.hash import scrypt

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Secret key for sessions and security


# Database connection function
def get_db_connection():
    """
    Establishes a connection to the SQLite database and sets the row factory to sqlite3.Row 
    for dict-like access to columns.
    """
    conn = sqlite3.connect('music.db', timeout=5)
    conn.row_factory = sqlite3.Row
    return conn


# Middleware to enforce login before accessing protected routes
@app.before_request
def require_login():
    """
    This function runs before each request. It checks if the user is trying to access
    a protected route without being logged in. If so, they are redirected to the login page.
    """
    protected_routes = ['bands', 'albums', 'timeline', 'genre', 'genre_bands']
    if request.endpoint in protected_routes and 'username' not in session:
        return redirect(url_for('login'))


# Home page route
@app.route('/')
def index():
    """
    Renders the index page. If the user is logged in, it shows the homepage with their username;
    otherwise, it shows the regular homepage.
    """
    if 'username' in session:
        return render_template('index.html', username=session['username'])
    return render_template('index.html')


# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handles the login process. On POST, it verifies the user's credentials.
    If valid, the user is logged in and redirected to the homepage. 
    Otherwise, an error message is displayed.
    """
    message = ""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            message = "Please provide both username and password."
            return render_template('login.html', message=message)

        try:
            conn = sqlite3.connect('music.db')
            cursor = conn.cursor()
            # Fetch user credentials from the database
            cursor.execute("SELECT user_id, password FROM users WHERE username = ?", (username,))
            result = cursor.fetchone()
            conn.close()

            if result:
                user_id, stored_hashed_password = result
                # Verify password using scrypt hash
                if scrypt.verify(password, stored_hashed_password):
                    # Login success, set session variables
                    session['logged_in'] = True
                    session['username'] = username
                    session['user_id'] = user_id
                    return redirect(url_for('index'))
                else:
                    message = "Incorrect password."
            else:
                message = "Username does not exist."

        except Exception as e:
            message = f"An error occurred: {e}"

    return render_template('login.html', message=message)


# Custom decorator to enforce login
def login_required(f):
    """
    A decorator that ensures the user is logged in before accessing the decorated route.
    If the user is not logged in, they are redirected to the login page.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session or not session['logged_in']:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# Account page route
@app.route('/account')
@login_required
def account():
    """
    Displays the user's account page, which includes their favorite albums. 
    The user must be logged in to access this page.
    """
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    conn = sqlite3.connect('music.db')
    cursor = conn.cursor()
    # Retrieve the user's favorite albums
    cursor.execute(
        '''
        SELECT album.album_id, album.album_name, album.image, album.band_name, album.released_year
        FROM album 
        JOIN favorites ON album.album_id = favorites.album_id 
        WHERE favorites.user_id = ?
        ''', (user_id,)
    )
    favorite_albums = cursor.fetchall()
    conn.close()

    return render_template('account.html', username=session['username'], favorite_albums=favorite_albums)


# Delete account route
@app.route('/delete_account', methods=['POST'])
def delete_account():
    """
    Allows a logged-in user to delete their account. After deletion, the session is cleared
    and the user is redirected to the homepage.
    """
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
        # Log the user out after account deletion
        session.pop('username', None)
        return redirect(url_for('index'))
    except sqlite3.Error as e:
        return f"An error occurred: {e}"


# Logout route
@app.route('/logout')
def logout():
    """
    Logs the user out by clearing the session data and redirects them to the homepage.
    """
    session.pop('username', None)
    return redirect(url_for('index'))


# Signup route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """
    Handles user signup. On POST, it creates a new user account with a securely hashed password.
    If the username is taken, an error message is displayed.
    """
    message = ""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            message = "Please provide both username and password."
            return render_template('signup.html', message=message)

        encrypted_password = scrypt.hash(password)

        try:
            conn = sqlite3.connect('music.db')
            cursor = conn.cursor()
            # Insert the new user into the database
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, encrypted_password))
            conn.commit()
            conn.close()
            message = "Signup successful!"
        except sqlite3.IntegrityError:
            message = "Username already exists."
        except Exception as e:
            message = f"An error occurred: {e}"

    return render_template('signup.html', message=message)


# Enabling Write-Ahead Logging (WAL) for better performance
def enable_wal_mode():
    """
    Enables the WAL (Write-Ahead Logging) mode for the SQLite database. This improves 
    concurrency and allows simultaneous read/write access.
    """
    conn = get_db_connection()
    conn.execute('PRAGMA journal_mode=WAL;')
    conn.close()


# Genre page route
@app.route('/genre')
@login_required
def genre():
    """
    Displays a list of all music genres from the database. Only accessible to logged-in users.
    """
    conn = get_db_connection()
    genre = conn.execute('SELECT * FROM genre').fetchall()
    conn.close()
    return render_template('genre.html', genre=genre)


# Bands within a genre route
@app.route('/genre/<int:genre_id>')
@login_required
def genre_bands(genre_id):
    """
    Displays all bands belonging to a specific genre. The genre is determined by the genre_id.
    """
    conn = get_db_connection()
    bands = conn.execute('SELECT * FROM band WHERE genre_id = ?', (genre_id,)).fetchall()
    conn.close()
    return render_template('genre_bands.html', bands=bands)


# Bands page route
@app.route('/bands')
@login_required
def bands():
    """
    Displays all bands. Users can search for bands by name. 
    """
    search_query = request.args.get('search', '').strip().lower()
    conn = get_db_connection()
    if search_query:
        bands = conn.execute('SELECT * FROM band WHERE LOWER(band_name) LIKE ?', ('%' + search_query + '%',)).fetchall()
    else:
        bands = conn.execute('SELECT * FROM band').fetchall()
    conn.close()
    return render_template('bands.html', bands=bands)


# Albums for a band route
@app.route('/band_albums/<int:band_id>')
@login_required
def band_albums(band_id):
    """
    Displays albums for a specific band, sorted by their release year.
    """
    sort_by = request.args.get('sort', 'released_year')
    conn = sqlite3.connect('music.db')
    cursor = conn.cursor()
    albums = cursor.execute(
        'SELECT album.album_id, album.album_name, album.image, album.released_year '
        'FROM album WHERE band_id = ? ORDER BY released_year',
        (band_id,)
    ).fetchall()
    cursor.execute('SELECT band_name FROM band WHERE band_id = ?', (band_id,))
    band_name = cursor.fetchone()[0]
    return render_template('band_albums.html', albums=albums)


# Albums page route with search and sorting options
@app.route('/albums')
@login_required
def albums():
    """
    Displays all albums with optional search and sort functionality.
    Users can search for albums by name and sort by name or release year.
    """
    search_query = request.args.get('search', '').strip().lower()
    sort_by = request.args.get('sort', 'released_year')

    conn = get_db_connection()
    if search_query:
        if sort_by == 'name':
            albums = conn.execute(
                'SELECT * FROM album WHERE LOWER(album_name) LIKE ? ORDER BY album_name',
                ('%' + search_query + '%',)
            ).fetchall()
        else:
            albums = conn.execute(
                'SELECT * FROM album WHERE LOWER(album_name) LIKE ? ORDER BY released_year',
                ('%' + search_query + '%',)
            ).fetchall()
    else:
        if sort_by == 'name':
            albums = conn.execute('SELECT * FROM album ORDER BY album_name').fetchall()
        else:
            albums = conn.execute('SELECT * FROM album ORDER BY released_year').fetchall()

    conn.close()
    return render_template('albums.html', albums=albums, sort_by=sort_by, search_query=search_query)


@app.route('/favorite/<int:album_id>', methods=['POST'])
@login_required
def favorite(album_id):
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    conn = sqlite3.connect('music.db')
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM favorites WHERE user_id = ? AND album_id = ?", (user_id, album_id))
        exists = cursor.fetchone()

        if exists:
            message = "Album already in favorites."
        else:
            cursor.execute("INSERT INTO favorites (user_id, album_id) VALUES (?, ?)", (user_id, album_id))
            conn.commit()
            message = "Album added to favorites!"
    except Exception as e:
        message = f"An error occurred: {e}"
    finally:
        conn.close()

    return redirect(url_for('albums', message=message))



# Route to delete an album from user's favorites
@app.route('/delete_favorite/<int:album_id>', methods=['POST'])
@login_required
def delete_favorite(album_id):
    """
    Allows the logged-in user to remove an album from their favorites.
    The album is identified by album_id.
    """
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = sqlite3.connect('music.db')

    try:
        # Remove album from favorites
        conn.execute("DELETE FROM favorites WHERE user_id = ? AND album_id = ?", (user_id, album_id))
        conn.commit()
        message = "Album removed from favorites!"
    except Exception as e:
        message = f"An error occurred: {e}"
    finally:
        conn.close()

    return redirect(url_for('account', message=message))


# Timeline page route
@app.route('/timeline')
@login_required
def timeline():
    """
    Displays the timeline page. This route is accessible only to logged-in users.
    """
    return render_template('timeline.html')


# Main application runner
if __name__ == '__main__':
    """
    Starts the Flask application in debug mode.
    """
    app.run(debug=True)
