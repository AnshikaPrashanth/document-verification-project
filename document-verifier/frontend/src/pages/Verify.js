import React, { useState } from "react";
import axios from "axios";

export default function Verify() {
  const [hash, setHash] = useState("");
  const [result, setResult] = useState(null);

  const submit = async () => {
    if (!hash.trim()) return alert("Enter hash");
    
    try {
      const res = await axios.get(`http://127.0.0.1:5000/verify/${hash}`);
      setResult(res.data);
    } catch (err) {
      alert(err.response?.data?.message || "Verification failed");
    }
  };

  return (
    <section className="gov-container">
      <div className="card">
        <h2>Verify Document</h2>
        <input
          className="input"
          placeholder="Enter document hash"
          value={hash}
          onChange={(e) => setHash(e.target.value)}
        />
        <div className="form-row">
          <button className="btn-secondary" onClick={submit}>
            Verify
          </button>
        </div>

        {result && (
          <div className="result-box">
            <pre>{JSON.stringify(result, null, 2)}</pre>
          </div>
        )}
      </div>
    </section>
  );
}