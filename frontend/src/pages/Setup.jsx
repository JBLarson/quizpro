// src/pages/SetupPage.jsx
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
// Removed NavLink and menu-specific imports as GlobalMenu handles navigation
import { FaFileUpload, FaPaperPlane, FaCheckCircle, FaTimesCircle } from 'react-icons/fa'; // Icons for form elements

import '../styles/Global.css'; // Still needed for global variables and .page-container
import '../styles/Setup.css';  // Page-specific styles we will overhaul

// Constants for models and types
const MODELS = ['Gemini', 'OpenAI', 'Deepseek'];
const TYPES = ['Multiple-Choice', 'Free-Response'];

export default function SetupPage() {
  const navigate = useNavigate();

  // Quiz setup state - this is the core state for this page
  const [model, setModel] = useState(MODELS[0]);
  const [questionType, setQuestionType] = useState(TYPES[0]);
  const [numQuestions, setNumQuestions] = useState(20);
  const [files, setFiles] = useState([]); // Store File objects
  const [fileNames, setFileNames] = useState([]); // Store just names for display
  const [text, setText] = useState('');
  const [isLoading, setIsLoading] = useState(false); // For loading state on submit
  const [error, setError] = useState(''); // For displaying submission errors

  // Effect to update fileNames when files change
  useEffect(() => {
    setFileNames(files.map(file => file.name));
  }, [files]);

  const handleFileChange = (e) => {
    const selectedFiles = Array.from(e.target.files);
    // You might want to add validation for file types or number of files here
    setFiles(selectedFiles);
    // Clear the input value so the same file can be selected again if removed
    e.target.value = null; 
  };

  const removeFile = (fileNameToRemove) => {
    setFiles(prevFiles => prevFiles.filter(file => file.name !== fileNameToRemove));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError(''); // Clear previous errors

    if (files.length === 0 && text.trim() === '') {
        setError('Please provide content by pasting text or uploading files.');
        setIsLoading(false);
        return;
    }

    const formData = new FormData();
    if (files.length > 0) {
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
        body: formData,
      });

      if (!response.ok) {
        // Try to get error message from backend if available
        const errorData = await response.json().catch(() => ({ message: `Quiz start failed with status: ${response.status}` }));
        throw new Error(errorData.message || `Quiz start failed with status: ${response.status}`);
      }
      // Assuming successful response means quiz started
      navigate('/quiz');
    } catch (err) {
      console.error("Error starting quiz:", err);
      setError(err.message || "An unexpected error occurred. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    // The GlobalMenu is rendered by Layout.jsx, which wraps this component via App.jsx
    <div className="page-container">
      <div className="setup-card">
        <header className="setup-header">
          <h1>Create Your Quiz</h1>
          <p>Configure the options below to generate a personalized quiz.</p>
        </header>

        <form onSubmit={handleSubmit} className="quiz-setup-form">
          {error && <div className="form-error-message"><FaTimesCircle /> {error}</div>}

          {/* Model Selection */}
          <div className="form-section">
            <label htmlFor="model-select" className="form-label">Choose AI Model</label>
            <div className="pill-group" id="model-select" role="radiogroup" aria-labelledby="model-select-label">
              {MODELS.map(m => (
                <button
                  type="button"
                  key={m}
                  role="radio"
                  aria-checked={model === m}
                  className={`pill${model === m ? ' selected' : ''}`}
                  onClick={() => setModel(m)}
                >
                  {/* Optional: Add icons for models if you have them */}
                  {m}
                </button>
              ))}
            </div>
          </div>

          {/* Question Type Selection */}
          <div className="form-section">
            <label htmlFor="question-type-select" className="form-label">Select Question Type</label>
            <div className="pill-group" id="question-type-select" role="radiogroup" aria-labelledby="question-type-label">
              {TYPES.map(t => (
                <button
                  type="button"
                  key={t}
                  role="radio"
                  aria-checked={questionType === t}
                  className={`pill${questionType === t ? ' selected' : ''}`}
                  onClick={() => setQuestionType(t)}
                >
                  {t}
                </button>
              ))}
            </div>
          </div>

          {/* Number of Questions */}
          <div className="form-section">
            <label htmlFor="num-questions-range" className="form-label">
              Number of Questions: <span className="num-questions-value">{numQuestions}</span>
            </label>
            <input
              id="num-questions-range"
              type="range"
              min="1"
              max="50"
              value={numQuestions}
              onChange={e => setNumQuestions(parseInt(e.target.value, 10))}
              className="range-slider"
            />
          </div>
          
          {/* Content Input Method Tabs (Optional Enhancement) */}
          {/* For simplicity, we'll keep them separate for now, but tabs could be a future step */}

          {/* Paste Text Section */}
          <div className="form-section">
            <label htmlFor="paste-text-area" className="form-label">Paste Your Content</label>
            <textarea
              id="paste-text-area"
              value={text}
              onChange={e => setText(e.target.value)}
              placeholder="Paste text from articles, notes, or documents here..."
              className="text-input large"
              rows="8"
            />
          </div>

          {/* File Upload Section */}
          <div className="form-section">
            <label htmlFor="file-upload-input" className="form-label file-upload-label">
              Or Upload Files
              <span className="file-upload-button">
                <FaFileUpload /> Select Files
              </span>
            </label>
            <input
              id="file-upload-input"
              type="file"
              accept=".pdf,.doc,.docx,.txt,.pptx" // Common text-based formats
              multiple
              onChange={handleFileChange}
              className="file-input-hidden" // Visually hide the default input
            />
            {fileNames.length > 0 && (
              <div className="file-list">
                <p>Selected files:</p>
                <ul>
                  {fileNames.map(name => (
                    <li key={name}>
                      <span>{name}</span>
                      <button type="button" onClick={() => removeFile(name)} className="remove-file-btn" aria-label={`Remove ${name}`}>
                        <FaTimesCircle />
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            <p className="form-hint">Accepted formats: PDF, DOC, DOCX, TXT, PPTX. Max 5 files, 10MB each.</p>
          </div>
          
          <div className="form-actions">
            <button type="submit" className="submit-button primary-button" disabled={isLoading}>
              {isLoading ? (
                <>
                  <span className="spinner" role="status" aria-hidden="true"></span>
                  Generating...
                </>
              ) : (
                <>
                  <FaPaperPlane /> Generate Quiz
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
