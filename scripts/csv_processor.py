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
        
        # Extract variant info
        variant_col = column_mapping.get('variants')
        quantity_col = column_mapping.get('quantity') 
        price_col = column_mapping.get('price')
        
        variant_size = clean_and_format_data(row.get(variant_col) if variant_col else '', '50ml')
        quantity = int(row.get(quantity_col, 1)) if quantity_col and pd.notna(row.get(quantity_col)) else 1
        price = clean_and_format_data(row.get(price_col) if price_col else '', '0.00')
        
        # Generate SKU
        file_prefix = Path(filename).stem.replace('-', '').replace('_', '').upper()[:3]
        title_prefix = row[column_mapping['title']].replace(' ', '-').replace("'", "").upper()[:10]
        sku = f"{file_prefix}-{title_prefix}-{variant_size}"
        
        variant_data = {
            'title': f"{variant_size}ml" if variant_size.replace('.', '').isdigit() else variant_size,
            'price': str(price) if price != '' else '0.00',
            'sku': sku,
            'inventory_quantity': quantity,
            'weight': Config.DEFAULT_WEIGHT,
            'weight_unit': Config.DEFAULT_WEIGHT_UNIT,
            'inventory_management': 'shopify',
            'inventory_policy': Config.DEFAULT_INVENTORY_POLICY,
            'requires_shipping': True,
            'taxable': True
        }
        
        # Handle tax settings
        tax_col = column_mapping.get('tax')
        if tax_col and pd.notna(row.get(tax_col)):
            variant_data['taxable'] = str(row[tax_col]).upper() == 'TRUE'
        
        variants.append(variant_data)
        return variants

    def prepare_product_data(self, row, column_mapping, filename):
        """Convert CSV row to Shopify product format"""
        
        # Main product title
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
            logger.info(f"📊 Found {len(df)} products in {filename}")
            
            # Detect CSV structure
            column_mapping = self.column_mapper.detect_csv_structure(df, filename)
            
            # Process products
            processed_products = []
            title_col = column_mapping['title']
            grouped = df.groupby(title_col)
            
            for title, group in grouped:
                try:
                    # Handle multiple variants of same product
                    if len(group) > 1:
                        base_row = group.iloc[0].copy()
                        quantity_col = column_mapping.get('quantity')
                        if quantity_col:
                            total_pieces = group[quantity_col].sum()
                            base_row[quantity_col] = total_pieces
                        product_data = self.prepare_product_data(base_row, column_mapping, filename)
                    else:
                        product_data = self.prepare_product_data(group.iloc[0], column_mapping, filename)
                    
                    processed_products.append(product_data)
                    
                except Exception as e:
                    logger.error(f"❌ Error processing {title} from {filename}: {str(e)}")
                    continue
            
            return {
                'filename': filename,
                'products': processed_products,
                'column_mapping': column_mapping,
                'total_rows': len(df)
            }
            
        except Exception as e:
            logger.error(f"❌ Error processing CSV file {filename}: {str(e)}")
            return None
