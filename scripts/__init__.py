"""
Shopify CSV Import Scripts Package

This package contains modules for importing products to Shopify from CSV files.
"""

from .shopify_importer import ShopifyImporter
from .csv_processor import CSVProcessor
from .column_mapper import ColumnMapper
from .utils import setup_logging, clean_and_format_data, parse_file_list, validate_file_exists

__version__ = "1.0.0"
__author__ = "Your Team"
__description__ = "Modular Shopify CSV Import System"

# Package-level imports for easier access
__all__ = [
    'ShopifyImporter',
    'CSVProcessor', 
    'ColumnMapper',
    'setup_logging',
    'clean_and_format_data',
    'parse_file_list',
    'validate_file_exists'
]

# Package configuration
SUPPORTED_CSV_FORMATS = [
    'YSL-PERFUME-LIST',
    'GENERIC-PRODUCT-LIST',
    'INVENTORY-UPDATE'
]

DEFAULT_SETTINGS = {
    'api_delay': 1.0,
    'max_retries': 3,
    'log_level': 'INFO'
}
