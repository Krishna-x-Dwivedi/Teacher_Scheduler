
from flask import Blueprint, jsonify
from backend.database import get_db
from mysql.connector import Error
import random

scheduler_bp = Blueprint('scheduler', __name__)

def fetch_scheduling_data(cursor):
    """Fetches all necessary data for timetable generation."""
    data = {}
    try:
        cursor.execute("SELECT class_id, year, class_name FROM Classes")
        data['classes'] = cursor.fetchall()

        cursor.execute("SELECT subject_id, name, is_lab FROM Subjects")
        data['subjects'] = {s['subject_id']: s for s in cursor.fetchall()}

        cursor.execute("SELECT faculty_id, name FROM Faculties")
        data['faculties'] = {f['faculty_id']: f for f in cursor.fetchall()}

        cursor.execute("SELECT location_id, room_no, is_lab FROM Locations")
        data['locations'] = cursor.fetchall()

        cursor.execute("SELECT faculty_id, subject_id FROM FacultySubjects")
        mappings = cursor.fetchall()
        data['faculty_subjects'] = {}
        for mapping in mappings:
            sub_id = mapping['subject_id']
            fac_id = mapping['faculty_id']
            if sub_id not in data['faculty_subjects']:
                data['faculty_subjects'][sub_id] = []
            data['faculty_subjects'][sub_id].append(fac_id)

        # Order timeslots to prefer earlier days/times
        cursor.execute("""
            SELECT slot_id, day_of_week, period_number, applicable_year_group 
            FROM TimeSlots 
            ORDER BY FIELD(day_of_week, 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'), period_number ASC
        """)
        data['timeslots'] = cursor.fetchall()

        cursor.execute("""
            SELECT CS.class_id, CS.subject_id, CS.hours_per_week, S.is_lab
            FROM ClassSubjects CS
            JOIN Subjects S ON CS.subject_id = S.subject_id
        """)
        requirements = cursor.fetchall()
        data['class_subject_requirements'] = {}
        for req in requirements:
            cls_id = req['class_id']
            if cls_id not in data['class_subject_requirements']:
                data['class_subject_requirements'][cls_id] = []
            
            data['class_subject_requirements'][cls_id].append((req['subject_id'], req['hours_per_week'], bool(req['is_lab'])))

        return data

    except Error as e:
        print(f"Error fetching scheduling data: {e}")
        return None

def solve_timetable_backtracking(assignments_needed, context):
    """
    Backtracking solver for the timetable.
    
    Args:
        assignments_needed: List of required assignments (dicts).
        context: Dict containing static data and current assignments state.
    
    Returns:
        True if solution found, False otherwise.
    """
    if not assignments_needed:
        return True

    # MRV Heuristic: Sort specific assignments? 
    # For now, we rely on the order passed in (which could be pre-sorted).
    
    current_assignment = assignments_needed[0]
    remaining_assignments = assignments_needed[1:]

    cls_id = current_assignment['class_id']
    subject_id = current_assignment['subject_id']
    is_lab = current_assignment['is_lab']
    cls_year = current_assignment['year']

    # Get Candidates
    possible_faculty_ids = context['faculty_subjects'].get(subject_id, [])
    possible_locations = context['lab_rooms'] if is_lab else context['lecture_rooms']
    
    # Shuffle candidates to vary results
    random.shuffle(possible_faculty_ids)
    random.shuffle(possible_locations)
    
    # Try all valid slots
    for slot in context['timeslots']:
        slot_id = slot['slot_id']
        
        # Check Year Group validity
        if slot['applicable_year_group'] != 'ALL':
            if slot['applicable_year_group'] == '1' and cls_year != 1: continue
            if slot['applicable_year_group'] == '2-3+' and cls_year < 2: continue

        # Conflict Checks
        # 1. Class already busy in this slot
        if context['class_schedule'].get((cls_id, slot_id)): continue
        
        for fac_id in possible_faculty_ids:
            # 2. Faculty already busy in this slot
            if context['faculty_schedule'].get((fac_id, slot_id)): continue
            
            for loc in possible_locations:
                loc_id = loc['location_id']
                # 3. Location already busy in this slot
                if context['location_schedule'].get((loc_id, slot_id)): continue
                
                # Make Assignment
                context['class_schedule'][(cls_id, slot_id)] = True
                context['faculty_schedule'][(fac_id, slot_id)] = True
                context['location_schedule'][(loc_id, slot_id)] = True
                
                # Store result
                context['results'].append({
                    'class_id': cls_id, 'slot_id': slot_id, 'subject_id': subject_id,
                    'faculty_id': fac_id, 'location_id': loc_id
                })
                
                # Recurse
                if solve_timetable_backtracking(remaining_assignments, context):
                    return True
                
                # Backtrack
                context['class_schedule'].pop((cls_id, slot_id), None)
                context['faculty_schedule'].pop((fac_id, slot_id), None)
                context['location_schedule'].pop((loc_id, slot_id), None)
                context['results'].pop()

    return False

@scheduler_bp.route('/generate-timetable', methods=['POST'])
def generate_timetable():
    print("Received request to generate timetable (Improved Backtracking).")
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    try:
        # Clear old entries
        cursor.execute("DELETE FROM TimetableEntries")
        print(f"Cleared {cursor.rowcount} previous entries.")

        # Fetch Data
        data = fetch_scheduling_data(cursor)
        if not data:
             return jsonify({'error': 'Failed to fetch data'}), 500

        # Prepare static lists
        lecture_rooms = [loc for loc in data['locations'] if not loc['is_lab']]
        lab_rooms = [loc for loc in data['locations'] if loc['is_lab']]
        
        # Prepare Requirements List
        assignments_needed = []
        for cls_id, reqs in data['class_subject_requirements'].items():
            # Find class object for year info
            cls_info = next((c for c in data['classes'] if c['class_id'] == cls_id), None)
            if not cls_info: continue
            
            for subject_id, hours, is_lab in reqs:
                for _ in range(hours):
                    assignments_needed.append({
                        'class_id': cls_id,
                        'subject_id': subject_id,
                        'is_lab': is_lab,
                        'year': cls_info['year']
                    })
        
        # Sort assignments by "difficulty" (heuristic)
        # Labs are harder (scarce rooms), Higher year assignments might be harder constrained?
        # Random shuffle is good for variety, but sorting by constrained-ness is better for solving.
        # Let's put Labs first, then random.
        random.shuffle(assignments_needed)
        assignments_needed.sort(key=lambda x: not x['is_lab']) # False (Is Lab) comes before True (Not Lab)? No. True=1. not True=0. So not x['is_lab'] puts True (is not lab) last. 
        # Wait: key=lambda x: x['is_lab'] (True=1, False=0). We want Labs (1) first. 
        # So reverse=True. 
        assignments_needed.sort(key=lambda x: x['is_lab'], reverse=True)

        # Context for recursion
        context = {
            'timeslots': data['timeslots'],
            'faculty_subjects': data['faculty_subjects'],
            'lecture_rooms': lecture_rooms,
            'lab_rooms': lab_rooms,
            'class_schedule': {},   # (class_id, slot_id) -> True
            'faculty_schedule': {}, # (fac_id, slot_id) -> True
            'location_schedule': {},# (loc_id, slot_id) -> True
            'results': []
        }

        print(f"Starting solver for {len(assignments_needed)} assignments...")
        success = solve_timetable_backtracking(assignments_needed, context)

        generated_entries = 0
        failed_assignments = 0

        if success:
            print("Solution found!")
            insert_query = """
                INSERT INTO TimetableEntries (class_id, slot_id, subject_id, faculty_id, location_id)
                VALUES (%s, %s, %s, %s, %s)
            """
            entries_to_insert = [
                (r['class_id'], r['slot_id'], r['subject_id'], r['faculty_id'], r['location_id'])
                for r in context['results']
            ]
            cursor.executemany(insert_query, entries_to_insert)
            db.commit()
            generated_entries = len(entries_to_insert)
            message = f"Successfully generated {generated_entries} entries."
        else:
            print("No complete solution found. Saving partial results if any? (Not implemented)")
            # In a real backtracking, checks might fail early. 
            # We could try to return "best effort", but pure backtracking fails completely if one task fails.
            # Fallback to the Greedy approach if backtracking fails? 
            # For now, report failure.
            failed_assignments = len(assignments_needed) # All failed technically
            message = "Could not generate a conflict-free timetable for all requirements."

        return jsonify({
            'message': message,
            'entries_generated': generated_entries,
            'failed_assignments': failed_assignments
        }), 200

    except Error as e:
        db.rollback()
        print(f"Error generation: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
