import os
import hashlib
import uuid
import re
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import mysql.connector
from pymongo import MongoClient
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from PIL import Image
import pytesseract
import spacy
from difflib import SequenceMatcher

# --- Configuration ---
UPLOAD_DIR = os.environ.get('UPLOAD_DIR', './uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'tiff', 'bmp', 'pdf'}
os.makedirs(UPLOAD_DIR, exist_ok=True)

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Load spaCy model for NLP
try:
    nlp = spacy.load("en_core_web_sm")
    print("✅ spaCy NLP model loaded successfully!")
except Exception:
    print("⚠️  spaCy model not found. Run: python -m spacy download en_core_web_sm")
    nlp = None

# --- Initialize Flask App ---
app = Flask(__name__)
CORS(app)

# --- Database Connections (globals used only for health checks) ---
mysql_db = None
mongo_collection = None

def get_mysql():
    """Return a fresh MySQL connection for each request."""
    return mysql.connector.connect(
        host=os.environ.get('MYSQL_HOST', 'localhost'),
        user=os.environ.get('MYSQL_USER', 'root'),
        password=os.environ.get('MYSQL_PASSWORD', 'NewPassword123'),
        database=os.environ.get('MYSQL_DB', 'doc_verifier_db'),
        port=int(os.environ.get('MYSQL_PORT', 3306)),
        autocommit=False
    )

def init_mysql():
    """Initialize MySQL connection (used for health check)."""
    global mysql_db
    try:
        # Try opening a connection (we won't reuse this global connection for requests)
        conn = get_mysql()
        conn.close()
        mysql_db = True
        print("✅ MySQL reachable!")
        return True
    except mysql.connector.Error as err:
        print(f"❌ MySQL Connection Error: {err}")
        mysql_db = False
        return False

def init_mongodb():
    """Initialize MongoDB connection"""
    global mongo_collection
    try:
        mongo_client = MongoClient(os.environ.get('MONGO_URI', 'mongodb://localhost:27017/'))
        mongo_db = mongo_client[os.environ.get('MONGO_DB', 'doc_verifier_logs')]
        mongo_collection = mongo_db[os.environ.get('MONGO_COLLECTION', 'logs')]
        # Safe test write
        mongo_collection.insert_one({
            "status": "MongoDB initialized",
            "timestamp": datetime.now()
        })
        print("✅ MongoDB connected successfully!")
        return True
    except Exception as e:
        print(f"❌ MongoDB Connection Error: {e}")
        mongo_collection = None
        return False

# --- Helpers ---

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_file_storage(file_storage):
    filename = secure_filename(file_storage.filename)
    unique = f"{uuid.uuid4().hex}_{filename}"
    path = os.path.join(UPLOAD_DIR, unique)
    file_storage.save(path)
    return path, filename

def sha256_bytes(data_bytes):
    return hashlib.sha256(data_bytes).hexdigest()

def fuzzy_ratio(a, b):
    return SequenceMatcher(None, a, b).ratio()

# --- Database Setup ---

def setup_databases():
    """Create all required tables according to ER diagram and helpful triggers/indexes"""
    try:
        conn = get_mysql()
        cursor = conn.cursor()
    except Exception as e:
        print(f"❌ setup_databases cannot connect to MySQL: {e}")
        return

    try:
        cursor.execute("SET FOREIGN_KEY_CHECKS=0")

        # 1. Users Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role ENUM('user', 'admin') DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_email (email)
            )
        """)

        # 2. Documents Table (Updated)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                doc_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                doc_name VARCHAR(255) NOT NULL,
                doc_type VARCHAR(100),
                file_path VARCHAR(1024),
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                blockchain_hash VARCHAR(255) UNIQUE,
                verification_status ENUM('pending', 'verified', 'rejected') DEFAULT 'pending',
                tx_hash VARCHAR(255),
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                INDEX idx_hash (blockchain_hash),
                INDEX idx_user (user_id)
            )
        """)

        # 3. AI Extracted Info Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_extracted_info (
                extract_id INT AUTO_INCREMENT PRIMARY KEY,
                doc_id INT NOT NULL,
                key_name VARCHAR(100) NOT NULL,
                value_text TEXT,
                confidence_score FLOAT DEFAULT 0.0,
                extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (doc_id) REFERENCES documents(doc_id) ON DELETE CASCADE,
                INDEX idx_doc (doc_id)
            )
        """)

        # 4. Verification Log Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS verification_log (
                verify_id INT AUTO_INCREMENT PRIMARY KEY,
                doc_id INT NOT NULL,
                admin_id INT,
                verification_status VARCHAR(50) NOT NULL,
                verified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                remarks TEXT,
                FOREIGN KEY (doc_id) REFERENCES documents(doc_id) ON DELETE CASCADE,
                FOREIGN KEY (admin_id) REFERENCES users(user_id) ON DELETE SET NULL,
                INDEX idx_doc (doc_id)
            )
        """)

        # Optional: trigger to auto-log document uploads into verification_log (auditing)
        try:
            cursor.execute("DROP TRIGGER IF EXISTS trg_after_doc_insert")
            # Some MySQL servers require delimiter changes to create triggers from clients;
            # creating trigger here may fail on some setups — we ignore non-fatal errors.
            cursor.execute("""
                CREATE TRIGGER trg_after_doc_insert
                AFTER INSERT ON documents
                FOR EACH ROW
                BEGIN
                    INSERT INTO verification_log (doc_id, admin_id, verification_status, remarks)
                    VALUES (NEW.doc_id, NULL, 'pending', 'Auto-created on upload');
                END
            """)
        except mysql.connector.Error:
            print("⚠️  Trigger creation skipped or failed (may need manual creation in MySQL shell).")

        cursor.execute("SET FOREIGN_KEY_CHECKS=1")
        conn.commit()
        print("✅ All database tables created/verified successfully!")

    except Exception as e:
        conn.rollback()
        print(f"❌ setup_databases error: {e}")
    finally:
        try:
            cursor.close()
        except:
            pass
        try:
            conn.close()
        except:
            pass

# --- NLP Helper Functions ---

def extract_entities_nlp(text):
    """Extract named entities using spaCy NLP"""
    if not nlp or not text:
        return []

    doc = nlp(text)
    results = []

    for ent in doc.ents:
        results.append({
            "key": ent.label_,
            "value": ent.text,
            "confidence": 0.85  # spaCy doesn't provide scores, default estimate
        })

    return results

def extract_structured_fields(text):
    """Extract specific document fields using regex patterns"""
    results = []

    # Date patterns (DD/MM/YYYY, DD-MM-YYYY, etc.)
    date_pattern = r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b'
    dates = re.findall(date_pattern, text)
    for date in dates:
        results.append({
            "key": "DATE",
            "value": date,
            "confidence": 0.90
        })

    # Email pattern
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    for email in emails:
        results.append({
            "key": "EMAIL",
            "value": email,
            "confidence": 0.95
        })

    # Phone number pattern (Indian format)
    phone_pattern = r'\b(?:\+91[-.\s]?)?[6-9]\d{9}\b'
    phones = re.findall(phone_pattern, text)
    for phone in phones:
        results.append({
            "key": "PHONE",
            "value": phone,
            "confidence": 0.90
        })

    # ID Number pattern (Aadhaar-like: 12 digits)
    id_pattern = r'\b\d{4}\s?\d{4}\s?\d{4}\b'
    ids = re.findall(id_pattern, text)
    for id_num in ids:
        results.append({
            "key": "ID_NUMBER",
            "value": id_num,
            "confidence": 0.88
        })

    return results

def process_document_text(text):
    """Combined NLP + Regex extraction pipeline"""
    all_extractions = []

    # Get NLP entities
    nlp_entities = extract_entities_nlp(text)
    all_extractions.extend(nlp_entities)

    # Get structured fields via regex
    structured_fields = extract_structured_fields(text)
    all_extractions.extend(structured_fields)

    # Add raw text snippet
    all_extractions.append({
        "key": "RAW_TEXT_SNIPPET",
        "value": text[:500] if len(text) > 500 else text,
        "confidence": 1.0
    })

    return all_extractions

# --- API Routes ---

@app.route('/')
def home():
    return jsonify({
        "message": "Document Verifier Backend API",
        "version": "2.0",
        "endpoints": {
            "POST /register": "Register new user",
            "POST /login": "User login",
            "POST /upload": "Upload document",
            "POST /verify_upload": "Upload file to verify against stored hash",
            "GET /verify/<hash>": "Verify document by hash",
            "GET /document/<doc_id>": "Get document details",
            "POST /admin/verify/<doc_id>": "Admin verification",
            "GET /user/<user_id>/documents": "Get user's documents",
            "GET /admin/pending": "List pending documents",
            "GET /admin/compare?doc1=<id>&doc2=<id>": "Compare two documents by extracted fields/text"
        }
    })

# --- User Management Routes ---

@app.route('/register', methods=['POST'])
def register_user():
    """Register a new user"""
    try:
        data = request.get_json()
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role', 'user')

        if not all([name, email, password]):
            return jsonify({"error": "Missing required fields"}), 400

        password_hash = generate_password_hash(password)

        conn = None
        cursor = None
        try:
            conn = get_mysql()
            cursor = conn.cursor()
            sql = "INSERT INTO users (name, email, password_hash, role) VALUES (%s, %s, %s, %s)"
            cursor.execute(sql, (name, email, password_hash, role))
            conn.commit()
            user_id = cursor.lastrowid
        except mysql.connector.IntegrityError:
            if conn:
                conn.rollback()
            return jsonify({"error": "Email already exists"}), 409
        except Exception as e:
            if conn:
                conn.rollback()
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

        if mongo_collection is not None:
            mongo_collection.insert_one({
                "action": "USER_REGISTER",
                "user_id": user_id,
                "email": email,
                "timestamp": datetime.now()
            })

        return jsonify({
            "message": "User registered successfully!",
            "user_id": user_id,
            "email": email
        }), 201

    except Exception as e:
        print(f"❌ Registration Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/login', methods=['POST'])
def login_user():
    """User login"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        if not all([email, password]):
            return jsonify({"error": "Missing credentials"}), 400

        conn = None
        cursor = None
        try:
            conn = get_mysql()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

        if not user or not check_password_hash(user['password_hash'], password):
            return jsonify({"error": "Invalid credentials"}), 401

        if mongo_collection is not None:
            mongo_collection.insert_one({
                "action": "USER_LOGIN",
                "user_id": user['user_id'],
                "timestamp": datetime.now()
            })

        return jsonify({
            "message": "Login successful",
            "user": {
                "user_id": user['user_id'],
                "name": user['name'],
                "email": user['email'],
                "role": user['role']
            }
        }), 200

    except Exception as e:
        print(f"❌ Login Error: {e}")
        return jsonify({"error": str(e)}), 500

# --- Document Management Routes ---

@app.route('/upload', methods=['POST'])
def upload_document():
    """Upload and process document with OCR + NLP + transactional DB writes"""
    try:
        # Validate file
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "Empty filename"}), 400

        if not allowed_file(file.filename):
            return jsonify({"error": "File type not allowed"}), 400

        # Get user_id (in production, get from JWT token)
        user_id = int(request.form.get('user_id', 1))  # Default to 1 for testing
        doc_type = request.form.get('doc_type', 'general')

        # Step 0: Save file to disk
        saved_path, original_name = save_file_storage(file)

        # Read bytes for hashing
        with open(saved_path, 'rb') as f:
            file_bytes = f.read()

        # --- Step 1: OCR - Extract Text (only for image files)
        extracted_text = ''
        try:
            img = Image.open(saved_path)
            extracted_text = pytesseract.image_to_string(img)
        except Exception:
            # If it's a PDF or non-image, skip OCR for now (could integrate pdfminer)
            extracted_text = ''

        # --- Step 2: Generate Blockchain Hash ---
        blockchain_hash = sha256_bytes(file_bytes)

        # --- Step 3: Simulate Blockchain Transaction ---
        tx_hash = "0x" + uuid.uuid4().hex

        # --- Step 4: Store Document Metadata (transactional) ---
        conn = None
        cursor = None
        try:
            conn = get_mysql()
            cursor = conn.cursor()
            conn.start_transaction()
            sql = """INSERT INTO documents 
                     (user_id, doc_name, doc_type, file_path, blockchain_hash, verification_status, tx_hash) 
                     VALUES (%s, %s, %s, %s, %s, %s, %s)"""
            cursor.execute(sql, (user_id, original_name, doc_type, saved_path, blockchain_hash, 'pending', tx_hash))
            doc_id = cursor.lastrowid

            # --- Step 5: NLP - Extract Structured Information ---
            nlp_results = process_document_text(extracted_text)

            # --- Step 6: Store AI Extracted Info ---
            for item in nlp_results:
                sql2 = """INSERT INTO ai_extracted_info 
                         (doc_id, key_name, value_text, confidence_score) 
                         VALUES (%s, %s, %s, %s)"""
                cursor.execute(sql2, (doc_id, item["key"], item["value"], item["confidence"]))

            conn.commit()

        except Exception as e:
            if conn:
                conn.rollback()
            # remove saved file on failure
            try:
                os.remove(saved_path)
            except Exception:
                pass
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

        # --- Step 7: Log in MongoDB ---
        if mongo_collection is not None:
            mongo_collection.insert_one({
                "action": "DOCUMENT_UPLOAD",
                "doc_id": doc_id,
                "user_id": user_id,
                "filename": original_name,
                "hash": blockchain_hash,
                "tx_hash": tx_hash,
                "entities_extracted": len(nlp_results),
                "timestamp": datetime.now()
            })

        # --- Step 8: Return Response ---
        return jsonify({
            "message": "Document uploaded and processed successfully!",
            "document": {
                "doc_id": doc_id,
                "filename": original_name,
                "doc_type": doc_type,
                "blockchain_hash": blockchain_hash,
                "tx_hash": tx_hash,
                "verification_status": "pending"
            },
            "extraction_summary": {
                "total_entities": len(nlp_results),
                "text_length": len(extracted_text),
                "entities": nlp_results[:5]  # First 5 for preview
            }
        }), 201

    except Exception as e:
        print(f"❌ Upload Error: {e}")
        if mongo_collection is not None:
            mongo_collection.insert_one({
                "action": "UPLOAD_FAIL",
                "error": str(e),
                "timestamp": datetime.now()
            })
        return jsonify({"error": str(e)}), 500

@app.route('/verify_upload', methods=['POST'])
def verify_upload_file():
    """User uploads a file to verify against stored blockchain hash"""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "Empty filename"}), 400

        # compute hash directly from upload
        file_bytes = file.read()
        computed_hash = sha256_bytes(file_bytes)

        conn = None
        cursor = None
        try:
            conn = get_mysql()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM documents WHERE blockchain_hash = %s", (computed_hash,))
            doc = cursor.fetchone()
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

        if not doc:
            return jsonify({"verified": False, "message": "No matching document found"}), 404

        return jsonify({
            "verified": True,
            "message": "File matches stored document",
            "document": {
                "doc_id": doc['doc_id'],
                "doc_name": doc['doc_name'],
                "upload_date": str(doc['upload_date'])
            }
        }), 200

    except Exception as e:
        print(f"❌ verify_upload Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/verify/<blockchain_hash>', methods=['GET'])
def verify_document(blockchain_hash):
    """Verify document by blockchain hash"""
    try:
        conn = None
        cursor = None
        try:
            conn = get_mysql()
            cursor = conn.cursor(dictionary=True)

            # Get document info
            query = """SELECT d.*, u.name as user_name, u.email as user_email 
                       FROM documents d 
                       JOIN users u ON d.user_id = u.user_id 
                       WHERE d.blockchain_hash = %s"""
            cursor.execute(query, (blockchain_hash,))
            doc = cursor.fetchone()

            if not doc:
                return jsonify({
                    "verified": False,
                    "message": "Document not found in blockchain"
                }), 404

            # Get extracted information
            query = """SELECT key_name, value_text, confidence_score 
                       FROM ai_extracted_info 
                       WHERE doc_id = %s"""
            cursor.execute(query, (doc['doc_id'],))
            extracted_info = cursor.fetchall()
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

        # Log verification attempt
        if mongo_collection is not None:
            mongo_collection.insert_one({
                "action": "DOCUMENT_VERIFY",
                "doc_id": doc['doc_id'],
                "hash": blockchain_hash,
                "result": "found",
                "timestamp": datetime.now()
            })

        return jsonify({
            "verified": True,
            "message": "Document verified successfully!",
            "document": {
                "doc_id": doc['doc_id'],
                "doc_name": doc['doc_name'],
                "doc_type": doc['doc_type'],
                "upload_date": str(doc['upload_date']),
                "verification_status": doc['verification_status'],
                "user_name": doc['user_name']
            },
            "extracted_info": extracted_info
        }), 200

    except Exception as e:
        print(f"❌ Verification Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/document/<int:doc_id>', methods=['GET'])
def get_document_details(doc_id):
    """Get full document details with extracted info"""
    try:
        conn = None
        cursor = None
        try:
            conn = get_mysql()
            cursor = conn.cursor(dictionary=True)

            # Get document
            cursor.execute("""
                SELECT d.*, u.name as user_name 
                FROM documents d 
                JOIN users u ON d.user_id = u.user_id 
                WHERE d.doc_id = %s
            """, (doc_id,))
            doc = cursor.fetchone()

            if not doc:
                return jsonify({"error": "Document not found"}), 404

            # Get extracted info
            cursor.execute("""
                SELECT * FROM ai_extracted_info WHERE doc_id = %s
            """, (doc_id,))
            extracted_info = cursor.fetchall()

            # Get verification history
            cursor.execute("""
                SELECT v.*, u.name as admin_name 
                FROM verification_log v 
                LEFT JOIN users u ON v.admin_id = u.user_id 
                WHERE v.doc_id = %s 
                ORDER BY v.verified_at DESC
            """, (doc_id,))
            verification_history = cursor.fetchall()
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

        return jsonify({
            "document": doc,
            "extracted_info": extracted_info,
            "verification_history": verification_history
        }), 200

    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/user/<int:user_id>/documents', methods=['GET'])
def get_user_documents(user_id):
    """Get all documents for a user"""
    try:
        conn = None
        cursor = None
        try:
            conn = get_mysql()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT doc_id, doc_name, doc_type, upload_date, 
                       verification_status, blockchain_hash 
                FROM documents 
                WHERE user_id = %s 
                ORDER BY upload_date DESC
            """, (user_id,))
            documents = cursor.fetchall()
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

        return jsonify({
            "user_id": user_id,
            "total_documents": len(documents),
            "documents": documents
        }), 200

    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({"error": str(e)}), 500

# --- Admin Routes ---

@app.route('/admin/pending', methods=['GET'])
def admin_pending_documents():
    """List all pending documents for admin dashboard"""
    try:
        conn = None
        cursor = None
        try:
            conn = get_mysql()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT doc_id, doc_name, user_id, upload_date FROM documents WHERE verification_status = 'pending' ORDER BY upload_date DESC")
            pending = cursor.fetchall()
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

        return jsonify({
            "total_pending": len(pending),
            "pending_documents": pending
        }), 200

    except Exception as e:
        print(f"❌ admin_pending_documents Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/admin/verify/<int:doc_id>', methods=['POST'])
def admin_verify_document(doc_id):
    """Admin verification/rejection of document (transactional + logging)"""
    try:
        data = request.get_json()
        admin_id = data.get('admin_id')
        status = data.get('status')  # 'verified' or 'rejected'
        remarks = data.get('remarks', '')

        if not all([admin_id, status]):
            return jsonify({"error": "Missing required fields"}), 400

        if status not in ['verified', 'rejected']:
            return jsonify({"error": "Invalid status"}), 400

        conn = None
        cursor = None
        try:
            conn = get_mysql()
            cursor = conn.cursor()
            conn.start_transaction()
            # Update document status
            cursor.execute("""
                UPDATE documents 
                SET verification_status = %s 
                WHERE doc_id = %s
            """, (status, doc_id))

            # Log verification
            cursor.execute("""
                INSERT INTO verification_log 
                (doc_id, admin_id, verification_status, remarks) 
                VALUES (%s, %s, %s, %s)
            """, (doc_id, admin_id, status, remarks))

            conn.commit()

        except Exception as e:
            if conn:
                conn.rollback()
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

        if mongo_collection is not None:
            mongo_collection.insert_one({
                "action": "ADMIN_VERIFICATION",
                "doc_id": doc_id,
                "admin_id": admin_id,
                "status": status,
                "timestamp": datetime.now()
            })

        return jsonify({
            "message": f"Document {status} successfully",
            "doc_id": doc_id,
            "status": status
        }), 200

    except Exception as e:
        print(f"❌ Admin Verification Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/admin/compare', methods=['GET'])
def admin_compare_documents():
    """Compare two documents by doc_id query params: ?doc1=ID&doc2=ID"""
    try:
        doc1 = request.args.get('doc1')
        doc2 = request.args.get('doc2')
        if not all([doc1, doc2]):
            return jsonify({"error": "Provide doc1 and doc2 as query params"}), 400

        conn = None
        cursor = None
        try:
            conn = get_mysql()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT doc_id, file_path FROM documents WHERE doc_id IN (%s,%s)", (doc1, doc2))
            rows = cursor.fetchall()

            if len(rows) < 2:
                return jsonify({"error": "One or both documents not found"}), 404

            # Load extracted text for each from ai_extracted_info (concatenate)
            cursor.execute("SELECT value_text FROM ai_extracted_info WHERE doc_id = %s", (doc1,))
            r1 = cursor.fetchall()
            cursor.execute("SELECT value_text FROM ai_extracted_info WHERE doc_id = %s", (doc2,))
            r2 = cursor.fetchall()
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

        text1 = ' '.join([r['value_text'] for r in r1 if r['value_text']])
        text2 = ' '.join([r['value_text'] for r in r2 if r['value_text']])

        ratio = fuzzy_ratio(text1, text2)

        return jsonify({
            "doc1": int(doc1),
            "doc2": int(doc2),
            "similarity_ratio": ratio,
            "conclusion": "likely-same" if ratio > 0.75 else "different"
        }), 200

    except Exception as e:
        print(f"❌ admin_compare_documents Error: {e}")
        return jsonify({"error": str(e)}), 500

# --- Run Application ---
if __name__ == '__main__':
    print("\n" + "="*50)
    print("🚀 Starting Document Verifier Backend v2.0")
    print("="*50 + "\n")

    # Initialize databases (health checks)
    mysql_connected = init_mysql()
    mongo_connected = init_mongodb()

    if mysql_connected:
        setup_databases()
    else:
        print("⚠️  Running without MySQL - some features disabled")

    if not mongo_connected:
        print("⚠️  Running without MongoDB - logging disabled")

    print("\n" + "="*50)
    print("✅ Backend Ready!")
    print("📍 Server running on http://localhost:5000")
    print("="*50 + "\n")

    app.run(debug=True, port=5000, host='0.0.0.0')
