import React, { useState, useEffect, useRef } from "react";
import { NavLink, useNavigate } from "react-router-dom"; // Changed Link to NavLink for active styling
import "../styles/Global.css";
import "../styles/Dashboard.css";

// Simple Caret Down Icon (Ideally, use an SVG or icon library)
const CaretDownIcon = () => (
  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ marginLeft: '8px', transition: 'transform 0.2s ease-in-out' }}>
    <polyline points="6 9 12 15 18 9"></polyline>
  </svg>
);

export default function Dashboard() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const userMenuRef = useRef(null); // For detecting clicks outside

  useEffect(() => {
    fetch("/api/user", {
      credentials: "include",
      headers: { Accept: "application/json" },
    })
      .then(async (res) => {
        if (!res.ok) {
          throw new Error("Network error");
        }
        const data = await res.json();
        if (data.logged_in) {
          setUser({ email: data.email });
        } else {
          navigate("/login");
        }
      })
      .catch((err) => {
        console.error("Failed to fetch user:", err);
        navigate("/login");
      });
  }, [navigate]);

  // Close dropdown if clicked outside
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
      setUser(null); // Clear user state
      setIsUserMenuOpen(false); // Close dropdown
      navigate("/login");
    } catch (err) {
      console.error("Logout failed", err);
    }
  };

  const toggleUserMenu = () => {
    setIsUserMenuOpen(!isUserMenuOpen);
  };

  return (
    <>
      {/* global menu */}
      <nav className="global-menu">
        <div className="menu-brand">QuizPro</div>
        <div className="menu-list">
          <NavLink
            to="/"
            className={({ isActive }) => (isActive ? "menu-link active" : "menu-link")}
            end // `end` prop ensures it's only active for the exact path "/"
          >
            Dashboard
          </NavLink>
          <NavLink
            to="/setup"
            className={({ isActive }) => (isActive ? "menu-link active" : "menu-link")}
          >
            Setup
          </NavLink>
        </div>
        <div className="menu-user-section" ref={userMenuRef}>
          {user && (
            <button onClick={toggleUserMenu} className="user-menu-trigger">
              <span>{user.email}</span>
              <CaretDownIcon />
            </button>
          )}
          {isUserMenuOpen && user && (
            <div className="user-dropdown-menu">
              {/* <NavLink to="/profile" className="dropdown-item">Profile</NavLink> */}
              {/* <NavLink to="/settings" className="dropdown-item">Settings</NavLink> */}
              {/* <div className="dropdown-divider"></div> */}
              <button onClick={handleLogout} className="dropdown-item logout-button">
                Logout
              </button>
            </div>
          )}
        </div>
      </nav>

      {/* dashboard content */}
      <div className="page-container dashboard-container">
        <h2>Welcome, {user?.email}</h2>
        <p>Use the menu above to start a quiz or update your settings.</p>
      </div>
    </>
  );
}