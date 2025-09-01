import csv
import json
import xml.etree.ElementTree as ET
import requests
from pathlib import Path
from decimal import Decimal
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from poi.models import PointOfInterest


class Command(BaseCommand):
    help = 'Import Point of Interest data from CSV, JSON, or XML files'

    def add_arguments(self, parser):
        parser.add_argument(
            'file_paths',
            nargs='+',
            type=str,
            help='Path(s) to the file(s) to import'
        )
        parser.add_argument(
            '--update',
            action='store_true',
            help='Update existing records instead of skipping them'
        )

    def handle(self, *args, **options):
        file_paths = options['file_paths']
        update_existing = options['update']
        
        total_imported = 0
        total_skipped = 0
        total_updated = 0
        
        for file_path in file_paths:
            try:
                imported, skipped, updated = self.import_file(str(file_path), update_existing)
                total_imported += imported
                total_skipped += skipped
                total_updated += updated
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Processed URL {file_path}: {imported} imported, {skipped} skipped, {updated} updated'
                    )
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error processing URL {file_path}: {str(e)}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nTotal: {total_imported} imported, {total_skipped} skipped, {total_updated} updated'
            )
        )

    def import_file(self, file_path, update_existing):
        """Import data from a single file or URL based on its extension."""
        # Check if it's a URL
        if str(file_path).startswith(('http://', 'https://')):
            return self.import_from_url(file_path, update_existing)
        
        # Handle local file
        # extension = file_path.suffix.lower()
        extension = Path(file_path).suffix.lower()
        
        if extension == '.csv':
            return self.import_csv(file_path, update_existing)
        elif extension == '.json':
            return self.import_json(file_path, update_existing)
        elif extension == '.xml':
            return self.import_xml(file_path, update_existing)
        else:
            raise CommandError(f'Unsupported file format: {extension}')

    def import_from_url(self, url, update_existing):
        """Import data from a remote URL."""
        try:
            self.stdout.write(f'Downloading data from: {url}')
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Determine file type from URL or content
            content_type = response.headers.get('content-type', '').lower()
            
            if 'csv' in content_type or url.lower().endswith('.csv'):
                return self.import_csv_from_content(response.text, update_existing, url)
            elif 'json' in content_type or url.lower().endswith('.json'):
                return self.import_json_from_content(response.text, update_existing, url)
            elif 'xml' in content_type or url.lower().endswith('.xml'):
                return self.import_xml_from_content(response.text, update_existing, url)
            else:
                raise CommandError(f'Could not determine file type for URL: {url}')
                    
        except requests.RequestException as e:
            raise CommandError(f'Failed to download from URL {url}: {str(e)}')
        except Exception as e:
            raise CommandError(f'Error processing URL {url}: {str(e)}')

    def import_csv_from_content(self, content, update_existing, source_name):
        """Import data from CSV content."""
        imported = 0
        skipped = 0
        updated = 0
        
        try:
            # Split content into lines and create a CSV reader
            lines = content.splitlines()
            if not lines:
                self.stdout.write(self.style.WARNING(f'Empty CSV content from {source_name}'))
                return 0, 0, 0
            
            reader = csv.DictReader(lines)
            
            for row in reader:
                try:
                    poi_data = {
                        'external_id': row['poi_id'],
                        'name': row['poi_name'],
                        'latitude': Decimal(row['poi_latitude']),
                        'longitude': Decimal(row['poi_longitude']),
                        'category': row['poi_category'],
                        'ratings': self.parse_ratings(row['poi_ratings']),
                    }
                    
                    imported_count, skipped_count, updated_count = self.save_poi(
                        poi_data, update_existing
                    )
                    imported += imported_count
                    skipped += skipped_count
                    updated += updated_count
                    
                except KeyError as e:
                    self.stdout.write(
                        self.style.WARNING(f'Missing required field in CSV from {source_name}: {e}')
                    )
                    skipped += 1
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f'Error processing CSV row from {source_name}: {e}')
                    )
                    skipped += 1
            
            return imported, skipped, updated
            
        except Exception as e:
            raise CommandError(f'Error processing CSV content from {source_name}: {str(e)}')

    def import_json_from_content(self, content, update_existing, source_name):
        """Import data from JSON content."""
        imported = 0
        skipped = 0
        updated = 0
        
        try:
            data = json.loads(content)
            
            # Handle both single object and array of objects
            if isinstance(data, dict):
                data = [data]
            
            for item in data:
                try:
                    poi_data = {
                        'external_id': str(item['id']),
                        'name': item['name'],
                        'latitude': Decimal(str(item['coordinates']['latitude'])),
                        'longitude': Decimal(str(item['coordinates']['longitude'])),
                        'category': item['category'],
                        'ratings': self.parse_ratings(item['ratings']),
                        'description': item.get('description', ''),
                    }
                    
                    imported_count, skipped_count, updated_count = self.save_poi(
                        poi_data, update_existing
                    )
                    imported += imported_count
                    skipped += skipped_count
                    updated += updated_count
                    
                except KeyError as e:
                    self.stdout.write(
                        self.style.WARNING(f'Missing required field in JSON from {source_name}: {e}')
                    )
                    skipped += 1
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f'Error processing JSON item from {source_name}: {e}')
                    )
                    skipped += 1
            
            return imported, skipped, updated
            
        except json.JSONDecodeError as e:
            raise CommandError(f'Invalid JSON content from {source_name}: {str(e)}')
        except Exception as e:
            raise CommandError(f'Error processing JSON content from {source_name}: {str(e)}')

    def import_xml_from_content(self, content, update_existing, source_name):
        """Import data from XML content."""
        imported = 0
        skipped = 0
        updated = 0
        
        try:
            root = ET.fromstring(content)
            
            # Handle different XML structures
            poi_elements = root.findall('.//poi') or root.findall('.//point') or root.findall('.//item') or root.findall('.//DATA_RECORD')
            
            if not poi_elements:
                # Try to treat the root as a single POI
                poi_elements = [root]
            
            # Check if we found any valid XML elements
            if not poi_elements or len(poi_elements) == 0:
                raise ET.ParseError("No valid XML elements found")
            
            for poi_element in poi_elements:
                try:
                    poi_data = {
                        'external_id': poi_element.find('pid').text,
                        'name': poi_element.find('pname').text,
                        'latitude': Decimal(poi_element.find('platitude').text),
                        'longitude': Decimal(poi_element.find('plongitude').text),
                        'category': poi_element.find('pcategory').text,
                        'ratings': self.parse_ratings(poi_element.find('pratings').text),
                    }
                    
                    imported_count, skipped_count, updated_count = self.save_poi(
                        poi_data, update_existing
                    )
                    imported += imported_count
                    skipped += skipped_count
                    updated += updated_count
                    
                except AttributeError as e:
                    self.stdout.write(
                        self.style.WARNING(f'Missing required field in XML from {source_name}: {e}')
                    )
                    skipped += 1
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f'Error processing XML element from {source_name}: {e}')
                    )
                    skipped += 1
                    
        except (ET.ParseError, AttributeError, ValueError) as e:
            # If XML parsing fails, try to parse as space-separated format (SearchSmartly format)
            self.stdout.write(f'XML parsing failed, trying SearchSmartly format: {e}')
    
        return imported, skipped, updated

    def import_csv(self, file_path, update_existing):
        """Import data from CSV file."""
        imported = 0
        skipped = 0
        updated = 0
        
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                try:
                    poi_data = {
                        'external_id': row['poi_id'],
                        'name': row['poi_name'],
                        'latitude': Decimal(row['poi_latitude']),
                        'longitude': Decimal(row['poi_longitude']),
                        'category': row['poi_category'],
                        'ratings': self.parse_ratings(row['poi_ratings']),
                    }
                    
                    imported_count, skipped_count, updated_count = self.save_poi(
                        poi_data, update_existing
                    )
                    imported += imported_count
                    skipped += skipped_count
                    updated += updated_count
                    
                except KeyError as e:
                    self.stdout.write(
                        self.style.WARNING(f'Missing required field in CSV: {e}')
                    )
                    skipped += 1
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f'Error processing CSV row: {e}')
                    )
                    skipped += 1
        
        return imported, skipped, updated

    def import_json(self, file_path, update_existing):
        """Import data from JSON file."""
        imported = 0
        skipped = 0
        updated = 0
        
        with open(file_path, 'r', encoding='utf-8') as file:
            return self.import_json_from_content(file.read(), update_existing, file_path)

        return imported, skipped, updated

    def import_xml(self, file_path, update_existing):
        """Import data from XML file."""
        imported = 0
        skipped = 0
        updated = 0
        
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Handle different XML structures
            poi_elements = root.findall('.//poi') or root.findall('.//point') or root.findall('.//item')
            
            if not poi_elements:
                # Try to treat the root as a single POI
                poi_elements = [root]
            
            for poi_element in poi_elements:
                try:
                    poi_data = {
                        'external_id': poi_element.find('pid').text,
                        'name': poi_element.find('pname').text,
                        'latitude': Decimal(poi_element.find('platitude').text),
                        'longitude': Decimal(poi_element.find('plongitude').text),
                        'category': poi_element.find('pcategory').text,
                        'ratings': self.parse_ratings(poi_element.find('pratings').text),
                    }
                    
                    imported_count, skipped_count, updated_count = self.save_poi(
                        poi_data, update_existing
                    )
                    imported += imported_count
                    skipped += skipped_count
                    updated += updated_count
                    
                except AttributeError as e:
                    self.stdout.write(
                        self.style.WARNING(f'Missing required field in XML: {e}')
                    )
                    skipped += 1
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f'Error processing XML element: {e}')
                    )
                    skipped += 1
                    
        except ET.ParseError as e:
            raise CommandError(f'Invalid XML file: {e}')
        
        return imported, skipped, updated

    def parse_ratings(self, ratings_data):
        """Parse ratings data from various formats."""
        if isinstance(ratings_data, list):
            return ratings_data
        elif isinstance(ratings_data, str):
            try:
                # Try to parse as JSON
                return json.loads(ratings_data)
            except json.JSONDecodeError:
                # Try to parse as comma-separated values
                try:
                    return [float(x.strip()) for x in ratings_data.strip("{}").split(',') if x]
                except ValueError:
                    # Try to parse as single number
                    try:
                        return [float(ratings_data)]
                    except ValueError:
                        return []
        else:
            return []

    @transaction.atomic
    def save_poi(self, poi_data, update_existing):
        """Save a Point of Interest to the database."""
        try:
            poi, created = PointOfInterest.objects.get_or_create(
                external_id=poi_data['external_id'],
                defaults=poi_data
            )
            
            if created:
                return 1, 0, 0  # imported, skipped, updated
            elif update_existing:
                # Update existing record
                for field, value in poi_data.items():
                    setattr(poi, field, value)
                poi.save()
                return 0, 0, 1  # imported, skipped, updated
            else:
                return 0, 1, 0  # imported, skipped, updated
                
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'Error saving POI {poi_data.get("external_id", "unknown")}: {e}')
            )
            return 0, 1, 0  # imported, skipped, updated
