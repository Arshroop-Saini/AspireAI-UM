import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
import json
from app import create_app
from models.student_model import Student
from models.crew_suggestions_model import CrewSuggestions

class TestCollegeListGenerator(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()
        self.auth0_id = 'google-oauth2|123456789'
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
        self.mock_token = 'mock_token'
        self.headers = {
            'Authorization': f'Bearer {self.mock_token}',
            'Content-Type': 'application/json'
        }

    @patch('routes.college_list_generator_route.verify_google_token')
    @patch('routes.college_list_generator_route.check_subscription')
    @patch('routes.college_list_generator_route.generate_college_list')
    @patch('models.student_model.Student.get_by_auth0_id')
    @patch('models.crew_suggestions_model.CrewSuggestions.update_suggestions')
    def test_generate_list(self, mock_update_suggestions, mock_get_student, 
                          mock_generate_list, mock_check_sub, mock_verify_token):
        """Test generating college list"""
        # Mock token verification
        mock_verify_token.return_value = {'sub': self.auth0_id}
        mock_check_sub.return_value = True

        # Mock student retrieval
        mock_student = MagicMock()
        mock_student.email = 'test@example.com'
        mock_get_student.return_value = mock_student

        # Mock college list generation
        mock_generate_list.return_value = {
            'colleges': [self.sample_college],
            'message': None
        }

        # Mock suggestions update
        mock_update_suggestions.return_value = True

        # Test the endpoint
        response = self.client.post('/api/college-list', 
                                  headers=self.headers,
                                  json={'email': 'test@example.com'})
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('colleges', data)
        self.assertEqual(len(data['colleges']), 1)
        mock_update_suggestions.assert_called_once()

    @patch('routes.college_list_generator_route.verify_google_token')
    @patch('routes.college_list_generator_route.check_subscription')
    @patch('models.student_model.Student.get_by_auth0_id')
    @patch('models.crew_suggestions_model.CrewSuggestions.remove_college')
    @patch('models.student_model.Student.add_target_college')
    def test_add_to_target_colleges(self, mock_add_target, mock_remove_suggestions,
                                  mock_get_student, mock_check_sub, mock_verify_token):
        """Test adding college to target list"""
        # Mock token verification
        mock_verify_token.return_value = {'sub': self.auth0_id}
        mock_check_sub.return_value = True

        # Mock student retrieval
        mock_student = MagicMock()
        mock_student.email = 'test@example.com'
        mock_get_student.return_value = mock_student

        # Mock add and remove operations
        mock_add_target.return_value = True
        mock_remove_suggestions.return_value = True

        # Test the endpoint
        response = self.client.post('/api/college-list/add-target',
                                  headers=self.headers,
                                  json={'college': self.sample_college})
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        mock_add_target.assert_called_once()
        mock_remove_suggestions.assert_called_once()

    @patch('routes.college_list_generator_route.verify_google_token')
    def test_invalid_token(self, mock_verify_token):
        """Test request with invalid token"""
        mock_verify_token.side_effect = Exception('Invalid token')

        response = self.client.post('/api/college-list',
                                  headers=self.headers,
                                  json={'email': 'test@example.com'})
        
        self.assertEqual(response.status_code, 401)

    @patch('routes.college_list_generator_route.verify_google_token')
    @patch('routes.college_list_generator_route.check_subscription')
    def test_invalid_subscription(self, mock_check_sub, mock_verify_token):
        """Test request with invalid subscription"""
        mock_verify_token.return_value = {'sub': self.auth0_id}
        mock_check_sub.return_value = False

        response = self.client.post('/api/college-list',
                                  headers=self.headers,
                                  json={'email': 'test@example.com'})
        
        self.assertEqual(response.status_code, 403)

    def test_missing_token(self):
        """Test request without token"""
        headers = {'Content-Type': 'application/json'}
        response = self.client.post('/api/college-list',
                                  headers=headers,
                                  json={'email': 'test@example.com'})
        
        self.assertEqual(response.status_code, 401)

if __name__ == '__main__':
    unittest.main() 