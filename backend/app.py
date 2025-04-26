from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os

app = Flask(__name__, static_folder='../static', template_folder='../templates')
CORS(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/extract_text', methods=['POST'])
def extract_text():
    # TODO: Implement pptx extraction
    return jsonify({'slides': ['Sample slide 1', 'Sample slide 2']})

@app.route('/quiz', methods=['POST'])
def quiz():
    # TODO: Implement quiz generation
    return jsonify({'question': 'Sample question?'})

@app.route('/evaluate', methods=['POST'])
def evaluate():
    # TODO: Implement answer evaluation
    return jsonify({'result': 'correct', 'explanation': 'Sample explanation.'})

# route for api key setup
@app.route('/setup')
def setup():
    return render_template('setup.html')







if __name__ == '__main__':
    app.run(debug=True) 