import os
from pathlib import Path

class Config:
    # Shopify API settings
    SHOPIFY_SHOP_DOMAIN = os.getenv('SHOPIFY_SHOP_DOMAIN')
    SHOPIFY_ACCESS_TOKEN = os.getenv('SHOPIFY_ACCESS_TOKEN')
    SHOPIFY_API_VERSION = os.getenv('SHOPIFY_API_VERSION', '2023-10')
    
    # File processing settings
    DEFAULT_DELAY = 1.0  # Delay between API calls
    MAX_RETRIES = 3
    
    # Directory settings
    BASE_DIR = Path(__file__).parent.parent
    PRODUCT_DATA_DIR = BASE_DIR / 'product-data'
    LOGS_DIR = BASE_DIR / 'logs'
    
    # Default values
    DEFAULT_WEIGHT = 0.5
    DEFAULT_WEIGHT_UNIT = 'kg'
    DEFAULT_INVENTORY_POLICY = 'deny'
    DEFAULT_STATUS = 'active'
    
    @classmethod
    def validate_required_settings(cls):
        """Validate that all required settings are present"""
        required = [cls.SHOPIFY_SHOP_DOMAIN, cls.SHOPIFY_ACCESS_TOKEN]
        missing = [name for name, value in zip(['SHOPIFY_SHOP_DOMAIN', 'SHOPIFY_ACCESS_TOKEN'], required) if not value]
        if missing:
            raise ValueError(f"Missing required environment variables: {missing}")
        return True
