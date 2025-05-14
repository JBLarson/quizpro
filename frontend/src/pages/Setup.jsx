// src/pages/SetupPage.jsx
import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import '../styles/Global.css'
import '../styles/Setup.css'

const MODELS = ['Gemini', 'OpenAI', 'Deepseek']
const TYPES  = ['Multiple-Choice', 'Free-Response']

export default function SetupPage() {
  const navigate = useNavigate()
  const [model, setModel]               = useState('Gemini')
  const [questionType, setQuestionType] = useState('Multiple-Choice')
  const [numQuestions, setNumQuestions] = useState(20)
  const [files, setFiles]               = useState([])
  const [text, setText]                 = useState('')

  const handleSubmit = async e => {
    e.preventDefault()
    const form = new FormData()
    files.forEach(f => form.append('contentFiles', f))
    form.append('pastedText', text)
    form.append('modelSelect', model.toLowerCase())
    form.append(
      'questionType',
      questionType === 'Multiple-Choice' ? 'multiple_choice' : 'free_response'
    )
    form.append('numQuestions', numQuestions)
    await fetch('/api/quiz/start', {
      method: 'POST',
      credentials: 'include',
      body: form,
    })
    navigate('/quiz')
  }

  return (
    <div className="setup-card">

      <h2>Setup Your Quiz</h2>
      <form onSubmit={handleSubmit}>
        {/* Model pills */}
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

        {/* Question Type pills */}
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

        {/* Number slider */}
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

        {/* Paste/Text upload */}
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
            onChange={e => setFiles([...e.target.files])}
          />
        </label>

        <button type="submit">Generate Quiz</button>
      </form>
  </div>
  )
}
