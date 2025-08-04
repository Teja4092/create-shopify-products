"""
Shopify CSV Import Scripts Package
"""

# Import with error handling to avoid import failures
try:
    from .shopify_importer import ShopifyImporter
except ImportError as e:
    print(f"Warning: Could not import ShopifyImporter: {e}")
    ShopifyImporter = None

try:
    from .csv_processor import CSVProcessor
except ImportError as e:
    print(f"Warning: Could not import CSVProcessor: {e}")
    CSVProcessor = None

try:
    from .column_mapper import ColumnMapper
except ImportError as e:
    print(f"Warning: Could not import ColumnMapper: {e}")
    ColumnMapper = None

try:
    from .utils import setup_logging, clean_and_format_data, parse_file_list, validate_file_exists
except ImportError as e:
    print(f"Warning: Could not import utils: {e}")
    setup_logging = None
    clean_and_format_data = None
    parse_file_list = None
    validate_file_exists = None

__all__ = [
    'ShopifyImporter',
    'CSVProcessor', 
    'ColumnMapper',
    'setup_logging',
    'clean_and_format_data',
    'parse_file_list',
    'validate_file_exists'
]
