# backend/models.py
# Defines the database models for QuizPro using SQLAlchemy ORM and Flask-Login.

from datetime import datetime
from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

# ------------------------------------------------------------------------------
# User Model
# Represents a registered user; inherits from UserMixin to support Flask-Login.
# Columns:
# - id: unique primary key
# - email: unique user email address
# - password_hash: hashed password for authentication
# - created_at: timestamp when the account was created
# Relationships:
# - api_keys: stored API keys for AI services
# - sessions: quiz sessions initiated by the user
# ------------------------------------------------------------------------------
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    api_keys = db.relationship('ApiKey', backref='user', lazy=True)
    # sessions initiated by user
    sessions = db.relationship('QuizSession', backref='user', lazy=True)

    def set_password(self, password):
        # Hashes and stores the user's plain-text password securely.
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        # Verifies a plain-text password against the stored hash.
        return check_password_hash(self.password_hash, password)

# ------------------------------------------------------------------------------
# ApiKey Model
# Associates a user with an external AI API key for a specific model.
# Columns:
# - id: unique primary key
# - user_id: links to User.id via ForeignKey
# - model: name of the AI model (e.g., 'gemini')
# - key: the actual API key string
# - created_at: timestamp when the key was added
# Unique constraint ensures one key per user-model pair.
# ------------------------------------------------------------------------------
class ApiKey(db.Model):
    __tablename__ = 'api_key'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    model = db.Column(db.String(50), nullable=False)
    key = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('user_id', 'model', name='uq_user_model'),)

# ------------------------------------------------------------------------------
# QuizSession Model
# Groups multiple QuizQuestion entries as part of one quiz attempt.
# Columns:
# - id: unique primary key
# - user_id: links to User.id to attribute the session
# - created_at: timestamp when the quiz session started
# Relationships:
# - questions: list of QuizQuestion records in this session
# ------------------------------------------------------------------------------
class QuizSession(db.Model):
    __tablename__ = 'quiz_session'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    questions = db.relationship('QuizQuestion', backref='session', lazy=True)

# ------------------------------------------------------------------------------
# QuizQuestion Model
# Stores each individual question prompt and user-provided answer.
# Columns:
# - id: unique primary key
# - session_id: links to QuizSession.id to group questions
# - index: numeric order of question within session
# - prompt: text of the quiz question
# - user_answer: the response submitted by the user
# - created_at: timestamp when the question was generated/answered
# ------------------------------------------------------------------------------
class QuizQuestion(db.Model):
    __tablename__ = 'quiz_question'
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('quiz_session.id'), nullable=False)
    index = db.Column(db.Integer, nullable=False)
    prompt = db.Column(db.Text, nullable=False)
    user_answer = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
