import logging
import sys
from pathlib import Path
import pandas as pd

def setup_logging(log_file='import.log'):
    """Setup logging configuration"""
    # Ensure logs directory exists
    Path('logs').mkdir(exist_ok=True)
    log_path = Path('logs') / log_file
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def clean_and_format_data(value, default=''):
    """Clean and format CSV data"""
    if pd.isna(value) or value == '':
        return default
    return str(value).strip()

def parse_file_list(file_string):
    """Parse space-separated file list from environment"""
    if not file_string:
        return []
    return [f.strip() for f in file_string.split() if f.strip()]

def validate_file_exists(file_path):
    """Check if file exists and is readable"""
    path = Path(file_path)
    return path.exists() and path.is_file()
