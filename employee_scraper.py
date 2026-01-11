"""
Employee Data Scraper
It Fetches employee data from API and normalizes it according to business rules.
"""

import requests
import pandas as pd
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EmployeeScraper:
    """Scraper class for fetching and processing employee data from API."""
    
    def __init__(self, api_url: str, max_retries: int = 3, timeout: int = 30):
        """
        Initialize the scraper.
        
        Args:
            api_url: URL of the API endpoint
            max_retries: Maximum number of retry attempts for failed requests
            timeout: Request timeout in seconds
        """
        self.api_url = api_url
        self.max_retries = max_retries
        self.timeout = timeout
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """Create a requests session with retry strategy."""
        session = requests.Session()
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session
    
    def fetch_data(self) -> Optional[Dict]:
        """
        Fetch employee data from the API endpoint.
        
        Returns:
            Dictionary containing the JSON response or None if failed
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            response = None
            try:
                if attempt > 0:
                    logger.info(f"Retrying request (attempt {attempt + 1}/{self.max_retries + 1})")
                
                logger.info(f"Fetching data from {self.api_url}")
                response = self.session.get(self.api_url, timeout=self.timeout)
                
                # Check status code before raise_for_status to avoid retrying on HTTP errors
                if response.status_code >= 400:
                    logger.error(f"API returned error status code: {response.status_code}")
                    response.raise_for_status()  # This will raise HTTPError, but we've already logged
                    return None
                
                response.raise_for_status()
                
                if response.status_code == 200:
                    logger.info("Successfully retrieved data from API")
                    return response.json()
                else:
                    logger.error(f"API returned non-200 status code: {response.status_code}")
                    return None
                    
            except requests.exceptions.Timeout as e:
                last_exception = e
                logger.error(f"Request timeout after {self.timeout} seconds (attempt {attempt + 1}/{self.max_retries + 1})")
                if attempt == self.max_retries:
                    return None
            except requests.exceptions.ConnectionError as e:
                last_exception = e
                logger.error(f"Connection error: {str(e)} (attempt {attempt + 1}/{self.max_retries + 1})")
                if attempt == self.max_retries:
                    return None
            except requests.exceptions.HTTPError as e:
                logger.error(f"HTTP error occurred: {str(e)}")
                return None  # Don't retry HTTP errors (4xx, 5xx) as they're usually permanent
            except requests.exceptions.RequestException as e:
                last_exception = e
                logger.error(f"Request exception occurred: {str(e)} (attempt {attempt + 1}/{self.max_retries + 1})")
                if attempt == self.max_retries:
                    return None
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {str(e)}")
                return None  # Don't retry JSON decode errors
            except Exception as e:
                # Catch any other exceptions (including generic ones from mocks)
                # Check if this is an HTTP error by checking the response status code
                # If raise_for_status() raised a generic Exception for a 4xx/5xx, don't retry
                if response is not None and hasattr(response, 'status_code'):
                    status_code = response.status_code
                    if 400 <= status_code < 600:
                        logger.error(f"HTTP error {status_code} occurred: {str(e)}")
                        return None  # Don't retry HTTP errors
                
                last_exception = e
                logger.error(f"Unexpected error occurred: {str(e)} (attempt {attempt + 1}/{self.max_retries + 1})")
                if attempt == self.max_retries:
                    return None
        
        return None
    
    def normalize_phone(self, phone: str) -> str:
        """
        Normalize phone number. Mark as 'Invalid Number' if contains 'x'.
        
        Args:
            phone: Phone number string
            
        Returns:
            Normalized phone number or 'Invalid Number'
        """
        if pd.isna(phone) or phone == '':
            return 'Invalid Number'
        
        phone_str = str(phone).lower()
        if 'x' in phone_str:
            return 'Invalid Number'
        # Remove non-digit characters except '+' for phone parsing
        return str(phone)
    
    def get_designation(self, years_of_experience: float) -> str:
        """
        Get designation based on years of experience.
        
        Args:
            years_of_experience: Years of experience
            
        Returns:
            Designation string
        """
        if pd.isna(years_of_experience):
            return 'Unknown'
        
        years = float(years_of_experience)
        if years < 3:
            return 'system engineer'
        elif 3 <= years < 5:
            return 'data engineer'
        elif 5 <= years < 10:
            return 'senior data engineer'
        else:  # years >= 10
            return 'lead'
    
    def convert_currency(self, amount: float, from_currency: str = 'USD', 
                        to_currency: str = 'USD') -> float:
        """
        Convert currency using exchange rate API (optional).
        Uses exchangerate-api.com free API for currency conversion.
        
        Args:
            amount: Amount to convert
            from_currency: Source currency code (e.g., 'USD', 'EUR')
            to_currency: Target currency code (e.g., 'USD', 'EUR')
            
        Returns:
            Converted amount
        """
        if from_currency == to_currency:
            return amount
        
        try:
            # Using exchangerate-api.com free API
            exchange_url = f"https://api.exchangerate-api.com/v4/latest/{from_currency}"
            response = self.session.get(exchange_url, timeout=self.timeout)
            
            if response.status_code == 200:
                exchange_data = response.json()
                if 'rates' in exchange_data and to_currency in exchange_data['rates']:
                    exchange_rate = exchange_data['rates'][to_currency]
                    converted_amount = amount * exchange_rate
                    logger.info(f"Converted {amount} {from_currency} to {converted_amount:.2f} {to_currency} "
                              f"(rate: {exchange_rate})")
                    return converted_amount
                else:
                    logger.warning(f"Exchange rate for {to_currency} not found. Returning original amount.")
                    return amount
            else:
                logger.warning(f"Exchange rate API returned status {response.status_code}. Returning original amount.")
                return amount
        except Exception as e:
            logger.warning(f"Currency conversion failed: {str(e)}. Returning original amount.")
            return amount
    
    def normalize_date(self, date_value: str) -> str:
        """
        Normalize date to YYYY-MM-DD format.
        
        Args:
            date_value: Date string in various formats
            
        Returns:
            Date string in YYYY-MM-DD format
        """
        if pd.isna(date_value) or date_value == '':
            return ''
        
        try:
            # Try parsing various date formats
            date_obj = pd.to_datetime(date_value, errors='coerce')
            if pd.isna(date_obj):
                return ''
            return date_obj.strftime('%Y-%m-%d')
        except Exception as e:
            logger.warning(f"Date parsing failed for {date_value}: {str(e)}")
            return ''
    
    def process_data(self, json_data: Dict) -> pd.DataFrame:
        """
        Process and normalize employee data.
        
        Args:
            json_data: Raw JSON data from API
            
        Returns:
            Normalized pandas DataFrame
        """
        try:
            # Extract employees array from JSON response
            if 'employees' in json_data:
                employees = json_data['employees']
            elif isinstance(json_data, dict) and 'data' in json_data:
                employees = json_data['data']
            elif isinstance(json_data, list):
                employees = json_data
            else:
                # Try to find any list/array in the response
                employees = [json_data] if isinstance(json_data, dict) else []
            
            if not employees:
                logger.warning("No employee data found in JSON response")
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame(employees)
            logger.info(f"Loaded {len(df)} employee records")
            
            # Normalize column names (handle various naming conventions)
            column_mapping = {
                'id': 'employee_id',
                'employee_id': 'employee_id',
                'first_name': 'first_name',
                'firstname': 'first_name',
                'firstName': 'first_name',
                'last_name': 'last_name',
                'lastname': 'last_name',
                'lastName': 'last_name',
                'email': 'email',
                'job_title': 'job_title',
                'jobTitle': 'job_title',
                'phone': 'phone',
                'phone_number': 'phone',
                'phoneNumber': 'phone',
                'hire_date': 'hire_date',
                'hireDate': 'hire_date',
                'years_of_experience': 'years_of_experience',
                'yearsOfExperience': 'years_of_experience',
                'gender': 'gender',
                'age': 'age',
                'salary': 'salary',
                'department': 'department'
            }
            
            df = df.rename(columns=column_mapping)
            
            # Create Full Name column
            if 'first_name' in df.columns and 'last_name' in df.columns:
                df['Full Name'] = df['first_name'].astype(str) + ' ' + df['last_name'].astype(str)
            else:
                logger.warning("First name or last name columns not found")
                df['Full Name'] = ''
            
            # Create designation column
            if 'years_of_experience' in df.columns:
                df['designation'] = df['years_of_experience'].apply(self.get_designation)
            else:
                logger.warning("years_of_experience column not found")
                df['designation'] = 'Unknown'
            
            # Normalize phone numbers
            if 'phone' in df.columns:
                df['phone'] = df['phone'].apply(self.normalize_phone)
            else:
                logger.warning("phone column not found")
                df['phone'] = 'Invalid Number'
            
            # Normalize hire date
            if 'hire_date' in df.columns:
                df['hire_date'] = df['hire_date'].apply(self.normalize_date)
            elif 'Hire Date' in df.columns:
                df['hire_date'] = df['Hire Date'].apply(self.normalize_date)
            
            # Ensure correct data types
            type_mapping = {
                'Full Name': 'string',
                'email': 'string',
                'phone': 'string',  # Keep as string to handle 'Invalid Number'
                'gender': 'string',
                'age': 'Int64',  # Nullable integer
                'job_title': 'string',
                'years_of_experience': 'Int64',
                'salary': 'Int64',
                'department': 'string',
                'designation': 'string'
            }
            
            for col, dtype in type_mapping.items():
                if col in df.columns:
                    if dtype == 'string':
                        df[col] = df[col].astype(str)
                    elif dtype == 'Int64':
                        df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')
            
            # Handle phone column: convert to int where possible, keep 'Invalid Number' as string
            if 'phone' in df.columns:
                def convert_phone_to_int(phone_val):
                    if phone_val == 'Invalid Number' or pd.isna(phone_val):
                        return 'Invalid Number'
                    # Remove non-digit characters
                    phone_clean = ''.join(filter(str.isdigit, str(phone_val)))
                    try:
                        return int(phone_clean) if phone_clean else 'Invalid Number'
                    except:
                        return 'Invalid Number'
                
                df['phone'] = df['phone'].apply(convert_phone_to_int)
            
            # Optional: Currency conversion if salary is in different currency
            # Uncomment and modify the currency codes as needed
            # if 'salary' in df.columns and 'currency' in df.columns:
            #     df['salary'] = df.apply(
            #         lambda row: self.convert_currency(row['salary'], row['currency'], 'USD'),
            #         axis=1
            #     )
            
            # Select and reorder columns for final output
            output_columns = ['employee_id', 'Full Name', 'email', 'phone', 'gender', 
                            'age', 'job_title', 'years_of_experience', 'salary', 
                            'department', 'designation', 'hire_date']
            
            # Keep only columns that exist
            final_columns = [col for col in output_columns if col in df.columns]
            df = df[final_columns]
            
            logger.info(f"Successfully processed {len(df)} employee records")
            return df
            
        except Exception as e:
            logger.error(f"Error processing data: {str(e)}")
            raise
    
    def scrape(self) -> Optional[pd.DataFrame]:
        """
        Main method to scrape and process employee data.
        
        Returns:
            Processed DataFrame or None if failed
        """
        json_data = self.fetch_data()
        if json_data is None:
            return None
        
        return self.process_data(json_data)
    
    def save_to_csv(self, df: pd.DataFrame, filename: str = 'employees.csv'):
        """
        Save DataFrame to CSV file.
        
        Args:
            df: DataFrame to save
            filename: Output filename
        """
        try:
            df.to_csv(filename, index=False)
            logger.info(f"Data saved to {filename}")
        except Exception as e:
            logger.error(f"Error saving to CSV: {str(e)}")
            raise
    
    def save_to_json(self, df: pd.DataFrame, filename: str = 'employees.json'):
        """
        Save DataFrame to JSON file.
        
        Args:
            df: DataFrame to save
            filename: Output filename
        """
        try:
            df.to_json(filename, orient='records', indent=2, date_format='iso')
            logger.info(f"Data saved to {filename}")
        except Exception as e:
            logger.error(f"Error saving to JSON: {str(e)}")
            raise


def main():
    """Main function to run the scraper."""
    api_url = "https://api.slingacademy.com/v1/sample-data/files/employees.json"
    scraper = EmployeeScraper(api_url)
    
    df = scraper.scrape()
    
    if df is not None and not df.empty:
        print(f"\nSuccessfully scraped {len(df)} employee records")
        print("\nFirst few records:")
        print(df.head())
        
        # Save to files
        scraper.save_to_csv(df)
        scraper.save_to_json(df)
    else:
        print("Failed to scrape employee data")


if __name__ == "__main__":
    main()
