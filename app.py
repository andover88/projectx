from flask import Flask, redirect, request, session, url_for, render_template, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from authlib.integrations.flask_client import OAuth
import os
from dotenv import load_dotenv
from datetime import datetime
from sqlalchemy import or_

# Load environment variables
load_dotenv()

events= []

# Flask app setup
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///your_database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your_secret_key')
app.config['DEBUG'] = False  # Turn off debug mode in production
app.config['ENV'] = 'production'  # Set environment to production
db = SQLAlchemy(app)

# OAuth setup
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    access_token_url='https://accounts.google.com/o/oauth2/token',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    api_base_url='https://www.googleapis.com/oauth2/v2/',
    client_kwargs={'scope': 'openid profile email'},
    redirect_uri=os.getenv('GOOGLE_REDIRECT_URI')
)

# Models
class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    importance = db.Column(db.String(50), nullable=False)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=True)
    email = db.Column(db.String(150), unique=True, nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    date = db.Column(db.Date, nullable=False)
    importance = db.Column(db.String(50), nullable=False)

class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<BlogPost {self.title}>'

# Routes
@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        session['username'] = username
        return redirect(url_for('dashboard'))
    flash("Invalid Username or Password!")
    return redirect(url_for('home'))

@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    user = User.query.filter_by(username=username).first()
    if user:
        flash('Username already exists.')
    else:
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        session['username'] = username
        return redirect(url_for('dashboard'))
    return redirect(url_for('home'))

@app.route('/login/google')
def login_google():
    try:
        redirect_uri = url_for('authorize_google', _external=True)
        return google.authorize_redirect(redirect_uri)
    except Exception as e:
        app.logger.error(f"Error during Google login: {str(e)}")
        return "An error occurred while trying to log in with Google. Please try again later.", 500

@app.route('/dashboard')
def dashboard():
    if 'username' in session:
        user = User.query.filter_by(username=session['username']).first()
        search_query = request.args.get('search', '').strip()
        if search_query:
            notes = Note.query.filter(
                or_(
                    Note.title.ilike(f'%{search_query}%'),
                    Note.description.ilike(f'%{search_query}%')
                )
            ).all()
        else:
            notes = Note.query.all()
        return render_template('dashboard.html', user=user, notes=notes)
    return redirect(url_for('login_google'))

@app.route('/add', methods=['POST'])
def add_note():
    title = request.form.get('title')
    description = request.form.get('description')
    
    if not title or not description:
        flash('Title and description are required.')
        return redirect(url_for('dashboard'))
    
    new_note = Note(
        title=title,
        description=description,
        date=datetime.utcnow(),
        importance='low'
    )
    
    try:
        db.session.add(new_note)
        db.session.commit()
        flash('Note added successfully!')
    except Exception as e:
        db.session.rollback()
        flash('Error adding note.')
    
    return redirect(url_for('dashboard'))

@app.route('/delete/<int:id>')
def delete_note(id):
    note = Note.query.get(id)
    if note:
        try:
            db.session.delete(note)
            db.session.commit()
            flash('Note deleted successfully!')
        except Exception as e:
            db.session.rollback()
            flash('Error deleting note.')
    else:
        flash('Note not found.')
    
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

@app.route('/auth/callback')
def authorize_google():
    try:
        token = google.authorize_access_token()
        user_info = google.parse_id_token(token)
        email = user_info.get('email')
        
        if not email:
            flash("Unable to retrieve user information from Google. Please try again.")
            return redirect(url_for('home'))
        
        user = User.query.filter_by(username=email).first()
        if not user:
            new_user = User(username=email, email=email)
            db.session.add(new_user)
            db.session.commit()
        
        session['username'] = email
        return redirect(url_for('dashboard'))
    
    except Exception as e:
        app.logger.error(f"Error during Google authorization: {str(e)}")
        flash("An error occurred during Google authorization. Please try again later.")
        return redirect(url_for('home'))

@app.route('/videos')
def videos():
    return render_template('videos.html')

@app.route('/go-to-videos')
def go_to_videos():
    return redirect(url_for('videos'))

@app.route('/get_events', methods=['GET'])
def get_events():
    return jsonify({"events": events})

@app.route('/calendar')
def calendar():
    return render_template('calendar.html')

@app.route('/add_event', methods=['POST'])
def add_event():
    try:
        data = request.form
        title = data.get('title')
        date = data.get('date')
        importance = data.get('importance')

        if not title or not date or not importance:
            return jsonify({"error": "Missing required fields"}), 400

        event = {
            "title": title,
            "date": date,
            "importance": importance
        }

        events.append(event)
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/blog')
def blog():
    posts = BlogPost.query.order_by(BlogPost.created_at.desc()).all()
    return render_template('blog.html', posts=posts)

@app.route('/blog/<int:post_id>')
def blog_post(post_id):
    post = BlogPost.query.get_or_404(post_id)
    return render_template('blog_post.html', post=post)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Creates the database tables
    app.run()
