import React from 'react';
import { Routes, Route } from 'react-router-dom';

import Setup from './pages/Setup';
import QuizPage   from './pages/QuizPage';
import Dashboard  from './pages/Dashboard';
import Login  from './pages/Login';

export default function App() {
  return (
    <Routes>
      <Route path="/"        element={<Dashboard />} />
      <Route path="/login"        element={<Login />} />
      <Route path="/setup" element={<Setup />} />
      <Route path="/quiz"    element={<QuizPage />} />
    </Routes>
  );
}
