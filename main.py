#!/usr/bin/env python3
"""
Shopify Multi-CSV Product Import Tool

Main entry point for importing products from CSV files to Shopify.
"""

import os
import sys
from pathlib import Path

# Ensure the project root is in the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Now we can import from our packages
from scripts import (
    setup_logging, 
    parse_file_list, 
    validate_file_exists,
    CSVProcessor,
    ShopifyImporter
)
from config import Config

def main():
    """Main execution function"""
    # Setup logging
    logger = setup_logging('multi_csv_import.log')
    
    logger.info("🚀 Starting Shopify Multi-CSV Import Tool")
    logger.info(f"📍 Working directory: {project_root}")
    
    try:
        # Validate configuration
        Config.validate_required_settings()
        logger.info("✅ Configuration validated")
    except ValueError as e:
        logger.error(f"❌ Configuration error: {e}")
        sys.exit(1)
    
    # Get file list from environment
    changed_files = os.getenv('CHANGED_FILES', '').strip()
    
    if not changed_files:
        logger.error("❌ No files specified for processing")
        logger.info("💡 Set CHANGED_FILES environment variable with space-separated file paths")
        sys.exit(1)
    
    file_list = parse_file_list(changed_files)
    
    if not file_list:
        logger.error("❌ No valid files found in the list")
        sys.exit(1)
    
    # Validate files exist
    valid_files = []
    for f in file_list:
        if validate_file_exists(f):
            valid_files.append(f)
            logger.info(f"✅ File found: {f}")
        else:
            logger.warning(f"⚠️  File not found: {f}")
    
    if not valid_files:
        logger.error("❌ No valid files found")
        sys.exit(1)
    
    logger.info(f"📁 Processing {len(valid_files)} files")
    
    # Initialize components
    csv_processor = CSVProcessor()
    shopify_importer = ShopifyImporter()
    
    try:
        # Process each file
        for csv_file in valid_files:
            logger.info(f"🔄 Processing: {csv_file}")
            
            # Process CSV
            processed_data = csv_processor.process_csv_file(csv_file)
            if not processed_data:
                logger.error(f"❌ Failed to process {csv_file}")
                continue
            
            logger.info(f"📊 Found {len(processed_data['products'])} products in {csv_file}")
            
            # Import to Shopify
            shopify_importer.import_products(processed_data)
        
        # Print summary
        shopify_importer.print_summary()
        
        # Exit with error if any products failed
        if shopify_importer.overall_results.get('failed', 0) > 0:
            logger.warning("⚠️  Some products failed to import")
            sys.exit(1)
            
        logger.info("🎉 Multi-file import completed successfully!")
        
    except KeyboardInterrupt:
        logger.info("🛑 Import interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Import failed with exception: {str(e)}")
        logger.exception("Full traceback:")
        sys.exit(1)
    finally:
        shopify_importer.cleanup()

if __name__ == "__main__":
    main()
