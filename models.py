from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask import Flask
# models.py





app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///notes.db'  # Ensure this is the correct path

db = SQLAlchemy(app)  # Initialize SQLAlchemy with the app
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    # Add other fields as needed

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    importance = db.Column(db.String(50), nullable=False)
    # Add other fields as needed


    def __repr__(self):
        return f'<Note {self.title}>'

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # This creates the tables in the database
