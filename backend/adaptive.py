from .models import TopicPerformance
from .extensions import db


def record_performance(user_id, question):
    """Record each attempt and whether it was correct to update TopicPerformance."""
    topic = getattr(question, 'topic', None)
    if not topic:
        return
    perf = TopicPerformance.query.filter_by(user_id=user_id, topic=topic).first()
    if not perf:
        perf = TopicPerformance(user_id=user_id, topic=topic, attempts=0, correct=0)
        db.session.add(perf)
    perf.attempts += 1
    if getattr(question, 'is_correct', False):
        perf.correct += 1
    db.session.commit()


def get_poor_topics(user_id, threshold=0.7):
    """Return a list of topics where the user's accuracy is below the threshold."""
    perfs = TopicPerformance.query.filter_by(user_id=user_id).all()
    return [p.topic for p in perfs if p.attempts > 0 and (p.correct / p.attempts) < threshold]


def order_questions(questions, poor_topics):
    """Reorder questions so those from poor_topics appear first."""
    poor = [q for q in questions if getattr(q, 'topic', None) in poor_topics]
    rest = [q for q in questions if getattr(q, 'topic', None) not in poor_topics]
    return poor + rest 