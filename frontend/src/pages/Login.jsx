import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { FaEnvelope, FaLock, FaUserPlus, FaSignInAlt } from 'react-icons/fa';

// Import your logos (adjust path if necessary)
import logoBlue from '../assets/images/QuizProLogo-Blue.png';
import logoWhite from '../assets/images/QuizProLogo-White.png';

// Import styles
import "../styles/Global.css";
import "../styles/Login.css";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault(); // Prevent default form submission which causes a page reload
    setError("");

    if (!email.trim() || !password.trim()) {
      setError("Email and password are required.");
      return;
    }
    if (!/\S+@\S+\.\S+/.test(email)) {
        setError("Please enter a valid email address.");
        return;
    }

    setLoading(true);

    try {
      // --- ACTUAL API CALL ---
      // Replace '/api/login' with your actual Flask login endpoint
      const response = await fetch('/api/login', {
        method: 'POST', // Crucial: Use POST for login
        headers: {
          'Content-Type': 'application/json', // Tell the server we're sending JSON
        },
        body: JSON.stringify({ email, password }), // Send email and password as JSON
      });

      setLoading(false); // Stop loading indicator regardless of outcome

      if (!response.ok) {
        // Handle server-side errors (e.g., 401 Unauthorized, 400 Bad Request)
        const errorData = await response.json().catch(() => ({ message: "Invalid response from server." }));
        setError(errorData.message || `Login failed with status: ${response.status}`);
        console.error("Login error from server:", errorData);
        return;
      }

      // Assuming the server responds with JSON, e.g., { token: "...", user: { ... } }
      const data = await response.json();

      // --- SUCCESSFUL LOGIN ---
      console.log("Login successful:", data);

      // TODO: Store authentication token (e.g., in localStorage or context)
      // For example: localStorage.setItem('authToken', data.token);

      // TODO: Update global authentication state (e.g., using Context API or Redux/Zustand)
      // For example: authContext.login(data.user, data.token);

      // Navigate to a protected page
      navigate("/dashboard"); // Or wherever your app should go after login

    } catch (err) {
      // Handle network errors or other unexpected issues with the fetch call
      setLoading(false);
      setError(err.message || "Login request failed. Please check your network or contact support.");
      console.error("Network or other login error:", err);
    }
    // The finally block is removed as setLoading(false) is called within try/catch
  };

  return (
    <div className="login-page-wrapper">
      <div className="login-card">
        <div className="login-logo-animation-container">
          <img
            src={logoBlue}
            alt="QuizPro Logo"
            className="animated-logo logo-1"
            onError={(e) => { e.target.src = 'https://placehold.co/120x50/CCCCCC/FFFFFF?text=Logo+Error'; }}
          />
          <img
            src={logoWhite}
            alt="QuizPro Logo Alternate"
            className="animated-logo logo-2"
            onError={(e) => { e.target.src = 'https://placehold.co/120x50/666666/FFFFFF?text=Logo+Error'; }}
          />
        </div>

        <h1 className="login-title">Welcome Back!</h1>
        <p className="login-subtitle">Log in to continue your QuizPro journey.</p>

        <form className="login-form" onSubmit={handleSubmit} noValidate>
          {error && <div className="login-error-message">{error}</div>}

          <div className="input-group">
            <FaEnvelope className="input-icon" />
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder=" "
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
              placeholder=" "
              aria-label="Password"
              required
              disabled={loading}
            />
            <label htmlFor="password" className="floating-label">Password</label>
          </div>

          <div className="login-options">
            <label htmlFor="remember-me" className="remember-me">
              <input type="checkbox" id="remember-me" name="remember-me" />
              Remember me
            </label>
            <Link to="/forgot-password" className="forgot-password-link">Forgot password?</Link>
          </div>

          <div className="form-actions-container">
            
            <button
              type="submit"
              className="login-button primary-button"
              disabled={loading}
            >
              {loading ? (
                <>
                  <span className="button-spinner" role="status" aria-hidden="true"></span>
                  Logging In...
                </>
              ) : (
                <>
                  <FaSignInAlt /> Log In
                </>
              )}
            </button>
          </div>
        </form>

        <p className="signup-link-container">
          Don't have an account? <Link to="/register" className="signup-link">Sign Up</Link>
        </p>
      </div>
    </div>
  );
}
