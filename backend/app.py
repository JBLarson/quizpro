from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from flask_cors import CORS
import os
from dotenv import load_dotenv
# Explicitly load .env from project root
import os as _os
_root = _os.path.dirname(_os.path.dirname(__file__))
load_dotenv(_os.path.join(_root, '.env'))
print(f"[DEBUG] Database URI: { _os.getenv('DATABASE_URL') }")
from .extensions import db, migrate, login_manager
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_login import login_user, logout_user, current_user, login_required
from .models import ApiKey

app = Flask(__name__, static_folder='../static', template_folder='../templates')
# Set a secret key for Flask session management
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///quizpro.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
CORS(app)
db.init_app(app)
# Initialize Alembic migrations
migrate.init_app(app, db)

# Initialize login manager
login_manager.init_app(app)

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    from .models import User
    return User.query.get(int(user_id))

@app.route('/')
@login_required
def index():
    return render_template('index.html')

# route for api key setup
@app.route('/setup')
@login_required
def setup():
    return render_template('setup.html')

# route for chat configuration
@app.route('/config')
@login_required
def config():
    return render_template('setup.html')

# route for adding content
@app.route('/content')
@login_required
def content():
    return render_template('setup.html')

# Add endpoint to save API keys per user
@app.route('/api_key', methods=['POST'])
@login_required
def save_api_key():
    data = request.get_json()
    model = data.get('model')
    key = data.get('key')
    if not model or not key:
        return jsonify({'error': 'Missing model or key'}), 400
    # store one key per user+model
    api_key = ApiKey.query.filter_by(user_id=current_user.id, model=model).first()
    if api_key:
        api_key.key = key
    else:
        api_key = ApiKey(user_id=current_user.id, model=model, key=key)
        db.session.add(api_key)
    db.session.commit()
    return jsonify({'status': 'success'}), 201

@app.route('/pptx', methods=['POST'])
def pptxRetrieval():
    data = request.json.get('data')
    session['stored_data'] = data
    return jsonify({'status': 'success'}), 201

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        from .models import User
        if User.query.filter_by(email=email).first():
            return 'Email already registered', 400
        user = User(email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        from .models import User
        user = User.query.filter_by(email=email).first()
        if not user:
            flash('No account found with that email. Please register first.')
            return render_template('login.html')
        if not user.check_password(password):
            flash('Incorrect password. Please try again.')
            return render_template('login.html')
        login_user(user)
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

admin = Admin(app, name="QuizPro Admin", template_mode="bootstrap4")
admin.add_view(ModelView(ApiKey, db.session))

if __name__ == '__main__':
    app.run(debug=True) 