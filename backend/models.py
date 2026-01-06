
from backend.database import db
from datetime import datetime

# Association Tables
faculty_subjects = db.Table('faculty_subjects',
    db.Column('faculty_id', db.Integer, db.ForeignKey('faculties.faculty_id', ondelete='CASCADE'), primary_key=True),
    db.Column('subject_id', db.Integer, db.ForeignKey('subjects.subject_id', ondelete='CASCADE'), primary_key=True)
)

class_subjects_req = db.Table('class_subjects_req',
    db.Column('class_id', db.Integer, db.ForeignKey('classes.class_id', ondelete='CASCADE'), primary_key=True),
    db.Column('subject_id', db.Integer, db.ForeignKey('subjects.subject_id', ondelete='CASCADE'), primary_key=True),
    # Note: If we need extra fields like 'hours_per_week', we should use a Model instead of a Table.
    # The original schema had hours_per_week. So we should probably make this a Model.
)

# Since ClassSubjects had 'hours_per_week', we define it as a Model.
class ClassSubject(db.Model):
    __tablename__ = 'class_subjects'
    class_subject_id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.class_id', ondelete='CASCADE'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.subject_id', ondelete='CASCADE'), nullable=False)
    hours_per_week = db.Column(db.Integer, default=1, nullable=False)
    
    # Relationships/Proxies if needed
    subject = db.relationship("Subject")

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

class Reminder(db.Model):
    __tablename__ = 'reminders'
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    reminder_datetime = db.Column(db.DateTime, nullable=False)

class Faculty(db.Model):
    __tablename__ = 'faculties'
    faculty_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    faculty_code = db.Column(db.String(50), unique=True, nullable=True)
    
    subjects = db.relationship('Subject', secondary=faculty_subjects, backref='faculties')

class Subject(db.Model):
    __tablename__ = 'subjects'
    subject_id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), nullable=False, unique=True)
    name = db.Column(db.String(255), nullable=False)
    is_lab = db.Column(db.Boolean, default=False, nullable=False)

class Branch(db.Model):
    __tablename__ = 'branches'
    branch_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    code = db.Column(db.String(20), unique=True, nullable=True)

class Section(db.Model):
    __tablename__ = 'sections'
    section_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(10), nullable=False, unique=True)

class Class(db.Model):
    __tablename__ = 'classes'
    class_id = db.Column(db.Integer, primary_key=True)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.branch_id', ondelete='CASCADE'), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('sections.section_id', ondelete='CASCADE'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    class_name = db.Column(db.String(100), unique=True, nullable=True)

    branch = db.relationship('Branch', backref='classes')
    section = db.relationship('Section', backref='classes')
    requirements = db.relationship('ClassSubject', backref='class_obj', cascade="all, delete-orphan")

class Location(db.Model):
    __tablename__ = 'locations'
    location_id = db.Column(db.Integer, primary_key=True)
    room_no = db.Column(db.String(50), nullable=False)
    building = db.Column(db.String(100), nullable=True)
    is_lab = db.Column(db.Boolean, default=False, nullable=False)

class TimeSlot(db.Model):
    __tablename__ = 'timeslots'
    slot_id = db.Column(db.Integer, primary_key=True)
    day_of_week = db.Column(db.String(20), nullable=False) # Enum validation handled in app logic or DB constraints
    period_number = db.Column(db.Integer, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    applicable_year_group = db.Column(db.String(10), nullable=False) # '1', '2-3+', 'ALL'

class TimetableEntry(db.Model):
    __tablename__ = 'timetable_entries'
    entry_id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.class_id', ondelete='CASCADE'), nullable=False)
    slot_id = db.Column(db.Integer, db.ForeignKey('timeslots.slot_id', ondelete='CASCADE'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.subject_id', ondelete='CASCADE'), nullable=False)
    faculty_id = db.Column(db.Integer, db.ForeignKey('faculties.faculty_id', ondelete='CASCADE'), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.location_id', ondelete='CASCADE'), nullable=False)
    lab_batch_info = db.Column(db.String(100), nullable=True)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    class_obj = db.relationship('Class')
    slot = db.relationship('TimeSlot')
    subject = db.relationship('Subject')
    faculty = db.relationship('Faculty')
    location = db.relationship('Location')
