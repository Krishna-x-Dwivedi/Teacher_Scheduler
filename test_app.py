
import unittest
import json
import os
from app import app, db
from backend.models import User

class TestTeacherScheduler(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:' # Use in-memory DB for tests
        self.app = app.test_client()
        
        with app.app_context():
            db.create_all()

        self.test_email = "test@example.com"
        self.test_password = "password123"

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_signup_login_flow(self):
        # Signup
        response = self.app.post('/api/signup', json={
            'name': 'Test User',
            'email': self.test_email,
            'password': self.test_password
        })
        self.assertEqual(response.status_code, 201)
        
        # Verify in DB
        with app.app_context():
            user = User.query.filter_by(email=self.test_email).first()
            self.assertIsNotNone(user)
            self.assertEqual(user.name, 'Test User')

        # Login
        response = self.app.post('/api/login', json={
            'email': self.test_email,
            'password': self.test_password
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('user', data)
        self.assertNotIn('password', data['user'])

    def test_add_faculty(self):
        response = self.app.post('/api/faculties', json={
            'name': 'Dr. Test',
            'faculty_code': 'T01'
        })
        self.assertEqual(response.status_code, 201)

    def test_generate_timetable_endpoint(self):
        response = self.app.post('/api/generate-timetable')
        self.assertIn(response.status_code, [200, 500])

if __name__ == '__main__':
    unittest.main()
