import os
import mysql.connector
from pymongo import MongoClient
from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


# --- 1. INITIALIZE APP & DATABASES ---

# Initialize Flask App
app = Flask(__name__)
CORS(app) # Enable Cross-Origin Resource Sharing

# --- MySQL Connection ---
# !! Make sure your MySQL server is running!
# !! And that you have created a database named 'doc_verifier_db'
try:
    mysql_db = mysql.connector.connect(
        host="localhost",
        user="root",        # <-- Change to your MySQL username
        password="NewPassword123", # <-- Change to your MySQL password
        database="doc_verifier_db",
        port=3306

    )
    print("MySQL connected successfully!")
except mysql.connector.Error as err:
    print(f"Error connecting to MySQL: {err}")
    mysql_db = None

# --- MongoDB Connection ---
# !! Make sure your MongoDB server is running!
try:
    mongo_client = MongoClient("mongodb://localhost:27017/")
    mongo_db = mongo_client["doc_verifier_logs"] # Database name
    mongo_collection = mongo_db["logs"]          # Collection name
    mongo_collection.insert_one({"status": "MongoDB connected successfully!"})
    print("MongoDB connected successfully!")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")


# --- 2. SETUP DATABASE TABLES (Run this part once) ---
def setup_databases():
    if mysql_db:
        cursor = mysql_db.cursor()
        # Create a table for document metadata (as planned)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INT AUTO_INCREMENT PRIMARY KEY,
                filename VARCHAR(255),
                verification_status VARCHAR(50),
                blockchain_hash VARCHAR(255) DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("MySQL 'documents' table checked/created.")
        cursor.close()

# --- 3. CREATE API ENDPOINTS ---

@app.route('/')
def home():
    return "Hello! This is the Document Verifier Backend."

@app.route('/upload', methods=['POST'])
def upload_document():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file:
        try:
            # 1. Save file temporarily
            filename = file.filename
            
            # Use Pillow to open the image from the file stream
            img = Image.open(file.stream)

            # 2. --- AI LAYER (OCR) ---
            # Extract text from the image
            extracted_text = pytesseract.image_to_string(img)
            
            # (Your AI logic would go here - e.g., check for keywords, etc.)
            print(f"--- Extracted Text ---\n{extracted_text}\n----------------------")

            # 3. --- SQL DATABASE (Store Metadata) ---
            verification_status = "Uploaded" # Default status
            
            sql = "INSERT INTO documents (filename, verification_status) VALUES (%s, %s)"
            val = (filename, verification_status)
            
            cursor = mysql_db.cursor()
            cursor.execute(sql, val)
            mysql_db.commit()
            document_id = cursor.lastrowid # Get the new ID
            cursor.close()

            # 4. --- NoSQL DATABASE (Store Logs/AI Results) ---
            log_entry = {
                "document_id": document_id,
                "filename": filename,
                "action": "UPLOAD_SUCCESS",
                "extracted_text_snippet": extracted_text[:100] + "..." # Store snippet
            }
            mongo_collection.insert_one(log_entry)

            return jsonify({
                "message": "File uploaded and processed successfully!",
                "document_id": document_id,
                "filename": filename,
                "extracted_text": extracted_text
            }), 201

        except Exception as e:
            print(f"An error occurred: {e}")
            # Log error to MongoDB
            mongo_collection.insert_one({"action": "UPLOAD_FAIL", "error": str(e)})
            return jsonify({"error": str(e)}), 500

# --- 4. RUN THE APP ---
if __name__ == '__main__':
    setup_databases() # Check/Create tables when app starts
    app.run(debug=True, port=5000)