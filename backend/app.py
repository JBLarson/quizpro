from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
from dotenv import load_dotenv
load_dotenv()  # load variables from .env into environment
from .extensions import db, migrate
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

app = Flask(__name__, static_folder='../static', template_folder='../templates')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///quizpro.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
CORS(app)
db.init_app(app)
migrate.init_app(app, db)

# import models after extensions are set up to avoid circular imports
from .models import Presentation, Slide, Question

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/extract_text', methods=['POST'])
def extract_text():
    # Handle PPTX file upload and extract text from slides
    pptx_file = request.files.get('file')
    # TODO: Replace with actual PPTX extraction logic
    slides_texts = ['Sample slide 1', 'Sample slide 2']
    # Create a new Presentation record
    pres = Presentation(title=pptx_file.filename if pptx_file else 'Untitled')
    db.session.add(pres)
    db.session.commit()
    slides_response = []
    for idx, content in enumerate(slides_texts):
        slide = Slide(presentation_id=pres.id, index=idx, content=content)
        db.session.add(slide)
        slides_response.append({'id': slide.id, 'index': slide.index, 'content': slide.content})
    db.session.commit()
    return jsonify({'presentation_id': pres.id, 'slides': slides_response})

@app.route('/quiz', methods=['POST'])
def quiz():
    data = request.get_json()
    slide_id = data.get('slide_id')
    slide = Slide.query.get_or_404(slide_id)
    # TODO: Replace with actual quiz generation logic based on slide.content
    prompt = f'Quiz question for slide {slide_id}'
    question = Question(slide_id=slide.id, prompt=prompt)
    db.session.add(question)
    db.session.commit()
    return jsonify({'question_id': question.id, 'prompt': question.prompt})

@app.route('/evaluate', methods=['POST'])
def evaluate():
    data = request.get_json()
    question_id = data.get('question_id')
    answer = data.get('answer')
    question = Question.query.get_or_404(question_id)
    # TODO: Replace with actual evaluation logic
    question.answer = answer
    db.session.commit()
    result = 'correct'
    explanation = 'Sample explanation.'
    return jsonify({'result': result, 'explanation': explanation})

# route for api key setup
@app.route('/setup')
def setup():
    return render_template('setup.html')

# route for chat configuration
@app.route('/config')
def config():
    return render_template('config.html')


# route for adding content
@app.route('/content')
def content():
    return render_template('content.html')

admin = Admin(app, name="QuizPro Admin", template_mode="bootstrap4")
admin.add_view(ModelView(Presentation, db.session))
admin.add_view(ModelView(Slide,      db.session))
admin.add_view(ModelView(Question,   db.session))

if __name__ == '__main__':
    app.run(debug=True) 