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
        # Support for multiple option values (comma-separated)
        option1_name = row.get('Option1 Name')
        option1_values = [v.strip() for v in str(row.get('Option1 Value', '')).split(',') if v.strip()]
        option2_name = row.get('Option2 Name')
        option2_values = [v.strip() for v in str(row.get('Option2 Value', '')).split(',') if v.strip()]
        price_col    = column_mapping.get('price')
        # Use 'inventory_quantity' directly from the row
        quantity_col = 'inventory_quantity'
        variants = []

        # If only option1 is present
        if option1_name and option1_values and not option2_name:
            for val in option1_values:
                price_raw = clean_and_format_data(row.get(price_col) if price_col else '', '0')
                try:
                    price_float = float(price_raw)
                except ValueError:
                    price_float = 0.0
                price_formatted = f"{price_float:.2f}"
                quantity = int(row.get(quantity_col, 1)) if quantity_col and pd.notna(row.get(quantity_col)) else 1
                file_prefix  = Path(filename).stem.replace('-', '').replace('_', '').upper()[:3]
                title_prefix = row[column_mapping['title']].replace(' ', '-').replace("'", "").upper()[:10]
                sku          = f"{file_prefix}-{title_prefix}-{val}"
                variant_data = {
                    'title': val,
                    'option1': val,
                    'price': price_formatted,
                    'sku': sku,
                    'inventory_quantity': quantity,
                    'weight': Config.DEFAULT_WEIGHT,
                    'weight_unit': Config.DEFAULT_WEIGHT_UNIT,
                    'inventory_management': 'shopify',
                    'inventory_policy': Config.DEFAULT_INVENTORY_POLICY,
                    'requires_shipping': True,
                    'taxable': True
                }
                variants.append(variant_data)
        # If both option1 and option2 are present (cross product)
        elif option1_name and option1_values and option2_name and option2_values:
            for val1 in option1_values:
                for val2 in option2_values:
                    price_raw = clean_and_format_data(row.get(price_col) if price_col else '', '0')
                    try:
                        price_float = float(price_raw)
                    except ValueError:
                        price_float = 0.0
                    price_formatted = f"{price_float:.2f}"
                    quantity = int(row.get(quantity_col, 1)) if quantity_col and pd.notna(row.get(quantity_col)) else 1
                    file_prefix  = Path(filename).stem.replace('-', '').replace('_', '').upper()[:3]
                    title_prefix = row[column_mapping['title']].replace(' ', '-').replace("'", "").upper()[:10]
                    sku          = f"{file_prefix}-{title_prefix}-{val1}-{val2}"
                    variant_data = {
                        'title': f"{val1} / {val2}",
                        'option1': val1,
                        'option2': val2,
                        'price': price_formatted,
                        'sku': sku,
                        'inventory_quantity': quantity,
                        'weight': Config.DEFAULT_WEIGHT,
                        'weight_unit': Config.DEFAULT_WEIGHT_UNIT,
                        'inventory_management': 'shopify',
                        'inventory_policy': Config.DEFAULT_INVENTORY_POLICY,
                        'requires_shipping': True,
                        'taxable': True
                    }
                    variants.append(variant_data)
        else:
            # fallback to original logic
            variant_col  = column_mapping.get('variants')
            variant_size_raw = clean_and_format_data(row.get(variant_col) if variant_col else '', '50')
            variant_display  = f"{variant_size_raw}ml" if variant_size_raw.isdigit() else variant_size_raw
            quantity = int(row.get(quantity_col, 1)) if quantity_col and pd.notna(row.get(quantity_col)) else 1
            price_raw = clean_and_format_data(row.get(price_col) if price_col else '', '0')
            try:
                price_float = float(price_raw)
            except ValueError:
                price_float = 0.0
            price_formatted = f"{price_float:.2f}"
            file_prefix  = Path(filename).stem.replace('-', '').replace('_', '').upper()[:3]
            title_prefix = row[column_mapping['title']].replace(' ', '-').replace("'", "").upper()[:10]
            sku          = f"{file_prefix}-{title_prefix}-{variant_size_raw}"
            variant_data = {
                'title': variant_display,
                'option1': variant_display,
                'price': price_formatted,
                'sku': sku,
                'inventory_quantity': quantity,
                'weight': Config.DEFAULT_WEIGHT,
                'weight_unit': Config.DEFAULT_WEIGHT_UNIT,
                'inventory_management': 'shopify',
                'inventory_policy': Config.DEFAULT_INVENTORY_POLICY,
                'requires_shipping': True,
                'taxable': True
            }
            variants.append(variant_data)
        logger.info(f"🏷️ Created {len(variants)} variants for product {row[column_mapping['title']]}")
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

        # Handle (optional)
        handle = row.get('Handle')
        if not handle:
            # fallback: generate from title
            handle = title.lower().replace(' ', '-').replace("'", "")

        # Product Category (optional)
        product_category = row.get('Product Category')
        if not product_category:
            product_category = row.get(column_mapping.get('category')) if column_mapping.get('category') else ''

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

        # Options (dynamic, support multiple values)
        options = []
        option1_name = row.get('Option1 Name')
        option1_values = [v.strip() for v in str(row.get('Option1 Value', '')).split(',') if v.strip()]
        option2_name = row.get('Option2 Name')
        option2_values = [v.strip() for v in str(row.get('Option2 Value', '')).split(',') if v.strip()]
        if option1_name and option1_values:
            options.append({'name': option1_name, 'values': option1_values})
        if option2_name and option2_values:
            options.append({'name': option2_name, 'values': option2_values})

        product_data = {
            'title'       : title,
            'handle'      : handle,
            'body_html'   : description,
            'vendor'      : clean_and_format_data(row.get(column_mapping.get('vendor')) if column_mapping.get('vendor') else '', 'Default Vendor'),
            'product_type': clean_and_format_data(row.get(column_mapping.get('category')) if column_mapping.get('category') else '', 'General'),
            'product_category': product_category,
            'tags'        : tags,
            'status'      : 'draft',                # ← CREATED AS DRAFT
            'variants'    : variants,
            'images'      : images,
            'options'     : options
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
            for handle, group in df.groupby('Handle'):
                # Build variants from all rows in the group
                variants = []
                option1_name = None
                option1_values = set()
                option2_name = None
                option2_values = set()
                for _, row in group.iterrows():
                    # Use parse_variants_from_row to build variant dict for each row
                    v = self.parse_variants_from_row(row, column_mapping, filename)
                    if v:
                        variants.extend(v)
                    # Collect option values
                    if row.get('Option1 Name'):
                        option1_name = row.get('Option1 Name')
                        option1_values.add(str(row.get('Option1 Value')).strip())
                    if row.get('Option2 Name') and pd.notna(row.get('Option2 Value')):
                        option2_name = row.get('Option2 Name')
                        option2_values.add(str(row.get('Option2 Value')).strip())
                # Use the first row for shared product fields
                first_row = group.iloc[0]
                # Build options list
                options = []
                if option1_name and option1_values:
                    options.append({'name': option1_name, 'values': sorted(option1_values)})
                if option2_name and option2_values:
                    options.append({'name': option2_name, 'values': sorted(option2_values)})
                # Build product data
                product_data = self.prepare_product_data(first_row, column_mapping, filename)
                product_data['variants'] = variants
                product_data['options'] = options
                processed_products.append(product_data)

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
