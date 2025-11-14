import React from "react";

export default function Footer() {
  return (
    <footer className="gov-footer">
      <div className="gov-container">
        © {new Date().getFullYear()} GovVerify — Secure Document Services
      </div>
    </footer>
  );
}