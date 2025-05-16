import React, { useState, useEffect } from "react";
// NO NavLink, useNavigate needed here FOR THE MENU ITSELF
// NO GlobalMenu import here
import "../styles/Dashboard.css"; // Your page-specific styles

export default function Dashboard() {
  const [userName, setUserName] = useState(''); // Simplified user state for example

  useEffect(() => {
    // Fetch user email if needed specifically for dashboard content,
    // otherwise, user info is primarily for the GlobalMenu.
    // This fetch might be redundant if GlobalMenu handles all user display.
    fetch("/api/user", { credentials: "include" })
      .then(res => res.json())
      .then(data => {
        if (data.logged_in) {
          setUserName(data.userName);
        }
        // No navigate to /login here, GlobalMenu handles that protection.
      })
      .catch(err => console.error("Failed to fetch user for dashboard content:", err));
  }, []);

  return (
    <div className="page-container dashboard-container"> {/* .page-container for content card */}
      <h2>Welcome, {userName || 'Guest'}!</h2>
      <p>Use the menu above to start a quiz or update your settings.</p>
      {/* Other dashboard-specific content */}
    </div>
  );
}