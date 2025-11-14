🟦 AI-Powered Document Verification System
OCR + NLP + Cryptographic Hashing + Secure Audit Logging + Admin Verification Dashboard
📌 Overview

This project is an AI-powered document verification platform that enables users to upload identity documents (Aadhaar, passport, certificates, etc.) and validates them using:

OCR (Tesseract)

NLP (spaCy & Regex)

SHA-256 cryptographic hashing

Secure database logging

Verification by re-uploading or hash lookup

Admin dashboard for manual validation

MongoDB audit logs for tamper-proof tracking

This system is designed to simulate a government-grade secure verification service.

⭐ Key Features
🔹 User Authentication

Register, login, session persistence

Passwords securely hashed using Werkzeug

Roles: user, admin

🔹 Document Upload

Allows file uploads (JPG/PNG/PDF/TIFF)

Generates a secure SHA-256 fingerprint

Saves document metadata + file path

Stores audit logs in MongoDB

🔹 AI Data Extraction

OCR extracts full text from image documents

NLP automatically extracts:

Names

Dates

Phone numbers

Email IDs

Aadhaar-like ID patterns

Stores all extracted key-values in SQL table

🔹 Document Verification

Verify via blockchain hash

Verify by uploading a file again (recompute hash)

🔹 Admin Panel

View all pending documents

Approve / reject documents

Logs all actions in SQL + MongoDB

Compare similarity between two documents (text fuzzy ratio)

🔹 Clean React Frontend

Government UI theme

File uploads with preview

Dashboard displaying document statuses

Admin dashboard integrated

🏗 Project Architecture
┌───────────────┐         ┌───────────────┐
│    React UI   │  <----> │   Flask API   │
└───────────────┘         └───────────────┘
         │                         │
         ▼                         ▼
 ┌──────────────┐        ┌───────────────────┐
 │  OCR Engine  │        │  MySQL (metadata) │
 │ (Tesseract)  │        └───────────────────┘
 └──────────────┘
         │
         ▼
 ┌──────────────────┐
 │ MongoDB (logs)    │
 └──────────────────┘

🧬 ER Diagram
Users
------
user_id (PK)
name
email (unique)
password_hash
role
created_at

Documents
------
doc_id (PK)
user_id (FK)
doc_name
doc_type
file_path
blockchain_hash (unique)
verification_status
tx_hash
upload_date

AI_Extracted_Info
------
extract_id (PK)
doc_id (FK)
key_name
value_text
confidence_score

Verification_Log
------
verify_id (PK)
doc_id (FK)
admin_id (FK)
verification_status
remarks
verified_at

🔌 API Documentation
### 1. POST /register

Register a new user.

Body:

{
  "name": "John",
  "email": "john@gmail.com",
  "password": "1234"
}

### 2. POST /login
{
  "email": "john@gmail.com",
  "password": "1234"
}

### 3. POST /upload

Multipart form-data:

Field	Type
file	file
user_id	int
doc_type	string
### 4. GET /user/<user_id>/documents

Returns list of user's documents.

### 5. GET /verify/<hash>

Verify by blockchain hash.

### 6. POST /verify_upload

Verify by uploading a document again.

### 7. GET /admin/pending

List all pending documents.

### 8. POST /admin/verify/<doc_id>

Approve/reject a document.

### 9. GET /admin/compare?doc1=1&doc2=2

Compare similarity.

⚙️ Backend Setup
1. Create venv & install dependencies:
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

2. Run server:
python app.py


Runs at:
👉 http://127.0.0.1:5000/

🎨 Frontend Setup
cd frontend
npm install
npm start


Runs at:
👉 http://localhost:3000/

🛡 Security Measures

✔ Password hashing using Werkzeug
✔ No plain-text credentials stored
✔ SQL transactions used for document insert
✔ MongoDB audit logs for all actions
✔ SHA-256 ensures tamper-proof identity
✔ File system and DB paths protected
✔ Cross-origin handled via CORS
✔ Per-user route protection via frontend

📂 Project Folder Structure
backend/
  ├── app.py
  ├── requirements.txt
  ├── uploads/

frontend/
  ├── src/
  ├── public/
  ├── package.json

README.md
.gitignore

🧪 Tech Stack
Frontend

React.js

React Router

Axios

Custom CSS (government theme)

Backend

Python Flask

Tesseract OCR

spaCy NLP

Regex extractors

MySQL

MongoDB

Cryptographic hashing

🎓 Research Gap (For academic projects)

Existing systems fail to provide:

❌ Integrity verification using cryptographic hash
❌ Multi-database secure storage
❌ NLP-based extraction
❌ Admin verification workflow
❌ Real-world document comparison

This project fills all gaps by combining AI + Cryptography + Multi-stage security + Admin workflow.

📘 Justification (DBMS Project)

This system uses:

✔ Proper relational schema
✔ Foreign keys
✔ Triggers
✔ Multi-table transactions
✔ Indexes
✔ Two databases (MySQL + MongoDB)
✔ Full CRUD operations
✔ Stored logs
✔ Relational joins
✔ Audit trails

It is a perfect DBMS + Cloud + AI hybrid project.
