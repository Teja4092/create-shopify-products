import shopify
import logging
import time
from config.settings import Config

logger = logging.getLogger(__name__)

class ShopifyImporter:
    """Handles Shopify API operations"""
    
    def __init__(self):
        Config.validate_required_settings()
        
        # List of API versions to try (newest first)
        api_versions_to_try = [
            Config.SHOPIFY_API_VERSION,
            "2024-01",
            "2023-07", 
            "2023-04",
            "2023-01"
        ]
        
        self.session = None
        
        for api_version in api_versions_to_try:
            if not api_version or api_version in ['***', '']:
                continue
                
            # Clean the API version string
            api_version = str(api_version).strip()
            
            try:
                logger.info(f"🔧 Attempting to connect with API version: {api_version}")
                self.session = shopify.Session(
                    Config.SHOPIFY_SHOP_DOMAIN, 
                    api_version, 
                    Config.SHOPIFY_ACCESS_TOKEN
                )
                shopify.ShopifyResource.activate_session(self.session)
                logger.info(f"✅ Connected to Shopify store: {Config.SHOPIFY_SHOP_DOMAIN} (API v{api_version})")
                break
                
            except shopify.api_version.VersionNotFoundError:
                logger.warning(f"⚠️ API version {api_version} not supported, trying next...")
                continue
            except Exception as e:
                logger.error(f"❌ Connection failed with API version {api_version}: {str(e)}")
                continue
        
        if not self.session:
            try:
                supported_versions = list(shopify.ApiVersion.versions.keys())
                logger.error(f"❌ No supported API version found!")
                logger.error(f"📋 Available versions in your ShopifyAPI library: {supported_versions}")
            except:
                logger.error("❌ Could not determine supported API versions")
            raise ValueError("Unable to establish Shopify connection with any supported API version")
        
        self.overall_results = {
            'files_processed': 0,
            'total_products': 0,
            'successful_products': 0,
            'failed_products': 0,
            'skipped_products': 0,
            'file_results': []
        }

    def check_existing_product(self, title):
        """Check if product already exists"""
        try:
            products = shopify.Product.find(title=title)
            return len(products) > 0
        except:
            return False

    def create_product(self, product_data, filename):
        """Create product in Shopify"""
        title = product_data['title']
        
        try:
            if self.check_existing_product(title):
                logger.info(f"⚠️  Product already exists: {title} (from {filename})")
                return {'success': True, 'action': 'skipped', 'title': title, 'file': filename}

            product = shopify.Product()
            for key, value in product_data.items():
                setattr(product, key, value)

            success = product.save()
            
            if success:
                logger.info(f"✅ Created product: {title} (ID: {product.id}) from {filename}")
                return {
                    'success': True, 
                    'action': 'created',
                    'product_id': product.id, 
                    'title': title,
                    'file': filename,
                    'variants_count': len(product_data['variants'])
                }
            else:
                error_msg = f"API Error: {product.errors.full_messages()}"
                logger.error(f"❌ Failed to create {title} from {filename}: {error_msg}")
                return {'success': False, 'error': error_msg, 'title': title, 'file': filename}
                
        except Exception as e:
            error_msg = f"Exception: {str(e)}"
            logger.error(f"❌ Error with {title} from {filename}: {error_msg}")
            return {'success': False, 'error': error_msg, 'title': title, 'file': filename}

    def import_products(self, processed_data, delay=None):
        """Import processed products to Shopify - THIS METHOD WAS MISSING"""
        if delay is None:
            delay = Config.DEFAULT_DELAY
            
        filename = processed_data['filename']
        products = processed_data['products']
        
        logger.info(f"🚀 Starting import for {filename} with {len(products)} products")
        
        file_results = {
            'filename': filename,
            'total_products': len(products),
            'created': [],
            'skipped': [],
            'failed': []
        }
        
        for product_data in products:
            logger.info(f"🔄 Processing product: {product_data['title']}")
            result = self.create_product(product_data, filename)
            
            if result['success']:
                if result['action'] == 'created':
                    file_results['created'].append(result)
                    self.overall_results['successful_products'] += 1
                else:
                    file_results['skipped'].append(result)
                    self.overall_results['skipped_products'] += 1
            else:
                file_results['failed'].append(result)
                self.overall_results['failed_products'] += 1
            
            # Add delay to avoid rate limiting
            time.sleep(delay)
        
        self.overall_results['files_processed'] += 1
        self.overall_results['total_products'] += processed_data['total_rows']
        self.overall_results['file_results'].append(file_results)
        
        logger.info(f"📊 Completed {filename}: {len(file_results['created'])} created, {len(file_results['skipped'])} skipped, {len(file_results['failed'])} failed")
        
        return file_results

    def print_summary(self):
        """Print comprehensive import summary"""
        logger.info("\n" + "="*80)
        logger.info("🌟 SHOPIFY IMPORT SUMMARY")
        logger.info("="*80)
        logger.info(f"Files processed: {self.overall_results['files_processed']}")
        logger.info(f"Total products: {self.overall_results['total_products']}")
        logger.info(f"✅ Successfully created: {self.overall_results['successful_products']}")
        logger.info(f"⚠️  Skipped (already exist): {self.overall_results['skipped_products']}")
        logger.info(f"❌ Failed imports: {self.overall_results['failed_products']}")
        
        if self.overall_results['successful_products'] > 0:
            success_rate = (self.overall_results['successful_products'] / self.overall_results['total_products']) * 100
            logger.info(f"Overall success rate: {success_rate:.1f}%")
        
        for file_result in self.overall_results['file_results']:
            logger.info(f"\n📄 {file_result['filename']}:")
            logger.info(f"  - Created: {len(file_result['created'])}")
            logger.info(f"  - Skipped: {len(file_result['skipped'])}")
            logger.info(f"  - Failed: {len(file_result['failed'])}")
        
        logger.info("="*80)

    def cleanup(self):
        """Clean up Shopify session"""
        try:
            shopify.ShopifyResource.clear_session()
            logger.info("✅ Session cleaned up")
        except Exception as e:
            logger.warning(f"⚠️ Warning during cleanup: {e}")
