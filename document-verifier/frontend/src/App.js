import React from "react";
import { BrowserRouter as Router } from "react-router-dom";
import AppShell from "./components/AppShell";
import "./styles/global.css";

export default function App() {
  return (
    <Router>
      <AppShell />
    </Router>
  );
}