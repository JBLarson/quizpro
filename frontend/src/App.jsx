import React from 'react';
import { Routes, Route, useLocation } from 'react-router-dom';
import Layout from './components/Layout'; // Path to your Layout component
import Dashboard from './pages/Dashboard';
import Setup from './pages/Setup';
import QuizPage from './pages/QuizPage';
import Login from './pages/Login';
import Register from './pages/Register'; // Corrected: Import Register component

// Ensure Global.css is imported, typically in index.jsx or main.jsx (or here if not done elsewhere)
// import './styles/Global.css'; // If not already in your entry point file (e.g., main.jsx or index.js)

export default function App() {
  const location = useLocation();

  // Determine if the current path is for login or registration
  const isAuthPage = location.pathname === '/login' || location.pathname === '/register';

  // If it's a login or registration page, render it directly without the main Layout
  if (isAuthPage) {
    return (
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        {/* You could add a catch-all or redirect here if an auth page route is mistyped,
            but usually, these are the only two. */}
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
        {/* Add other authenticated/main application routes here */}
        {/* It's good practice to also have a "catch-all" route for 404 pages within the layout */}
        {/* <Route path="*" element={<NotFoundPage />} /> */}
      </Routes>
    </Layout>
  );
}