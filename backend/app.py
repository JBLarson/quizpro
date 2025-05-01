# backend/app.py

# Main application file for QuizPro
# --------------------------------
# - Loads configuration and environment variables
# - Initializes Flask app, database, migrations, login, and CORS
# - Defines routes for user authentication, quiz setup, chat flow, and results

# --------------------------------
# Imports & SDK Configuration
# --------------------------------
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, session  # Core Flask components
from flask_cors import CORS  # Enable cross-origin requests for frontend static files
import os, json  # os for file paths/env, json for data serialization
from dotenv import load_dotenv  # Load .env file into environment
from .questions import *  # Quiz content helpers (extract text, parse JSON)
import os as _os  # alias to avoid collision with main os import
from .extensions import db, migrate, login_manager  # Initialize DB, migrations, and login manager
from flask_admin import Admin  # Admin UI for managing models
from flask_admin.contrib.sqla import ModelView  # SQLAlchemy views for admin
from flask_login import login_user, logout_user, current_user, login_required  # User session management
from .models import User, ApiKey, QuizSession, QuizQuestion  # ORM models
from .parser_pptx_json import pptx_to_json  # PPTX parsing utility
import google.generativeai as genai  # Google Gemini SDK for AI generation

# --------------------------------
# Environment & App Initialization
# --------------------------------
# Determine project root and load .env variables (SECRET_KEY, DATABASE_URL, GEMINI_API_KEY)
_root = _os.path.dirname(_os.path.dirname(__file__))
load_dotenv(_os.path.join(_root, '.env'))
print(f"[DEBUG] Database URI: {os.getenv('DATABASE_URL')}")

# Create Flask app, pointing to static files and Jinja2 templates
app = Flask(__name__, static_folder='../static', template_folder='../templates')
# Make Python's built-in zip() available in templates (e.g., pairing arrays)
app.jinja_env.globals.update(zip=zip)

# Configure secret key and database
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')  # Session and CSRF protection
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///quizpro.db')  # Connection string
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Disable event notifications to conserve resources

# Initialize extensions with the app context
CORS(app)            # Allow frontend JS to call these endpoints
db.init_app(app)     # Bind SQLAlchemy
migrate.init_app(app, db)  # Bind Alembic migrations
login_manager.init_app(app)  # Set up Flask-Login
login_manager.login_view = 'login'  # Redirect unauthorized to login page

# --------------------------------
# Ensure database tables exist before handling any request (development/demo)
# --------------------------------
@app.before_request
def initialize_database():
    # Create all tables defined by SQLAlchemy models (idempotent)
    db.create_all()

# --------------------------------
# Flask-Login User Loader
# --------------------------------
@login_manager.user_loader
# Given a user_id, load the corresponding User from the database
def load_user(user_id):
    return User.query.get(int(user_id))

# --------------------------------
# Helper: Retrieve Stored API Key
# --------------------------------
def get_user_api_key(model_name="gemini"):
    """
    Fetch the current_user's API key for the specified LLM model.
    Flashes an error and returns None if not found.
    """
    record = ApiKey.query.filter_by(user_id=current_user.id, model=model_name).first()
    if not record:
        flash(f"No API key saved for '{model_name}'. Please add one under Setup.", "error")
        return None
    return record.key

# --------------------------------
# Authentication Routes
# --------------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    User registration:
    GET  -> render registration form
    POST -> validate input, create new User, log them in, redirect to setup
    """
    if request.method == 'POST':
        email    = request.form['email']
        password = request.form['password']
        # Prevent duplicate registrations
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
    """
    User login:
    GET  -> render login form
    POST -> verify credentials, log in user, redirect to setup
    """
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
    """Log out the current user and redirect to login page."""
    logout_user()
    return redirect(url_for('login'))

# --------------------------------
# API Key Save Endpoint
# --------------------------------
@app.route('/api_key', methods=['POST'])
@login_required
def save_api_key():
    """
    Save or update the current user's AI service API key.
    Expects JSON payload: { model: 'gemini', key: 'XYZ' }
    Returns JSON status.
    """
    data = request.get_json() or {}
    model = data.get('model') or 'gemini'
    key = data.get('key')
    if not key:
        return jsonify(error="Missing API key"), 400
    # Upsert pattern: update if exists, else create
    record = ApiKey.query.filter_by(user_id=current_user.id, model=model).first()
    if record:
        record.key = key
    else:
        db.session.add(ApiKey(user_id=current_user.id, model=model, key=key))
    db.session.commit()
    return jsonify(status="ok", model=model, key=key), 200

# --------------------------------
# Root Redirect
# --------------------------------
@app.route('/')
@login_required
def index():
    """Redirect authenticated users to the quiz setup page."""
    return redirect(url_for('setup'))

# --------------------------------
# Quiz Setup Route
# --------------------------------
@app.route('/setup', methods=['GET', 'POST'])
@login_required
def setup():
    """
    Display or process the quiz setup form:
    - GET  -> render setup template with existing API key
    - POST -> handle PPTX upload or pasted text, build prompt, generate questions via LLM
    """
    # Fetch stored Gemini API key for current user
    gemini_record = ApiKey.query.filter_by(user_id=current_user.id, model='gemini').first()
    keys = {'gemini': gemini_record.key if gemini_record else ''}
    if request.method == 'POST':
        selected_model = 'gemini'
        # Use form API key input or fallback to stored
        api_key = request.form.get('apiKey') or keys['gemini']
        # Persist API key in database
        if api_key:
            if gemini_record:
                gemini_record.key = api_key
            else:
                gemini_record = ApiKey(user_id=current_user.id, model='gemini', key=api_key)
                db.session.add(gemini_record)
            db.session.commit()
            keys['gemini'] = api_key
        # Retrieve content inputs and combine slide text with pasted text
        pptx_file = request.files.get('pptxFile')
        pasted_text = (request.form.get('pastedText') or '').strip()
        content_parts = []
        # If a PPTX was uploaded, extract slide text
        if pptx_file and pptx_file.filename:
            slides_data = pptx_to_json(pptx_file)
            # Filter out title slide but include lines with dates (4-digit years) or substantive content
            import re
            filtered_slides = []
            for slide in slides_data.get('slides', [])[1:]:  # skip the first slide (title)
                lines = []
                for line in slide.get('text', []):
                    # include if substantive (>3 words) or contains a 4-digit year
                    if len(line.split()) > 3 or re.search(r'\b\d{4}\b', line):
                        lines.append(line)
                if lines:
                    filtered_slides.append(' '.join(lines))
            slide_texts = '\n\n'.join(filtered_slides)
            content_parts.append(slide_texts)
        # If the user pasted text, include it
        if pasted_text:
            content_parts.append(pasted_text)
        # Ensure there is some content
        if not content_parts:
            flash("Please upload a PPTX and/or paste some text.", "error")
            return render_template('setup.html', keys=keys)
        content_str = '\n\n'.join(content_parts)
        # Prompt LLM: no intros, start immediately with questions
        prompt = (
            f"Please list exactly 20 multiple-choice quiz questions based solely on the following content: {content_str}. "
            "Do not include any introductory or explanatory text—start directly with '1.'. "
            "Only generate questions on substantive topics and concepts; ignore metadata such as presenter names and slide header dates. "
            "However, if a date is part of the substantive content (e.g., date of an event), you may create questions about it. "
            "For each question, provide four options labeled A, B, C, D, then 'Answer: X' where X is the correct option. "
            "Separate each question with <|Q|>."
        )
        # Generate questions and parse to structured dicts
        questions = generate_questions(api_key, 'gemini', prompt)
        if not questions:
            flash("Error generating questions. Please check the API configuration.", "error")
            return render_template('setup.html', keys=keys)
        import re
        raw_items = questions.split('<|Q|>')
        parsed_qs = []
        for item in raw_items:
            lines = [l.strip() for l in item.splitlines() if l.strip()]
            if not lines:
                continue
            # Remove leading numbering (e.g., '1.')
            question_text = re.sub(r'^\d+\.\s*', '', lines[0])
            options = {}
            correct = None
            for line in lines[1:]:
                m = re.match(r'^([A-D])[\)\.\:]\s*(.*)', line)
                if m:
                    options[m.group(1)] = m.group(2).strip()
                    continue
                m2 = re.search(r'Answer[:\s]*([A-D])', line, re.IGNORECASE)
                if m2:
                    correct = m2.group(1)
            # Only keep entries with a valid correct answer and exactly 4 options
            if correct and len(options) == 4:
                parsed_qs.append({'prompt': question_text, 'options': options, 'answer': correct})
        # Initialize quiz in session and redirect
        session['questions'] = parsed_qs
        # Store desired total for progress display (always 20 questions)
        session['desired_total'] = 20
        session['answers'] = []
        session['current_question_index'] = 0
        return redirect(url_for('chat'))

    # GET request: render setup with stored Gemini key
    return render_template('setup.html', keys=keys)


# --------------------------------
# Chat Route: display and process quiz questions
# --------------------------------
@app.route('/chat', methods=['GET', 'POST'])
@login_required
def chat():
    """
    GET  -> render the next quiz question with options
    POST -> record the user's answer, advance index, redirect to next question or results
    """
    qs  = session.get('questions', [])
    idx = session.get('current_question_index', 0)
    # Skip any non-MCQ entries (e.g., free-response placeholder) at the start
    while idx < len(qs) and not qs[idx].get('options'):
        idx += 1
    session['current_question_index'] = idx

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
    # Always display the actual number of questions in the session
    total_questions = len(qs)
    return render_template('chat.html',
                           question=current,
                           index=idx+1,
                           total=total_questions)


# --------------------------------
# Results Route: show quiz summary and detailed feedback
# --------------------------------
@app.route('/results')
@login_required
def results():
    """
    Display overall performance, list each question with user and correct answers,
    and provide actions to retry incorrect or start a new quiz.
    """
    qs = session.get('questions', [])
    ans = session.get('answers', [])
    # Count incorrect answers
    wrong_count = sum(1 for q, a in zip(qs, ans) if a != q.get('answer'))
    total_answered = len(ans)
    # Calculate percentage wrong (rounded to nearest integer)
    percent_wrong = int((wrong_count / total_answered) * 100) if total_answered else 0
    # Determine if any answers were incorrect for UI flags
    incorrect = wrong_count > 0
    return render_template('results.html',
                           questions=qs,
                           answers=ans,
                           incorrect=incorrect,
                           wrong_count=wrong_count,
                           total_answered=total_answered,
                           percent_wrong=percent_wrong)


# --------------------------------
# Retry Incorrect Route: retake only missed questions
# --------------------------------
@app.route('/retry_incorrect', methods=['POST'])
@login_required
def retry_incorrect():
    """
    Filter stored questions to those answered incorrectly, reset session tracking,
    and redirect to chat for retrying these questions.
    """
    qs = session.get('questions', [])
    ans = session.get('answers', [])
    # Filter to only questions where user's answer != correct
    retry_qs = [q for q, a in zip(qs, ans) if a != q.get('answer')]
    if not retry_qs:
        flash('No incorrect questions to retry.', 'info')
        return redirect(url_for('results'))
    session['questions'] = retry_qs
    session['answers'] = []
    session['current_question_index'] = 0
    # Update display total to match retry set
    session['desired_total'] = len(retry_qs)
    return redirect(url_for('chat'))


# --------------------------------
# PPTX Upload API: parse slides and return JSON
# --------------------------------
@app.route('/upload_pptx', methods=['POST'])
@login_required
def upload_pptx():
    """
    Accept a PowerPoint file upload, parse it into JSON slide data,
    and return the slide texts in a JSON response.
    """
    file = request.files.get('file')
    if not file:
        return jsonify({'error': 'No file provided'}), 400
    data   = pptx_to_json(file)
    slides = data.get('slides', [])
    return jsonify({'slides': slides}), 200


# --------------------------------
# Helper: generate_questions via AI model
# --------------------------------
def generate_questions(api_key, model_name, prompt):
    """
    Configure the AI SDK with the provided key and model,
    send the prompt text to the model, and return its generated response.
    """
    if not api_key:
        return ""
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(f"{model_name}-2.0-flash")
    response = model.generate_content(prompt)
    return getattr(response, "text", response)


# --------------------------------
# Adaptive Follow-up Route: generate new questions on incorrect topics
# --------------------------------
@app.route('/adaptive_followup', methods=['POST'])
@login_required
def adaptive_followup():
    """
    Build a follow-up prompt for questions answered incorrectly,
    generate new MCQs, reset session, and redirect to chat for review.
    """
    # Fetch stored API key
    api_key = get_user_api_key()
    if not api_key:
        return redirect(url_for('setup'))
    # Get current quiz and answers from session
    qs = session.get('questions', [])
    ans = session.get('answers', [])
    # Filter incorrect questions
    wrong_qs = [q for q, a in zip(qs, ans) if a != q.get('answer')]
    if not wrong_qs:
        flash('No incorrect questions to generate follow-ups.', 'info')
        return redirect(url_for('results'))
    # Build a textual list of the mis-answered prompts
    import re
    payload_prompts = "\n".join([
        f"{i+1}. {re.sub(r'^\d+\.\s*', '', q['prompt'])}" for i, q in enumerate(wrong_qs)
    ])
    # Always generate exactly 10 follow-up questions
    num_followups = 10
    # Prompt LLM for follow-up quiz on the same topics, phrased differently
    prompt_text = (
        f"Here are the questions you answered incorrectly:\n{payload_prompts}\n"
        f"Please generate 10 new multiple-choice questions on these same topics, phrased differently. "
        "Provide four options labeled A, B, C, D, then 'Answer: X' for the correct option. "
        "Separate each question with <|Q|> and start immediately without any extra text."
    )
    raw = generate_questions(api_key, 'gemini', prompt_text)
    if not raw:
        flash('Error generating follow-up questions. Please try again.', 'error')
        return redirect(url_for('results'))
    # Parse generated follow-up questions
    items = raw.split('<|Q|>')
    followups = []
    for item in items:
        lines = [l.strip() for l in item.splitlines() if l.strip()]
        if not lines:
            continue
        question_text = re.sub(r'^\d+\.\s*', '', lines[0])
        options = {}
        correct = None
        for line in lines[1:]:
            m = re.match(r'^([A-D])[\)\.\:]\s*(.*)', line)
            if m:
                options[m.group(1)] = m.group(2).strip()
                continue
            m2 = re.search(r'Answer[:\s]*([A-D])', line, re.IGNORECASE)
            if m2:
                correct = m2.group(1)
        # Only include true MCQs with 4 options
        if correct and len(options) == 4:
            followups.append({'prompt': question_text, 'options': options, 'answer': correct})
    # Restart session with follow-up questions
    session['questions'] = followups
    session['answers'] = []
    session['current_question_index'] = 0
    # Update display total to match follow-up set
    session['desired_total'] = len(followups)
    return redirect(url_for('chat'))


# --------------------------------
# Application entry point
# --------------------------------
if __name__ == '__main__':
    # Start Flask in debug mode
    app.run(debug=True)
