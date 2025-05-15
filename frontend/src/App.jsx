import React from 'react';
import { Routes, Route, useLocation } from 'react-router-dom';
import Layout from './components/Layout'; // Path to your Layout component
import Dashboard from './pages/Dashboard';
import Setup from './pages/Setup';
import QuizPage from './pages/QuizPage';
import Login from './pages/Login';
// Ensure Global.css is imported, typically in main.jsx or App.jsx
// import './styles/Global.css'; // If not already in main.jsx

export default function App() {
  const location = useLocation();
  const isLoginPage = location.pathname === '/login';

  // If it's the login page, render it directly without the Layout (and thus without GlobalMenu)
  if (isLoginPage) {
    return (
      <Routes>
        <Route path="/login" element={<Login />} />
      </Routes>
    );
  }

  // For all other pages, use the Layout which includes the GlobalMenu
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/setup" element={<Setup />} />
        <Route path="/quiz" element={<QuizPage />} />
        {/* Add other routes that need the GlobalMenu here */}
      </Routes>
    </Layout>
  );
}