import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class ColumnMapper:
    """Handles CSV column detection and mapping"""
    
    COLUMN_MAPPINGS = {
        'title': ['TITLE', 'title', 'name', 'product_name'],
        'description': ['Description', 'description', 'body_html', 'desc', 'details'],
        'price': ['Price', 'price', 'cost', 'amount', 'unit_price'],
        'variants': ['variants', 'variant', 'size', 'ml', 'volume'],
        'quantity': ['NO.OF PIECES', 'quantity', 'stock', 'inventory', 'pieces'],
        'tags': ['TAGS', 'tags', 'tag', 'keywords'],
        'vendor': ['Vendor', 'vendor', 'brand', 'supplier', 'manufacturer'],
        'category': ['Category', 'category', 'type', 'product_type'],
        'image': ['Media Link', 'image', 'photo', 'media', 'image_url'],
        'tax': ['Charge tax on this product', 'tax', 'taxable'],
        'track': ['Track quantity', 'track', 'inventory_tracking']
    }

    @classmethod
    def detect_csv_structure(cls, df, filename):
        """Detect and validate CSV structure"""
        columns = df.columns.tolist()
        logger.info(f"📋 File: {Path(filename).name} - Columns: {columns}")
        
        # Check for required columns
        title_found = any(col in columns for col in cls.COLUMN_MAPPINGS['title'])
        if not title_found:
            raise ValueError(f"Missing required TITLE column in {filename}")
        
        # Map columns
        column_mapping = {}
        for field, possible_names in cls.COLUMN_MAPPINGS.items():
            found_column = next((col for col in columns if col in possible_names), None)
            column_mapping[field] = found_column
        
        logger.info(f"🔍 Detected mapping for {Path(filename).name}: {column_mapping}")
        return column_mapping

    @classmethod
    def get_required_columns(cls):
        """Return list of required columns"""
        return cls.COLUMN_MAPPINGS['title']
