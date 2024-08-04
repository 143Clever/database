from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///path_to_your_db_file.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Album(db.Model):
    __tablename__ = 'albums'
    band_id = db.Column(db.Integer, primary_key=True)
    band_name = db.Column(db.String(100), nullable=False)
    formed_year = db.Column(db.Integer, nullable=False)
    genre_id = db.Column(db.Integer, nullable=False)
    genre_name = db.Column(db.String(100), nullable=False)
    image = db.Column(db.String(100), nullable=False)

@app.route("/")
def home():
    return render_template("index.html")

@app.route('/albums')
def albums():
    albums = Album.query.all()
    return render_template('albums.html', albums=albums)

if __name__ == '__main__':
    app.run(debug=True)
