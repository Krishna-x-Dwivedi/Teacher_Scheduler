
from flask import Blueprint, request, jsonify
from backend.database import get_db
from mysql.connector import Error, IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/signup', methods=['POST'])
def signup():
    """Handles user registration."""
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')

    if not name or not email or not password:
        return jsonify({'error': 'Missing required fields'}), 400

    hashed_password = generate_password_hash(password)

    db = get_db()
    cursor = db.cursor()
    try:
        query = "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)"
        cursor.execute(query, (name, email, hashed_password))
        db.commit()
        user_id = cursor.lastrowid
        return jsonify({'message': 'User created successfully', 'user_id': user_id}), 201
    except IntegrityError:
        db.rollback()
        return jsonify({'error': 'Email already exists'}), 409
    except Error as e:
        db.rollback()
        print(f"Error during signup: {e}")
        return jsonify({'error': 'An internal server error occurred'}), 500
    finally:
        cursor.close()

@auth_bp.route('/login', methods=['POST'])
def login():
    """Handles user login."""
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400

    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        query = "SELECT id, name, email, password FROM users WHERE email = %s"
        cursor.execute(query, (email,))
        user = cursor.fetchone()

        if user and check_password_hash(user['password'], password):
            # Remove password from response
            user.pop('password')
            return jsonify({'message': 'Login successful', 'user': user}), 200
        else:
            return jsonify({'error': 'Invalid email or password'}), 401
    except Error as e:
        print(f"Error during login: {e}")
        return jsonify({'error': 'An internal server error occurred'}), 500
    finally:
        cursor.close()
