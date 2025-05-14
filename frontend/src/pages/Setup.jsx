// src/pages/SetupPage.jsx
import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import '../styles/Global.css';
import '../styles/Setup.css';

const MODELS = ['Gemini', 'OpenAI', 'Deepseek'];
const TYPES  = ['Multiple-Choice', 'Free-Response'];

export default function SetupPage() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);

  // Fetch current user for menu
  useEffect(() => {
    fetch('/api/user', {
      credentials: 'include',
      headers: { Accept: 'application/json' }
    })
      .then(res => res.json())
      .then(data => {
        if (data.logged_in) {
          setUser(data);
        } else {
          navigate('/login');
        }
      })
      .catch(() => navigate('/login'));
  }, [navigate]);

  // Logout handler
  const handleLogout = async () => {
    await fetch('/api/logout', {
      method: 'POST',
      credentials: 'include'
    });
    navigate('/login');
  };

  // Quiz setup state
  const [model, setModel]               = useState('Gemini');
  const [questionType, setQuestionType] = useState('Multiple-Choice');
  const [numQuestions, setNumQuestions] = useState(20);
  const [files, setFiles]               = useState([]);
  const [text, setText]                 = useState('');

  const handleSubmit = async e => {
    e.preventDefault();
    const formData = new FormData();
    files.forEach(f => formData.append('contentFiles', f));
    formData.append('pastedText', text);
    formData.append('modelSelect', model.toLowerCase());
    formData.append(
      'questionType',
      questionType === 'Multiple-Choice' ? 'multiple_choice' : 'free_response'
    );
    formData.append('numQuestions', numQuestions);

    await fetch('/api/quiz/start', {
      method: 'POST',
      credentials: 'include',
      body: formData
    });

    navigate('/quiz');
  };

  return (
    <>
      <nav className="global-menu">
        <div className="menu-brand">QuizPro</div>
        <div className="menu-list">
          <Link to="/">Dashboard</Link>
          <Link to="/setup">Setup</Link>
          <button onClick={handleLogout}>Logout</button>
        </div>
        <div className="menu-user">{user?.email}</div>
      </nav>

      <div className="setup-card">
        <h2>Setup Your Quiz</h2>
        <form onSubmit={handleSubmit}>
          <label>Model:</label>
          <div className="pill-group">
            {MODELS.map(m => (
              <div
                key={m}
                className={`pill${model === m ? ' selected' : ''}`}
                onClick={() => setModel(m)}
              >
                {m}
              </div>
            ))}
          </div>

          <label>Question Type:</label>
          <div className="pill-group">
            {TYPES.map(t => (
              <div
                key={t}
                className={`pill${questionType === t ? ' selected' : ''}`}
                onClick={() => setQuestionType(t)}
              >
                {t}
              </div>
            ))}
          </div>

          <label>
            Number of Questions: {numQuestions}
            <input
              type="range"
              min="1"
              max="50"
              value={numQuestions}
              onChange={e => setNumQuestions(e.target.value)}
            />
          </label>

          <label>
            Paste Text:
            <textarea
              value={text}
              onChange={e => setText(e.target.value)}
              placeholder="Paste content here..."
            />
          </label>

          <label>
            Or Upload Files:
            <input
              type="file"
              accept=".pptx,.pdf,.docx,.xlsx"
              multiple
              onChange={e => setFiles(Array.from(e.target.files))}
            />
          </label>

          <button type="submit">Generate Quiz</button>
        </form>
      </div>
    </>
  );
}
