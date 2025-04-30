# backend/extensions.py
# Initializes Flask extensions used throughout the QuizPro application.

# SQLAlchemy: ORM for database models
from flask_sqlalchemy import SQLAlchemy
# Migrate: handles database migrations (schema changes)
from flask_migrate import Migrate
# LoginManager: manages user session and authentication
from flask_login import LoginManager

# Create extension instances (not yet bound to app)
# db: exposes the SQLAlchemy object for defining and querying models
db = SQLAlchemy()
# migrate: binds Alembic migrations to the SQLAlchemy db
migrate = Migrate()
# login_manager: controls the Flask-Login login process
login_manager = LoginManager()
# login_manager.login_view: default view to redirect unauthorized users
login_manager.login_view = 'login' 