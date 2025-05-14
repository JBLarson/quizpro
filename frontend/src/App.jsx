import React from 'react';
import { Routes, Route } from 'react-router-dom';

import Setup from './pages/Setup';
import QuizPage   from './pages/QuizPage';
import Dashboard  from './pages/Dashboard';
import Login  from './pages/Login';

export default function App() {
  return (
    <div className="page-container">
      <Routes>
        <Route path="/"        element={<Setup />} />
        <Route path="/login"        element={<Login />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/quiz"    element={<QuizPage />} />
      </Routes>
    </div>
  );
}
