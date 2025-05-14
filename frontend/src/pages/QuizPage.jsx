import React, { useState, useEffect } from 'react';

export default function QuizPage() {
  const [raw, setRaw] = useState('');

  useEffect(() => {
    fetch('/api/quiz/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ numQuestions: 5, questionType: 'multiple_choice' }),
    })
      .then(res => res.json())
      .then(data => {
        console.log('quiz-start response:', data);
        setRaw(data.raw);
      })
      .catch(err => console.error(err));
  }, []);


  return (
    <div className="p-4">
      <h1 className="text-3xl font-bold mb-4">Quiz</h1>
      <pre className="bg-gray-100 p-2 rounded">{raw || 'Loading…'}</pre>
    </div>
  );
}
