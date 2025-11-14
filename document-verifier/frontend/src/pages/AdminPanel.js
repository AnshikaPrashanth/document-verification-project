import React, { useState, useEffect } from "react";
import axios from "axios";

export default function AdminPanel({ user }) {
  const [pending, setPending] = useState([]);

  useEffect(() => {
    fetchPending();
  }, []);

  const fetchPending = async () => {
    try {
      const res = await axios.get("http://127.0.0.1:5000/admin/pending");
      setPending(res.data.pending_documents || []);
    } catch (err) {
      console.error(err);
    }
  };

  const handleAction = async (doc_id, status) => {
    try {
      await axios.post(`http://127.0.0.1:5000/admin/verify/${doc_id}`, {
        admin_id: user.user_id,
        status,
        remarks: status === "verified" ? "Approved" : "Rejected",
      });
      fetchPending();
      alert("Action taken");
    } catch (err) {
      alert("Action failed");
    }
  };

  return (
    <section className="gov-container">
      <div className="card">
        <h2>Admin — Pending Documents</h2>
        {pending.length === 0 ? (
          <p className="muted">No pending documents</p>
        ) : (
          <table className="doc-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Name</th>
                <th>User</th>
                <th>Uploaded</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {pending.map((p) => (
                <tr key={p.doc_id}>
                  <td>{p.doc_id}</td>
                  <td>{p.doc_name}</td>
                  <td>{p.user_id}</td>
                  <td>{new Date(p.upload_date).toLocaleString()}</td>
                  <td>
                    <button
                      className="btn-primary small"
                      onClick={() => handleAction(p.doc_id, "verified")}
                    >
                      Approve
                    </button>
                    <button
                      className="btn-secondary small"
                      onClick={() => handleAction(p.doc_id, "rejected")}
                    >
                      Reject
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </section>
  );
}