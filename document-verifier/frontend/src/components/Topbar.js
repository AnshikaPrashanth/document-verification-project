import React from "react";
import { Link } from "react-router-dom";

export default function Topbar({ user, onLogout }) {
  return (
    <header className="gov-topbar">
      <div className="gov-container">
        <div className="brand">GovVerify</div>
        <nav className="nav">
          <Link to="/">Home</Link>
          <Link to="/upload">Upload</Link>
          <Link to="/verify">Verify</Link>
          {user && <Link to="/dashboard">Dashboard</Link>}
          {user && user.role === "admin" && <Link to="/admin">Admin</Link>}
          {!user ? (
            <Link to="/login" className="btn-outline">
              Sign in
            </Link>
          ) : (
            <button className="btn-ghost" onClick={onLogout}>
              Sign out
            </button>
          )}
        </nav>
      </div>
    </header>
  );
}