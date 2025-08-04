"""
Test package for Shopify CSV Import

Contains unit tests and integration tests for all modules.
"""

import sys
from pathlib import Path

# Add the project root to Python path for testing
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Test configuration
TEST_DATA_DIR = Path(__file__).parent / 'data'
TEST_CSV_FILE = TEST_DATA_DIR / 'test-products.csv'

__all__ = ['TEST_DATA_DIR', 'TEST_CSV_FILE']
