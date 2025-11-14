import React, { useState } from "react";
import axios from "axios";

export default function Upload({ user }) {
  const [file, setFile] = useState(null);
  const [docType, setDocType] = useState("aadhaar");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const submit = async () => {
    if (!file) return alert("Select a file");
    
    setLoading(true);
    try {
      const fd = new FormData();
      fd.append("file", file);
      fd.append("user_id", user.user_id || 1);
      fd.append("doc_type", docType);

      const res = await axios.post("http://127.0.0.1:5000/upload", fd, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setResult(res.data);
    } catch (err) {
      alert(err.response?.data?.error || "Upload failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="gov-container">
      <div className="card">
        <h2>Upload Document</h2>
        <p className="muted">Accepted: PNG/JPG/JPEG/TIFF/BMP/PDF</p>

        <label className="file-drop">
          <input
            type="file"
            onChange={(e) => setFile(e.target.files[0])}
            className="file-input-hidden"
          />
          <div className="file-drop-inner">
            {file ? file.name : "Click or drop a file here"}
          </div>
        </label>

        <div className="form-row">
          <select
            className="input small"
            value={docType}
            onChange={(e) => setDocType(e.target.value)}
          >
            <option value="aadhaar">Aadhaar</option>
            <option value="passport">Passport</option>
            <option value="certificate">Certificate</option>
            <option value="other">Other</option>
          </select>

          <button className="btn-primary" onClick={submit} disabled={loading}>
            {loading ? "Uploading..." : "Upload"}
          </button>
        </div>

        {result && (
          <div className="result-box">
            <h4>Upload result</h4>
            <pre>{JSON.stringify(result, null, 2)}</pre>
          </div>
        )}
      </div>
    </section>
  );
}