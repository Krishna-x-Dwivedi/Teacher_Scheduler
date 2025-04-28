# app.py: Flask Backend for Teacher Scheduler (with MySQL)

import os
import mysql.connector # Import MySQL connector
from mysql.connector import Error # Import Error class
from flask import Flask, request, jsonify, g # g is used to store db connection per request
from flask_cors import CORS # Required for allowing requests from the frontend origin
import datetime # Needed for TimeSlot time conversion

# --- App Configuration ---
app = Flask(__name__)
CORS(app) # Enable Cross-Origin Resource Sharing for all routes

# --- !!! IMPORTANT: CONFIGURE YOUR MYSQL DETAILS HERE !!! ---
# Replace placeholders with your actual MySQL credentials
MYSQL_CONFIG = {
    'user': 'root',     # Replace with your MySQL username (e.g., 'root')
    'password': '7530', # Replace with your MySQL password
    'host': 'localhost',               # Replace if your MySQL server is on a different host
    'database': 'timetable_db',        # Replace with the name of the database you created
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
            g.db = mysql.connector.connect(**MYSQL_CONFIG)
        except Error as e:
            print(f"Error connecting to MySQL Database: {e}")
            raise e
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

        # Locations Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Locations (
                location_id INT AUTO_INCREMENT PRIMARY KEY,
                room_no VARCHAR(50) NOT NULL,
                building VARCHAR(100) NULL,
                is_lab BOOLEAN NOT NULL DEFAULT FALSE
                -- Consider UNIQUE constraint on (room_no, building)
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
                applicable_year_group ENUM('1', '2-3+', 'ALL') NOT NULL,
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
                lab_batch_info VARCHAR(100) NULL,
                FOREIGN KEY (class_id) REFERENCES Classes(class_id) ON DELETE CASCADE,
                FOREIGN KEY (slot_id) REFERENCES TimeSlots(slot_id) ON DELETE CASCADE,
                FOREIGN KEY (subject_id) REFERENCES Subjects(subject_id) ON DELETE CASCADE,
                FOREIGN KEY (faculty_id) REFERENCES Faculties(faculty_id) ON DELETE CASCADE,
                FOREIGN KEY (location_id) REFERENCES Locations(location_id) ON DELETE CASCADE,
                UNIQUE KEY unique_class_slot (class_id, slot_id),
                UNIQUE KEY unique_faculty_slot (faculty_id, slot_id),
                UNIQUE KEY unique_location_slot (location_id, slot_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        print("Checked/Created TimetableEntries table.")

        db.commit()
        print("Database tables checked/created successfully.")

    except Error as e:
        print(f"Error during database initialization: {e}")
        if 'db' in g and g.db.is_connected():
            g.db.rollback()
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()

# --- Helper Function to convert time objects ---
def time_converter(o):
    if isinstance(o, datetime.timedelta):
        # Format timedelta (representing TIME) as HH:MM:SS string
        total_seconds = int(o.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02}:{minutes:02}:{seconds:02}"
    # Handle datetime objects if they appear unexpectedly
    if isinstance(o, (datetime.date, datetime.datetime)):
        return o.isoformat()
    return str(o) # Fallback for other types

# --- API Endpoints ---

@app.route('/')
def index():
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
@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password') # WARNING: Still plain text!

    if not name or not email or not password:
        return jsonify({'error': 'Missing required fields'}), 400

    db = get_db()
    cursor = db.cursor()
    try:
        query = "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)"
        cursor.execute(query, (name, email, password))
        db.commit()
        user_id = cursor.lastrowid
        return jsonify({'message': 'User created successfully', 'user_id': user_id}), 201
    except mysql.connector.IntegrityError:
        db.rollback()
        return jsonify({'error': 'Email already exists'}), 409
    except Error as e:
        db.rollback()
        print(f"Error during signup: {e}")
        return jsonify({'error': 'An internal server error occurred'}), 500
    finally:
        cursor.close()

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password') # WARNING: Still plain text!

    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400

    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        query = "SELECT id, name, email FROM users WHERE email = %s AND password = %s"
        cursor.execute(query, (email, password))
        user = cursor.fetchone()

        if user:
            return jsonify({'message': 'Login successful', 'user': user}), 200
        else:
            return jsonify({'error': 'Invalid email or password'}), 401
    except Error as e:
        print(f"Error during login: {e}")
        return jsonify({'error': 'An internal server error occurred'}), 500
    finally:
        cursor.close()

# --- Reminders (Adapted for MySQL) ---
@app.route('/api/reminders', methods=['GET'])
def get_reminders():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        query = "SELECT id, text, reminder_datetime FROM reminders ORDER BY reminder_datetime ASC"
        cursor.execute(query)
        reminders = cursor.fetchall()
        for r in reminders:
            if r.get('reminder_datetime'):
                 r['reminder_datetime'] = r['reminder_datetime'].isoformat()
        return jsonify(reminders), 200
    except Error as e:
        print(f"Error fetching reminders: {e}")
        return jsonify({'error': 'An internal server error occurred'}), 500
    finally:
        cursor.close()

@app.route('/api/reminders', methods=['POST'])
def add_reminder():
    data = request.get_json()
    text = data.get('text')
    reminder_datetime_str = data.get('reminder_datetime')

    if not text or not reminder_datetime_str:
        return jsonify({'error': 'Text and reminder_datetime are required'}), 400

    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        query = "INSERT INTO reminders (text, reminder_datetime) VALUES (%s, %s)"
        cursor.execute(query, (text, reminder_datetime_str))
        db.commit()
        new_reminder_id = cursor.lastrowid

        cursor.execute("SELECT id, text, reminder_datetime FROM reminders WHERE id = %s", (new_reminder_id,))
        new_reminder = cursor.fetchone()
        if new_reminder and new_reminder.get('reminder_datetime'):
             new_reminder['reminder_datetime'] = new_reminder['reminder_datetime'].isoformat()
        return jsonify(new_reminder), 201
    except Error as e:
        db.rollback()
        print(f"Error adding reminder: {e}")
        return jsonify({'error': 'An internal server error occurred'}), 500
    finally:
        cursor.close()

@app.route('/api/reminders/<int:reminder_id>', methods=['DELETE'])
def delete_reminder(reminder_id):
    db = get_db()
    cursor = db.cursor()
    try:
        query = "DELETE FROM reminders WHERE id = %s"
        cursor.execute(query, (reminder_id,))
        db.commit()
        if cursor.rowcount > 0:
            return jsonify({'message': 'Reminder deleted successfully'}), 200
        else:
            return jsonify({'error': 'Reminder not found'}), 404
    except Error as e:
        db.rollback()
        print(f"Error deleting reminder: {e}")
        return jsonify({'error': 'An internal server error occurred'}), 500
    finally:
        cursor.close()


# --- Admin Input Endpoints ---

# --- Faculties ---
@app.route('/api/faculties', methods=['POST'])
def add_faculty():
    data = request.get_json()
    name = data.get('name')
    faculty_code = data.get('faculty_code')

    if not name: return jsonify({'error': 'Faculty name is required'}), 400

    db = get_db(); cursor = db.cursor(dictionary=True)
    try:
        query = "INSERT INTO Faculties (name, faculty_code) VALUES (%s, %s)"
        cursor.execute(query, (name, faculty_code))
        db.commit()
        new_id = cursor.lastrowid
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
    db = get_db(); cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM Faculties ORDER BY name")
        faculties = cursor.fetchall()
        return jsonify(faculties), 200
    except Error as e: print(f"Error fetching faculties: {e}"); return jsonify({'error': 'An internal server error occurred'}), 500
    finally: cursor.close()

# --- Subjects ---
@app.route('/api/subjects', methods=['POST'])
def add_subject():
    data = request.get_json()
    code = data.get('code'); name = data.get('name'); is_lab = data.get('is_lab', False)
    if not code or not name: return jsonify({'error': 'Subject code and name are required'}), 400

    db = get_db(); cursor = db.cursor(dictionary=True)
    try:
        query = "INSERT INTO Subjects (code, name, is_lab) VALUES (%s, %s, %s)"
        cursor.execute(query, (code, name, bool(is_lab)))
        db.commit()
        new_id = cursor.lastrowid
        cursor.execute("SELECT * FROM Subjects WHERE subject_id = %s", (new_id,))
        new_subject = cursor.fetchone()
        return jsonify(new_subject), 201
    except mysql.connector.IntegrityError: db.rollback(); return jsonify({'error': f'Subject code "{code}" already exists.'}), 409
    except Error as e: db.rollback(); print(f"Error adding subject: {e}"); return jsonify({'error': 'An internal server error occurred'}), 500
    finally: cursor.close()

@app.route('/api/subjects', methods=['GET'])
def get_subjects():
    db = get_db(); cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM Subjects ORDER BY code")
        subjects = cursor.fetchall()
        return jsonify(subjects), 200
    except Error as e: print(f"Error fetching subjects: {e}"); return jsonify({'error': 'An internal server error occurred'}), 500
    finally: cursor.close()

# --- Faculty-Subject Mappings ---
@app.route('/api/faculty-subjects', methods=['POST'])
def add_faculty_subject_mapping():
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
@app.route('/api/branches', methods=['POST'])
def add_branch():
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
    db = get_db(); cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM Branches ORDER BY name")
        branches = cursor.fetchall()
        return jsonify(branches), 200
    except Error as e: print(f"Error fetching branches: {e}"); return jsonify({'error': 'An internal server error occurred'}), 500
    finally: cursor.close()

# --- Sections ---
@app.route('/api/sections', methods=['POST'])
def add_section():
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
    db = get_db(); cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM Sections ORDER BY name")
        sections = cursor.fetchall()
        return jsonify(sections), 200
    except Error as e: print(f"Error fetching sections: {e}"); return jsonify({'error': 'An internal server error occurred'}), 500
    finally: cursor.close()

# --- Classes ---
@app.route('/api/classes', methods=['POST'])
def add_class():
    data = request.get_json()
    branch_id = data.get('branch_id'); section_id = data.get('section_id'); year = data.get('year')
    class_name = data.get('class_name') # Optional, can be generated

    if not branch_id or not section_id or not year:
        return jsonify({'error': 'Branch ID, Section ID, and Year are required'}), 400

    # Basic validation
    try: year = int(year)
    except ValueError: return jsonify({'error': 'Year must be an integer'}), 400

    db = get_db(); cursor = db.cursor(dictionary=True)
    try:
        # Optional: Generate class_name if not provided
        if not class_name:
            cursor.execute("SELECT name FROM Branches WHERE branch_id = %s", (branch_id,))
            branch = cursor.fetchone()
            cursor.execute("SELECT name FROM Sections WHERE section_id = %s", (section_id,))
            section = cursor.fetchone()
            if branch and section:
                class_name = f"{branch['name']} Year {year} Section {section['name']}"
            else:
                class_name = f"Class_{branch_id}_{section_id}_{year}" # Fallback name

        query = "INSERT INTO Classes (branch_id, section_id, year, class_name) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (branch_id, section_id, year, class_name))
        db.commit(); new_id = cursor.lastrowid
        # Fetch the created class with joined names for better response
        fetch_query = """ SELECT C.*, B.name as branch_name, S.name as section_name
                          FROM Classes C
                          JOIN Branches B ON C.branch_id = B.branch_id
                          JOIN Sections S ON C.section_id = S.section_id
                          WHERE C.class_id = %s """
        cursor.execute(fetch_query, (new_id,))
        new_class = cursor.fetchone()
        return jsonify(new_class), 201
    except mysql.connector.IntegrityError: db.rollback(); return jsonify({'error': f'Class name "{class_name}" already exists or invalid Branch/Section ID.'}), 409
    except Error as e: db.rollback(); print(f"Error adding class: {e}"); return jsonify({'error': 'An internal server error occurred'}), 500
    finally: cursor.close()

@app.route('/api/classes', methods=['GET'])
def get_classes():
    db = get_db(); cursor = db.cursor(dictionary=True)
    try:
        query = """ SELECT C.*, B.name as branch_name, S.name as section_name
                    FROM Classes C
                    JOIN Branches B ON C.branch_id = B.branch_id
                    JOIN Sections S ON C.section_id = S.section_id
                    ORDER BY B.name, C.year, S.name """
        cursor.execute(query)
        classes = cursor.fetchall()
        return jsonify(classes), 200
    except Error as e: print(f"Error fetching classes: {e}"); return jsonify({'error': 'An internal server error occurred'}), 500
    finally: cursor.close()

# --- Locations ---
@app.route('/api/locations', methods=['POST'])
def add_location():
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
    # Add specific integrity error handling if needed (e.g., unique room+building)
    except Error as e: db.rollback(); print(f"Error adding location: {e}"); return jsonify({'error': 'An internal server error occurred'}), 500
    finally: cursor.close()

@app.route('/api/locations', methods=['GET'])
def get_locations():
    db = get_db(); cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM Locations ORDER BY building, room_no")
        locations = cursor.fetchall()
        return jsonify(locations), 200
    except Error as e: print(f"Error fetching locations: {e}"); return jsonify({'error': 'An internal server error occurred'}), 500
    finally: cursor.close()

# --- TimeSlots ---
@app.route('/api/timeslots', methods=['POST'])
def add_timeslot():
    data = request.get_json()
    day = data.get('day_of_week'); period = data.get('period_number')
    start = data.get('start_time'); end = data.get('end_time'); year_group = data.get('applicable_year_group')

    if not all([day, period, start, end, year_group]):
        return jsonify({'error': 'All fields (day, period, start, end, year_group) are required'}), 400
    if year_group not in ['1', '2-3+', 'ALL']:
        return jsonify({'error': 'Invalid applicable_year_group. Must be "1", "2-3+", or "ALL".'}), 400
    # Basic validation
    try: period = int(period)
    except ValueError: return jsonify({'error': 'Period number must be an integer'}), 400
    # Basic time format check (HH:MM or HH:MM:SS) - more robust validation recommended
    if not (len(start) >= 5 and ':' in start and len(end) >= 5 and ':' in end):
         return jsonify({'error': 'Invalid time format. Use HH:MM or HH:MM:SS'}), 400


    db = get_db(); cursor = db.cursor(dictionary=True)
    try:
        query = """ INSERT INTO TimeSlots (day_of_week, period_number, start_time, end_time, applicable_year_group)
                    VALUES (%s, %s, %s, %s, %s) """
        cursor.execute(query, (day, period, start, end, year_group))
        db.commit(); new_id = cursor.lastrowid
        cursor.execute("SELECT * FROM TimeSlots WHERE slot_id = %s", (new_id,))
        new_slot = cursor.fetchone()
        # Convert time objects before returning JSON
        if new_slot:
            new_slot['start_time'] = time_converter(new_slot.get('start_time'))
            new_slot['end_time'] = time_converter(new_slot.get('end_time'))
        return jsonify(new_slot), 201
    except mysql.connector.IntegrityError: db.rollback(); return jsonify({'error': f'Time slot for {day} Period {period} ({year_group}) already exists.'}), 409
    except Error as e: db.rollback(); print(f"Error adding timeslot: {e}"); return jsonify({'error': 'An internal server error occurred'}), 500
    finally: cursor.close()

@app.route('/api/timeslots', methods=['GET'])
def get_timeslots():
    db = get_db(); cursor = db.cursor(dictionary=True)
    try:
        query = "SELECT * FROM TimeSlots ORDER BY FIELD(day_of_week, 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'), period_number"
        cursor.execute(query)
        timeslots = cursor.fetchall()
        # Convert time objects before returning JSON
        for slot in timeslots:
            slot['start_time'] = time_converter(slot.get('start_time'))
            slot['end_time'] = time_converter(slot.get('end_time'))
        return jsonify(timeslots), 200
    except Error as e: print(f"Error fetching timeslots: {e}"); return jsonify({'error': 'An internal server error occurred'}), 500
    finally: cursor.close()


# --- Timetable Generation (Placeholder) ---
@app.route('/api/generate-timetable', methods=['POST'])
def generate_timetable():
    # --- THIS IS A PLACEHOLDER ---
    # The actual generation logic will be complex and needs to be implemented here.
    # It will involve:
    # 1. Fetching all necessary data (Classes, Subjects required per class, Faculties, FacultySubjects, Locations, TimeSlots).
    # 2. Applying constraints (faculty availability, location availability, subject requirements, etc.).
    # 3. Using an algorithm (e.g., constraint satisfaction, backtracking, genetic algorithm) to find a valid schedule.
    # 4. Clearing old TimetableEntries (optional, or maybe versioning).
    # 5. Inserting the generated entries into the TimetableEntries table.

    print("Received request to generate timetable (Not Implemented Yet).")
    # For now, just return a message indicating it's not implemented.
    return jsonify({'message': 'Timetable generation endpoint reached, but logic is not yet implemented.'}), 501 # 501 Not Implemented


# --- Main Execution ---
if __name__ == '__main__':
    with app.app_context():
         init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
