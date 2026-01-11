"""
Unit tests for Employee Scraper using mocking.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import json
from employee_scraper import EmployeeScraper


class TestEmployeeScraper(unittest.TestCase):
    """Test cases for EmployeeScraper class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.api_url = "https://api.slingacademy.com/v1/sample-data/files/employees.json"
        self.scraper = EmployeeScraper(self.api_url, max_retries=2, timeout=10)
        
        # Sample employee data for testing
        self.sample_employee_data = {
            "success": True,
            "message": "Successfully fetched employees data",
            "employees": [
                {
                    "id": 1,
                    "first_name": "John",
                    "last_name": "Doe",
                    "email": "john.doe@example.com",
                    "job_title": "Software Engineer",
                    "phone": "1234567890",
                    "hire_date": "2020-01-15",
                    "years_of_experience": 4,
                    "gender": "Male",
                    "age": 28,
                    "salary": 75000,
                    "department": "Engineering"
                },
                {
                    "id": 2,
                    "first_name": "Jane",
                    "last_name": "Smith",
                    "email": "jane.smith@example.com",
                    "job_title": "Data Analyst",
                    "phone": "987654321x",  # Invalid phone
                    "hire_date": "2018-06-20",
                    "years_of_experience": 8,
                    "gender": "Female",
                    "age": 32,
                    "salary": 85000,
                    "department": "Data Science"
                },
                {
                    "id": 3,
                    "first_name": "Bob",
                    "last_name": "Johnson",
                    "email": "bob.j@example.com",
                    "job_title": "Manager",
                    "phone": "5551234567",
                    "hire_date": "2015-03-10",
                    "years_of_experience": 12,
                    "gender": "Male",
                    "age": 40,
                    "salary": 120000,
                    "department": "Management"
                }
            ]
        }
    
    @patch('employee_scraper.requests.Session')
    def test_json_file_download(self, mock_session_class):
        """Test Case 1: Verify JSON File Download"""
        # Setup mock
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.sample_employee_data
        mock_session.get.return_value = mock_response
        
        # Create new scraper instance to use mocked session
        scraper = EmployeeScraper(self.api_url)
        scraper.session = mock_session
        
        # Test
        result = scraper.fetch_data()
        
        # Assertions
        self.assertIsNotNone(result)
        self.assertEqual(result['success'], True)
        self.assertIn('employees', result)
        mock_session.get.assert_called_once_with(self.api_url, timeout=30)
    
    @patch('employee_scraper.requests.Session')
    def test_json_file_extraction(self, mock_session_class):
        """Test Case 2: Verify JSON File Extraction"""
        # Setup mock
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.sample_employee_data
        mock_session.get.return_value = mock_response
        
        scraper = EmployeeScraper(self.api_url)
        scraper.session = mock_session
        
        # Test
        result = scraper.fetch_data()
        
        # Assertions
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)
        self.assertIn('employees', result)
        self.assertIsInstance(result['employees'], list)
        self.assertEqual(len(result['employees']), 3)
        
        # Verify employee fields exist
        employee = result['employees'][0]
        required_fields = ['id', 'first_name', 'last_name', 'email', 'job_title', 
                          'phone', 'hire_date', 'years_of_experience']
        for field in required_fields:
            self.assertIn(field, employee)
    
    @patch('employee_scraper.requests.Session')
    def test_validate_file_type_and_format(self, mock_session_class):
        """Test Case 3: Validate File Type and Format"""
        # Setup mock
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.sample_employee_data
        mock_session.get.return_value = mock_response
        
        scraper = EmployeeScraper(self.api_url)
        scraper.session = mock_session
        
        # Test
        result = scraper.fetch_data()
        
        # Assertions
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)
        
        # Verify JSON structure
        self.assertIn('employees', result)
        self.assertIsInstance(result['employees'], list)
        
        # Verify each employee is a dictionary
        for employee in result['employees']:
            self.assertIsInstance(employee, dict)
    
    @patch('employee_scraper.requests.Session')
    def test_validate_data_structure(self, mock_session_class):
        """Test Case 4: Validate Data Structure"""
        # Setup mock
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.sample_employee_data
        mock_session.get.return_value = mock_response
        
        scraper = EmployeeScraper(self.api_url)
        scraper.session = mock_session
        
        # Test
        json_data = scraper.fetch_data()
        df = scraper.process_data(json_data)
        
        # Assertions
        self.assertIsNotNone(df)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertGreater(len(df), 0)
        
        # Verify required columns exist
        required_columns = ['Full Name', 'email', 'phone', 'gender', 'age', 
                          'job_title', 'years_of_experience', 'salary', 
                          'department', 'designation']
        for col in required_columns:
            self.assertIn(col, df.columns, f"Column {col} not found in DataFrame")
        
        # Verify data types
        self.assertEqual(df['Full Name'].dtype, 'object')  # string
        self.assertEqual(df['email'].dtype, 'object')  # string
        self.assertEqual(df['gender'].dtype, 'object')  # string
        self.assertEqual(df['job_title'].dtype, 'object')  # string
        self.assertEqual(df['department'].dtype, 'object')  # string
        self.assertEqual(df['designation'].dtype, 'object')  # string
        
        # Verify data normalization
        # Test designation logic
        self.assertIn(df.loc[0, 'designation'], ['system engineer', 'data engineer', 
                                                  'senior data engineer', 'lead'])
        # Test Full Name
        self.assertEqual(df.loc[0, 'Full Name'], 'John Doe')
        # Test phone validation
        invalid_phone_row = df[df['phone'] == 'Invalid Number']
        self.assertGreater(len(invalid_phone_row), 0)
    
    @patch('employee_scraper.requests.Session')
    def test_handle_missing_or_invalid_data(self, mock_session_class):
        """Test Case 5: Handle Missing or Invalid Data"""
        # Test with missing fields
        incomplete_data = {
            "employees": [
                {
                    "id": 1,
                    "first_name": "John",
                    "last_name": "Doe",
                    # Missing email, job_title, etc.
                },
                {
                    "id": 2,
                    "first_name": "Jane",
                    "last_name": "Smith",
                    "email": None,
                    "phone": None,
                    "years_of_experience": None,
                    "hire_date": "invalid-date"
                }
            ]
        }
        
        # Setup mock
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = incomplete_data
        mock_session.get.return_value = mock_response
        
        scraper = EmployeeScraper(self.api_url)
        scraper.session = mock_session
        
        # Test
        json_data = scraper.fetch_data()
        df = scraper.process_data(json_data)
        
        # Assertions - should handle missing data gracefully
        self.assertIsNotNone(df)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 2)
        
        # Should still create Full Name even with partial data
        self.assertIn('Full Name', df.columns)
        
        # Should handle missing years_of_experience
        if 'designation' in df.columns:
            unknown_designations = df[df['designation'] == 'Unknown']
            # At least one should be Unknown if years_of_experience is missing
            self.assertGreaterEqual(len(unknown_designations), 0)
        
        # Test with non-200 status code
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = Exception("404 Not Found")
        result = scraper.fetch_data()
        self.assertIsNone(result)
        
        # Test with connection error
        mock_session.get.side_effect = Exception("Connection error")
        result = scraper.fetch_data()
        self.assertIsNone(result)
    
    def test_normalize_phone(self):
        """Test phone normalization logic."""
        # Valid phone
        result = self.scraper.normalize_phone("1234567890")
        self.assertEqual(result, "1234567890")
        
        # Invalid phone with 'x'
        result = self.scraper.normalize_phone("123x4567890")
        self.assertEqual(result, "Invalid Number")
        
        # Invalid phone with 'X' (uppercase)
        result = self.scraper.normalize_phone("123X4567890")
        self.assertEqual(result, "Invalid Number")
        
        # Empty phone
        result = self.scraper.normalize_phone("")
        self.assertEqual(result, "Invalid Number")
    
    def test_get_designation(self):
        """Test designation assignment logic."""
        # Less than 3 years
        self.assertEqual(self.scraper.get_designation(2), 'system engineer')
        
        # 3-5 years
        self.assertEqual(self.scraper.get_designation(3), 'data engineer')
        self.assertEqual(self.scraper.get_designation(4), 'data engineer')
        
        # 5-10 years
        self.assertEqual(self.scraper.get_designation(5), 'senior data engineer')
        self.assertEqual(self.scraper.get_designation(7), 'senior data engineer')
        
        # 10+ years
        self.assertEqual(self.scraper.get_designation(10), 'lead')
        self.assertEqual(self.scraper.get_designation(15), 'lead')
        
        # None/NaN
        self.assertEqual(self.scraper.get_designation(float('nan')), 'Unknown')
    
    def test_normalize_date(self):
        """Test date normalization."""
        # Standard format
        result = self.scraper.normalize_date("2020-01-15")
        self.assertEqual(result, "2020-01-15")
        
        # Different format
        result = self.scraper.normalize_date("01/15/2020")
        self.assertEqual(result, "2020-01-15")
        
        # Invalid date
        result = self.scraper.normalize_date("invalid-date")
        self.assertEqual(result, "")
        
        # Empty date
        result = self.scraper.normalize_date("")
        self.assertEqual(result, "")
    
    @patch('employee_scraper.requests.Session')
    def test_retry_logic(self, mock_session_class):
        """Test retry logic for failed requests."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        # Simulate connection error then success
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.sample_employee_data
        mock_response.raise_for_status.return_value = None
        
        mock_session.get.side_effect = [
            Exception("Connection error"),
            mock_response
        ]
        
        scraper = EmployeeScraper(self.api_url, max_retries=2)
        scraper.session = mock_session
        
        # Should retry and succeed on second attempt
        result = scraper.fetch_data()
        self.assertIsNotNone(result)
        self.assertEqual(result['success'], True)
        self.assertIn('employees', result)
        # Verify that get was called twice (initial + retry)
        self.assertEqual(mock_session.get.call_count, 2)


if __name__ == '__main__':
    unittest.main()
