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

    # ────────────────────────────────────────────────────────────
    #  PARSE VARIANTS  (price fix added)
    # ────────────────────────────────────────────────────────────
    def parse_variants_from_row(self, row, column_mapping, filename):
        variants = []

        variant_col  = column_mapping.get('variants')
        quantity_col = column_mapping.get('quantity')
        price_col    = column_mapping.get('price')

        # Variant-size
        variant_size_raw = clean_and_format_data(row.get(variant_col) if variant_col else '', '50')
        variant_display  = f"{variant_size_raw}ml" if variant_size_raw.isdigit() else variant_size_raw

        # Quantity
        quantity = int(row.get(quantity_col, 1)) if quantity_col and pd.notna(row.get(quantity_col)) else 1

        # ─── PRICE 2-decimal formatting (✅ fix) ─────────────────
        price_raw = clean_and_format_data(row.get(price_col) if price_col else '', '0')
        try:
            price_float = float(price_raw)
        except ValueError:
            price_float = 0.0
        price_formatted = f"{price_float:.2f}"       # always “100.00”

        # SKU
        file_prefix  = Path(filename).stem.replace('-', '').replace('_', '').upper()[:3]
        title_prefix = row[column_mapping['title']].replace(' ', '-').replace("'", "").upper()[:10]
        sku          = f"{file_prefix}-{title_prefix}-{variant_size_raw}"

        variant_data = {
            'title'              : variant_display,
            'price'              : price_formatted,
            'sku'                : sku,
            'inventory_quantity' : quantity,
            'weight'             : Config.DEFAULT_WEIGHT,
            'weight_unit'        : Config.DEFAULT_WEIGHT_UNIT,
            'inventory_management': 'shopify',
            'inventory_policy'   : Config.DEFAULT_INVENTORY_POLICY,
            'requires_shipping'  : True,
            'taxable'            : True
        }

        variants.append(variant_data)
        logger.info(f"🏷️ Created variant: {variant_display} with {quantity} pieces at ${price_formatted}")
        return variants

    # ────────────────────────────────────────────────────────────
    #  PREPARE PRODUCT  (status set to “draft”)
    # ────────────────────────────────────────────────────────────
    def prepare_product_data(self, row, column_mapping, filename):
        title = clean_and_format_data(row[column_mapping['title']])

        # Description
        desc_col    = column_mapping.get('description')
        description = clean_and_format_data(
            row.get(desc_col) if desc_col else '',
            f"<p>{title} - Imported from {Path(filename).stem}</p>"
        )

        # Tags
        tags_col = column_mapping.get('tags')
        tags     = clean_and_format_data(row.get(tags_col) if tags_col else '', 'imported')
        if tags:
            tags = ','.join(tag.strip() for tag in tags.split(','))

        # Images (optional)
        images = []
        image_col = column_mapping.get('image')
        if image_col:
            media_link = clean_and_format_data(row.get(image_col))
            if media_link.startswith(('http', 'https')):
                images.append({'src': media_link})

        # Variants
        variants = self.parse_variants_from_row(row, column_mapping, filename)

        product_data = {
            'title'       : title,
            'body_html'   : description,
            'vendor'      : clean_and_format_data(row.get(column_mapping.get('vendor')) if column_mapping.get('vendor') else '', 'Default Vendor'),
            'product_type': clean_and_format_data(row.get(column_mapping.get('category')) if column_mapping.get('category') else '', 'General'),
            'tags'        : tags,
            'status'      : 'draft',                # ← CREATED AS DRAFT
            'variants'    : variants,
            'images'      : images,
            'options'     : [{'name': 'Size', 'values': [v['title'] for v in variants]}] if len(variants) > 1 else []
        }
        return product_data

    # ────────────────────────────────────────────────────────────
    #  PROCESS CSV (unchanged except for enhanced logging earlier)
    # ────────────────────────────────────────────────────────────
    def process_csv_file(self, csv_file_path):
        filename = Path(csv_file_path).name
        logger.info(f"🔄 Processing file: {filename}")

        try:
            df = pd.read_csv(csv_file_path)
            logger.info(f"📊 Found {len(df)} rows in {filename}")
            logger.info(f"📋 CSV columns: {list(df.columns)}")

            # Filter invalid rows
            df = df[df['TITLE'].notna()]
            df = df[~df['TITLE'].astype(str).str.startswith('#')]
            df = df[df['TITLE'].astype(str).str.strip() != '']
            if df.empty:
                logger.error(f"⚠️ No valid products in {filename}")
                return None

            # Column mapping
            column_mapping = self.column_mapper.detect_csv_structure(df, filename)
            logger.info(f"✅ Column mapping successful: {column_mapping}")

            processed_products = []
            for title, group in df.groupby(column_mapping['title']):
                row = group.iloc[0]
                processed_products.append(self.prepare_product_data(row, column_mapping, filename))

            logger.info(f"🎉 Successfully processed {len(processed_products)} products from {filename}")

            return {
                'filename'    : filename,
                'products'    : processed_products,
                'column_mapping': column_mapping,
                'total_rows'  : len(df)
            }

        except Exception as e:
            logger.error(f"❌ Critical error processing {filename}: {e}")
            return None
