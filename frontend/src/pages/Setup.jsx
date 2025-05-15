// src/pages/SetupPage.jsx
import React, { useState, useEffect, useRef } from 'react'; // Added useRef
import { NavLink, useNavigate } from 'react-router-dom'; // Changed Link to NavLink
import '../styles/Global.css';
import '../styles/Setup.css';

const MODELS = ['Gemini', 'OpenAI', 'Deepseek'];
const TYPES  = ['Multiple-Choice', 'Free-Response'];

// Simple Caret Down Icon (Copied from Dashboard.jsx)
// Ideally, this would be a shared component
const CaretDownIcon = () => (
  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ marginLeft: '8px', transition: 'transform 0.2s ease-in-out' }}>
    <polyline points="6 9 12 15 18 9"></polyline>
  </svg>
);

export default function SetupPage() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false); // Added state for dropdown
  const userMenuRef = useRef(null); // Added ref for dropdown

  // Fetch current user for menu
  useEffect(() => {
    fetch('/api/user', {
      credentials: 'include',
      headers: { Accept: 'application/json' }
    })
      .then(async (res) => { // Added async
        if (!res.ok) { // Check if response is ok
          throw new Error("Network error fetching user");
        }
        const data = await res.json();
        if (data.logged_in) {
          setUser({ email: data.email }); // Ensure user state matches expected structure
        } else {
          navigate('/login');
        }
      })
      .catch((err) => {
        console.error("Failed to fetch user:", err); // Log error
        navigate('/login');
      });
  }, [navigate]);

  // Close dropdown if clicked outside (Copied from Dashboard.jsx)
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target)) {
        setIsUserMenuOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  // Logout handler
  const handleLogout = async () => {
    try {
      await fetch('/api/logout', {
        method: 'POST',
        credentials: 'include'
      });
      setUser(null); // Clear user state
      setIsUserMenuOpen(false); // Close dropdown
      navigate('/login');
    } catch (err) {
        console.error("Logout failed:", err); // Log error
    }
  };

  // Toggle user menu visibility (Copied from Dashboard.jsx)
  const toggleUserMenu = () => {
    setIsUserMenuOpen(!isUserMenuOpen);
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
    // Ensure files is always an array before calling forEach
    if (files && files.length > 0) {
        files.forEach(f => formData.append('contentFiles', f));
    }
    formData.append('pastedText', text);
    formData.append('modelSelect', model.toLowerCase());
    formData.append(
      'questionType',
      questionType === 'Multiple-Choice' ? 'multiple_choice' : 'free_response'
    );
    formData.append('numQuestions', numQuestions);

    try {
        const response = await fetch('/api/quiz/start', {
          method: 'POST',
          credentials: 'include',
          body: formData
        });
        if (!response.ok) {
            throw new Error(`Quiz start failed with status: ${response.status}`)
        }
        navigate('/quiz');
    } catch (error) {
        console.error("Error starting quiz:", error);
        // Potentially show an error message to the user
    }
  };

  return (
    <>
      {/* global menu - Copied from Dashboard.jsx */}
      <nav className="global-menu">
        <div className="menu-brand">QuizPro</div>
        <div className="menu-list">
          <NavLink
            to="/"
            className={({ isActive }) => (isActive ? "menu-link active" : "menu-link")}
            end
          >
            Dashboard
          </NavLink>
          <NavLink
            to="/setup"
            className={({ isActive }) => (isActive ? "menu-link active" : "menu-link")}
          >
            Setup
          </NavLink>
        </div>
        <div className="menu-user-section" ref={userMenuRef}>
          {user && (
            <button onClick={toggleUserMenu} className="user-menu-trigger" aria-expanded={isUserMenuOpen}>
              <span>{user.email}</span>
              <CaretDownIcon />
            </button>
          )}
          {isUserMenuOpen && user && (
            <div className="user-dropdown-menu">
              <button onClick={handleLogout} className="dropdown-item logout-button">
                Logout
              </button>
            </div>
          )}
        </div>
      </nav>

      {/*
        IMPORTANT: The main content container needs to respect the fixed navbar.
        In Global.css, we added `padding-top: var(--navbar-height);` to `body`
        and styled `.page-container`.
        Ensure your `.setup-card` or its parent wrapper is styled similarly to `.page-container`
        or that `.setup-card` is a child of a `.page-container` div.

        Option 1: Wrap with .page-container
        <div className="page-container">
            <div className="setup-card"> ... your form ... </div>
        </div>

        Option 2: Add .page-container class to setup-card (if it's the main full-page block)
        <div className="setup-card page-container"> ... your form ... </div>

        For now, I'll assume Option 1 for clarity, as .page-container has specific centering.
      */}
      <div className="page-container"> {/* Added page-container wrapper */}
        <div className="setup-card">
          <h2>Setup Your Quiz</h2>
          <form onSubmit={handleSubmit}>
            <label htmlFor="model-select">Model:</label> {/* Added htmlFor */}
            <div className="pill-group" id="model-select">
              {MODELS.map(m => (
                <div
                  key={m}
                  role="button" // Add role for accessibility
                  tabIndex={0}  // Add tabIndex for keyboard navigation
                  className={`pill${model === m ? ' selected' : ''}`}
                  onClick={() => setModel(m)}
                  onKeyDown={(e) => e.key === 'Enter' || e.key === ' ' ? setModel(m) : null} // Keyboard accessibility
                >
                  {m}
                </div>
              ))}
            </div>

            <label htmlFor="question-type-select">Question Type:</label> {/* Added htmlFor */}
            <div className="pill-group" id="question-type-select">
              {TYPES.map(t => (
                <div
                  key={t}
                  role="button"
                  tabIndex={0}
                  className={`pill${questionType === t ? ' selected' : ''}`}
                  onClick={() => setQuestionType(t)}
                  onKeyDown={(e) => e.key === 'Enter' || e.key === ' ' ? setQuestionType(t) : null}
                >
                  {t}
                </div>
              ))}
            </div>

            <label htmlFor="num-questions-range"> {/* Added htmlFor */}
              Number of Questions: {numQuestions}
            </label>
            <input
              id="num-questions-range" /* Added id */
              type="range"
              min="1"
              max="50"
              value={numQuestions}
              onChange={e => setNumQuestions(e.target.value)}
            />

            <label htmlFor="paste-text-area">Paste Text:</label> {/* Added htmlFor */}
            <textarea
              id="paste-text-area" /* Added id */
              value={text}
              onChange={e => setText(e.target.value)}
              placeholder="Paste content here..."
            />

            <label htmlFor="file-upload-input">Or Upload Files:</label> {/* Added htmlFor */}
            <input
              id="file-upload-input" /* Added id */
              type="file"
              accept=".pptx,.pdf,.docx,.xlsx"
              multiple
              onChange={e => setFiles(Array.from(e.target.files))}
            />

            <button type="submit" className="submit-button">Generate Quiz</button> {/* Added class for styling if needed */}
          </form>
        </div>
      </div>
    </>
  );
}