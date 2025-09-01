# Point of Interest (PoI) Import System

A Django application for importing and managing Point of Interest data from CSV, JSON, and XML files. This system allows you to import PoI data via command-line and browse the information through the Django Admin Panel.

## Features

- **Multi-format Import**: Supports CSV, JSON, and XML file formats
- **Remote URL Support**: Import data directly from HTTP/HTTPS URLs
- **Command-line Import**: Easy-to-use management command for importing files
- **Django Admin Interface**: Browse and search PoI data with filtering capabilities
- **Search Functionality**: Search by internal ID, external ID, name, category, and description
- **Category Filtering**: Filter PoIs by category
- **Average Rating Calculation**: Automatically calculates and displays average ratings
- **Duplicate Handling**: Configurable duplicate handling (skip or update existing records)
- **Flexible XML Parsing**: Supports both standard XML and SearchSmartly DATA_RECORD format

## Requirements

- Python 3.10 or above
- Django 5.2.5 or above
- requests 2.31.0 or above (for remote URL imports)

## Installation

1. **Clone the repository**:

   ```bash
   git clone <repository-url>
   cd TestProject
   ```

2. **Create a virtual environment** (recommended):

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Run migrations**:

   ```bash
   python manage.py migrate
   ```

5. **Create a superuser** (for admin access):

   ```bash
   python manage.py createsuperuser
   ```

6. **Run the development server**:
   ```bash
   python manage.py runserver
   ```

## Usage

### Importing Data

Since `pois.csv` is too large to include in the repository, please download it from the remote URL before importing:

```bash
# Download pois.csv from the remote source

# Copy the pois.csv file to the current folder

# Import the downloaded file
python manage.py import_poi pois.csv
```

You can also import other formats and sources as shown below:

```bash
python manage.py import_poi https://searchsmartly-staging-assets.s3.eu-west-1.amazonaws.com/pois.xml
python manage.py import_poi https://searchsmartly-staging-assets.s3.eu-west-1.amazonaws.com/pois.json
```

# Mix local files and remote URLs

python manage.py import_poi local_file.csv https://remote.com/data.json

# Update existing records instead of skipping them

python manage.py import_poi file.csv --update

````

### File Format Specifications

#### CSV Format

```csv
poi_id,poi_name,poi_latitude,poi_longitude,poi_category,poi_ratings
POI001,Central Park,40.7829,-73.9654,Park,"4.5,4.2,4.8,4.1,4.6"
````

#### JSON Format

```json
[
  {
    "id": "POI001",
    "name": "Central Park",
    "coordinates": {
      "latitude": 40.7829,
      "longitude": -73.9654
    },
    "category": "Park",
    "ratings": [4.5, 4.2, 4.8, 4.1, 4.6],
    "description": "Famous urban park in Manhattan"
  }
]
```

#### XML Format

```xml
<?xml version="1.0" encoding="UTF-8"?>
<pois>
  <poi>
    <pid>POI001</pid>
    <pname>Central Park</pname>
    <platitude>40.7829</platitude>
    <plongitude>-73.9654</plongitude>
    <pcategory>Park</pcategory>
    <pratings>4.5,4.2,4.8,4.1,4.6</pratings>
  </poi>
</pois>
```

### Admin Interface

1. Start the development server: `python manage.py runserver`
2. Navigate to `http://127.0.0.1:8000/admin/`
3. Log in with your superuser credentials
4. Click on "Points of Interest" to view and manage the data

### Sample Data

The project includes sample data files for testing:

- `sample_data.csv` - 5 sample PoIs in CSV format
- `sample_data.json` - 3 sample PoIs in JSON format
- `sample_data.xml` - 3 sample PoIs in XML format

To import the sample data:

```bash
python manage.py import_poi sample_data.csv sample_data.json sample_data.xml
```

### Real-world Data Sources

You can import data from real-world sources:

```bash
# Import from SearchSmartly staging assets
python manage.py import_poi https://searchsmartly-staging-assets.s3.eu-west-1.amazonaws.com/pois.xml
python manage.py import_poi https://searchsmartly-staging-assets.s3.eu-west-1.amazonaws.com/pois.json

# Import from local large CSV file
python manage.py import_poi pois.csv
```

### Database Recreation

If you encounter database issues, you can recreate the database:

```bash
# Remove the database file (if using SQLite)
rm db.sqlite3

# Recreate the database
python manage.py migrate

# Create a new superuser
python manage.py createsuperuser

# Re-import your data
python manage.py import_poi your_data_files
```
