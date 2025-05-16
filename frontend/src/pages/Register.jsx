import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { FaEnvelope, FaLock, FaUser, FaUserPlus } from 'react-icons/fa';

// Import your logos (adjust path if necessary)
// For the purpose of this example, I'll use placeholder URLs.
// Replace these with your actual logo paths.
import logoBlue from '../assets/images/QuizProLogo-Blue.png'; // Assuming same logos
import logoWhite from '../assets/images/QuizProLogo-White.png'; // Assuming same logos

// Import styles
import "../styles/Global.css"; // For global variables
import "../styles/Register.css"; // Specific styles for this page

export default function Register() {
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState(""); // State for confirm password
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (!firstName.trim() || !lastName.trim() || !email.trim() || !password.trim()) {
      setError("All fields are required.");
      return;
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }
    // Add more robust email validation if needed
    if (!/\S+@\S+\.\S+/.test(email)) {
        setError("Please enter a valid email address.");
        return;
    }
    // Add password strength validation if desired

    setLoading(true);

    try {
      // Simulate API call (replace with actual fetch call)
      // console.log("Attempting to register with:", { firstName, lastName, email, password });
      // const res = await fetch("/api/register", {
      //   method: "POST",
      //   credentials: "include", // or "same-origin"
      //   headers: { "Content-Type": "application/json" },
      //   body: JSON.stringify({ firstName, lastName, email, password }),
      // });

      // const payload = await res.json();
      // if (!res.ok) {
      //   throw new Error(payload.message || "Registration failed. Please try again.");
      // }
      
      // Simulate a successful API call for now
      await new Promise(resolve => setTimeout(resolve, 1500));
      console.log("Simulated registration successful for:", { firstName, lastName, email });
      
      // On successful registration:
      // Potentially show a success message before navigating
      navigate("/login"); // Navigate to login page

    } catch (err) {
      // setError(err.message); // Use this if the server provides good error messages
      setError(err.message || "Registration failed. Please try again or contact support.");
      console.error("Registration error:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="register-page-wrapper">
      <div className="register-card">
        <div className="register-logo-animation-container">
          <img
            src={logoBlue}
            alt="QuizPro Logo"
            className="animated-logo logo-1"
          />
          <img
            src={logoWhite} 
            alt="QuizPro Logo Alternate"
            className="animated-logo logo-2"          />
        </div>

        <h1 className="register-title">Create Your Account</h1>
        <p className="register-subtitle">Join QuizPro Today</p>

        <form className="register-form" onSubmit={handleSubmit} noValidate>
          {error && <div className="register-error-message">{error}</div>}

          {/* Row for First Name and Last Name */}
          <div className="form-field-row form-field-row-pair">
            <div className="input-group">
              <FaUser className="input-icon" />
              <input
                type="text"
                id="firstName"
                value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
                placeholder=" " /* For floating label */
                aria-label="First Name"
                required
                disabled={loading}
              />
              <label htmlFor="firstName" className="floating-label">First Name</label>
            </div>

            <div className="input-group">
              <FaUser className="input-icon" />
              <input
                type="text"
                id="lastName"
                value={lastName}
                onChange={(e) => setLastName(e.target.value)}
                placeholder=" " /* For floating label */
                aria-label="Last Name"
                required
                disabled={loading}
              />
              <label htmlFor="lastName" className="floating-label">Last Name</label>
            </div>
          </div>

          {/* Row for Email */}
          <div className="form-field-row">
            <div className="input-group">
              <FaEnvelope className="input-icon" />
              <input
                type="email"
                id="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder=" " /* For floating label */
                aria-label="Email Address"
                required
                disabled={loading}
              />
              <label htmlFor="email" className="floating-label">Email Address</label>
            </div>
          </div>

          {/* Row for Password */}
          <div className="form-field-row">
            <div className="input-group">
              <FaLock className="input-icon" />
              <input
                type="password"
                id="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder=" " /* For floating label */
                aria-label="Password"
                required
                disabled={loading}
              />
              <label htmlFor="password" className="floating-label">Password</label>
            </div>
          </div>

          {/* Row for Confirm Password - ADDED THIS FIELD */}
          <div className="form-field-row">
            <div className="input-group">
              <FaLock className="input-icon" />
              <input
                type="password"
                id="confirmPassword"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder=" " /* For floating label */
                aria-label="Confirm Password"
                required
                disabled={loading}
              />
              <label htmlFor="confirmPassword" className="floating-label">Confirm Password</label>
            </div>
          </div>

          <button type="submit" className="register-button primary-button" disabled={loading}>
            {loading ? (
              <>
                <span className="button-spinner" role="status" aria-hidden="true"></span>
                Creating Account...
              </>
            ) : (
              <>
                <FaUserPlus /> Sign Up
              </>
            )}
          </button>
        </form>

        <p className="login-link-container">
          Already have an account? <Link to="/login" className="login-link">Log In</Link>
        </p>
      </div>
    </div>
  );
}
