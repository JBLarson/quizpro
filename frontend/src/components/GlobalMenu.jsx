import React, { useState, useEffect, useRef } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import {
  FaTachometerAlt,
  FaCog,
  FaUserCircle,
  FaChevronDown,
  FaSignOutAlt
} from 'react-icons/fa';

// Import your logos
import logoBlue from '../assets/images/QuizProLogo-Blue.png';
import logoWhite from '../assets/images/QuizProLogo-White.png';

export default function GlobalMenu() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const userMenuRef = useRef(null);

  useEffect(() => {
    fetch("/api/user", {
      credentials: "include",
      headers: { Accept: "application/json" },
    })
      .then(async (res) => {
        if (!res.ok) {
          if (res.status === 401 || res.status === 403) {
            navigate("/login", { replace: true });
            return null; 
          }
          throw new Error(`Network error: ${res.status}`);
        }
        return res.json();
      })
      .then(data => {
        if (data && data.logged_in) {
          setUser({ email: data.email });
        } else if (data) { 
          navigate("/login", { replace: true });
        }
      })
      .catch((err) => {
        console.error("Failed to fetch user:", err);
        navigate("/login", { replace: true });
      });
  }, [navigate]);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target)) {
        setIsUserMenuOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  const handleLogout = async () => {
    try {
      await fetch("/api/logout", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
      });
      setUser(null);
      setIsUserMenuOpen(false);
      navigate("/login", { replace: true });
    } catch (err) {
      console.error("Logout failed", err);
    }
  };

  const toggleUserMenu = () => {
    setIsUserMenuOpen(!isUserMenuOpen);
  };

  if (!user) {
    return null; 
  }

  return (
    <nav className="global-menu">
      <div className="menu-left-section">
        {/* Updated Menu Brand to use logos */}
        <NavLink to="/" className="menu-brand">
          <div className="logo-container">
            <img 
              src={logoBlue} 
              alt="QuizPro Logo" 
              className="logo-image logo-default" 
            />
            <img 
              src={logoWhite} 
              alt="QuizPro Logo Hover" 
              className="logo-image logo-hover" 
            />
          </div>
        </NavLink>
        <div className="menu-links">
          <NavLink
            to="/"
            className={({ isActive }) => (isActive ? "menu-link active" : "menu-link")}
            end
          >
            <FaTachometerAlt className="menu-link-icon" />
            <span>Dashboard</span>
          </NavLink>
          <NavLink
            to="/setup"
            className={({ isActive }) => (isActive ? "menu-link active" : "menu-link")}
          >
            <FaCog className="menu-link-icon" />
            <span>Setup</span>
          </NavLink>
        </div>
      </div>

      <div className="menu-user-section" ref={userMenuRef}>
        <button
          onClick={toggleUserMenu}
          className="user-menu-trigger"
          aria-expanded={isUserMenuOpen}
          aria-controls="user-dropdown"
        >
          <FaUserCircle className="user-avatar-icon" />
          <span className="user-email-display">{user.email}</span>
          <FaChevronDown className="user-caret-icon" />
        </button>
        {isUserMenuOpen && (
          <div className="user-dropdown-menu" id="user-dropdown" role="menu">
            <button onClick={handleLogout} className="dropdown-item logout-button" role="menuitem">
              <FaSignOutAlt className="dropdown-icon" />
              Logout
            </button>
          </div>
        )}
      </div>
    </nav>
  );
}
