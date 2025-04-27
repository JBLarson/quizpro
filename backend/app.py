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

# Create Flask app
app = Flask(__name__, static_folder='../static', template_folder='../templates')
# Make Python's built-in zip() available in Jinja templates
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


# ----- Helper to fetch the stored API key -----
def get_user_api_key(model_name="gemini"):
    """Retrieve the current_user's API key for the given model."""
    record = ApiKey.query.filter_by(user_id=current_user.id, model=model_name).first()
    if not record:
        flash(f"No API key saved for '{model_name}'. Please add one under Setup.", "error")
        return None
    return record.key


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
@app.route('/api_key', methods=['POST'])
@login_required
def save_api_key():
    data = request.get_json() or {}
    model = data.get('model') or 'gemini'
    key = data.get('key')
    if not key:
        return jsonify(error="Missing API key"), 400
    # Upsert API key record for the user and model
    record = ApiKey.query.filter_by(user_id=current_user.id, model=model).first()
    if record:
        record.key = key
    else:
        db.session.add(ApiKey(user_id=current_user.id, model=model, key=key))
    db.session.commit()
    return jsonify(status="ok", model=model, key=key), 200

@app.route('/')
@login_required
def index():
    # Redirect root to setup since index.html is removed
    return redirect(url_for('setup'))


@app.route('/setup', methods=['GET', 'POST'])
@login_required
def setup():
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


@app.route('/chat', methods=['GET', 'POST'])
@login_required
def chat():
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


@app.route('/results')
@login_required
def results():
    qs = session.get('questions', [])
    ans = session.get('answers', [])
    # Determine if any answers were incorrect
    incorrect = any(a != q.get('answer') for q, a in zip(qs, ans))
    return render_template('results.html',
                           questions=qs,
                           answers=ans,
                           incorrect=incorrect)


# Route to retry only the questions the user got wrong
@app.route('/retry_incorrect', methods=['POST'])
@login_required
def retry_incorrect():
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


# ----- Helper Functions -----
def generate_questions(api_key, model_name, prompt):
    """Configure per-call and generate via Gemini."""
    if not api_key:
        return ""
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(f"{model_name}-2.0-flash")
    response = model.generate_content(prompt)
    return getattr(response, "text", response)


@app.route('/adaptive_followup', methods=['POST'])
@login_required
def adaptive_followup():
    """Generate follow-up MCQs on topics you got wrong."""
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


if __name__ == '__main__':
    app.run(debug=True)
