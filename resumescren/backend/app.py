# AI-Powered Resume Screening Tool Backend
# Flask app entry point

from flask import Flask, request, jsonify, send_from_directory, render_template, redirect, url_for, flash, session
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
import os
import logging
import json
import csv
import sqlite3
from datetime import datetime
from io import StringIO
import uuid
import ats_utils  # Import the ATS utilities

# Initialize extensions
login_manager = LoginManager()
login_manager.login_view = 'login'

# Database setup
def get_db_connection():
    conn = sqlite3.connect('resume_screener.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db_connection() as conn:
        # Users table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Resume history table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS resume_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                job_title TEXT,
                match_score REAL,
                filepath TEXT,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Job templates table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS job_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                is_public BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Analytics table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()

# Initialize database tables
init_db()

# User model
class User(UserMixin):
    def __init__(self, user_id, username, email):
        self.id = user_id
        self.username = username
        self.email = email

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    if user is None:
        return None
    return User(user['id'], user['username'], user['email'])

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY') or 'dev-key-123'
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Initialize extensions
CORS(app, supports_credentials=True, origins=['http://localhost:3000', 'http://localhost:5000'])
login_manager.init_app(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'docx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'service': 'resume-screener-api',
        'version': '1.0.0'
    })

@app.route('/api/upload', methods=['POST'])
@login_required
def upload_resume():
    """Handle multiple resume file uploads and job matching"""
    try:
        logger.info("Received upload request")
        
        # Check if the post request has the file part and job description
        if 'resume' not in request.files:
            logger.error("No file part in the request")
            return jsonify({'error': 'No file part'}), 400
            
        if 'job_description' not in request.form:
            logger.error("No job description provided")
            return jsonify({'error': 'Job description is required'}), 400
        
        files = request.files.getlist('resume')
        job_desc = request.form['job_description']
        
        if not files or not any(files):
            logger.error("No files selected")
            return jsonify({'error': 'No files selected'}), 400
        
        results = []
        
        for file in files:
            file_result = {'filename': file.filename, 'error': None}
            
            if file.filename == '':
                file_result['error'] = 'Empty filename'
                results.append(file_result)
                continue
                
            if not allowed_file(file.filename):
                file_result['error'] = f'Invalid file type: {file.filename}. Allowed types: pdf, docx, doc'
                results.append(file_result)
                continue
            
            # Process the file
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            try:
                file.save(filepath)
                logger.info(f"File saved to {filepath}")
                
                # Parse resume
                resume_text = ats_utils.parse_resume(filepath)
                
                # For now, use basic contact extraction from the raw text
                # In a real implementation, you'd use a proper resume parser
                contact_info = {
                    'name': 'Unknown',
                    'email': 'Not found',
                    'phone': 'Not found'
                }
                
                # Simple contact extraction (very basic)
                lines = resume_text.split('\n')
                for line in lines[:5]:  # Check first 5 lines
                    line = line.strip()
                    if '@' in line and '.' in line and ' ' not in line.strip():
                        contact_info['email'] = line.strip()
                    elif any(char.isdigit() for char in line) and len(line) > 8:
                        contact_info['phone'] = line.strip()
                    elif len(line.split()) <= 3 and len(line) > 2 and not any(char.isdigit() for char in line):
                        contact_info['name'] = line.strip()
                
                # Calculate match score with job description
                match_score, match_details = ats_utils.calculate_match_score(resume_text, job_desc)
                
                # Add contact info to match details
                match_details['contact'] = contact_info
                
                # Save to history
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute(
                    'INSERT INTO resume_history (user_id, filename, job_title, match_score) VALUES (?, ?, ?, ?)',
                    (current_user.id, filename, job_desc[:100], match_score)
                )
                conn.commit()
                
                file_result.update({
                    'success': True,
                    'match_score': match_score,
                    'details': match_details,
                    'resume_id': cursor.lastrowid,
                    'contact_info': contact_info,  # Add contact information to the response
                    'name': contact_info.get('name', 'Name not found'),
                    'email': contact_info.get('email', 'N/A'),
                    'phone': contact_info.get('phone', 'N/A')
                })
                
                logger.info(f"Processed {filename}. Match score: {match_score}")
                
            except Exception as e:
                logger.error(f"Error processing file {filename}: {str(e)}", exc_info=True)
                file_result['error'] = f'Error processing file: {str(e)}'
                
            finally:
                # Clean up the uploaded file
                if os.path.exists(filepath):
                    try:
                        os.remove(filepath)
                        logger.info(f"Temporary file {filepath} removed")
                    except Exception as e:
                        logger.error(f"Error removing file {filepath}: {str(e)}")
                
                results.append(file_result)
        
        # Return all results
        return jsonify({
            'success': True,
            'total_files': len(results),
            'processed': len([r for r in results if r.get('success')]),
            'failed': len([r for r in results if r.get('error')]),
            'results': results
        })
            
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Internal server error',
            'details': str(e)
        }), 500

@app.route('/')
def home():
    """Serve the home page"""
    return render_template('home.html')

@app.route('/screener')
def index():
    """Serve the resume screening interface"""
    return render_template('index.html')

@app.route('/api/info')
def api_info():
    """API information endpoint"""
    return jsonify({
        'service': 'AI Resume Screening Tool',
        'status': 'running',
        'endpoints': {
            'GET /': 'Home page',
            'GET /screener': 'Resume screening interface',
            'GET /api/health': 'Health check',
            'GET /api/info': 'API information',
            'POST /api/upload': 'Upload resume for screening'
        }
    })

# Authentication Routes
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        if not all([username, email, password]):
            return jsonify({'error': 'Missing required fields'}), 400
            
        hashed_password = generate_password_hash(password)
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
                (username, email, hashed_password)
            )
            user_id = cursor.lastrowid
            conn.commit()
            
            # Log the registration
            cursor.execute(
                'INSERT INTO analytics (user_id, action, details) VALUES (?, ?, ?)',
                (user_id, 'register', json.dumps({'username': username, 'email': email}))
            )
            conn.commit()
            
            # Log the user in
            user = User(user_id, username, email)
            login_user(user)
            
            return jsonify({
                'message': 'Registration successful',
                'user': {
                    'id': user_id,
                    'username': username,
                    'email': email
                }
            })
            
        except sqlite3.IntegrityError as e:
            conn.rollback()
            return jsonify({'error': 'Username or email already exists'}), 400
        finally:
            conn.close()
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Handle JSON API requests
        if request.is_json:
            data = request.get_json()
            username = data.get('username')
            password = data.get('password')
            
            conn = get_db_connection()
            user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
            
            if user and check_password_hash(user['password_hash'], password):
                # Log the login
                conn.execute(
                    'INSERT INTO analytics (user_id, action) VALUES (?, ?)',
                    (user['id'], 'login')
                )
                conn.commit()
                conn.close()
                
                user_obj = User(user['id'], user['username'], user['email'])
                login_user(user_obj)
                
                return jsonify({
                    'message': 'Login successful',
                    'user': {
                        'id': user['id'],
                        'username': user['username'],
                        'email': user['email']
                    },
                    'redirect': request.args.get('next', '/')
                })
            
            conn.close()
            return jsonify({'error': 'Invalid username or password'}), 401
        else:
            # Handle form submission from the login page
            username = request.form.get('username')
            password = request.form.get('password')
            
            conn = get_db_connection()
            user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
            
            if user and check_password_hash(user['password_hash'], password):
                # Log the login
                conn.execute(
                    'INSERT INTO analytics (user_id, action) VALUES (?, ?)',
                    (user['id'], 'login')
                )
                conn.commit()
                conn.close()
                
                user_obj = User(user['id'], user['username'], user['email'])
                login_user(user_obj)
                
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('index'))
            
            conn.close()
            flash('Invalid username or password', 'error')
    
    # For GET requests or failed login attempts, show the login page
    return render_template('login.html', next=request.args.get('next', ''))

@app.route('/logout')
@login_required
def logout():
    # Log the logout
    conn = get_db_connection()
    conn.execute(
        'INSERT INTO analytics (user_id, action) VALUES (?, ?)',
        (current_user.id, 'logout')
    )
    conn.commit()
    conn.close()
    
    logout_user()
    return redirect(url_for('home'))

# Job Templates
@app.route('/api/templates', methods=['GET', 'POST'])
@login_required
def templates():
    if request.method == 'POST':
        data = request.get_json()
        title = data.get('title')
        description = data.get('description')
        is_public = data.get('is_public', False)
        
        if not all([title, description]):
            return jsonify({'error': 'Title and description are required'}), 400
            
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO job_templates (user_id, title, description, is_public) VALUES (?, ?, ?, ?)',
            (current_user.id, title, description, 1 if is_public else 0)
        )
        template_id = cursor.lastrowid
        conn.commit()
        
        # Log the template creation
        conn.execute(
            'INSERT INTO analytics (user_id, action, details) VALUES (?, ?, ?)',
            (current_user.id, 'template_created', json.dumps({'template_id': template_id, 'title': title}))
        )
        conn.commit()
        conn.close()
        
        return jsonify({
            'message': 'Template created successfully',
            'template_id': template_id
        }), 201
    
    # GET request - list templates
    is_public = request.args.get('public', 'false').lower() == 'true'
    
    conn = get_db_connection()
    if is_public:
        templates = conn.execute(
            'SELECT * FROM job_templates WHERE is_public = 1 OR user_id = ?',
            (current_user.id,)
        ).fetchall()
    else:
        templates = conn.execute(
            'SELECT * FROM job_templates WHERE user_id = ?',
            (current_user.id,)
        ).fetchall()
    
    templates_list = [dict(template) for template in templates]
    conn.close()
    
    return jsonify(templates_list)

# Resume History
@app.route('/api/history')
@login_required
def get_history():
    limit = request.args.get('limit', 10, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    conn = get_db_connection()
    history = conn.execute(
        'SELECT * FROM resume_history WHERE user_id = ? ORDER BY processed_at DESC LIMIT ? OFFSET ?',
        (current_user.id, limit, offset)
    ).fetchall()
    
    total = conn.execute(
        'SELECT COUNT(*) as count FROM resume_history WHERE user_id = ?',
        (current_user.id,)
    ).fetchone()['count']
    
    conn.close()
    
    return jsonify({
        'items': [dict(item) for item in history],
        'total': total,
        'limit': limit,
        'offset': offset
    })

# Analytics
@app.route('/api/analytics')
@login_required
def get_analytics():
    time_range = request.args.get('range', '7d')  # 7d, 30d, 90d, all
    
    conn = get_db_connection()
    
    # Get activity summary
    activity_query = '''
        SELECT 
            DATE(created_at) as date,
            COUNT(*) as count
        FROM analytics 
        WHERE user_id = ? 
        GROUP BY DATE(created_at)
        ORDER BY date DESC
        LIMIT 30
    '''
    
    activity = conn.execute(activity_query, (current_user.id,)).fetchall()
    
    # Get action distribution
    actions_query = '''
        SELECT 
            action,
            COUNT(*) as count
        FROM analytics 
        WHERE user_id = ?
        GROUP BY action
        ORDER BY count DESC
    '''
    
    actions = conn.execute(actions_query, (current_user.id,)).fetchall()
    
    conn.close()
    
    return jsonify({
        'activity': [dict(item) for item in activity],
        'actions': [dict(item) for item in actions]
    })

# Export Data
@app.route('/api/export/<data_type>')
@login_required
def export_data(data_type):
    conn = get_db_connection()
    
    if data_type == 'history':
        data = conn.execute(
            'SELECT * FROM resume_history WHERE user_id = ?',
            (current_user.id,)
        ).fetchall()
        
        # Convert to CSV
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['ID', 'Filename', 'Job Title', 'Match Score', 'Processed At'])
        
        # Write data
        for row in data:
            writer.writerow([
                row['id'],
                row['filename'],
                row['job_title'] or '',
                row['match_score'] or '',
                row['processed_at']
            ])
        
        output.seek(0)
        return (
            output.getvalue(),
            200,
            {
                'Content-Type': 'text/csv',
                'Content-Disposition': f'attachment; filename=resume_history_{datetime.now().strftime("%Y%m%d")}.csv'
            }
        )
    
    elif data_type == 'analytics':
        data = conn.execute(
            'SELECT * FROM analytics WHERE user_id = ?',
            (current_user.id,)
        ).fetchall()
        
        # Convert to CSV
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['ID', 'Action', 'Details', 'Created At'])
        
        # Write data
        for row in data:
            writer.writerow([
                row['id'],
                row['action'],
                row['details'] or '',
                row['created_at']
            ])
        
        output.seek(0)
        return (
            output.getvalue(),
            200,
            {
                'Content-Type': 'text/csv',
                'Content-Disposition': f'attachment; filename=analytics_{datetime.now().strftime("%Y%m%d")}.csv'
            }
        )
    
    return jsonify({'error': 'Invalid export type'}), 400

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(401)
def unauthorized_error(error):
    return jsonify({'error': 'Authentication required'}), 401

@app.errorhandler(403)
def forbidden_error(error):
    return jsonify({'error': 'Forbidden'}), 403

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('templates', filename)

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    logger.info("Starting Flask development server...")
    app.run(host='0.0.0.0', port=5000, debug=True)
