import os
from pathlib import Path

class Config:
    # Shopify API
    SHOPIFY_SHOP_DOMAIN  = os.getenv('SHOPIFY_SHOP_DOMAIN')
    SHOPIFY_ACCESS_TOKEN = os.getenv('SHOPIFY_ACCESS_TOKEN')
    SHOPIFY_API_VERSION  = os.getenv('SHOPIFY_API_VERSION', '2024-01')

    # Delay / retries
    DEFAULT_DELAY  = 1.0
    MAX_RETRIES    = 3

    # Directories
    BASE_DIR            = Path(__file__).parent.parent
    PRODUCT_DATA_DIR    = BASE_DIR / 'product-data'
    LOGS_DIR            = BASE_DIR / 'logs'

    # Defaults
    DEFAULT_WEIGHT          = 0.5
    DEFAULT_WEIGHT_UNIT     = 'kg'
    DEFAULT_INVENTORY_POLICY= 'deny'
    DEFAULT_STATUS          = 'draft'        # ← default now “draft”

    @classmethod
    def validate_required_settings(cls):
        missing = [n for n,v in {
            'SHOPIFY_SHOP_DOMAIN' : cls.SHOPIFY_SHOP_DOMAIN,
            'SHOPIFY_ACCESS_TOKEN': cls.SHOPIFY_ACCESS_TOKEN
        }.items() if not v]
        if missing:
            raise ValueError(f"Missing env vars: {missing}")
        return True
