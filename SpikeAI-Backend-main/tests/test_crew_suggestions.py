import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
from models.crew_suggestions_model import CrewSuggestions
from bson import ObjectId

class TestCrewSuggestions(unittest.TestCase):
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

    def test_validate_college_data_valid(self):
        """Test college data validation with valid data"""
        self.assertTrue(CrewSuggestions.validate_college_data(self.sample_college))

    def test_validate_college_data_invalid(self):
        """Test college data validation with invalid data"""
        invalid_college = {
            'name': 'Test University',
            'stats': {
                'satRange': '1200-1400'  # Missing required fields
            }
        }
        self.assertFalse(CrewSuggestions.validate_college_data(invalid_college))

    @patch('models.crew_suggestions_model.get_db')
    def test_update_suggestions(self, mock_get_db):
        """Test updating college suggestions"""
        # Mock database response
        mock_db = MagicMock()
        mock_db.crewSuggestions.update_one.return_value = MagicMock(
            modified_count=1,
            upserted_id=None
        )
        mock_get_db.return_value = mock_db

        # Test update
        result = CrewSuggestions.update_suggestions(
            self.auth0_id,
            [self.sample_college]
        )
        self.assertTrue(result)
        mock_db.crewSuggestions.update_one.assert_called_once()

    @patch('models.crew_suggestions_model.get_db')
    def test_get_by_auth0_id(self, mock_get_db):
        """Test retrieving suggestions by auth0_id"""
        # Mock database response
        mock_db = MagicMock()
        mock_db.crewSuggestions.find_one.return_value = {
            '_id': ObjectId(),
            'auth0_id': self.auth0_id,
            'college_suggestions': [self.sample_college],
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        mock_get_db.return_value = mock_db

        # Test retrieval
        result = CrewSuggestions.get_by_auth0_id(self.auth0_id)
        self.assertIsNotNone(result)
        self.assertEqual(result['auth0_id'], self.auth0_id)
        mock_db.crewSuggestions.find_one.assert_called_once_with(
            {'auth0_id': self.auth0_id}
        )

    @patch('models.crew_suggestions_model.get_db')
    def test_remove_college(self, mock_get_db):
        """Test removing a college from suggestions"""
        # Mock database response
        mock_db = MagicMock()
        mock_db.crewSuggestions.update_one.return_value = MagicMock(
            modified_count=1
        )
        mock_get_db.return_value = mock_db

        # Test removal
        result = CrewSuggestions.remove_college(
            self.auth0_id,
            self.sample_college['name']
        )
        self.assertTrue(result)
        mock_db.crewSuggestions.update_one.assert_called_once()

    @patch('models.crew_suggestions_model.get_db')
    def test_retry_logic(self, mock_get_db):
        """Test retry logic on database operations"""
        # Mock database to fail twice then succeed
        mock_db = MagicMock()
        mock_db.crewSuggestions.find_one.side_effect = [
            Exception("Database error"),
            Exception("Database error"),
            {'auth0_id': self.auth0_id}
        ]
        mock_get_db.return_value = mock_db

        # Test that operation succeeds after retries
        result = CrewSuggestions.get_by_auth0_id(self.auth0_id)
        self.assertIsNotNone(result)
        self.assertEqual(mock_db.crewSuggestions.find_one.call_count, 3)

    def test_to_dict_conversion(self):
        """Test conversion of CrewSuggestions to dictionary"""
        suggestions = CrewSuggestions({
            '_id': ObjectId(),
            'auth0_id': self.auth0_id,
            'college_suggestions': [self.sample_college],
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        })

        result = suggestions.to_dict()
        self.assertIsInstance(result['_id'], str)
        self.assertIsInstance(result['created_at'], str)
        self.assertIsInstance(result['updated_at'], str)

if __name__ == '__main__':
    unittest.main() 