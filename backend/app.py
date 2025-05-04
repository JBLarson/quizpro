# backend/app.py

# Main application file for QuizPro
# --------------------------------
# - Loads configuration and environment variables
# - Initializes Flask app, database, migrations, login, and CORS
# - Defines routes for user authentication, quiz setup, chat flow, and results

# --------------------------------
# Imports & SDK Configuration
# --------------------------------
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, session, abort  # Core Flask components
from flask_cors import CORS  # Enable cross-origin requests for frontend static files
import os, json  # os for file paths/env, json for data serialization
from dotenv import load_dotenv  # Load .env file into environment
from .questions import *  # Quiz content helpers (extract text, parse JSON)
import os as _os  # alias to avoid collision with main os import
from .extensions import db, migrate, login_manager  # Initialize DB, migrations, and login manager
from flask_admin import Admin  # Admin UI for managing models
from flask_admin.contrib.sqla import ModelView  # SQLAlchemy views for admin
from flask_login import login_user, logout_user, current_user, login_required  # User session management
from .models import User, ApiKey, QuizSession, QuizQuestion, ChatMessage  # ORM models
from .parser_pptx_json import pptx_to_json  # PPTX parsing utility
from .parser_pdf_text import pdf_to_text  # PDF parsing utility
from .parser_docx_text import docx_to_text  # DOCX parsing utility
from .parser_xlsx_text import xlsx_to_text  # XLSX parsing utility
import google.genai as genai  # Google GenAI SDK for Gemini
import random

# --------------------------------
# Environment & App Initialization
# --------------------------------
# Determine project root and load .env variables (SECRET_KEY, DATABASE_URL, GEMINI_API_KEY)
_root = _os.path.dirname(_os.path.dirname(__file__))
load_dotenv(_os.path.join(_root, '.env'))
print(f"[DEBUG] Database URI: {os.getenv('DATABASE_URL')}")

# Create Flask app, pointing to static files and Jinja2 templates
app = Flask(__name__, static_folder='../static', template_folder='../templates')
# Hardcoded API keys for models (loaded from env or defaults)
app.config['GEMINI_API_KEY'] = os.getenv('GEMINI_API_KEY', '')
app.config['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY', '')
app.config['DEEPSEEK_API_KEY'] = os.getenv('DEEPSEEK_API_KEY', '')
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
    # Build session history for sidebar
    user_sessions = QuizSession.query.filter_by(user_id=current_user.id) \
        .order_by(QuizSession.created_at.desc()).all()
    sessions_stats = []
    for idx, s in enumerate(user_sessions, start=1):
        qs = QuizQuestion.query.filter_by(session_id=s.id).all()
        total = len(qs)
        correct = sum(1 for q in qs if q.user_answer == q.correct_answer)
        # include title if set, else fallback to Session #{idx}
        sessions_stats.append({
            'id': s.id,
            'title': s.title or f"Session {idx}",
            'created_at': s.created_at,
            'status': s.status,
            'total': total,
            'correct': correct
        })
    # Default selectors for GET
    selected_model = 'gemini'
    question_type = 'multiple_choice'
    num_questions = 20

    if request.method == 'POST':
        # Read selected LLM model
        selected_model = request.form.get('modelSelect', 'gemini')
        # Get API key from server config
        if selected_model == 'gemini':
            api_key = app.config['GEMINI_API_KEY']
        elif selected_model == 'openai':
            api_key = app.config['OPENAI_API_KEY']
        elif selected_model == 'deepseek':
            api_key = app.config['DEEPSEEK_API_KEY']
        else:
            api_key = None
        # Quiz options
        question_type = request.form.get('questionType', 'multiple_choice')
        try:
            num_questions = int(request.form.get('numQuestions', 20))
        except (TypeError, ValueError):
            num_questions = 20
        # Retrieve multiple file uploads and pasted text
        content_files = request.files.getlist('contentFiles') or []
        pasted_text = (request.form.get('pastedText') or '').strip()
        content_parts = []
        import re
        # Process up to 5 uploaded files
        for content_file in content_files[:5]:
            if content_file and content_file.filename:
                filename = content_file.filename.lower()
                if filename.endswith('.pptx'):
                    slides_data = pptx_to_json(content_file)
                    filtered_slides = []
                    for slide in slides_data.get('slides', [])[1:]:
                        lines = [line for line in slide.get('text', []) if len(line.split()) > 3 or re.search(r"\b\d{4}\b", line)]
                        if lines:
                            filtered_slides.append(' '.join(lines))
                    if filtered_slides:
                        content_parts.append('\n\n'.join(filtered_slides))
                elif filename.endswith('.pdf'):
                    content_parts.append(pdf_to_text(content_file))
                elif filename.endswith('.docx'):
                    content_parts.append(docx_to_text(content_file))
                elif filename.endswith('.xlsx'):
                    content_parts.append(xlsx_to_text(content_file))
                else:
                    content_file.seek(0)
                    content_parts.append(content_file.read().decode('utf-8', errors='ignore'))
        # Include pasted text
        if pasted_text:
            content_parts.append(pasted_text)
        # Ensure there is some content
        if not content_parts:
            flash("Please upload a file or paste some text.", "error")
            return render_template('setup.html', sessions=sessions_stats,
                                   selected_model=selected_model,
                                   question_type=question_type,
                                   num_questions=num_questions)
        content_str = '\n\n'.join(content_parts)
        # Prompt LLM: ask for a title, then the questions
        # Build dynamic prompt based on question type and count
        if question_type == 'multiple_choice':
            prompt = (
                "Give your quiz a concise, professional, and studious title that clearly references the subject matter being studied on the first line prefixed with 'Title: '. "
                f"Then list exactly {num_questions} multiple-choice quiz questions based solely on the following content: {content_str}. "
                "Ensure the correct answer is not always in the same position and that distractors are plausible, covering common misconceptions. "
                "Do not include any other text before the title or questions. "
                "Start each question directly with numbering (e.g., '1.'). "
                "For each question, provide four options labeled A, B, C, D, then 'Answer: X' where X is the correct option. "
                "Separate each question with <|Q|>."
            )
        else:
            prompt = (
                "Give your quiz a concise, professional, and studious title that clearly references the subject matter being studied on the first line prefixed with 'Title: '. "
                f"Then list exactly {num_questions} free-response quiz questions based solely on the following content: {content_str}. "
                "Do not include any other text before the title or questions. "
                "Start each question directly with numbering (e.g., '1.') on its own line. "
                "After each question, on a new line prefix 'Answer: ' followed by the complete answer. "
                "Separate each question with <|Q|>."
            )
        # Generate questions and parse to structured dicts
        questions = generate_questions(api_key, selected_model, prompt)
        print("[DEBUG] raw quiz string:", questions)
        # Attempt to extract a title line if AI provided one in the format "Title: ..."
        title = None
        lines = questions.splitlines()
        if lines and lines[0].lower().startswith('title:'):
            title = lines[0].split(':', 1)[1].strip()
            # remove title from questions body
            questions_body = '\n'.join(lines[1:])
        else:
            questions_body = questions
        if not questions_body:
            flash("Error generating questions. Please check the API configuration.", "error")
            return render_template('setup.html', sessions=sessions_stats,
                                   selected_model=selected_model,
                                   question_type=question_type,
                                   num_questions=num_questions)
        raw_items = questions_body.split('<|Q|>')
        parsed_qs = []
        for item in raw_items:
            lines = [l.strip() for l in item.splitlines() if l.strip()]
            if not lines:
                continue
            question_text = re.sub(r'^\d+\.\s*', '', lines[0])
            if question_type == 'multiple_choice':
                options = {}
                correct = None
                for line in lines[1:]:
                    m = re.match(r'^([A-D])[\)\.:]\s*(.*)', line)
                    if m:
                        options[m.group(1)] = m.group(2).strip()
                        continue
                    m2 = re.search(r'Answer[:\s]*([A-D])', line, re.IGNORECASE)
                    if m2:
                        correct = m2.group(1)
                if correct and len(options) == 4:
                    parsed_qs.append({'prompt': question_text, 'options': options, 'answer': correct})
            else:
                answer = ''
                for line in lines[1:]:
                    m2 = re.match(r'^Answer[:\s]*(.*)', line, re.IGNORECASE)
                    if m2:
                        answer = m2.group(1).strip()
                        break
                if answer:
                    parsed_qs.append({'prompt': question_text, 'options': {}, 'answer': answer})
        # Shuffle MC options so initial sessions have varied order
        if question_type == 'multiple_choice':
            import random
            for qst in parsed_qs:
                items = list(qst['options'].items())
                random.shuffle(items)
                opt_map = {}
                ans_map = None
                for i, (old_letter, text) in enumerate(items):
                    letter = chr(ord('A') + i)
                    opt_map[letter] = text
                    if old_letter == qst['answer']:
                        ans_map = letter
                qst['options'] = opt_map
                qst['answer'] = ans_map
        # Persist a new quiz session and its questions
        new_session = QuizSession(
            user_id=current_user.id,
            session_type='quiz',
            question_type=question_type,
            num_questions=num_questions
        )
        # Save extracted title if present
        if title:
            new_session.title = title
        db.session.add(new_session)
        db.session.commit()
        # Save each question to the database
        for idx, q in enumerate(parsed_qs):
            qq = QuizQuestion(
                session_id=new_session.id,
                question_index=idx,
                prompt=q['prompt'],
                options=q['options'],
                correct_answer=q['answer']
            )
            db.session.add(qq)
        db.session.commit()
        # Track this quiz in user session for navigation
        session.pop('quiz_session_id', None)
        session.pop('current_question_index', None)
        session['quiz_session_id'] = new_session.id
        session['current_question_index'] = 0
        return redirect(url_for('chat'))

    # GET: render setup with default selectors
    return render_template('setup.html', sessions=sessions_stats,
                           selected_model=selected_model,
                           question_type=question_type,
                           num_questions=num_questions)


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
    # Fetch current quiz session
    session_id = session.get('quiz_session_id')
    # Load session object to get title
    session_obj = QuizSession.query.get(session_id)
    quiz_title = session_obj.title or f"Quiz Session {session_obj.id}"
    if not session_id:
        flash('No active quiz. Please start a quiz.', 'info')
        return redirect(url_for('setup'))
    # Load questions from DB
    qs = QuizQuestion.query.filter_by(session_id=session_id).order_by(QuizQuestion.question_index).all()
    if not qs:
        flash('No questions found for this quiz.', 'info')
        return redirect(url_for('setup'))
    idx = session.get('current_question_index', 0)
    # Ensure idx is within bounds
    if idx >= len(qs):
        return redirect(url_for('results'))

    if request.method == 'POST':
        # Record user answer in DB
        answer = request.form.get('answer', '').strip()
        q = qs[idx]
        q.user_answer = answer
        from datetime import datetime
        q.answered_at = datetime.utcnow()
        db.session.commit()
        idx += 1
        session['current_question_index'] = idx

        if idx < len(qs):
            return redirect(url_for('chat'))
        return redirect(url_for('results'))

    # Render next question
    current = qs[idx]
    total_questions = len(qs)
    return render_template('chat.html', question=current, index=idx+1,
                           total=total_questions, title=quiz_title)


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
    # Fetch current quiz session
    session_id = session.get('quiz_session_id')
    if not session_id:
        flash('No completed quiz to show results for.', 'info')
        return redirect(url_for('setup'))
    # Load session to get title
    session_obj = QuizSession.query.get(session_id)
    title = session_obj.title or f"Session {session_id}"
    qs = QuizQuestion.query.filter_by(session_id=session_id).order_by(QuizQuestion.question_index).all()
    ans = [q.user_answer for q in qs]
    total_answered = len(qs)
    wrong_count = sum(1 for q in qs if q.user_answer != q.correct_answer)
    percent_wrong = int((wrong_count / total_answered) * 100) if total_answered else 0
    incorrect = wrong_count > 0
    # Evaluate free-response answers via AI
    # Fetch user's API key
    gemini_record = ApiKey.query.filter_by(user_id=current_user.id, model='gemini').first()
    api_key = gemini_record.key if gemini_record else None
    evaluations = []
    for q in qs:
        if not q.options:
            # free-response: evaluate
            ev = evaluate_answer(api_key, 'gemini', q.prompt, q.user_answer or '', q.correct_answer)
        else:
            ev = None
        evaluations.append(ev)
    return render_template('results.html',
                           title=title,
                           questions=qs,
                           answers=ans,
                           evaluations=evaluations,
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
    Create a new quiz session for only the questions answered incorrectly.
    """
    session_id = session.get('quiz_session_id')
    if not session_id:
        flash('No active quiz session. Please start a quiz.', 'info')
        return redirect(url_for('setup'))
    # Load incorrect questions from DB
    wrong_qs = QuizQuestion.query.filter_by(session_id=session_id).\
               filter(QuizQuestion.user_answer != QuizQuestion.correct_answer).all()
    if not wrong_qs:
        flash('No incorrect questions to retry.', 'info')
        return redirect(url_for('results'))
    # Create new quiz session preserving type and count based on wrong questions
    orig = QuizSession.query.get(session_id)
    new_session = QuizSession(
        user_id=current_user.id,
        session_type='quiz',
        question_type=orig.question_type,
        num_questions=len(wrong_qs)
    )
    db.session.add(new_session)
    db.session.commit()
    # Persist only wrong questions to new session
    for idx, q in enumerate(wrong_qs):
        new_q = QuizQuestion(
            session_id=new_session.id,
            question_index=idx,
            prompt=q.prompt,
            options=q.options,
            correct_answer=q.correct_answer
        )
        db.session.add(new_q)
    db.session.commit()
    # Reset session tracking
    session.pop('quiz_session_id', None)
    session.pop('current_question_index', None)
    session['quiz_session_id'] = new_session.id
    session['current_question_index'] = 0
    return redirect(url_for('chat'))


# --------------------------------
# Retry Same Quiz Route: retake all questions with shuffled options
@app.route('/retry_same', methods=['POST'])
@login_required
def retry_same():
    """
    Create a new quiz session with the same questions (shuffled options for MC).
    """
    session_id = session.get('quiz_session_id')
    if not session_id:
        flash('No active quiz session to retry.', 'info')
        return redirect(url_for('setup'))
    orig = QuizSession.query.get(session_id)
    # Load all questions from original session
    all_qs = QuizQuestion.query.filter_by(session_id=session_id).order_by(QuizQuestion.question_index).all()
    # Create new session copying type/count/title
    new_session = QuizSession(
        user_id=current_user.id,
        session_type=orig.session_type,
        question_type=orig.question_type,
        num_questions=orig.num_questions,
        title=orig.title
    )
    db.session.add(new_session)
    db.session.commit()
    # Clone and (if MC) shuffle options
    for q in all_qs:
        if q.options:
            items = list(q.options.items())
            # identify correct text
            correct_text = q.options.get(q.correct_answer)
            random.shuffle(items)
            new_opts = {}
            new_correct = None
            for idx, (_, text) in enumerate(items):
                letter = chr(ord('A') + idx)
                new_opts[letter] = text
                if text == correct_text:
                    new_correct = letter
        else:
            new_opts = {}
            new_correct = q.correct_answer
        new_q = QuizQuestion(
            session_id=new_session.id,
            question_index=q.question_index,
            prompt=q.prompt,
            options=new_opts,
            correct_answer=new_correct
        )
        db.session.add(new_q)
    db.session.commit()
    session['quiz_session_id'] = new_session.id
    session['current_question_index'] = 0
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
    Use Google GenAI client to send the prompt text and return its generated response.
    """
    if not api_key:
        return ""
    # Initialize the GenAI client with API key
    client = genai.Client(api_key=api_key)
    # Call the GenAI model, handling overloads or API errors gracefully
    try:
        response = client.models.generate_content(
            model=f"{model_name}-2.0-flash",
            contents=[{"text": prompt}],
            config={"temperature": 0.2, "max_output_tokens": 512}
        )
    except Exception as e:
        # Handle API errors (e.g., model overload) and other exceptions
        print(f"[ERROR] GenAI API call failed: {e}")
        return ""
    # Extract the generated text from the first candidate's content parts
    text = ""
    if response and getattr(response, 'candidates', None):
        content = response.candidates[0].content
        # Combine all text parts into a single string
        text = "".join(part.text or "" for part in (content.parts or []))
    return text


# --------------------------------
# Helper: evaluate free-response answers via AI model
# --------------------------------
def evaluate_answer(api_key, model_name, question_text, user_ans, correct_ans):
    """
    Use AI to judge a free-response answer against the correct answer.
    Returns a dict with 'status' (Correct/Partially Correct/Incorrect) and 'explanation'.
    """
    if not api_key:
        return {'status': 'Error', 'explanation': 'No API key.'}
    client = genai.Client(api_key=api_key)
    # Build evaluation prompt
    eval_prompt = (
        f"Here is a quiz question: \"{question_text}\". "
        f"The correct answer is: \"{correct_ans}\". "
        f"The student's answer is: \"{user_ans}\". "
        "Assess if the student's answer demonstrates understanding of the topic. "
        "Respond in the exact format:\nStatus: <Correct|Partially Correct|Incorrect>\nExplanation: <brief reasoning>."
    )
    try:
        response = client.models.generate_content(
            model=f"{model_name}-2.0-flash",
            contents=[{"text": eval_prompt}],
            config={"temperature": 0.0, "max_output_tokens": 256}
        )
    except Exception as e:
        print(f"[ERROR] Evaluation API call failed: {e}")
        return {'status': 'Error', 'explanation': 'Evaluation call failed.'}
    # Extract text
    raw = ""
    if response and getattr(response, 'candidates', None):
        parts = response.candidates[0].content.parts or []
        raw = "".join(part.text or "" for part in parts)
    # Parse Status and Explanation
    status = ''
    explanation = ''
    for line in raw.splitlines():
        if line.lower().startswith('status:'):
            status = line.split(':',1)[1].strip()
        elif line.lower().startswith('explanation:'):
            explanation = line.split(':',1)[1].strip()
    if not status:
        status = 'Error'
    return {'status': status, 'explanation': explanation}


# --------------------------------
# Adaptive Follow-up Route: generate new questions on incorrect topics
# --------------------------------
@app.route('/adaptive_followup', methods=['POST'])
@login_required
def adaptive_followup():
    """
    Generate new follow-up quiz on topics user got wrong, using AI and DB.
    """
    api_key = get_user_api_key()
    if not api_key:
        return redirect(url_for('setup'))
    session_id = session.get('quiz_session_id')
    if not session_id:
        flash('No active quiz session. Please start a quiz.', 'info')
        return redirect(url_for('setup'))
    # Load incorrect questions from DB
    wrong_qs = QuizQuestion.query.filter_by(session_id=session_id)\
               .filter(QuizQuestion.user_answer != QuizQuestion.correct_answer).all()
    if not wrong_qs:
        flash('No incorrect questions to generate follow-ups.', 'info')
        return redirect(url_for('results'))
    # Build AI prompt list
    import re
    payload_prompts = "\n".join([f"{i+1}. {re.sub(r'^\d+\.\s*', '', q.prompt)}" for i, q in enumerate(wrong_qs)])
    prompt_text = (
        f"Here are the questions you answered incorrectly:\n{payload_prompts}\n"
        "Please generate 10 new multiple-choice questions on these same topics, phrased differently. "
        "Provide four options labeled A, B, C, D, then 'Answer: X' for the correct option. "
        "Separate each question with <|Q|> and start immediately without any extra text."
    )
    raw = generate_questions(api_key, 'gemini', prompt_text)
    if not raw:
        flash('Error generating follow-up questions. Please try again.', 'error')
        return redirect(url_for('results'))
    # Parse AI output
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
        if correct and len(options) == 4:
            followups.append({'prompt': question_text, 'options': options, 'answer': correct})
    if not followups:
        flash('No follow-up questions generated. Please try again.', 'error')
        return redirect(url_for('results'))
    # Create new quiz session for follow-ups
    new_session = QuizSession(
        user_id=current_user.id,
        session_type='quiz',
        question_type='multiple_choice',
        num_questions=len(followups)
    )
    db.session.add(new_session)
    db.session.commit()
    for idx, f in enumerate(followups):
        qq = QuizQuestion(
            session_id=new_session.id,
            question_index=idx,
            prompt=f['prompt'],
            options=f['options'],
            correct_answer=f['answer']
        )
        db.session.add(qq)
    db.session.commit()
    session.pop('quiz_session_id', None)
    session.pop('current_question_index', None)
    session['quiz_session_id'] = new_session.id
    session['current_question_index'] = 0
    return redirect(url_for('chat'))


# --------------------------------
# Delete Session Route
# --------------------------------
@app.route('/sessions/<int:session_id>/delete', methods=['POST'])
@login_required
def delete_session(session_id):
    """Delete a quiz session and its associated questions and messages."""
    s = QuizSession.query.get_or_404(session_id)
    if s.user_id != current_user.id:
        abort(403)
    # delete related records
    QuizQuestion.query.filter_by(session_id=session_id).delete()
    ChatMessage.query.filter_by(session_id=session_id).delete()
    db.session.delete(s)
    db.session.commit()
    flash('Quiz session deleted.', 'success')
    return redirect(url_for('setup'))


# --------------------------------
# Session Rename Route
# --------------------------------
@app.route('/sessions/<int:session_id>/rename', methods=['POST'])
@login_required
def rename_session(session_id):
    """Rename a quiz session title via AJAX."""
    s = QuizSession.query.get_or_404(session_id)
    if s.user_id != current_user.id:
        abort(403)
    data = request.get_json() or {}
    new_title = data.get('title', '').strip()
    if not new_title:
        return jsonify(error='Invalid title'), 400
    s.title = new_title
    db.session.commit()
    return jsonify(status='ok', title=s.title)


# --------------------------------
# Session History Routes
# --------------------------------
@app.route('/sessions')
@login_required
def sessions_list():
    """Show all quiz/chat sessions for the current user."""
    user_sessions = QuizSession.query.filter_by(user_id=current_user.id) \
        .order_by(QuizSession.created_at.desc()).all()
    stats = []
    for s in user_sessions:
        qs = QuizQuestion.query.filter_by(session_id=s.id).all()
        total = len(qs)
        correct = sum(1 for q in qs if q.user_answer == q.correct_answer)
        stats.append({
            'id': s.id,
            'title': s.title or f"Session {s.id}",
            'created_at': s.created_at,
            'status': s.status,
            'total': total,
            'correct': correct
        })
    return render_template('sessions.html', sessions=stats)

@app.route('/sessions/<int:session_id>/resume')
@login_required
def resume_session(session_id):
    """Restore a past session and redirect to the quiz/chat at the next unanswered question."""
    s = QuizSession.query.get_or_404(session_id)
    if s.user_id != current_user.id:
        abort(403)
    qs = QuizQuestion.query.filter_by(session_id=session_id) \
        .order_by(QuizQuestion.question_index).all()
    next_idx = 0
    for idx, q in enumerate(qs):
        if not q.user_answer:
            next_idx = idx
            break
        next_idx = idx + 1
    session.pop('quiz_session_id', None)
    session.pop('current_question_index', None)
    session['quiz_session_id'] = session_id
    session['current_question_index'] = next_idx
    return redirect(url_for('chat'))


# --------------------------------
# Application entry point
# --------------------------------
if __name__ == '__main__':
    # Start Flask in debug mode
    app.run(debug=True)
