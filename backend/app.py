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
from .models import QuizSession, QuizQuestion
from .parser_pptx_json import pptx_to_json
try:
    from .gemini import client, promptGemini
except ImportError:
    # Gemini module might not be available during migrations
    client = None
    def promptGemini(c, p):
        raise RuntimeError("Gemini integration unavailable")
import json

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
@app.route('/setup', methods=['GET', 'POST'])
@login_required
def setup():
    if request.method == 'POST':
        api_key = request.form.get('apiKey')
        pptx_file = request.files.get('pptxFile')
        pasted_text = request.form.get('pastedText')
        selected_model = request.form.get('modelSelect')  # Get the selected model

        # Debugging: Print the values to check if they are being captured correctly
        print(f"API Key: {api_key}, Model: {selected_model}, PPTX File: {pptx_file}, Pasted Text: {pasted_text}")

        # Handle API Key
        if api_key:
            # Call save_api_key with the model and key
            response = save_api_key(api_key, selected_model)  # Pass the model and key

        # Handle PPTX Upload
        if pptx_file:
            data = pptx_to_json(pptx_file)  # Process the PPTX file
            # Handle the data as needed

        # Handle Pasted Text
        if pasted_text:
            save_pasted_text(pasted_text)  # Implement your logic for pasted text

        # Redirect or render a success message
        return redirect(url_for('some_success_page'))  # Change to your desired redirect

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
    # Store one key per user+model
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
        return redirect(url_for('setup'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

admin = Admin(app, name="QuizPro Admin", template_mode="bootstrap4")
admin.add_view(ModelView(ApiKey, db.session))

### Quiz workflow endpoints
@app.route('/upload_pptx', methods=['POST'])
@login_required
def upload_pptx():
    file = request.files.get('file')
    if not file:
        return jsonify({'error': 'No file provided'}), 400
    data = pptx_to_json(file)
    slides = data.get('slides', [])
    return jsonify({'slides': slides}), 200

@app.route('/generate_quiz', methods=['POST'])
@login_required
def generate_quiz():
    payload = request.get_json() or {}
    slides = payload.get('slides', [])
    count = payload.get('count', len(slides))
    slide_text = '\n'.join(slides)
    prompt = f"Generate {count} quiz questions from the following slide texts. Separate each with <|Q|>:\n{slide_text}"
    response = promptGemini(client, prompt)
    questions_raw = getattr(response, 'text', response)
    items = questions_raw.split('<|Q|>')
    session = QuizSession(user_id=current_user.id)
    db.session.add(session)
    db.session.commit()
    for idx, item in enumerate(items):
        q_text = item.strip()
        if not q_text:
            continue
        q = QuizQuestion(session_id=session.id, index=idx, prompt=q_text)
        db.session.add(q)
    db.session.commit()
    first = QuizQuestion.query.filter_by(session_id=session.id, index=0).first()
    return jsonify({'session_id': session.id, 'question_id': first.id, 'prompt': first.prompt}), 201

@app.route('/answer_question', methods=['POST'])
@login_required
def answer_question():
    payload = request.get_json() or {}
    session_id = payload.get('session_id')
    question_id = payload.get('question_id')
    answer = payload.get('answer')
    question = QuizQuestion.query.get_or_404(question_id)
    question.user_answer = answer
    db.session.commit()
    next_q = QuizQuestion.query.filter(
        QuizQuestion.session_id == session_id,
        QuizQuestion.index > question.index
    ).order_by(QuizQuestion.index).first()
    if next_q:
        return jsonify({'question_id': next_q.id, 'prompt': next_q.prompt}), 200
    return jsonify({'done': True}), 200

@app.route('/evaluate_quiz', methods=['POST'])
@login_required
def evaluate_quiz():
    payload = request.get_json() or {}
    session_id = payload.get('session_id')
    session = QuizSession.query.get_or_404(session_id)
    qas = [{'prompt': q.prompt, 'answer': q.user_answer} for q in session.questions]
    eval_prompt = (
        f"Here are the questions and your answers: {json.dumps(qas)}. "
        "Determine which are correct or wrong, then generate follow-up questions to close learning gaps, separate each with <|Q|>."
    )
    response = promptGemini(client, eval_prompt)
    followup_raw = getattr(response, 'text', response)
    items = followup_raw.split('<|Q|>')
    return jsonify({'followup_questions': items}), 200

if __name__ == '__main__':
    app.run(debug=True) 