import shopify
import logging
import time
from config.settings import Config

logger = logging.getLogger(__name__)

class ShopifyImporter:
    """Handles Shopify API operations"""
    
    def __init__(self):
        Config.validate_required_settings()
        
        # Ensure we have a valid API version
        api_version = Config.SHOPIFY_API_VERSION
        if not api_version or api_version in ['***', '']:
            api_version = '2023-10'
            logger.warning(f"⚠️ Invalid API version detected, using default: {api_version}")
        
        try:
            self.session = shopify.Session(
                Config.SHOPIFY_SHOP_DOMAIN, 
                api_version, 
                Config.SHOPIFY_ACCESS_TOKEN
            )
            shopify.ShopifyResource.activate_session(self.session)
            logger.info(f"✅ Connected to Shopify store: {Config.SHOPIFY_SHOP_DOMAIN} (API v{api_version})")
        except shopify.api_version.VersionNotFoundError as e:
            logger.error(f"❌ Invalid Shopify API version: {api_version}")
            logger.info("📋 Valid API versions: 2023-01, 2023-04, 2023-07, 2023-10, 2024-01, 2024-04")
            raise ValueError(f"Unsupported Shopify API version: {api_version}")
        
        self.overall_results = {
            'files_processed': 0,
            'total_products': 0,
            'successful_products': 0,
            'failed_products': 0,
            'skipped_products': 0,
            'file_results': []
        }

    # ... rest of your existing methods remain the same
