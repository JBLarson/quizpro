# tests/test_adaptive.py
import pytest
from backend.adaptive import order_questions

class DummyQuestion:
    def __init__(self, topic):
        self.topic = topic

def test_order_questions_puts_poor_topics_first():
    # Setup dummy questions with topics
    q1 = DummyQuestion('math')
    q2 = DummyQuestion('history')
    q3 = DummyQuestion('science')
    questions = [q1, q2, q3]
    # Define poor topics threshold results
    poor_topics = ['science', 'math']
    ordered = order_questions(questions, poor_topics)
    # Poor-topic questions should come first in original relative order
    assert ordered[0].topic in poor_topics
    assert ordered[1].topic in poor_topics
    # Remaining topics follow
    assert ordered[-1].topic not in poor_topics 