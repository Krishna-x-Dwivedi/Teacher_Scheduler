
from flask import Blueprint, request, jsonify
from backend.database import get_db, time_converter
from mysql.connector import Error, IntegrityError
import datetime

api_bp = Blueprint('api', __name__)

# --- REMINDERS ---
@api_bp.route('/reminders', methods=['GET'])
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

@api_bp.route('/reminders', methods=['POST'])
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

@api_bp.route('/reminders/<int:reminder_id>', methods=['DELETE'])
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

# --- FACULTIES ---
@api_bp.route('/faculties', methods=['POST'])
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
    except IntegrityError as e:
         db.rollback()
         if e.errno == 1062: return jsonify({'error': f'Faculty code "{faculty_code}" already exists.'}), 409
         else: print(f"Integrity error adding faculty: {e}"); return jsonify({'error': 'Database integrity error.'}), 400
    except Error as e: db.rollback(); print(f"Error adding faculty: {e}"); return jsonify({'error': 'An internal server error occurred'}), 500
    finally: cursor.close()

@api_bp.route('/faculties', methods=['GET'])
def get_faculties():
    """Fetches all faculty members."""
    db = get_db(); cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM Faculties ORDER BY name")
        faculties = cursor.fetchall()
        return jsonify(faculties), 200
    except Error as e: print(f"Error fetching faculties: {e}"); return jsonify({'error': 'An internal server error occurred'}), 500
    finally: cursor.close()

# --- SUBJECTS ---
@api_bp.route('/subjects', methods=['POST'])
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
    except IntegrityError: db.rollback(); return jsonify({'error': f'Subject code "{code}" already exists.'}), 409
    except Error as e: db.rollback(); print(f"Error adding subject: {e}"); return jsonify({'error': 'An internal server error occurred'}), 500
    finally: cursor.close()

@api_bp.route('/subjects', methods=['GET'])
def get_subjects():
    """Fetches all subjects."""
    db = get_db(); cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM Subjects ORDER BY code")
        subjects = cursor.fetchall()
        return jsonify(subjects), 200
    except Error as e: print(f"Error fetching subjects: {e}"); return jsonify({'error': 'An internal server error occurred'}), 500
    finally: cursor.close()

# --- MAPPINGS ---
@api_bp.route('/faculty-subjects', methods=['POST'])
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
    except IntegrityError: db.rollback(); return jsonify({'error': 'Mapping already exists or invalid Faculty/Subject ID.'}), 409
    except Error as e: db.rollback(); print(f"Error adding faculty-subject mapping: {e}"); return jsonify({'error': 'An internal server error occurred'}), 500
    finally: cursor.close()

@api_bp.route('/faculty-subjects/<int:faculty_id>', methods=['GET'])
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

@api_bp.route('/faculty-subjects/<int:faculty_id>/<int:subject_id>', methods=['DELETE'])
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

# --- BRANCHES ---
@api_bp.route('/branches', methods=['POST'])
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
    except IntegrityError: db.rollback(); return jsonify({'error': f'Branch name "{name}" or code "{code}" already exists.'}), 409
    except Error as e: db.rollback(); print(f"Error adding branch: {e}"); return jsonify({'error': 'An internal server error occurred'}), 500
    finally: cursor.close()

@api_bp.route('/branches', methods=['GET'])
def get_branches():
    """Fetches all academic branches."""
    db = get_db(); cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM Branches ORDER BY name")
        branches = cursor.fetchall()
        return jsonify(branches), 200
    except Error as e: print(f"Error fetching branches: {e}"); return jsonify({'error': 'An internal server error occurred'}), 500
    finally: cursor.close()

# --- SECTIONS ---
@api_bp.route('/sections', methods=['POST'])
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
    except IntegrityError: db.rollback(); return jsonify({'error': f'Section name "{name}" already exists.'}), 409
    except Error as e: db.rollback(); print(f"Error adding section: {e}"); return jsonify({'error': 'An internal server error occurred'}), 500
    finally: cursor.close()

@api_bp.route('/sections', methods=['GET'])
def get_sections():
    """Fetches all section designations."""
    db = get_db(); cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM Sections ORDER BY name")
        sections = cursor.fetchall()
        return jsonify(sections), 200
    except Error as e: print(f"Error fetching sections: {e}"); return jsonify({'error': 'An internal server error occurred'}), 500
    finally: cursor.close()

# --- CLASSES ---
@api_bp.route('/classes', methods=['POST'])
def add_class():
    """Adds a new class (combination of branch, section, year)."""
    data = request.get_json()
    branch_id = data.get('branch_id'); section_id = data.get('section_id'); year = data.get('year')
    class_name = data.get('class_name')

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
    except IntegrityError: db.rollback(); return jsonify({'error': f'Class name "{class_name}" already exists or invalid Branch/Section ID.'}), 409
    except Error as e: db.rollback(); print(f"Error adding class: {e}"); return jsonify({'error': 'An internal server error occurred'}), 500
    finally: cursor.close()

@api_bp.route('/classes', methods=['GET'])
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

@api_bp.route('/class-subjects/<int:class_id>', methods=['GET'])
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

@api_bp.route('/class-subjects', methods=['POST'])
def add_class_subject():
    """Adds a subject requirement for a class."""
    data = request.get_json()
    class_id = data.get('class_id')
    subject_id = data.get('subject_id')
    hours_per_week = data.get('hours_per_week', 1)

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
    except IntegrityError:
        db.rollback()
        return jsonify({'error': 'Requirement already exists or invalid Class/Subject ID.'}), 409
    except Error as e:
        db.rollback()
        print(f"Error adding class subject requirement: {e}")
        return jsonify({'error': 'An internal server error occurred'}), 500
    finally:
        cursor.close()

# --- LOCATIONS ---
@api_bp.route('/locations', methods=['POST'])
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

@api_bp.route('/locations', methods=['GET'])
def get_locations():
    """Fetches all locations."""
    db = get_db(); cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM Locations ORDER BY building, room_no")
        locations = cursor.fetchall()
        return jsonify(locations), 200
    except Error as e: print(f"Error fetching locations: {e}"); return jsonify({'error': 'An internal server error occurred'}), 500
    finally: cursor.close()

# --- TIMESLOTS ---
@api_bp.route('/timeslots', methods=['POST'])
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
        datetime.time.fromisoformat(start.split('T')[-1])
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
    except IntegrityError: db.rollback(); return jsonify({'error': f'Time slot for {day} Period {period} ({year_group}) already exists.'}), 409
    except Error as e: db.rollback(); print(f"Error adding timeslot: {e}"); return jsonify({'error': 'An internal server error occurred'}), 500
    finally: cursor.close()

@api_bp.route('/timeslots', methods=['GET'])
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
