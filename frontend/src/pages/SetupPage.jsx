// src/pages/SetupPage.jsx
import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import '../styles/SetupPage.css'

export default function SetupPage() {
  const navigate = useNavigate()
  const [model, setModel]               = useState('gemini')
  const [questionType, setQuestionType] = useState('multiple_choice')
  const [numQuestions, setNumQuestions] = useState(20)
  const [files, setFiles]               = useState([])
  const [text, setText]                 = useState('')

  const handleSubmit = async e => {
    e.preventDefault()
    const form = new FormData()
    files.forEach(f => form.append('contentFiles', f))
    form.append('pastedText', text)
    form.append('modelSelect', model)
    form.append('questionType', questionType)
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
        <label>
          Model:
          <select
            value={model}
            onChange={e => setModel(e.target.value)}
          >
            <option value="gemini">Gemini</option>
            <option value="openai">OpenAI</option>
            <option value="deepseek">DeepSeek</option>
          </select>
        </label>

        <label>
          Question Type:
          <select
            value={questionType}
            onChange={e => setQuestionType(e.target.value)}
          >
            <option value="multiple_choice">Multiple-Choice</option>
            <option value="free_response">Free-Response</option>
          </select>
        </label>

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
            onChange={e => setFiles([...e.target.files])}
          />
        </label>

        <button type="submit">Generate Quiz</button>
      </form>
    </div>
  )
}
