# tests/test_hints_ui.py
import pytest
from backend.app import app
from backend.extensions import db
from backend.models import User, QuizSession, QuizQuestion

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
        with app.app_context():
            db.drop_all()


def login_user(client):
    # Create and log in a test user by setting session directly
    user = User(email='test@example.com')
    user.set_password('password')
    db.session.add(user)
    db.session.commit()
    with client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
    return user


def test_hint_and_explanation_ui(client):
    user = login_user(client)
    # Create a quiz session and a question with hint and explanation
    quiz = QuizSession(user_id=user.id)
    db.session.add(quiz)
    db.session.commit()
    question = QuizQuestion(
        session_id=quiz.id,
        question_index=0,
        prompt='Test Prompt',
        options={},
        correct_answer='',
        hint='Sample hint',
        explanation='Sample explanation'
    )
    db.session.add(question)
    db.session.commit()
    # Set session vars to point at our quiz and question
    with client.session_transaction() as sess:
        sess['quiz_session_id'] = quiz.id
        sess['current_question_index'] = 0

    # Access the chat page
    response = client.get('/chat')
    html = response.get_data(as_text=True)

    # Assert that hint and explanation UI elements are present
    assert 'id="hint-btn"' in html
    assert 'id="hint-text"' in html
    assert 'id="explanation-text"' in html 