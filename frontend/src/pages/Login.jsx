import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom"; // Added Link for potential "Sign Up"
import { FaEnvelope, FaLock, FaSignInAlt } from 'react-icons/fa';

// Import your logos (adjust path if necessary)
import logoBlue from '../assets/images/QuizProLogo-Blue.png';
import logoWhite from '../assets/images/QuizProLogo-White.png';

// Import styles
import "../styles/Global.css"; // For global variables
import "../styles/Login.css";  // Specific styles for this page

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const res = await fetch("/api/login", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      const payload = await res.json();
      if (!res.ok) {
        throw new Error(payload.message || "Login failed. Please check your credentials.");
      }
      // Successful login
      navigate("/"); // Navigate to dashboard or intended page
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page-wrapper">
      <div className="login-card">
        <div className="login-logo-animation-container">
          <img 
            src={logoBlue} 
            alt="QuizPro Logo" 
            className="animated-logo logo-1" 
          />
          <img 
            src={logoWhite} 
            alt="QuizPro Logo Alternate" 
            className="animated-logo logo-2" 
          />
        </div>

        <h1 className="login-title">Welcome Back!</h1>
        <p className="login-subtitle">Please sign in to continue to QuizPro.</p>

        <form className="login-form" onSubmit={handleSubmit} noValidate>
          {error && <div className="login-error-message">{error}</div>}

          <div className="input-group">
            <FaEnvelope className="input-icon" />
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              aria-label="Email Address"
              required
              disabled={loading}
            />
            <label htmlFor="email" className="floating-label">Email Address</label>
          </div>

          <div className="input-group">
            <FaLock className="input-icon" />
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              aria-label="Password"
              required
              disabled={loading}
            />
            <label htmlFor="password" className="floating-label">Password</label>
          </div>
          
          {/* Optional: Remember Me & Forgot Password 
          <div className="login-options">
            <label className="remember-me">
              <input type="checkbox" name="remember" /> Remember me
            </label>
            <Link to="/forgot-password"className="forgot-password-link">Forgot password?</Link>
          </div>
          */}

          <button type="submit" className="login-button primary-button" disabled={loading}>
            {loading ? (
              <>
                <span className="button-spinner" role="status" aria-hidden="true"></span>
                Signing In...
              </>
            ) : (
              <>
                <FaSignInAlt /> Log In
              </>
            )}
          </button>
        </form>
        
        {/* Optional: Sign Up Link 
        <p className="signup-link-container">
          Don't have an account? <Link to="/signup" className="signup-link">Sign Up</Link>
        </p>
        */}
      </div>
    </div>
  );
}
