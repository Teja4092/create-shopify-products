"""
Configuration package for Shopify CSV Import
"""

try:
    from .settings import Config
    __all__ = ['Config']
except ImportError as e:
    print(f"Configuration import error: {e}")
    # Create a minimal Config class as fallback
    import os
    
    class Config:
        SHOPIFY_SHOP_DOMAIN = os.getenv('SHOPIFY_SHOP_DOMAIN')
        SHOPIFY_ACCESS_TOKEN = os.getenv('SHOPIFY_ACCESS_TOKEN')
        SHOPIFY_API_VERSION = os.getenv('SHOPIFY_API_VERSION', '2024-01')
        DEFAULT_DELAY = 1.0
        DEFAULT_WEIGHT = 0.5
        DEFAULT_WEIGHT_UNIT = 'kg'
        DEFAULT_INVENTORY_POLICY = 'deny'
        DEFAULT_STATUS = 'active'
        
        @classmethod
        def validate_required_settings(cls):
            required = [cls.SHOPIFY_SHOP_DOMAIN, cls.SHOPIFY_ACCESS_TOKEN]
            missing = [name for name, value in zip(['SHOPIFY_SHOP_DOMAIN', 'SHOPIFY_ACCESS_TOKEN'], required) if not value]
            if missing:
                raise ValueError(f"Missing required environment variables: {missing}")
            return True
    
    __all__ = ['Config']
