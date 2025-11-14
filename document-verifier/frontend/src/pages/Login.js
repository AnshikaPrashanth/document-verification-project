import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import axios from "axios";

export default function Login({ onLogin }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const navigate = useNavigate();

  const submit = async (e) => {
    e.preventDefault();
    try {
      const res = await axios.post("http://127.0.0.1:5000/login", {
        email,
        password,
      });
      const user = res.data.user;
      localStorage.setItem("dv_user", JSON.stringify(user));
      onLogin(user);
      navigate("/dashboard");
    } catch (err) {
      alert(err.response?.data?.error || "Login failed");
    }
  };

  return (
    <section className="gov-container card small">
      <h2>Sign in</h2>
      <form onSubmit={submit} className="form">
        <input
          className="input"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="Email"
        />
        <input
          className="input"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Password"
        />
        <div className="form-row">
          <button className="btn-primary">Sign in</button>
          <Link to="/register" className="btn-secondary">
            Register
          </Link>
        </div>
      </form>
    </section>
  );
}