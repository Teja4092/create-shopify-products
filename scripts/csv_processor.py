def process_csv_file(self, csv_file_path):
    """Process a single CSV file and return processed data"""
    filename = Path(csv_file_path).name
    logger.info(f"🔄 Processing file: {filename}")
    
    try:
        # Read CSV file
        df = pd.read_csv(csv_file_path)
        logger.info(f"📊 Found {len(df)} rows in {filename}")
        
        # Filter out invalid rows (comments, empty titles, etc.)
        original_count = len(df)
        
        # Remove rows where TITLE starts with # or is empty/NaN
        df = df[df['TITLE'].notna()]  # Remove NaN titles
        df = df[~df['TITLE'].astype(str).str.startswith('#')]  # Remove comment lines
        df = df[df['TITLE'].astype(str).str.strip() != '']  # Remove empty titles
        
        filtered_count = len(df)
        if filtered_count < original_count:
            logger.info(f"🧹 Filtered out {original_count - filtered_count} invalid rows (comments/empty titles)")
        
        if filtered_count == 0:
            logger.warning(f"⚠️ No valid products found in {filename} after filtering")
            return None
        
        logger.info(f"📊 Processing {filtered_count} valid products from {filename}")
        
        # Detect CSV structure
        column_mapping = self.column_mapper.detect_csv_structure(df, filename)
        
        # Process products
        processed_products = []
        title_col = column_mapping['title']
        grouped = df.groupby(title_col)
        
        for title, group in grouped:
            try:
                # Skip if title is still invalid after filtering
                if not title or str(title).strip().startswith('#'):
                    logger.warning(f"⚠️ Skipping invalid title: {title}")
                    continue
                
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
