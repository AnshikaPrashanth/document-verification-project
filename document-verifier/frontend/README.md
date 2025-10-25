# 🔐 AI-Powered Document Verification System

This project is a secure, modern system for verifying the authenticity of documents using AI-driven OCR and an immutable blockchain ledger. It is designed to combat document fraud by providing a tamper-proof verification process.

---

## 🚀 Project Goal

The system aims to:

- Verify document authenticity using blockchain (e.g., Ethereum localnet).  
- Store document metadata (hash, timestamp, owner) immutably.  
- Extract document contents using AI (Tesseract-OCR).  
- Integrate a hybrid database solution (SQL + NoSQL) for efficient data management.

---

## 💻 Tech Stack

- **Frontend:** React, Bootstrap, Axios  
- **Backend:** Flask (Python)  
- **Databases:**  
  - MySQL (SQL): For structured data (users, document metadata)  
  - MongoDB (NoSQL): For unstructured data (OCR text logs, errors)  
- **AI/ML:** Tesseract-OCR (via `pytesseract`)  
- **Blockchain (WIP):** Solidity, Ganache, Web3.py  

---

## ⚙️ Project Architecture

**Data flow overview:**

React Frontend (Client)
↓
Flask Backend (API Server)
↓
AI (OCR) - Extracts text
↓
Databases
MySQL → Stores metadata (filename, user ID, hash)
MongoDB → Stores OCR text and logs
↓
Blockchain → Stores immutable hash for verification

yaml
Copy code

---

## 🚀 Getting Started

### Prerequisites

- Git  
- Python 3.10+  
- Node.js (LTS)  
- MongoDB Community Server (running)  
- Tesseract-OCR (installed on your system)  
- Ganache (Ethereum local blockchain, optional for blockchain feature)

---

### Clone the repository

```bash
git clone [YOUR_GITHUB_REPO_URL_HERE]
cd document-verifier
Backend Setup (Flask)
bash
Copy code
cd backend
# Create a Python virtual environment
python -m venv venv

# Activate the environment
# Windows
.\venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# Install all required packages
pip install -r requirements.txt
Note: Before pushing to GitHub, create requirements.txt by running:

bash
Copy code
pip freeze > requirements.txt
Database Setup
Make sure your MySQL server is running.

Log in to MySQL and run:

sql
Copy code
CREATE DATABASE doc_verifier_db;
Update the MySQL username and password in backend/app.py.

Frontend Setup (React)
bash
Copy code
cd frontend
npm install
🏃‍♂️ Running the Application
You need two separate terminals:

Terminal 1: Backend

bash
Copy code
cd backend
# Activate virtual environment
# Windows
.\venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

python app.py
Your backend will run at http://localhost:5000.

Terminal 2: Frontend

bash
Copy code
cd frontend
npm start
Your frontend will open at http://localhost:3000.

🤝 How to Contribute
Create a new branch:

bash
Copy code
git checkout -b feature/YourNewFeature
Make your changes.

Commit your changes:

bash
Copy code
git commit -m "Add some feature"
Push to the branch:

bash
Copy code
git push origin feature/YourNewFeature
Open a Pull Request.

vbnet
Copy code

I can also make an **even more polished version with badges, screenshots, and folder structure** so it looks professional on GitHub.  

Do you want me to do that?
