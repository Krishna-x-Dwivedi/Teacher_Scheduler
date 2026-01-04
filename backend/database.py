
import os
import mysql.connector
from mysql.connector import Error
from flask import g
from dotenv import load_dotenv
import datetime

load_dotenv()

MYSQL_CONFIG = {
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'timetable_db'),
    'raise_on_warnings': True
}

def get_db():
    """Opens a new database connection if there is none yet for the current request context."""
    if 'db' not in g:
        try:
            g.db = mysql.connector.connect(**MYSQL_CONFIG)
        except Error as e:
            print(f"Error connecting to MySQL Database: {e}")
            raise e
    return g.db

def close_db(error=None):
    """Closes the database connection at the end of the request."""
    db = g.pop('db', None)
    if db is not None and db.is_connected():
        db.close()

def time_converter(o):
    """Helper to convert time/timedelta objects to string for JSON serialization."""
    if isinstance(o, datetime.timedelta):
        total_seconds = int(o.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02}:{minutes:02}:{seconds:02}"
    if isinstance(o, datetime.time):
        return o.strftime("%H:%M:%S")
    return str(o)

def init_db():
    """Initializes the database by creating tables if they don't exist (MySQL version)."""
    try:
        # Connect using config
        db = get_db()
        cursor = db.cursor()
        print("Initializing MySQL database tables...")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id INT AUTO_INCREMENT PRIMARY KEY,
                text TEXT NOT NULL,
                reminder_datetime DATETIME NOT NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Faculties (
                faculty_id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                faculty_code VARCHAR(50) UNIQUE NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Subjects (
                subject_id INT AUTO_INCREMENT PRIMARY KEY,
                code VARCHAR(50) NOT NULL UNIQUE,
                name VARCHAR(255) NOT NULL,
                is_lab BOOLEAN NOT NULL DEFAULT FALSE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

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

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Branches (
                branch_id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL UNIQUE,
                code VARCHAR(20) UNIQUE NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Sections (
                section_id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(10) NOT NULL UNIQUE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Classes (
                class_id INT AUTO_INCREMENT PRIMARY KEY,
                branch_id INT NOT NULL,
                section_id INT NOT NULL,
                year INT NOT NULL,
                class_name VARCHAR(100) UNIQUE NULL,
                FOREIGN KEY (branch_id) REFERENCES Branches(branch_id) ON DELETE CASCADE,
                FOREIGN KEY (section_id) REFERENCES Sections(section_id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        cursor.execute("""
             CREATE TABLE IF NOT EXISTS ClassSubjects (
                class_subject_id INT AUTO_INCREMENT PRIMARY KEY,
                class_id INT NOT NULL,
                subject_id INT NOT NULL,
                hours_per_week INT NOT NULL DEFAULT 1,
                FOREIGN KEY (class_id) REFERENCES Classes(class_id) ON DELETE CASCADE,
                FOREIGN KEY (subject_id) REFERENCES Subjects(subject_id) ON DELETE CASCADE,
                UNIQUE KEY unique_class_subject (class_id, subject_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Locations (
                location_id INT AUTO_INCREMENT PRIMARY KEY,
                room_no VARCHAR(50) NOT NULL,
                building VARCHAR(100) NULL,
                is_lab BOOLEAN NOT NULL DEFAULT FALSE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

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

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS TimetableEntries (
                entry_id INT AUTO_INCREMENT PRIMARY KEY,
                class_id INT NOT NULL,
                slot_id INT NOT NULL,
                subject_id INT NOT NULL,
                faculty_id INT NOT NULL,
                location_id INT NOT NULL,
                lab_batch_info VARCHAR(100) NULL,
                generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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

        db.commit()
        print("Database tables checked/created successfully.")

    except Error as e:
        print(f"Error during database initialization: {e}")
        if 'db' in g and g.db and g.db.is_connected():
            g.db.rollback()
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
