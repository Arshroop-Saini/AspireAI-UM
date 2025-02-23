import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
from models.student_model import Student
from bson import ObjectId

class TestStudent(unittest.TestCase):
    def setUp(self):
        self.sample_college = {
            'name': 'Test University',
            'stats': {
                'satRange': '1200-1400',
                'gpaRange': '3.5-4.0',
                'totalCost': '$50,000',
                'scholarships': 'Available',
                'applicationDeadlines': 'January 1',
                'costCalculator': 'https://test.edu/calculator',
                'size': 'Medium',
                'location': 'Test City, State',
                'type': 'Private'
            }
        }
        self.auth0_id = 'google-oauth2|123456789'
        self.student_data = {
            '_id': ObjectId(),
            'auth0_id': self.auth0_id,
            'email': 'test@example.com',
            'name': 'Test Student',
            'target_colleges': [],
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }

    @patch('models.student_model.get_db')
    def test_add_target_college(self, mock_get_db):
        """Test adding a college to target_colleges"""
        # Mock database response
        mock_db = MagicMock()
        mock_db.students.update_one.return_value = MagicMock(
            modified_count=1
        )
        mock_get_db.return_value = mock_db

        # Create student instance
        student = Student(self.student_data)

        # Test adding college
        result = student.add_target_college(self.sample_college)
        self.assertTrue(result)
        mock_db.students.update_one.assert_called_once()

        # Verify college was added to target_colleges
        self.assertEqual(len(student.target_colleges), 1)
        self.assertEqual(student.target_colleges[0]['name'], self.sample_college['name'])

    @patch('models.student_model.get_db')
    def test_add_duplicate_target_college(self, mock_get_db):
        """Test adding a duplicate college to target_colleges"""
        # Mock database response
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        # Create student instance with existing college
        self.student_data['target_colleges'] = [self.sample_college]
        student = Student(self.student_data)

        # Test adding duplicate college
        result = student.add_target_college(self.sample_college)
        self.assertFalse(result)
        mock_db.students.update_one.assert_not_called()

    @patch('models.student_model.get_db')
    def test_remove_target_college(self, mock_get_db):
        """Test removing a college from target_colleges"""
        # Mock database response
        mock_db = MagicMock()
        mock_db.students.update_one.return_value = MagicMock(
            modified_count=1
        )
        mock_get_db.return_value = mock_db

        # Create student instance with existing college
        self.student_data['target_colleges'] = [self.sample_college]
        student = Student(self.student_data)

        # Test removing college
        result = student.remove_target_college(self.sample_college['name'])
        self.assertTrue(result)
        mock_db.students.update_one.assert_called_once()
        self.assertEqual(len(student.target_colleges), 0)

    @patch('models.student_model.get_db')
    def test_get_target_colleges(self, mock_get_db):
        """Test retrieving target_colleges"""
        # Mock database response
        mock_db = MagicMock()
        mock_db.students.find_one.return_value = self.student_data
        mock_get_db.return_value = mock_db

        # Test retrieval
        student = Student.get_by_auth0_id(self.auth0_id)
        self.assertIsNotNone(student)
        self.assertIsInstance(student.target_colleges, list)

    def test_validate_target_college(self):
        """Test target college data validation"""
        # Test with valid data
        student = Student(self.student_data)
        self.assertTrue(student.validate_target_college(self.sample_college))

        # Test with invalid data
        invalid_college = {
            'name': 'Test University',
            'stats': {
                'satRange': '1200-1400'  # Missing required fields
            }
        }
        self.assertFalse(student.validate_target_college(invalid_college))

if __name__ == '__main__':
    unittest.main() 