# QuizPro

**QuizPro** is a full-stack web application that transforms PowerPoint presentations into interactive AI-powered quizzes. Users can upload `.pptx` files, configure quiz parameters, and receive multiple-choice questions generated and evaluated by modern LLMs.

---

## 🚀 Features
- **Slide Parsing**: Extract text content from PPTX slides on the backend using Python.
- **AI Question Generation**: Generate 20 multiple-choice quiz questions via Google Gemini or OpenAI.
- **Answer Evaluation**: Real-time grading with explanations for correct/incorrect answers.
- **Customization**: Configure quiz tone (casual/professional), difficulty (easy/medium/hard), and style (MCQ/open-ended).
- **User Accounts**: Register and log in to securely save API keys and quiz history.
- **Admin Interface**: Built-in admin panel (Flask-Admin) to manage users, API keys, and quiz sessions.

---

## 🏗 Architecture
```
quizpro/
├── backend/            # Flask API + business logic
│   ├── app.py          # Main Flask routes and app factory
│   ├── extensions.py   # DB, migration, login extensions
│   ├── models.py       # SQLAlchemy models: User, ApiKey, QuizSession, QuizQuestion
│   ├── questions.py    # Helpers for parsing/generating quiz text
│   ├── parser_pptx_json.py  # PPTX → JSON slide extractor
│   └── gemini.py       # Google Gemini AI SDK wrapper
│   └── requirements.txt
│   └── .env            # Environment vars (SECRET_KEY, DB URL, etc.)
│
├── static/             # Client-side assets
│   ├── css/style.css
│   ├── js/main.js      # Frontend logic (upload, fetch, chat UI)
│   ├── js/api.js       # Frontend API handlers
│   └── assets/         # Images, icons (tracked via .gitkeep)
│
├── templates/          # Jinja2 HTML templates
│   ├── setup.html      # Quiz configuration form
│   ├── chat.html       # Interactive Q&A interface
│   ├── login.html
│   ├── register.html
│   └── results.html    # Quiz summary and follow-up options
│
└── README.md           # Project documentation (you're here)
```

---

## 🛠️ Installation & Setup
1. **Clone the Repo**
   ```bash
   git clone https://github.com/jblarson/quizpro.git
   cd quizpro
   ```
2. **Create & Activate venv**
   ```bash
   python3 -m venv venv
   source venv/bin/activate   # macOS/Linux
   # venv\Scripts\activate  # Windows
   ```
3. **Install Dependencies**
   ```bash
   cd backend
   pip install -r reqs.txt
   ```
4. **Configure Environment**
   - Copy or create `backend/.env`:
     ```dotenv
     SECRET_KEY=your_secret_key
     DATABASE_URL=sqlite:///quizpro.db  # or your Postgres URL
     GEMINI_API_KEY=your_gemini_api_key
     FLASK_ENV=development
     ```
5. **Run the App**
   ```bash
   flask --app backend.app run --reload
   or 
   ./run.sh
   ```
6. **Open in Browser**
   Visit [http://127.0.0.1:5000](http://127.0.0.1:5000) and register/login to begin!

---

## 🎯 Usage
1. **Register / Login**: Create an account or log in to save your quiz history.
2. **Setup Quiz**: Upload a PPTX or paste text, enter/confirm your API key, and set quiz parameters.
3. **Take Quiz**: Answer 20 AI-generated questions in the chat interface.
4. **View Results**: See your score, explanations, and retry incorrect items.

---

## 🚧 Roadmap & Future Enhancements
- **Image-based Questions**: Extract images from slides and quiz on their content.
- **Adaptive Difficulty**: Dynamic question difficulty based on user performance.
- **Analytics Dashboard**: Visualize progress and topic accuracy over time.
- **Mobile App Integration**: Turn QuizPro into a native or PWA mobile experience.
- **Dockerization**: Provide Dockerfile & docker-compose for one-click deployment.
