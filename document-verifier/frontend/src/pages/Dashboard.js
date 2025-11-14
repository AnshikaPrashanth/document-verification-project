import React, { useState, useEffect } from "react";
import axios from "axios";

export default function Dashboard({ user }) {
  const [docs, setDocs] = useState([]);

  useEffect(() => {
    const fetchDocuments = async () => {
      try {
        const res = await axios.get(
          `http://127.0.0.1:5000/user/${user.user_id}/documents`
        );
        setDocs(res.data.documents || []);
      } catch (err) {
        console.error(err);
      }
    };
    fetchDocuments();
  }, [user]);

  return (
    <section className="gov-container">
      <div className="card">
        <h2>My Documents</h2>
        {docs.length === 0 ? (
          <p className="muted">No documents found</p>
        ) : (
          <table className="doc-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Type</th>
                <th>Status</th>
                <th>Uploaded</th>
              </tr>
            </thead>
            <tbody>
              {docs.map((d) => (
                <tr key={d.doc_id}>
                  <td>{d.doc_id}</td>
                  <td>{d.doc_name}</td>
                  <td>{d.doc_type}</td>
                  <td>{d.verification_status}</td>
                  <td>{new Date(d.upload_date).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </section>
  );
}