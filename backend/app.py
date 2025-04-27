# backend/app.py

from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, session
from flask_cors import CORS
import os, json
from dotenv import load_dotenv
from .questions import *
import os as _os
from .extensions import db, migrate, login_manager
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_login import login_user, logout_user, current_user, login_required
from .models import User, ApiKey, QuizSession, QuizQuestion
from .parser_pptx_json import pptx_to_json

# Real Gemini SDK
import google.generativeai as genai

# Load environment variables
_root = _os.path.dirname(_os.path.dirname(__file__))
load_dotenv(_os.path.join(_root, '.env'))
print(f"[DEBUG] Database URI: {os.getenv('DATABASE_URL')}")

# Legacy Gemini integration fallback
try:
    from .gemini import client, promptGemini
except ImportError:
    client = None
    def promptGemini(c, p):
        raise RuntimeError("Gemini integration unavailable")

# Create Flask app
app = Flask(__name__, static_folder='../static', template_folder='../templates')
# 1) Make Python's built-in zip() available in Jinja templates
app.jinja_env.globals.update(zip=zip)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///quizpro.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

CORS(app)
db.init_app(app)
migrate.init_app(app, db)

login_manager.init_app(app)
login_manager.login_view = 'login'  # redirect unauthorized users here

# Flask-Login user loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ----- Authentication Routes -----
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email    = request.form['email']
        password = request.form['password']
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('register.html')
        user = User(email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for('setup'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email    = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            flash('Invalid email or password', 'error')
            return render_template('login.html')
        login_user(user)
        return redirect(url_for('setup'))
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# ----- Main Quiz Flow -----
@app.route('/')
@login_required
def index():
    return render_template('index.html')


@app.route('/setup', methods=['GET', 'POST'])
@login_required
def setup():
    if request.method == 'POST':
        api_key = request.form.get('apiKey')
        content = request.form.get('pastedText', '').strip()

        if not content:
            flash("Please upload a PPTX or paste some text first.", "error")
            return render_template('setup.html')

        prompt = (
            "Generate 20 quiz questions based on the following content:\n\n"
            f"{content}\n\n"
            "Separate each question with <|Q|>."
        )
        # Call Gemini via GenAI SDK
        questions = generate_questions(api_key, prompt)

        # Fallback to dummy if Gemini returns nothing
        if not questions or not questions.strip():
            questions = (
                "1. Dummy question?<|Q|>"
                "2. Another dummy question?<|Q|>"
                "3. Final dummy question?<|Q|>"
            )

        qs = [q.strip() for q in questions.split('<|Q|>') if q.strip()]
        session['questions']              = qs
        session['answers']                = []
        session['current_question_index'] = 0
        return redirect(url_for('chat'))

    return render_template('setup.html')


@app.route('/chat', methods=['GET', 'POST'])
@login_required
def chat():
    qs  = session.get('questions', [])
    idx = session.get('current_question_index', 0)

    if request.method == 'POST':
        ans = request.form.get('answer', '').strip()
        session['answers'].append(ans)
        idx += 1
        session['current_question_index'] = idx

        if idx < len(qs):
            return redirect(url_for('chat'))
        else:
            return redirect(url_for('results'))

    current = qs[idx] if idx < len(qs) else None
    return render_template('chat.html',
                           question=current,
                           index=idx+1,
                           total=len(qs))


@app.route('/results')
@login_required
def results():
    return render_template('results.html',
                           questions=session.get('questions', []),
                           answers=session.get('answers', []))


# ----- PPTX Upload Endpoint -----
@app.route('/upload_pptx', methods=['POST'])
@login_required
def upload_pptx():
    file = request.files.get('file')
    if not file:
        return jsonify({'error': 'No file provided'}), 400
    data   = pptx_to_json(file)
    slides = data.get('slides', [])
    return jsonify({'slides': slides}), 200


# ----- Legacy / Optional Endpoints -----
@app.route('/generate_quiz', methods=['POST'])
@login_required
def generate_quiz():
    payload    = request.get_json() or {}
    slides     = payload.get('slides', [])
    count      = payload.get('count', len(slides))
    slide_text = '\n'.join(slides)
    prompt     = (
        f"Generate {count} quiz questions from the following slide texts. "
        "Separate each with <|Q|>:\n" + slide_text
    )
    # using legacy promptGemini
    response   = promptGemini(client, prompt)
    raw        = getattr(response, 'text', response)
    items      = raw.split('<|Q|>')
    session_db = QuizSession(user_id=current_user.id)
    db.session.add(session_db)
    db.session.commit()
    for idx, itm in enumerate(items):
        text = itm.strip()
        if text:
            q = QuizQuestion(session_id=session_db.id, index=idx, prompt=text)
            db.session.add(q)
    db.session.commit()
    first = QuizQuestion.query.filter_by(session_id=session_db.id, index=0).first()
    return jsonify({'session_id': session_db.id,
                    'question_id': first.id,
                    'prompt': first.prompt}), 201


@app.route('/answer_question', methods=['POST'])
@login_required
def answer_question():
    payload     = request.get_json() or {}
    session_id  = payload.get('session_id')
    question_id = payload.get('question_id')
    answer      = payload.get('answer')
    question    = QuizQuestion.query.get_or_404(question_id)
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
    payload    = request.get_json() or {}
    session_db = QuizSession.query.get_or_404(payload.get('session_id'))
    qas        = [{'prompt': q.prompt, 'answer': q.user_answer} for q in session_db.questions]
    eval_prompt = (
        f"Here are the questions and your answers: {json.dumps(qas)}. "
        "Determine which are correct or wrong, then generate follow-up questions "
        "to close learning gaps, separate each with <|Q|>."
    )
    resp  = promptGemini(client, eval_prompt)
    items = getattr(resp, 'text', resp).split('<|Q|>')
    return jsonify({'followup_questions': items}), 200


@app.route('/success')
@login_required
def success():
    return render_template('success.html')


# ----- Helper Functions -----
def generate_questions(api_key, prompt):
    """Configure per-call and generate via Gemini."""
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(prompt)
    return getattr(response, "text", response)


if __name__ == '__main__':
    app.run(debug=True)
