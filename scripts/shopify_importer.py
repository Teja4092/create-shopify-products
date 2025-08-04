import shopify
import logging
import time
from config.settings import Config

logger = logging.getLogger(__name__)

class ShopifyImporter:
    """Handles Shopify API operations"""
    
    def __init__(self):
        Config.validate_required_settings()
        self.session = shopify.Session(
            Config.SHOPIFY_SHOP_DOMAIN, 
            Config.SHOPIFY_API_VERSION, 
            Config.SHOPIFY_ACCESS_TOKEN
        )
        shopify.ShopifyResource.activate_session(self.session)
        logger.info(f"✅ Connected to Shopify store: {Config.SHOPIFY_SHOP_DOMAIN}")
        
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

            # Create new product
            product = shopify.Product()
            
            # Set basic product attributes (not variants or images)
            basic_attributes = ['title', 'body_html', 'vendor', 'product_type', 'tags', 'status']
            for key in basic_attributes:
                if key in product_data:
                    setattr(product, key, product_data[key])
            
            # Handle variants separately - convert dicts to Shopify Variant objects
            if 'variants' in product_data and product_data['variants']:
                shopify_variants = []
                for variant_data in product_data['variants']:
                    variant = shopify.Variant()
                    for key, value in variant_data.items():
                        if hasattr(variant, key):
                            setattr(variant, key, value)
                    shopify_variants.append(variant)
                product.variants = shopify_variants
            
            # Handle images separately - convert dicts to Shopify Image objects
            if 'images' in product_data and product_data['images']:
                shopify_images = []
                for image_data in product_data['images']:
                    if isinstance(image_data, dict) and 'src' in image_data:
                        image = shopify.Image()
                        image.src = image_data['src']
                        shopify_images.append(image)
                product.images = shopify_images
            
            # Handle options separately
            if 'options' in product_data and product_data['options']:
                shopify_options = []
                for option_data in product_data['options']:
                    option = shopify.Option()
                    for key, value in option_data.items():
                        if hasattr(option, key):
                            setattr(option, key, value)
                    shopify_options.append(option)
                product.options = shopify_options

            # Save the product
            success = product.save()
            
            if success:
                logger.info(f"✅ Created product: {title} (ID: {product.id}) from {filename}")
                return {
                    'success': True, 
                    'action': 'created',
                    'product_id': product.id, 
                    'title': title,
                    'file': filename,
                    'variants_count': len(product_data.get('variants', []))
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
        """Import processed products to Shopify"""
        if delay is None:
            delay = Config.DEFAULT_DELAY
            
        filename = processed_data['filename']
        products = processed_data['products']
        
        file_results = {
            'filename': filename,
            'total_products': len(products),
            'created': [],
            'skipped': [],
            'failed': []
        }
        
        for product_data in products:
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
            
            time.sleep(delay)
        
        self.overall_results['files_processed'] += 1
        self.overall_results['total_products'] += processed_data['total_rows']
        self.overall_results['file_results'].append(file_results)
        
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
        shopify.ShopifyResource.clear_session()
        logger.info("✅ Session cleaned up")
