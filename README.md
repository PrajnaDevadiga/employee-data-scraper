# Employee Data Scraper

A Python-based scraper for fetching and processing employee data from the Sling Academy API endpoint.

## Features

- **Data Retrieval**: Fetches employee data from the API with automatic retry logic
- **Error Handling**: Handles timeouts, connection errors, and HTTP errors gracefully
- **Data Normalization**: 
  - Creates "designation" column based on years of experience
  - Combines first and last names into "Full Name" column
  - Validates phone numbers (marks invalid if contains 'x')
  - Ensures correct data types for all columns
  - Normalizes dates to YYYY-MM-DD format
  - Optional currency conversion support
- **Test Coverage**: Comprehensive unit tests with mocking

## Installation

1. Install required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

Run the scraper directly:
```bash
python employee_scraper.py
```

This will:
- Fetch data from the API
- Process and normalize the data
- Save results to `employees.csv` and `employees.json`

### Programmatic Usage

```python
from employee_scraper import EmployeeScraper

# Initialize scraper
scraper = EmployeeScraper(
    api_url="https://api.slingacademy.com/v1/sample-data/files/employees.json",
    max_retries=3,
    timeout=30
)

# Fetch and process data
df = scraper.scrape()

if df is not None:
    # Save to files
    scraper.save_to_csv(df, 'output.csv')
    scraper.save_to_json(df, 'output.json')
    
    # Access the data
    print(df.head())
```

## Data Normalization Rules

### Designation Assignment
- **< 3 years**: system engineer
- **3-5 years**: data engineer
- **5-10 years**: senior data engineer
- **10+ years**: lead

### Phone Validation
- Phone numbers containing 'x' (case-insensitive) are marked as "Invalid Number"
- Valid phone numbers are converted to integers

### Data Types
- Full Name: string
- Email: string
- Phone: string (contains "Invalid Number" or integer values)
- Gender: string
- Age: int (nullable)
- Job Title: string
- Years of Experience: int (nullable)
- Salary: int (nullable)
- Department: string
- Designation: string
- Hire Date: string (YYYY-MM-DD format)

## Running Tests

Execute all unit tests:
```bash
python -m pytest test_employee_scraper.py -v
```

Or using unittest:
```bash
python test_employee_scraper.py
```

### Test Cases

1. **Test Case 1**: Verify JSON File Download
   - Tests successful API request
   - Validates response structure

2. **Test Case 2**: Verify JSON File Extraction
   - Tests JSON parsing
   - Validates employee data extraction

3. **Test Case 3**: Validate File Type and Format
   - Tests JSON format validation
   - Validates data structure

4. **Test Case 4**: Validate Data Structure
   - Tests data normalization
   - Validates column presence and data types
   - Tests designation, phone validation, and full name creation

5. **Test Case 5**: Handle Missing or Invalid Data
   - Tests handling of missing fields
   - Tests error handling for invalid data
   - Tests HTTP error handling

## Error Handling

The scraper includes robust error handling for:
- **HTTP Errors**: Logs and handles non-200 status codes
- **Timeouts**: Configurable timeout with logging
- **Connection Errors**: Automatic retry with exponential backoff
- **JSON Parsing Errors**: Handles malformed JSON responses
- **Missing Data**: Gracefully handles missing or null fields

## Logging

The scraper uses Python's logging module to track:
- API requests and responses
- Data processing steps
- Errors and warnings
- Success messages

Log level can be configured in the script (default: INFO).

## Output Files

- **employees.csv**: Processed data in CSV format
- **employees.json**: Processed data in JSON format (records orientation)

## Requirements

- Python 3.7+
- requests 2.31.0
- pandas 2.1.3
- urllib3 2.1.0

## License

This project is provided as-is for educational and development purposes.
