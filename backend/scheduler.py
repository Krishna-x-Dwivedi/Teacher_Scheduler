
from flask import Blueprint, jsonify
from backend.database import db
from backend.models import (
    Class, Subject, Faculty, Location, TimeSlot, ClassSubject, TimetableEntry,
    faculty_subjects
)
import random

scheduler_bp = Blueprint('scheduler', __name__)

def fetch_scheduling_data_orm():
    """Fetches all necessary data for timetable generation using ORM."""
    data = {}
    try:
        # We need plain lists or dicts usually for the algorithm, or we can use objects directly.
        # Using objects directly is cleaner in Python.
        
        data['classes'] = Class.query.all()
        data['subjects'] = {s.subject_id: s for s in Subject.query.all()}
        data['faculties'] = {f.faculty_id: f for f in Faculty.query.all()}
        data['locations'] = Location.query.all()
        
        # Sort Timeslots
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        all_slots = TimeSlot.query.all()
        all_slots.sort(key=lambda x: (days.index(x.day_of_week) if x.day_of_week in days else 99, x.period_number))
        data['timeslots'] = all_slots

        # Requirements
        # Group by class
        data['class_subject_requirements'] = {}
        all_reqs = ClassSubject.query.all()
        for req in all_reqs:
            if req.class_id not in data['class_subject_requirements']:
                data['class_subject_requirements'][req.class_id] = []
            
            # (subject_id, hours, is_lab)
            # Accessing subject via relationship req.subject
            data['class_subject_requirements'][req.class_id].append(
                (req.subject_id, req.hours_per_week, req.subject.is_lab)
            )

        return data

    except Exception as e:
        print(f"Error fetching scheduling data: {e}")
        return None

def solve_timetable_backtracking(assignments_needed, context):
    """
    Backtracking solver.
    Args:
        assignments_needed: List of dicts representing tasks.
        context: Dictionaries for fast lookups and state tracking.
    """
    if not assignments_needed:
        return True

    current_assignment = assignments_needed[0]
    remaining_assignments = assignments_needed[1:]

    cls_id = current_assignment['class_id']
    subject_id = current_assignment['subject_id']
    is_lab = current_assignment['is_lab']
    cls_year = current_assignment['year']

    # Get Candidates
    # Faculty ID list for this subject.
    # In ORM: Subject.faculties gives list of Faculty objects.
    subject_obj = context['subjects_map'].get(subject_id)
    possible_faculty_ids = [f.faculty_id for f in subject_obj.faculties] if subject_obj else []
    
    possible_locations = context['lab_rooms'] if is_lab else context['lecture_rooms']
    
    random.shuffle(possible_faculty_ids)
    random.shuffle(possible_locations)
    
    for slot in context['timeslots']:
        slot_id = slot.slot_id
        
        # Check Year Group validity
        if slot.applicable_year_group != 'ALL':
            if slot.applicable_year_group == '1' and cls_year != 1: continue
            if slot.applicable_year_group == '2-3+' and cls_year < 2: continue

        # Conflict Checks
        if context['class_schedule'].get((cls_id, slot_id)): continue
        
        for fac_id in possible_faculty_ids:
            if context['faculty_schedule'].get((fac_id, slot_id)): continue
            
            for loc in possible_locations:
                loc_id = loc.location_id
                if context['location_schedule'].get((loc_id, slot_id)): continue
                
                # Assign
                context['class_schedule'][(cls_id, slot_id)] = True
                context['faculty_schedule'][(fac_id, slot_id)] = True
                context['location_schedule'][(loc_id, slot_id)] = True
                
                context['results'].append({
                    'class_id': cls_id, 'slot_id': slot_id, 'subject_id': subject_id,
                    'faculty_id': fac_id, 'location_id': loc_id
                })
                
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
    print("Received request to generate timetable (ORM Backtracking).")
    
    try:
        # Clear old
        TimetableEntry.query.delete()
        db.session.commit()
        print("Cleared previous entries.")

        # Fetch Data
        data = fetch_scheduling_data_orm()
        if not data:
             return jsonify({'error': 'Failed to fetch data'}), 500

        lecture_rooms = [loc for loc in data['locations'] if not loc.is_lab]
        lab_rooms = [loc for loc in data['locations'] if loc.is_lab]
        
        # Build Assignments List
        assignments_needed = []
        for cls_id, reqs in data['class_subject_requirements'].items():
            # Find class object from list (inefficient but safe) or map
            cls_info = next((c for c in data['classes'] if c.class_id == cls_id), None)
            if not cls_info: continue
            
            for subject_id, hours, is_lab in reqs:
                for _ in range(hours):
                    assignments_needed.append({
                        'class_id': cls_id,
                        'subject_id': subject_id,
                        'is_lab': is_lab,
                        'year': cls_info.year
                    })
        
        random.shuffle(assignments_needed)
        # Labs first
        assignments_needed.sort(key=lambda x: x['is_lab'], reverse=True)

        context = {
            'timeslots': data['timeslots'],
            'subjects_map': data['subjects'], # To look up faculty
            'lecture_rooms': lecture_rooms,
            'lab_rooms': lab_rooms,
            'class_schedule': {},
            'faculty_schedule': {},
            'location_schedule': {},
            'results': []
        }

        print(f"Starting solver for {len(assignments_needed)} assignments...")
        success = solve_timetable_backtracking(assignments_needed, context)

        generated_entries = 0
        if success:
            print("Solution found!")
            for r in context['results']:
                entry = TimetableEntry(
                    class_id=r['class_id'],
                    slot_id=r['slot_id'],
                    subject_id=r['subject_id'],
                    faculty_id=r['faculty_id'],
                    location_id=r['location_id']
                )
                db.session.add(entry)
            
            db.session.commit()
            generated_entries = len(context['results'])
            message = f"Successfully generated {generated_entries} entries."
        else:
            message = "Could not generate a conflict-free timetable for all requirements."
            generated_entries = 0
            failed_assignments = len(assignments_needed) # Estimate

        return jsonify({
            'message': message,
            'entries_generated': generated_entries,
            'failed_assignments': 0 if success else "All"
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"Error generation: {e}")
        return jsonify({'error': str(e)}), 500
