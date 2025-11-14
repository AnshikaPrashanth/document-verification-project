import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import axios from "axios";

export default function Register({ onRegister }) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const navigate = useNavigate();

  const submit = async (e) => {
    e.preventDefault();
    try {
      await axios.post("http://127.0.0.1:5000/register", {
        name,
        email,
        password,
      });
      
      // Auto-login after registration
      const loginRes = await axios.post("http://127.0.0.1:5000/login", {
        email,
        password,
      });
      const user = loginRes.data.user;
      localStorage.setItem("dv_user", JSON.stringify(user));
      onRegister(user);
      navigate("/dashboard");
    } catch (err) {
      alert(err.response?.data?.error || "Registration failed");
    }
  };

  return (
    <section className="gov-container card small">
      <h2>Create account</h2>
      <form onSubmit={submit} className="form">
        <input
          className="input"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Full name"
        />
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
          <button className="btn-primary">Register</button>
          <Link to="/login" className="btn-secondary">
            Already have an account?
          </Link>
        </div>
      </form>
    </section>
  );
}