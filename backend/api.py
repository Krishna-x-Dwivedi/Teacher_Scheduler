
from flask import Blueprint, request, jsonify
from backend.database import db, time_converter
from backend.models import (
    Reminder, Faculty, Subject, Branch, Section, Class, 
    Location, TimeSlot, ClassSubject, faculty_subjects
)
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import datetime as dt

api_bp = Blueprint('api', __name__)

# --- REMINDERS ---
@api_bp.route('/reminders', methods=['GET'])
def get_reminders():
    try:
        reminders = Reminder.query.order_by(Reminder.reminder_datetime.asc()).all()
        return jsonify([{
            'id': r.id, 
            'text': r.text, 
            'reminder_datetime': r.reminder_datetime.isoformat() if r.reminder_datetime else None
        } for r in reminders]), 200
    except Exception as e:
        print(f"Error fetching reminders: {e}")
        return jsonify({'error': 'An internal server error occurred'}), 500

@api_bp.route('/reminders', methods=['POST'])
def add_reminder():
    data = request.get_json()
    text = data.get('text')
    reminder_datetime_str = data.get('reminder_datetime')
    if not text or not reminder_datetime_str:
        return jsonify({'error': 'Text and reminder_datetime are required'}), 400

    try:
        new_reminder = Reminder(
            text=text,
            reminder_datetime=datetime.fromisoformat(reminder_datetime_str)
        )
        db.session.add(new_reminder)
        db.session.commit()
        return jsonify({
            'id': new_reminder.id,
            'text': new_reminder.text,
            'reminder_datetime': new_reminder.reminder_datetime.isoformat()
        }), 201
    except Exception as e:
        db.session.rollback()
        print(f"Error adding reminder: {e}")
        return jsonify({'error': 'An internal server error occurred'}), 500

@api_bp.route('/reminders/<int:reminder_id>', methods=['DELETE'])
def delete_reminder(reminder_id):
    try:
        reminder = Reminder.query.get(reminder_id)
        if not reminder:
            return jsonify({'error': 'Reminder not found'}), 404
        db.session.delete(reminder)
        db.session.commit()
        return jsonify({'message': 'Reminder deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting reminder: {e}")
        return jsonify({'error': 'An internal server error occurred'}), 500

# --- FACULTIES ---
@api_bp.route('/faculties', methods=['POST'])
def add_faculty():
    data = request.get_json()
    name = data.get('name')
    faculty_code = data.get('faculty_code') or None # Ensure empty string is None if unique constraint
    if not name:
        return jsonify({'error': 'Faculty name is required'}), 400

    try:
        new_faculty = Faculty(name=name, faculty_code=faculty_code)
        db.session.add(new_faculty)
        db.session.commit()
        return jsonify({
            'faculty_id': new_faculty.faculty_id,
            'name': new_faculty.name,
            'faculty_code': new_faculty.faculty_code
        }), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': f'Faculty code "{faculty_code}" already exists.'}), 409
    except Exception as e:
        db.session.rollback()
        print(f"Error adding faculty: {e}")
        return jsonify({'error': 'An internal server error occurred'}), 500

@api_bp.route('/faculties', methods=['GET'])
def get_faculties():
    try:
        faculties = Faculty.query.order_by(Faculty.name).all()
        return jsonify([{
            'faculty_id': f.faculty_id,
            'name': f.name,
            'faculty_code': f.faculty_code
        } for f in faculties]), 200
    except Exception as e:
        print(f"Error fetching faculties: {e}")
        return jsonify({'error': 'An internal server error occurred'}), 500

# --- SUBJECTS ---
@api_bp.route('/subjects', methods=['POST'])
def add_subject():
    data = request.get_json()
    code = data.get('code')
    name = data.get('name')
    is_lab = data.get('is_lab', False)
    if not code or not name:
        return jsonify({'error': 'Subject code and name are required'}), 400

    try:
        new_subject = Subject(code=code, name=name, is_lab=bool(is_lab))
        db.session.add(new_subject)
        db.session.commit()
        return jsonify({
            'subject_id': new_subject.subject_id,
            'code': new_subject.code,
            'name': new_subject.name,
            'is_lab': new_subject.is_lab
        }), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': f'Subject code "{code}" already exists.'}), 409
    except Exception as e:
        db.session.rollback()
        print(f"Error adding subject: {e}")
        return jsonify({'error': 'An internal server error occurred'}), 500

@api_bp.route('/subjects', methods=['GET'])
def get_subjects():
    try:
        subjects = Subject.query.order_by(Subject.code).all()
        return jsonify([{
            'subject_id': s.subject_id,
            'code': s.code,
            'name': s.name,
            'is_lab': s.is_lab
        } for s in subjects]), 200
    except Exception as e:
        print(f"Error fetching subjects: {e}")
        return jsonify({'error': 'An internal server error occurred'}), 500

# --- MAPPINGS (Faculty-Subject) ---
@api_bp.route('/faculty-subjects', methods=['POST'])
def add_faculty_subject_mapping():
    data = request.get_json()
    faculty_id = data.get('faculty_id')
    subject_id = data.get('subject_id')
    
    if not faculty_id or not subject_id:
        return jsonify({'error': 'Faculty ID and Subject ID are required'}), 400

    try:
        faculty = Faculty.query.get(faculty_id)
        subject = Subject.query.get(subject_id)
        
        if not faculty or not subject:
             return jsonify({'error': 'Invalid Faculty or Subject ID'}), 400
             
        # Add to relationship
        # Check if already exists? set addition handles uniqueness usually in python, 
        # but db constraint will catch it.
        # SQLAlchemy association objects usually append.
        if subject in faculty.subjects:
            return jsonify({'error': 'Mapping already exists'}), 409

        faculty.subjects.append(subject)
        db.session.commit()
        return jsonify({'message': 'Faculty-Subject mapping added successfully'}), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Database integrity error.'}), 409
    except Exception as e:
        db.session.rollback()
        print(f"Error adding mapping: {e}")
        return jsonify({'error': 'An internal server error occurred'}), 500

@api_bp.route('/faculty-subjects/<int:faculty_id>', methods=['GET'])
def get_subjects_for_faculty(faculty_id):
    try:
        faculty = Faculty.query.get(faculty_id)
        if not faculty:
            return jsonify([]), 200
        
        # Sort manually or via query if we change relationship
        subjects = sorted(faculty.subjects, key=lambda s: s.code)
        
        return jsonify([{
            'subject_id': s.subject_id,
            'code': s.code,
            'name': s.name,
            'is_lab': s.is_lab
        } for s in subjects]), 200
    except Exception as e:
        print(f"Error fetching subjects for faculty: {e}")
        return jsonify({'error': 'An internal server error occurred'}), 500

@api_bp.route('/faculty-subjects/<int:faculty_id>/<int:subject_id>', methods=['DELETE'])
def delete_faculty_subject_mapping(faculty_id, subject_id):
    try:
        faculty = Faculty.query.get(faculty_id)
        subject = Subject.query.get(subject_id)
        
        if faculty and subject and subject in faculty.subjects:
            faculty.subjects.remove(subject)
            db.session.commit()
            return jsonify({'message': 'Faculty-Subject mapping deleted successfully'}), 200
        else:
            return jsonify({'error': 'Mapping not found'}), 404
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting mapping: {e}")
        return jsonify({'error': 'An internal server error occurred'}), 500

# --- BRANCHES ---
@api_bp.route('/branches', methods=['POST'])
def add_branch():
    data = request.get_json()
    name = data.get('name')
    code = data.get('code')
    if not name:
        return jsonify({'error': 'Branch name is required'}), 400

    try:
        new_branch = Branch(name=name, code=code)
        db.session.add(new_branch)
        db.session.commit()
        return jsonify({
            'branch_id': new_branch.branch_id,
            'name': new_branch.name,
            'code': new_branch.code
        }), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': f'Branch name or code already exists.'}), 409
    except Exception as e:
        db.session.rollback()
        print(f"Error adding branch: {e}")
        return jsonify({'error': 'An internal server error occurred'}), 500

@api_bp.route('/branches', methods=['GET'])
def get_branches():
    try:
        branches = Branch.query.order_by(Branch.name).all()
        return jsonify([{
            'branch_id': b.branch_id,
            'name': b.name,
            'code': b.code
        } for b in branches]), 200
    except Exception as e:
        return jsonify({'error': 'An internal server error occurred'}), 500

# --- SECTIONS ---
@api_bp.route('/sections', methods=['POST'])
def add_section():
    data = request.get_json()
    name = data.get('name')
    if not name: return jsonify({'error': 'Section name is required'}), 400

    try:
        new_section = Section(name=name)
        db.session.add(new_section)
        db.session.commit()
        return jsonify({'section_id': new_section.section_id, 'name': new_section.name}), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': f'Section name "{name}" already exists.'}), 409
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'An internal server error occurred'}), 500

@api_bp.route('/sections', methods=['GET'])
def get_sections():
    try:
        sections = Section.query.order_by(Section.name).all()
        return jsonify([{'section_id': s.section_id, 'name': s.name} for s in sections]), 200
    except Exception:
        return jsonify({'error': 'An internal server error occurred'}), 500

# --- CLASSES ---
@api_bp.route('/classes', methods=['POST'])
def add_class():
    data = request.get_json()
    branch_id = data.get('branch_id')
    section_id = data.get('section_id')
    year = data.get('year')
    class_name = data.get('class_name')

    if not branch_id or not section_id or not year:
        return jsonify({'error': 'Branch ID, Section ID, and Year are required'}), 400

    try:
        year = int(year)
        if not class_name:
            branch = Branch.query.get(branch_id)
            section = Section.query.get(section_id)
            if branch and section:
                class_name = f"{branch.name} Year {year} Section {section.name}"
            else:
                 return jsonify({'error': 'Invalid Branch or Section ID'}), 400

        new_class = Class(branch_id=branch_id, section_id=section_id, year=year, class_name=class_name)
        db.session.add(new_class)
        db.session.commit()
        
        # Determine names for response
        # Since we just added, we can access relationships if session is active
        # Or re-query, but object is attached. 
        # Actually accessing relationships might trigger lazy load.
        
        return jsonify({
            'class_id': new_class.class_id,
            'class_name': new_class.class_name,
            'branch_name': new_class.branch.name,
            'section_name': new_class.section.name,
            'year': new_class.year
        }), 201

    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': f'Class already exists.'}), 409
    except Exception as e:
        db.session.rollback()
        print(f"Error adding class: {e}")
        return jsonify({'error': 'An internal server error occurred'}), 500

@api_bp.route('/classes', methods=['GET'])
def get_classes():
    try:
        classes = Class.query.join(Branch).join(Section).order_by(Branch.name, Class.year, Section.name).all()
        return jsonify([{
            'class_id': c.class_id,
            'class_name': c.class_name,
            'branch_id': c.branch_id,
            'section_id': c.section_id,
            'branch_name': c.branch.name,
            'section_name': c.section.name,
            'year': c.year
        } for c in classes]), 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'An internal server error occurred'}), 500

# --- CLASS SUBJECTS ---
@api_bp.route('/class-subjects/<int:class_id>', methods=['GET'])
def get_class_subjects(class_id):
    try:
        reqs = ClassSubject.query.filter_by(class_id=class_id).join(Subject).order_by(Subject.code).all()
        return jsonify([{
            'class_subject_id': r.class_subject_id,
            'class_id': r.class_id,
            'subject_id': r.subject_id,
            'hours_per_week': r.hours_per_week,
            'subject_code': r.subject.code,
            'subject_name': r.subject.name,
            'is_lab': r.subject.is_lab
        } for r in reqs]), 200
    except Exception as e:
        print(e)
        return jsonify({'error': 'An internal server error occurred'}), 500

@api_bp.route('/class-subjects', methods=['POST'])
def add_class_subject():
    data = request.get_json()
    class_id = data.get('class_id')
    subject_id = data.get('subject_id')
    hours_per_week = data.get('hours_per_week', 1)

    if not class_id or not subject_id:
        return jsonify({'error': 'Class ID and Subject ID are required'}), 400

    try:
        new_req = ClassSubject(class_id=class_id, subject_id=subject_id, hours_per_week=hours_per_week)
        db.session.add(new_req)
        db.session.commit()
        return jsonify({'message': 'Requirement added', 'id': new_req.class_subject_id}), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Requirement already exists or invalid IDs.'}), 409
    except Exception as e:
        db.session.rollback()
        print(e)
        return jsonify({'error': 'Server Error'}), 500

# --- LOCATIONS ---
@api_bp.route('/locations', methods=['POST'])
def add_location():
    data = request.get_json()
    room_no = data.get('room_no')
    building = data.get('building')
    is_lab = data.get('is_lab', False)
    if not room_no: return jsonify({'error': 'Room number required'}), 400
    
    try:
        new_loc = Location(room_no=room_no, building=building, is_lab=bool(is_lab))
        db.session.add(new_loc)
        db.session.commit()
        return jsonify({'location_id': new_loc.location_id, 'room_no': new_loc.room_no}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error'}), 500

@api_bp.route('/locations', methods=['GET'])
def get_locations():
    try:
        locs = Location.query.order_by(Location.building, Location.room_no).all()
        return jsonify([{
            'location_id': l.location_id,
            'room_no': l.room_no,
            'building': l.building,
            'is_lab': l.is_lab
        } for l in locs]), 200
    except Exception: return jsonify({'error': 'Error'}), 500

# --- TIMESLOTS ---
@api_bp.route('/timeslots', methods=['POST'])
def add_timeslot():
    data = request.get_json()
    day = data.get('day_of_week')
    period = data.get('period_number')
    start = data.get('start_time')
    end = data.get('end_time')
    year_group = data.get('applicable_year_group')

    if not all([day, period, start, end, year_group]):
         return jsonify({'error': 'All fields required'}), 400

    try:
        # Values validation usually done here, skipping for brevity as types handle some
        new_slot = TimeSlot(
            day_of_week=day,
            period_number=int(period),
            start_time=dt.time.fromisoformat(start),
            end_time=dt.time.fromisoformat(end),
            applicable_year_group=year_group
        )
        db.session.add(new_slot)
        db.session.commit()
        
        return jsonify({
            'slot_id': new_slot.slot_id,
            'day_of_week': new_slot.day_of_week,
            'period_number': new_slot.period_number,
            'start_time': time_converter(new_slot.start_time),
            'end_time': time_converter(new_slot.end_time)
        }), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Duplicate timeslot.'}), 409
    except Exception as e:
        db.session.rollback()
        print(e)
        return jsonify({'error': 'Error'}), 500

@api_bp.route('/timeslots', methods=['GET'])
def get_timeslots():
    try:
        # SQLA doesn't inherently sort ENUM strings perfectly like 'Monday', 'Tuesday'
        # unless mapped to ints or using custom CASE/ORDER logic.
        # For simplicity we might just fetch and sort in python, or rely on insert order for now.
        slots = TimeSlot.query.all()
        # Custom sort helper
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        slots.sort(key=lambda x: (days.index(x.day_of_week) if x.day_of_week in days else 99, x.period_number))
        
        return jsonify([{
            'slot_id': s.slot_id,
            'day_of_week': s.day_of_week,
            'period_number': s.period_number,
            'start_time': time_converter(s.start_time),
            'end_time': time_converter(s.end_time),
            'applicable_year_group': s.applicable_year_group
        } for s in slots]), 200
    except Exception as e:
        print(e)
        return jsonify({'error': 'Error'}), 500
