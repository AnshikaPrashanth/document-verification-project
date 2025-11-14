import React from "react";
import { Link } from "react-router-dom";

export default function Home() {
  return (
    <section className="gov-container hero">
      <h1 className="hero-title">Secure Document Verification</h1>
      <p className="hero-sub">
        A government-grade portal for tamper-proof document verification using
        OCR, AI extraction and cryptographic hashing.
      </p>

      <div className="home-actions">
        <Link to="/upload" className="btn-primary">
          Upload Document
        </Link>
        <Link to="/verify" className="btn-secondary">
          Verify a Document
        </Link>
      </div>

      <div className="card">
        <h3>How it works</h3>
        <ol>
          <li>
            Upload document → server computes secure SHA-256 fingerprint and
            extracts text via OCR.
          </li>
          <li>
            Fingerprint and metadata saved to DB; a transactional audit trail is
            recorded.
          </li>
          <li>
            Verify any copy at any time by re-uploading or entering the stored
            hash.
          </li>
        </ol>
      </div>
    </section>
  );
}