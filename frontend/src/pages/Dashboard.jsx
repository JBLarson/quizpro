import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";  // import useNavigate
import "../styles/Global.css";
import "../styles/Dashboard.css";

export default function Dashboard() {
  const navigate = useNavigate();               // ← invoke it here
  const [user, setUser] = useState(null);

  useEffect(() => {
    fetch("/api/user", {
      credentials: "include",
      headers: { Accept: "application/json" },
    })
      .then(async res => {
        if (!res.ok) {
          throw new Error("Network error");
        }
        const data = await res.json();
        if (data.logged_in) {
          setUser({ email: data.email });
        } else {
          // not logged in: redirect or show placeholder
          navigate("/login");
        }
      })
      .catch(err => {
        console.error("Failed to fetch user:", err);
        navigate("/login");
      });
  }, [navigate]);

  const handleLogout = async () => {
    try {
      await fetch("/api/logout", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
      });
      navigate("/login");  // ← now navigate is defined
    } catch (err) {
      console.error("Logout failed", err);
    }
  };

  return (
    <>
      {/* global menu */}
      <nav className="global-menu">
        <div className="menu-brand">QuizPro</div>
        <div className="menu-list">
          <Link to="/">Dashboard</Link>
          <Link to="/setup">Setup</Link>
          <button onClick={handleLogout}>Logout</button>
        </div>
        <div className="menu-user">{user?.email}</div>
      </nav>

      {/* dashboard content */}
      <div className="page-container dashboard-container">
        <h2>Welcome, {user?.email}</h2>
        <p>Use the menu above to start a quiz or update your settings.</p>
      </div>
    </>
  );
}
