import React from 'react';
import { Routes, Route } from 'react-router-dom';

import SetupPage from './pages/SetupPage';
import QuizPage   from './pages/QuizPage';
import Dashboard  from './pages/Dashboard';

export default function App() {
  return (
    <div className="p-4">
      <Routes>
        <Route path="/"        element={<SetupPage />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/quiz"    element={<QuizPage />} />
      </Routes>
    </div>
  );
}
