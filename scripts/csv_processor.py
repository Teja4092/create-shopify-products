import pandas as pd
import logging
from pathlib import Path
from .column_mapper import ColumnMapper
from .utils import clean_and_format_data
from config.settings import Config

logger = logging.getLogger(__name__)

class CSVProcessor:
    """Handles CSV file processing and data preparation"""
    
    def __init__(self):
        self.column_mapper = ColumnMapper()

    def parse_variants_from_row(self, row, column_mapping, filename):
        """Create variants based on detected columns"""
        variants = []
        
        variant_col = column_mapping.get('variants')
        quantity_col = column_mapping.get('quantity') 
        price_col = column_mapping.get('price')
        
        # Better variant size handling
        variant_size = clean_and_format_data(row.get(variant_col) if variant_col else '', '50')
        
        # If variant_size is just a number, assume it's ml
        if variant_size.isdigit():
            variant_display = f"{variant_size}ml"
        else:
            variant_display = variant_size
        
        quantity = int(row.get(quantity_col, 1)) if quantity_col and pd.notna(row.get(quantity_col)) else 1
        price = clean_and_format_data(row.get(price_col) if price_col else '', '0.00')
        
        # Generate SKU
        file_prefix = Path(filename).stem.replace('-', '').replace('_', '').upper()[:3]
        title_prefix = row[column_mapping['title']].replace(' ', '-').replace("'", "").upper()[:10]
        sku = f"{file_prefix}-{title_prefix}-{variant_size}"
        
        variant_data = {
            'title': variant_display,  # "2ml" instead of just "2"
            'price': str(price),
            'sku': sku,
            'inventory_quantity': quantity,
            'weight': Config.DEFAULT_WEIGHT,
            'weight_unit': Config.DEFAULT_WEIGHT_UNIT,
            'inventory_management': 'shopify',
            'inventory_policy': Config.DEFAULT_INVENTORY_POLICY,
            'requires_shipping': True,
            'taxable': True
        }
        
        logger.info(f"🏷️ Created variant: {variant_display} with {quantity} pieces at ${price}")
        
        variants.append(variant_data)
        return variants


    def prepare_product_data(self, row, column_mapping, filename):
        """Convert CSV row to Shopify product format"""
        
        title = clean_and_format_data(row[column_mapping['title']])
        
        # Description
        desc_col = column_mapping.get('description')
        description = clean_and_format_data(
            row.get(desc_col) if desc_col else '', 
            f"<p>{title} - Imported from {Path(filename).stem}</p>"
        )
        
        # Tags
        tags_col = column_mapping.get('tags')
        tags = clean_and_format_data(row.get(tags_col) if tags_col else '', 'imported')
        if tags:
            tag_list = [tag.strip() for tag in tags.split(',')]
            tags = ','.join(tag_list)
        
        # Images
        images = []
        image_col = column_mapping.get('image')
        if image_col:
            media_link = clean_and_format_data(row.get(image_col))
            if media_link and media_link.startswith(('http', 'https')):
                images.append({'src': media_link})

        # Create variants
        variants = self.parse_variants_from_row(row, column_mapping, filename)

        # Product data
        product_data = {
            'title': title,
            'body_html': description,
            'vendor': clean_and_format_data(row.get(column_mapping.get('vendor')) if column_mapping.get('vendor') else '', 'Default Vendor'),
            'product_type': clean_and_format_data(row.get(column_mapping.get('category')) if column_mapping.get('category') else '', 'General'),
            'tags': tags,
            'status': Config.DEFAULT_STATUS,
            'variants': variants,
            'images': images,
            'options': [{'name': 'Size', 'values': [v['title'] for v in variants]}] if len(variants) > 1 else []
        }

        return product_data

    def process_csv_file(self, csv_file_path):
        """Process a single CSV file and return processed data"""
        filename = Path(csv_file_path).name
        logger.info(f"🔄 Processing file: {filename}")
        
        try:
            # Read CSV file
            df = pd.read_csv(csv_file_path)
            logger.info(f"📊 Found {len(df)} rows in {filename}")
            logger.info(f"📋 CSV columns: {list(df.columns)}")
            
            # Filter out invalid rows
            original_count = len(df)
            df = df[df['TITLE'].notna()]
            df = df[~df['TITLE'].astype(str).str.startswith('#')]
            df = df[df['TITLE'].astype(str).str.strip() != '']
            
            filtered_count = len(df)
            if filtered_count < original_count:
                logger.info(f"🧹 Filtered out {original_count - filtered_count} invalid rows")
            
            if filtered_count == 0:
                logger.error(f"⚠️ No valid products found in {filename} after filtering")
                return None
            
            logger.info(f"📊 Processing {filtered_count} valid products from {filename}")
            
            # Detect CSV structure
            try:
                column_mapping = self.column_mapper.detect_csv_structure(df, filename)
                logger.info(f"✅ Column mapping successful: {column_mapping}")
            except Exception as e:
                logger.error(f"❌ Column mapping failed: {str(e)}")
                return None
            
            # Process products
            processed_products = []
            title_col = column_mapping['title']
            
            try:
                grouped = df.groupby(title_col)
                logger.info(f"📊 Found {len(grouped)} unique product titles")
            except Exception as e:
                logger.error(f"❌ Groupby operation failed: {str(e)}")
                return None
            
            for title, group in grouped:
                logger.info(f"🔄 Processing product: {title}")
                
                try:
                    # Skip invalid titles
                    if not title or str(title).strip().startswith('#'):
                        logger.warning(f"⚠️ Skipping invalid title: {title}")
                        continue
                    
                    # Handle multiple variants
                    if len(group) > 1:
                        logger.info(f"📦 Multiple variants found for {title}: {len(group)}")
                        base_row = group.iloc[0].copy()
                        quantity_col = column_mapping.get('quantity')
                        if quantity_col:
                            total_pieces = group[quantity_col].sum()
                            base_row[quantity_col] = total_pieces
                            logger.info(f"📊 Combined quantity: {total_pieces}")
                        product_data = self.prepare_product_data(base_row, column_mapping, filename)
                    else:
                        logger.info(f"📦 Single variant for {title}")
                        product_data = self.prepare_product_data(group.iloc[0], column_mapping, filename)
                    
                    if product_data:
                        processed_products.append(product_data)
                        logger.info(f"✅ Successfully processed: {title}")
                    else:
                        logger.error(f"❌ Failed to prepare product data for: {title}")
                        
                except Exception as e:
                    logger.error(f"❌ Error processing {title}: {str(e)}")
                    import traceback
                    logger.error(f"📋 Full traceback: {traceback.format_exc()}")
                    continue
            
            if not processed_products:
                logger.error(f"❌ No products were successfully processed from {filename}")
                return None
            
            result = {
                'filename': filename,
                'products': processed_products,
                'column_mapping': column_mapping,
                'total_rows': len(df)
            }
            
            logger.info(f"🎉 Successfully processed {len(processed_products)} products from {filename}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Critical error processing CSV file {filename}: {str(e)}")
            import traceback
            logger.error(f"📋 Full traceback: {traceback.format_exc()}")
            return None

