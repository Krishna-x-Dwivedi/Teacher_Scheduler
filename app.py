# app.py: Flask Backend for Teacher Scheduler (with MySQL)

import os
import mysql.connector # Import MySQL connector
from mysql.connector import Error # Import Error class
from flask import Flask, request, jsonify, g # g is used to store db connection per request
from flask_cors import CORS # Required for allowing requests from the frontend origin
import datetime # Needed for TimeSlot time conversion
import random # Needed for basic shuffling in generation

# --- App Configuration ---
app = Flask(__name__)
CORS(app) # Enable Cross-Origin Resource Sharing for all routes

# --- MySQL Configuration using User Provided Details ---
MYSQL_CONFIG = {
    'user': 'root',     # As provided by user
    'password': '7530', # As provided by user
    'host': 'localhost',# As provided by user
    'database': 'timetable_db', # As provided by user
    'raise_on_warnings': True
}
# --- End MySQL Configuration ---

# IMPORTANT: Use a strong, secret key in a real application, preferably from environment variables
app.config['SECRET_KEY'] = os.urandom(24)

# --- Database Setup (MySQL) ---

def get_db():
    """Opens a new database connection if there is none yet for the current request context."""
    if 'db' not in g:
        try:
            # Establish the connection using the configuration dictionary
            g.db = mysql.connector.connect(**MYSQL_CONFIG)
            # Set session variables for better constraint handling if needed (optional)
            # cursor = g.db.cursor()
            # cursor.execute("SET SESSION sql_mode = 'STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION'")
            # cursor.close()
        except Error as e:
            # Log the error for debugging
            print(f"Error connecting to MySQL Database: {e}")
            raise e # Re-raise the exception to indicate failure
    return g.db

@app.teardown_appcontext
def close_db(error):
    """Closes the database connection at the end of the request."""
    db = g.pop('db', None)
    if db is not None and db.is_connected():
        db.close()

def init_db():
    """Initializes the database by creating tables if they don't exist (MySQL version)."""
    try:
        db = get_db()
        cursor = db.cursor()
        print("Initializing MySQL database tables...")

        # Users Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL -- WARNING: Still plain text! Hash passwords!
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        print("Checked/Created users table.")

        # Reminders Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id INT AUTO_INCREMENT PRIMARY KEY,
                text TEXT NOT NULL,
                reminder_datetime DATETIME NOT NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        print("Checked/Created reminders table.")

        # Faculties Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Faculties (
                faculty_id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                faculty_code VARCHAR(50) UNIQUE NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        print("Checked/Created Faculties table.")

        # Subjects Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Subjects (
                subject_id INT AUTO_INCREMENT PRIMARY KEY,
                code VARCHAR(50) NOT NULL UNIQUE,
                name VARCHAR(255) NOT NULL,
                is_lab BOOLEAN NOT NULL DEFAULT FALSE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        print("Checked/Created Subjects table.")

        # FacultySubjects Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS FacultySubjects (
                faculty_subject_id INT AUTO_INCREMENT PRIMARY KEY,
                faculty_id INT NOT NULL,
                subject_id INT NOT NULL,
                FOREIGN KEY (faculty_id) REFERENCES Faculties(faculty_id) ON DELETE CASCADE,
                FOREIGN KEY (subject_id) REFERENCES Subjects(subject_id) ON DELETE CASCADE,
                UNIQUE KEY unique_faculty_subject (faculty_id, subject_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        print("Checked/Created FacultySubjects table.")

        # Branches Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Branches (
                branch_id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL UNIQUE,
                code VARCHAR(20) UNIQUE NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        print("Checked/Created Branches table.")

        # Sections Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Sections (
                section_id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(10) NOT NULL UNIQUE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        print("Checked/Created Sections table.")

        # Classes Table
        cursor.execute("""
             CREATE TABLE IF NOT EXISTS Classes (
                class_id INT AUTO_INCREMENT PRIMARY KEY,
                branch_id INT NOT NULL,
                section_id INT NOT NULL,
                year INT NOT NULL,
                class_name VARCHAR(100) UNIQUE NULL, -- Can be generated
                FOREIGN KEY (branch_id) REFERENCES Branches(branch_id) ON DELETE CASCADE,
                FOREIGN KEY (section_id) REFERENCES Sections(section_id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        print("Checked/Created Classes table.")

        # --- NEW: ClassSubjects Table (Example - Adapt as needed!) ---
        # This table is crucial for knowing what needs scheduling
        cursor.execute("""
             CREATE TABLE IF NOT EXISTS ClassSubjects (
                class_subject_id INT AUTO_INCREMENT PRIMARY KEY,
                class_id INT NOT NULL,
                subject_id INT NOT NULL,
                hours_per_week INT NOT NULL DEFAULT 1, -- How many periods needed
                FOREIGN KEY (class_id) REFERENCES Classes(class_id) ON DELETE CASCADE,
                FOREIGN KEY (subject_id) REFERENCES Subjects(subject_id) ON DELETE CASCADE,
                UNIQUE KEY unique_class_subject (class_id, subject_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        print("Checked/Created ClassSubjects table (NEW).")
        # --- END NEW ---

        # Locations Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Locations (
                location_id INT AUTO_INCREMENT PRIMARY KEY,
                room_no VARCHAR(50) NOT NULL,
                building VARCHAR(100) NULL,
                is_lab BOOLEAN NOT NULL DEFAULT FALSE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        print("Checked/Created Locations table.")

        # TimeSlots Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS TimeSlots (
                slot_id INT AUTO_INCREMENT PRIMARY KEY,
                day_of_week ENUM('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday') NOT NULL,
                period_number INT NOT NULL,
                start_time TIME NOT NULL,
                end_time TIME NOT NULL,
                applicable_year_group ENUM('1', '2-3+', 'ALL') NOT NULL, -- Year group this slot applies to
                UNIQUE KEY unique_slot_day_period (day_of_week, period_number, applicable_year_group)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        print("Checked/Created TimeSlots table.")

        # TimetableEntries Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS TimetableEntries (
                entry_id INT AUTO_INCREMENT PRIMARY KEY,
                class_id INT NOT NULL,
                slot_id INT NOT NULL,
                subject_id INT NOT NULL,
                faculty_id INT NOT NULL,
                location_id INT NOT NULL,
                lab_batch_info VARCHAR(100) NULL, -- Optional info like "Batch 1" / "Batch 2"
                generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Track when entry was generated
                FOREIGN KEY (class_id) REFERENCES Classes(class_id) ON DELETE CASCADE,
                FOREIGN KEY (slot_id) REFERENCES TimeSlots(slot_id) ON DELETE CASCADE,
                FOREIGN KEY (subject_id) REFERENCES Subjects(subject_id) ON DELETE CASCADE,
                FOREIGN KEY (faculty_id) REFERENCES Faculties(faculty_id) ON DELETE CASCADE,
                FOREIGN KEY (location_id) REFERENCES Locations(location_id) ON DELETE CASCADE,
                UNIQUE KEY unique_class_slot (class_id, slot_id), -- A class can only have one entry per slot
                UNIQUE KEY unique_faculty_slot (faculty_id, slot_id), -- A faculty can only have one entry per slot
                UNIQUE KEY unique_location_slot (location_id, slot_id) -- A location can only have one entry per slot
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        print("Checked/Created TimetableEntries table.")

        db.commit()
        print("Database tables checked/created successfully.")

    except Error as e:
        print(f"Error during database initialization: {e}")
        if 'db' in g and g.db and g.db.is_connected():
            g.db.rollback()
    finally:
        if cursor: # Check if cursor was successfully created
             cursor.close()


# --- Helper Function to convert time objects ---
def time_converter(o):
    """Converts datetime.timedelta objects (used for TIME type) to string for JSON."""
    if isinstance(o, datetime.timedelta):
        total_seconds = int(o.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02}:{minutes:02}:{seconds:02}"
    if isinstance(o, (datetime.date, datetime.datetime)):
        return o.isoformat()
    return str(o)

# --- API Endpoints ---

@app.route('/')
def index():
    """Root endpoint to check backend status and DB connection."""
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()
        cursor.close()
        return f"Teacher Scheduler Backend is running! MySQL Version: {version[0]}"
    except Error as e:
        return f"Backend running, but DB connection failed: {e}", 500

# --- Authentication (Adapted for MySQL) ---
# ... (signup and login routes remain the same) ...
@app.route('/api/signup', methods=['POST'])
def signup():
    """Handles user registration."""
    data = request.get_json()
    name = data.get('name'); email = data.get('email'); password = data.get('password')
    if not name or not email or not password: return jsonify({'error': 'Missing required fields'}), 400

    db = get_db(); cursor = db.cursor()
    try:
        # WARNING: Storing plain text passwords! Use hashing in production.
        query = "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)"
        cursor.execute(query, (name, email, password))
        db.commit(); user_id = cursor.lastrowid
        return jsonify({'message': 'User created successfully', 'user_id': user_id}), 201
    except mysql.connector.IntegrityError: db.rollback(); return jsonify({'error': 'Email already exists'}), 409
    except Error as e: db.rollback(); print(f"Error during signup: {e}"); return jsonify({'error': 'An internal server error occurred'}), 500
    finally: cursor.close()

@app.route('/api/login', methods=['POST'])
def login():
    """Handles user login."""
    data = request.get_json(); email = data.get('email'); password = data.get('password')
    if not email or not password: return jsonify({'error': 'Email and password are required'}), 400

    db = get_db(); cursor = db.cursor(dictionary=True)
    try:
        # WARNING: Comparing plain text passwords! Use hashing in production.
        query = "SELECT id, name, email FROM users WHERE email = %s AND password = %s"
        cursor.execute(query, (email, password))
        user = cursor.fetchone()
        if user: return jsonify({'message': 'Login successful', 'user': user}), 200
        else: return jsonify({'error': 'Invalid email or password'}), 401
    except Error as e: print(f"Error during login: {e}"); return jsonify({'error': 'An internal server error occurred'}), 500
    finally: cursor.close()


# --- Reminders (Adapted for MySQL) ---
# ... (reminder routes remain the same) ...
@app.route('/api/reminders', methods=['GET'])
def get_reminders():
    """Fetches all reminders."""
    db = get_db(); cursor = db.cursor(dictionary=True)
    try:
        query = "SELECT id, text, reminder_datetime FROM reminders ORDER BY reminder_datetime ASC"
        cursor.execute(query)
        reminders = cursor.fetchall()
        for r in reminders:
            if r.get('reminder_datetime'): r['reminder_datetime'] = r['reminder_datetime'].isoformat()
        return jsonify(reminders), 200
    except Error as e: print(f"Error fetching reminders: {e}"); return jsonify({'error': 'An internal server error occurred'}), 500
    finally: cursor.close()

@app.route('/api/reminders', methods=['POST'])
def add_reminder():
    """Adds a new reminder."""
    data = request.get_json(); text = data.get('text'); reminder_datetime_str = data.get('reminder_datetime')
    if not text or not reminder_datetime_str: return jsonify({'error': 'Text and reminder_datetime are required'}), 400

    db = get_db(); cursor = db.cursor(dictionary=True)
    try:
        query = "INSERT INTO reminders (text, reminder_datetime) VALUES (%s, %s)"
        cursor.execute(query, (text, reminder_datetime_str))
        db.commit(); new_reminder_id = cursor.lastrowid
        cursor.execute("SELECT id, text, reminder_datetime FROM reminders WHERE id = %s", (new_reminder_id,))
        new_reminder = cursor.fetchone()
        if new_reminder and new_reminder.get('reminder_datetime'): new_reminder['reminder_datetime'] = new_reminder['reminder_datetime'].isoformat()
        return jsonify(new_reminder), 201
    except Error as e: db.rollback(); print(f"Error adding reminder: {e}"); return jsonify({'error': 'An internal server error occurred'}), 500
    finally: cursor.close()

@app.route('/api/reminders/<int:reminder_id>', methods=['DELETE'])
def delete_reminder(reminder_id):
    """Deletes a specific reminder by ID."""
    db = get_db(); cursor = db.cursor()
    try:
        query = "DELETE FROM reminders WHERE id = %s"
        cursor.execute(query, (reminder_id,))
        db.commit()
        if cursor.rowcount > 0: return jsonify({'message': 'Reminder deleted successfully'}), 200
        else: return jsonify({'error': 'Reminder not found'}), 404
    except Error as e: db.rollback(); print(f"Error deleting reminder: {e}"); return jsonify({'error': 'An internal server error occurred'}), 500
    finally: cursor.close()

# --- Admin Input Endpoints ---

# --- Faculties ---
# ... (faculty routes remain the same) ...
@app.route('/api/faculties', methods=['POST'])
def add_faculty():
    """Adds a new faculty member."""
    data = request.get_json(); name = data.get('name'); faculty_code = data.get('faculty_code')
    if not name: return jsonify({'error': 'Faculty name is required'}), 400

    db = get_db(); cursor = db.cursor(dictionary=True)
    try:
        query = "INSERT INTO Faculties (name, faculty_code) VALUES (%s, %s)"
        cursor.execute(query, (name, faculty_code))
        db.commit(); new_id = cursor.lastrowid
        cursor.execute("SELECT * FROM Faculties WHERE faculty_id = %s", (new_id,))
        new_faculty = cursor.fetchone()
        return jsonify(new_faculty), 201
    except mysql.connector.IntegrityError as e:
         db.rollback()
         if e.errno == 1062: return jsonify({'error': f'Faculty code "{faculty_code}" already exists.'}), 409
         else: print(f"Integrity error adding faculty: {e}"); return jsonify({'error': 'Database integrity error.'}), 400
    except Error as e: db.rollback(); print(f"Error adding faculty: {e}"); return jsonify({'error': 'An internal server error occurred'}), 500
    finally: cursor.close()

@app.route('/api/faculties', methods=['GET'])
def get_faculties():
    """Fetches all faculty members."""
    db = get_db(); cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM Faculties ORDER BY name")
        faculties = cursor.fetchall()
        return jsonify(faculties), 200
    except Error as e: print(f"Error fetching faculties: {e}"); return jsonify({'error': 'An internal server error occurred'}), 500
    finally: cursor.close()

# --- Subjects ---
# ... (subject routes remain the same) ...
@app.route('/api/subjects', methods=['POST'])
def add_subject():
    """Adds a new subject."""
    data = request.get_json(); code = data.get('code'); name = data.get('name'); is_lab = data.get('is_lab', False)
    if not code or not name: return jsonify({'error': 'Subject code and name are required'}), 400

    db = get_db(); cursor = db.cursor(dictionary=True)
    try:
        query = "INSERT INTO Subjects (code, name, is_lab) VALUES (%s, %s, %s)"
        cursor.execute(query, (code, name, bool(is_lab)))
        db.commit(); new_id = cursor.lastrowid
        cursor.execute("SELECT * FROM Subjects WHERE subject_id = %s", (new_id,))
        new_subject = cursor.fetchone()
        return jsonify(new_subject), 201
    except mysql.connector.IntegrityError: db.rollback(); return jsonify({'error': f'Subject code "{code}" already exists.'}), 409
    except Error as e: db.rollback(); print(f"Error adding subject: {e}"); return jsonify({'error': 'An internal server error occurred'}), 500
    finally: cursor.close()

@app.route('/api/subjects', methods=['GET'])
def get_subjects():
    """Fetches all subjects."""
    db = get_db(); cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM Subjects ORDER BY code")
        subjects = cursor.fetchall()
        return jsonify(subjects), 200
    except Error as e: print(f"Error fetching subjects: {e}"); return jsonify({'error': 'An internal server error occurred'}), 500
    finally: cursor.close()

# --- Faculty-Subject Mappings ---
# ... (faculty-subject mapping routes remain the same) ...
@app.route('/api/faculty-subjects', methods=['POST'])
def add_faculty_subject_mapping():
    """Creates a mapping between a faculty and a subject they can teach."""
    data = request.get_json(); faculty_id = data.get('faculty_id'); subject_id = data.get('subject_id')
    if not faculty_id or not subject_id: return jsonify({'error': 'Faculty ID and Subject ID are required'}), 400

    db = get_db(); cursor = db.cursor()
    try:
        query = "INSERT INTO FacultySubjects (faculty_id, subject_id) VALUES (%s, %s)"
        cursor.execute(query, (faculty_id, subject_id))
        db.commit()
        return jsonify({'message': 'Faculty-Subject mapping added successfully'}), 201
    except mysql.connector.IntegrityError: db.rollback(); return jsonify({'error': 'Mapping already exists or invalid Faculty/Subject ID.'}), 409
    except Error as e: db.rollback(); print(f"Error adding faculty-subject mapping: {e}"); return jsonify({'error': 'An internal server error occurred'}), 500
    finally: cursor.close()

@app.route('/api/faculty-subjects/<int:faculty_id>', methods=['GET'])
def get_subjects_for_faculty(faculty_id):
    """Gets all subjects taught by a specific faculty member."""
    db = get_db(); cursor = db.cursor(dictionary=True)
    try:
        query = """ SELECT S.subject_id, S.code, S.name, S.is_lab FROM Subjects S
                    JOIN FacultySubjects FS ON S.subject_id = FS.subject_id WHERE FS.faculty_id = %s ORDER BY S.code """
        cursor.execute(query, (faculty_id,))
        subjects = cursor.fetchall()
        return jsonify(subjects), 200
    except Error as e: print(f"Error fetching subjects for faculty {faculty_id}: {e}"); return jsonify({'error': 'An internal server error occurred'}), 500
    finally: cursor.close()

@app.route('/api/faculty-subjects/<int:faculty_id>/<int:subject_id>', methods=['DELETE'])
def delete_faculty_subject_mapping(faculty_id, subject_id):
    """Deletes a specific mapping between a faculty and a subject."""
    db = get_db(); cursor = db.cursor()
    try:
        query = "DELETE FROM FacultySubjects WHERE faculty_id = %s AND subject_id = %s"
        cursor.execute(query, (faculty_id, subject_id))
        db.commit()
        if cursor.rowcount > 0: return jsonify({'message': 'Faculty-Subject mapping deleted successfully'}), 200
        else: return jsonify({'error': 'Mapping not found'}), 404
    except Error as e: db.rollback(); print(f"Error deleting faculty-subject mapping: {e}"); return jsonify({'error': 'An internal server error occurred'}), 500
    finally: cursor.close()


# --- Branches ---
# ... (branch routes remain the same) ...
@app.route('/api/branches', methods=['POST'])
def add_branch():
    """Adds a new academic branch."""
    data = request.get_json(); name = data.get('name'); code = data.get('code')
    if not name: return jsonify({'error': 'Branch name is required'}), 400

    db = get_db(); cursor = db.cursor(dictionary=True)
    try:
        query = "INSERT INTO Branches (name, code) VALUES (%s, %s)"
        cursor.execute(query, (name, code))
        db.commit(); new_id = cursor.lastrowid
        cursor.execute("SELECT * FROM Branches WHERE branch_id = %s", (new_id,))
        new_branch = cursor.fetchone()
        return jsonify(new_branch), 201
    except mysql.connector.IntegrityError: db.rollback(); return jsonify({'error': f'Branch name "{name}" or code "{code}" already exists.'}), 409
    except Error as e: db.rollback(); print(f"Error adding branch: {e}"); return jsonify({'error': 'An internal server error occurred'}), 500
    finally: cursor.close()

@app.route('/api/branches', methods=['GET'])
def get_branches():
    """Fetches all academic branches."""
    db = get_db(); cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM Branches ORDER BY name")
        branches = cursor.fetchall()
        return jsonify(branches), 200
    except Error as e: print(f"Error fetching branches: {e}"); return jsonify({'error': 'An internal server error occurred'}), 500
    finally: cursor.close()


# --- Sections ---
# ... (section routes remain the same) ...
@app.route('/api/sections', methods=['POST'])
def add_section():
    """Adds a new section designation (e.g., A, B)."""
    data = request.get_json(); name = data.get('name')
    if not name: return jsonify({'error': 'Section name is required'}), 400

    db = get_db(); cursor = db.cursor(dictionary=True)
    try:
        query = "INSERT INTO Sections (name) VALUES (%s)"
        cursor.execute(query, (name,))
        db.commit(); new_id = cursor.lastrowid
        cursor.execute("SELECT * FROM Sections WHERE section_id = %s", (new_id,))
        new_section = cursor.fetchone()
        return jsonify(new_section), 201
    except mysql.connector.IntegrityError: db.rollback(); return jsonify({'error': f'Section name "{name}" already exists.'}), 409
    except Error as e: db.rollback(); print(f"Error adding section: {e}"); return jsonify({'error': 'An internal server error occurred'}), 500
    finally: cursor.close()

@app.route('/api/sections', methods=['GET'])
def get_sections():
    """Fetches all section designations."""
    db = get_db(); cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM Sections ORDER BY name")
        sections = cursor.fetchall()
        return jsonify(sections), 200
    except Error as e: print(f"Error fetching sections: {e}"); return jsonify({'error': 'An internal server error occurred'}), 500
    finally: cursor.close()

# --- Classes ---
# ... (class routes remain the same) ...
@app.route('/api/classes', methods=['POST'])
def add_class():
    """Adds a new class (combination of branch, section, year)."""
    data = request.get_json()
    branch_id = data.get('branch_id'); section_id = data.get('section_id'); year = data.get('year')
    class_name = data.get('class_name') # Optional, can be generated

    if not branch_id or not section_id or not year:
        return jsonify({'error': 'Branch ID, Section ID, and Year are required'}), 400

    try: year = int(year);
    except ValueError: return jsonify({'error': 'Year must be an integer'}), 400
    if year <= 0: return jsonify({'error': 'Year must be a positive integer'}), 400

    db = get_db(); cursor = db.cursor(dictionary=True)
    try:
        if not class_name:
            cursor.execute("SELECT name FROM Branches WHERE branch_id = %s", (branch_id,))
            branch = cursor.fetchone()
            cursor.execute("SELECT name FROM Sections WHERE section_id = %s", (section_id,))
            section = cursor.fetchone()
            if branch and section: class_name = f"{branch['name']} Year {year} Section {section['name']}"
            else: class_name = f"Class_{branch_id}_{section_id}_{year}"

        query = "INSERT INTO Classes (branch_id, section_id, year, class_name) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (branch_id, section_id, year, class_name))
        db.commit(); new_id = cursor.lastrowid
        fetch_query = """ SELECT C.*, B.name as branch_name, S.name as section_name FROM Classes C
                          JOIN Branches B ON C.branch_id = B.branch_id JOIN Sections S ON C.section_id = S.section_id
                          WHERE C.class_id = %s """
        cursor.execute(fetch_query, (new_id,))
        new_class = cursor.fetchone()
        return jsonify(new_class), 201
    except mysql.connector.IntegrityError: db.rollback(); return jsonify({'error': f'Class name "{class_name}" already exists or invalid Branch/Section ID.'}), 409
    except Error as e: db.rollback(); print(f"Error adding class: {e}"); return jsonify({'error': 'An internal server error occurred'}), 500
    finally: cursor.close()

@app.route('/api/classes', methods=['GET'])
def get_classes():
    """Fetches all classes with branch and section names."""
    db = get_db(); cursor = db.cursor(dictionary=True)
    try:
        query = """ SELECT C.*, B.name as branch_name, S.name as section_name FROM Classes C
                    JOIN Branches B ON C.branch_id = B.branch_id JOIN Sections S ON C.section_id = S.section_id
                    ORDER BY B.name, C.year, S.name """
        cursor.execute(query)
        classes = cursor.fetchall()
        return jsonify(classes), 200
    except Error as e: print(f"Error fetching classes: {e}"); return jsonify({'error': 'An internal server error occurred'}), 500
    finally: cursor.close()


# --- Class Subject Requirements (NEW Endpoint Example) ---
# You'll need endpoints to manage the ClassSubjects table
@app.route('/api/class-subjects/<int:class_id>', methods=['GET'])
def get_class_subjects(class_id):
    """Fetches subjects required for a specific class."""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        query = """
            SELECT CS.class_subject_id, CS.class_id, CS.subject_id, CS.hours_per_week,
                   S.code as subject_code, S.name as subject_name, S.is_lab
            FROM ClassSubjects CS
            JOIN Subjects S ON CS.subject_id = S.subject_id
            WHERE CS.class_id = %s
            ORDER BY S.code
        """
        cursor.execute(query, (class_id,))
        requirements = cursor.fetchall()
        return jsonify(requirements), 200
    except Error as e:
        print(f"Error fetching class subject requirements: {e}")
        return jsonify({'error': 'An internal server error occurred'}), 500
    finally:
        cursor.close()

@app.route('/api/class-subjects', methods=['POST'])
def add_class_subject():
    """Adds a subject requirement for a class."""
    data = request.get_json()
    class_id = data.get('class_id')
    subject_id = data.get('subject_id')
    hours_per_week = data.get('hours_per_week', 1) # Default to 1 if not provided

    if not class_id or not subject_id:
        return jsonify({'error': 'Class ID and Subject ID are required'}), 400
    try:
        hours_per_week = int(hours_per_week)
        if hours_per_week <= 0:
            return jsonify({'error': 'Hours per week must be positive'}), 400
    except ValueError:
        return jsonify({'error': 'Hours per week must be an integer'}), 400

    db = get_db()
    cursor = db.cursor()
    try:
        query = "INSERT INTO ClassSubjects (class_id, subject_id, hours_per_week) VALUES (%s, %s, %s)"
        cursor.execute(query, (class_id, subject_id, hours_per_week))
        db.commit()
        return jsonify({'message': 'Class subject requirement added successfully', 'id': cursor.lastrowid}), 201
    except mysql.connector.IntegrityError:
        db.rollback()
        return jsonify({'error': 'Requirement already exists or invalid Class/Subject ID.'}), 409
    except Error as e:
        db.rollback()
        print(f"Error adding class subject requirement: {e}")
        return jsonify({'error': 'An internal server error occurred'}), 500
    finally:
        cursor.close()

# Add DELETE and PUT endpoints for ClassSubjects as needed

# --- Locations ---
# ... (location routes remain the same) ...
@app.route('/api/locations', methods=['POST'])
def add_location():
    """Adds a new location (room/lab)."""
    data = request.get_json()
    room_no = data.get('room_no'); building = data.get('building'); is_lab = data.get('is_lab', False)
    if not room_no: return jsonify({'error': 'Room number is required'}), 400

    db = get_db(); cursor = db.cursor(dictionary=True)
    try:
        query = "INSERT INTO Locations (room_no, building, is_lab) VALUES (%s, %s, %s)"
        cursor.execute(query, (room_no, building, bool(is_lab)))
        db.commit(); new_id = cursor.lastrowid
        cursor.execute("SELECT * FROM Locations WHERE location_id = %s", (new_id,))
        new_location = cursor.fetchone()
        return jsonify(new_location), 201
    except Error as e: db.rollback(); print(f"Error adding location: {e}"); return jsonify({'error': 'An internal server error occurred'}), 500
    finally: cursor.close()

@app.route('/api/locations', methods=['GET'])
def get_locations():
    """Fetches all locations."""
    db = get_db(); cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM Locations ORDER BY building, room_no")
        locations = cursor.fetchall()
        return jsonify(locations), 200
    except Error as e: print(f"Error fetching locations: {e}"); return jsonify({'error': 'An internal server error occurred'}), 500
    finally: cursor.close()

# --- TimeSlots ---
# ... (timeslot routes remain the same) ...
@app.route('/api/timeslots', methods=['POST'])
def add_timeslot():
    """Adds a new time slot definition."""
    data = request.get_json()
    day = data.get('day_of_week'); period = data.get('period_number')
    start = data.get('start_time'); end = data.get('end_time'); year_group = data.get('applicable_year_group')

    if not all([day, period, start, end, year_group]): return jsonify({'error': 'All fields (day, period, start, end, year_group) are required'}), 400
    if year_group not in ['1', '2-3+', 'ALL']: return jsonify({'error': 'Invalid applicable_year_group. Must be "1", "2-3+", or "ALL".'}), 400
    try: period = int(period);
    except ValueError: return jsonify({'error': 'Period number must be an integer'}), 400
    if period <= 0: return jsonify({'error': 'Period number must be positive'}), 400
    try:
        # Basic time format validation (HH:MM or HH:MM:SS)
        datetime.time.fromisoformat(start.split('T')[-1]) # Handle potential datetime-local format
        datetime.time.fromisoformat(end.split('T')[-1])
    except ValueError: return jsonify({'error': 'Invalid time format. Use HH:MM or HH:MM:SS'}), 400

    db = get_db(); cursor = db.cursor(dictionary=True)
    try:
        query = """ INSERT INTO TimeSlots (day_of_week, period_number, start_time, end_time, applicable_year_group)
                    VALUES (%s, %s, %s, %s, %s) """
        cursor.execute(query, (day, period, start, end, year_group))
        db.commit(); new_id = cursor.lastrowid
        cursor.execute("SELECT * FROM TimeSlots WHERE slot_id = %s", (new_id,))
        new_slot = cursor.fetchone()
        if new_slot:
            new_slot['start_time'] = time_converter(new_slot.get('start_time'))
            new_slot['end_time'] = time_converter(new_slot.get('end_time'))
        return jsonify(new_slot), 201
    except mysql.connector.IntegrityError: db.rollback(); return jsonify({'error': f'Time slot for {day} Period {period} ({year_group}) already exists.'}), 409
    except Error as e: db.rollback(); print(f"Error adding timeslot: {e}"); return jsonify({'error': 'An internal server error occurred'}), 500
    finally: cursor.close()

@app.route('/api/timeslots', methods=['GET'])
def get_timeslots():
    """Fetches all defined time slots."""
    db = get_db(); cursor = db.cursor(dictionary=True)
    try:
        query = """ SELECT * FROM TimeSlots ORDER BY FIELD(day_of_week, 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'), period_number """
        cursor.execute(query)
        timeslots = cursor.fetchall()
        for slot in timeslots:
            slot['start_time'] = time_converter(slot.get('start_time'))
            slot['end_time'] = time_converter(slot.get('end_time'))
        return jsonify(timeslots), 200
    except Error as e: print(f"Error fetching timeslots: {e}"); return jsonify({'error': 'An internal server error occurred'}), 500
    finally: cursor.close()


# --- Timetable Generation ---

def fetch_scheduling_data(cursor):
    """Fetches all necessary data for timetable generation."""
    data = {}
    try:
        # Classes with year info
        cursor.execute("SELECT class_id, year, class_name FROM Classes")
        data['classes'] = cursor.fetchall()

        # Subjects with lab info
        cursor.execute("SELECT subject_id, name, is_lab FROM Subjects")
        data['subjects'] = {s['subject_id']: s for s in cursor.fetchall()} # Dict for easy lookup

        # Faculties
        cursor.execute("SELECT faculty_id, name FROM Faculties")
        data['faculties'] = {f['faculty_id']: f for f in cursor.fetchall()} # Dict for easy lookup

        # Locations with lab info
        cursor.execute("SELECT location_id, room_no, is_lab FROM Locations")
        data['locations'] = cursor.fetchall()

        # Faculty-Subject mappings
        cursor.execute("SELECT faculty_id, subject_id FROM FacultySubjects")
        mappings = cursor.fetchall()
        data['faculty_subjects'] = {} # {subject_id: [faculty_id1, faculty_id2]}
        for mapping in mappings:
            sub_id = mapping['subject_id']
            fac_id = mapping['faculty_id']
            if sub_id not in data['faculty_subjects']:
                data['faculty_subjects'][sub_id] = []
            data['faculty_subjects'][sub_id].append(fac_id)

        # TimeSlots with year group info
        cursor.execute("SELECT slot_id, day_of_week, period_number, applicable_year_group FROM TimeSlots")
        data['timeslots'] = cursor.fetchall()

        # Class Subject Requirements (Crucial!)
        cursor.execute("""
            SELECT CS.class_id, CS.subject_id, CS.hours_per_week, S.is_lab
            FROM ClassSubjects CS
            JOIN Subjects S ON CS.subject_id = S.subject_id
        """)
        requirements = cursor.fetchall()
        data['class_subject_requirements'] = {} # {class_id: [(subject_id, hours, is_lab), ...]}
        for req in requirements:
            cls_id = req['class_id']
            if cls_id not in data['class_subject_requirements']:
                data['class_subject_requirements'][cls_id] = []
            # Append tuple: (subject_id, hours_needed, is_lab)
            data['class_subject_requirements'][cls_id].append((req['subject_id'], req['hours_per_week'], bool(req['is_lab'])))

        return data

    except Error as e:
        print(f"Error fetching scheduling data: {e}")
        return None


@app.route('/api/generate-timetable', methods=['POST'])
def generate_timetable():
    """
    Attempts to generate a timetable using a *very* basic greedy algorithm.
    WARNING: This is a highly simplified placeholder and likely insufficient
             for real-world scheduling complexity. Consider using a constraint
             solver library (like Google OR-Tools) for a robust solution.
    """
    print("Received request to generate timetable.")
    db = get_db()
    cursor = db.cursor(dictionary=True) # Use dictionary cursor for easier data access
    generated_entries = 0
    failed_assignments = 0

    try:
        # 1. Clear existing timetable entries
        print("Clearing previous timetable entries...")
        cursor.execute("DELETE FROM TimetableEntries")
        # Optional: Reset auto-increment if needed (use with caution)
        # cursor.execute("ALTER TABLE TimetableEntries AUTO_INCREMENT = 1")
        print(f"{cursor.rowcount} previous entries deleted.")

        # 2. Fetch all necessary data
        print("Fetching scheduling data...")
        scheduling_data = fetch_scheduling_data(cursor)
        if not scheduling_data:
            return jsonify({'error': 'Failed to fetch necessary data for scheduling.'}), 500

        classes = scheduling_data['classes']
        subjects_dict = scheduling_data['subjects']
        faculties_dict = scheduling_data['faculties']
        locations = scheduling_data['locations']
        faculty_subjects = scheduling_data['faculty_subjects'] # {subj_id: [fac_id1, ...]}
        timeslots = scheduling_data['timeslots']
        class_reqs = scheduling_data['class_subject_requirements'] # {cls_id: [(subj_id, hours, is_lab), ...]}

        # Separate locations into labs and lecture rooms
        lecture_rooms = [loc for loc in locations if not loc['is_lab']]
        lab_rooms = [loc for loc in locations if loc['is_lab']]

        # Data structures to track resource usage
        # {slot_id: faculty_id}
        faculty_schedule = {}
        # {slot_id: location_id}
        location_schedule = {}
        # {slot_id: class_id}
        class_schedule = {}
        # Track hours scheduled for each class-subject requirement
        # {(class_id, subject_id): hours_scheduled}
        hours_tracker = {}

        # --- Simple Greedy Algorithm ---
        print("Starting basic greedy assignment...")

        # Create list of assignments needed: (class_id, subject_id, is_lab) repeated 'hours' times
        assignments_needed = []
        for cls in classes:
            cls_id = cls['class_id']
            if cls_id in class_reqs:
                for subject_id, hours, is_lab in class_reqs[cls_id]:
                    for _ in range(hours):
                         assignments_needed.append({'class_id': cls_id, 'subject_id': subject_id, 'is_lab': is_lab, 'year': cls['year']})
                    hours_tracker[(cls_id, subject_id)] = 0 # Initialize tracker

        # Shuffle assignments to avoid simple biases (optional)
        random.shuffle(assignments_needed)

        # Get timeslots ordered (e.g., by day then period)
        # Already ordered by query in get_timeslots, but let's sort here just in case
        timeslots.sort(key=lambda ts: (('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday').index(ts['day_of_week']), ts['period_number']))

        new_entries_data = [] # Store successful assignments to insert later

        # Iterate through each needed assignment
        for assignment in assignments_needed:
            cls_id = assignment['class_id']
            subject_id = assignment['subject_id']
            is_lab = assignment['is_lab']
            cls_year = assignment['year']
            found_slot = False

            # Check if already fully scheduled for this class-subject
            req_hours = next((h for s, h, l in class_reqs.get(cls_id, []) if s == subject_id), 0)
            if hours_tracker.get((cls_id, subject_id), 0) >= req_hours:
                 continue # Already done with this specific class-subject requirement

            # Find suitable faculties
            possible_faculty_ids = faculty_subjects.get(subject_id, [])
            if not possible_faculty_ids:
                print(f"Warning: No faculty found for subject {subject_id}. Skipping assignment for class {cls_id}.")
                failed_assignments += 1
                continue

            # Iterate through available timeslots appropriate for the class year
            for slot in timeslots:
                slot_id = slot['slot_id']
                slot_year_group = slot['applicable_year_group']

                # Check if timeslot is applicable to the class year
                year_group_match = False
                if slot_year_group == 'ALL':
                    year_group_match = True
                elif slot_year_group == '1' and cls_year == 1:
                     year_group_match = True
                elif slot_year_group == '2-3+' and cls_year >= 2:
                     year_group_match = True

                if not year_group_match:
                    continue # Skip slot not applicable to this year

                # Check if class is already scheduled for this slot
                if class_schedule.get(slot_id) == cls_id:
                    continue

                # Try to find an available faculty
                available_faculty_id = None
                random.shuffle(possible_faculty_ids) # Try faculties in random order
                for fac_id in possible_faculty_ids:
                    if faculty_schedule.get(slot_id) != fac_id: # Check if faculty is free
                         # Double check this specific faculty is not assigned anywhere else in this slot
                         is_faculty_busy = False
                         for s_id, booked_fac_id in faculty_schedule.items():
                              if s_id == slot_id and booked_fac_id == fac_id:
                                   is_faculty_busy = True
                                   break
                         if not is_faculty_busy:
                              available_faculty_id = fac_id
                              break # Found a free faculty

                if not available_faculty_id:
                    continue # No free faculty found for this slot

                # Try to find an available location
                available_location_id = None
                possible_locations = lab_rooms if is_lab else lecture_rooms
                random.shuffle(possible_locations) # Try locations in random order
                for loc in possible_locations:
                    loc_id = loc['location_id']
                    if location_schedule.get(slot_id) != loc_id: # Check if location is free
                         # Double check this specific location is not assigned anywhere else in this slot
                         is_location_busy = False
                         for s_id, booked_loc_id in location_schedule.items():
                              if s_id == slot_id and booked_loc_id == loc_id:
                                   is_location_busy = True
                                   break
                         if not is_location_busy:
                              available_location_id = loc_id
                              break # Found a free location

                if not available_location_id:
                    continue # No free location found for this slot

                # --- If we reach here, we found a slot, faculty, and location! ---
                print(f"Assigning Class {cls_id}, Subj {subject_id} to Slot {slot_id}, Fac {available_faculty_id}, Loc {available_location_id}")

                # Record the assignment
                faculty_schedule[slot_id] = available_faculty_id
                location_schedule[slot_id] = available_location_id
                class_schedule[slot_id] = cls_id
                hours_tracker[(cls_id, subject_id)] = hours_tracker.get((cls_id, subject_id), 0) + 1

                # Store data for batch insert
                new_entries_data.append((
                    cls_id, slot_id, subject_id, available_faculty_id, available_location_id
                ))

                found_slot = True
                break # Move to the next assignment

            if not found_slot:
                 print(f"Warning: Could not find suitable slot/faculty/location for Class {cls_id}, Subject {subject_id}")
                 failed_assignments += 1


        # 3. Batch Insert the generated entries
        if new_entries_data:
            print(f"Attempting to insert {len(new_entries_data)} generated entries...")
            insert_query = """
                INSERT INTO TimetableEntries (class_id, slot_id, subject_id, faculty_id, location_id)
                VALUES (%s, %s, %s, %s, %s)
            """
            try:
                 # Use executemany for efficiency
                 cursor.executemany(insert_query, new_entries_data)
                 generated_entries = cursor.rowcount
                 db.commit()
                 print(f"Successfully inserted {generated_entries} timetable entries.")
            except Error as insert_error:
                 db.rollback()
                 print(f"Error during batch insert: {insert_error}")
                 # Attempt individual inserts if batch fails due to a single conflict (less efficient)
                 print("Attempting individual inserts...")
                 generated_entries = 0
                 individual_failures = 0
                 for entry_data in new_entries_data:
                      try:
                           cursor.execute(insert_query, entry_data)
                           generated_entries += 1
                      except Error as individual_error:
                           print(f"Failed to insert individual entry {entry_data}: {individual_error}")
                           individual_failures +=1
                 if generated_entries > 0:
                     db.commit()
                     print(f"Successfully inserted {generated_entries} entries individually.")
                 if individual_failures > 0:
                      failed_assignments += individual_failures # Count these as failed too


        else:
            print("No timetable entries were generated.")

        # 4. Return result
        message = f"Timetable generation process finished. Successfully generated {generated_entries} entries."
        if failed_assignments > 0:
            message += f" Failed to schedule {failed_assignments} required periods due to conflicts or lack of resources."

        return jsonify({'message': message, 'entries_generated': generated_entries, 'failed_assignments': failed_assignments}), 200

    except Error as e:
        db.rollback() # Rollback any partial changes
        print(f"Error during timetable generation: {e}")
        return jsonify({'error': f'An internal server error occurred during generation: {e}'}), 500
    finally:
        cursor.close()


# --- Main Execution ---
if __name__ == '__main__':
    with app.app_context():
         init_db() # Ensure tables (including ClassSubjects) exist
    # Run on port 5000 as specified in user's last code snippet
    app.run(host='0.0.0.0', port=5000, debug=True) # Debug=True helps during development
