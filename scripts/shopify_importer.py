import logging
import time
from typing import List

import shopify
from config.settings import Config

logger = logging.getLogger(__name__)


class ShopifyImporter:
    """Create or update Shopify products from processed CSV data."""

    # ────────────────────────────────────────────────────────────
    #  INITIALISE – open session (handles multiple API versions)
    # ────────────────────────────────────────────────────────────
    def __init__(self):
        Config.validate_required_settings()

        tried: List[str] = []
        for api_ver in [Config.SHOPIFY_API_VERSION, "2024-01", "2023-07", "2023-04"]:
            if not api_ver or api_ver in tried:
                continue
            tried.append(api_ver)
            try:
                self.session = shopify.Session(
                    Config.SHOPIFY_SHOP_DOMAIN, api_ver, Config.SHOPIFY_ACCESS_TOKEN
                )
                shopify.ShopifyResource.activate_session(self.session)
                logger.info(f"✅ Connected to Shopify store: {Config.SHOPIFY_SHOP_DOMAIN} (API {api_ver})")
                break
            except shopify.api_version.VersionNotFoundError:
                logger.warning(f"⚠️  API version {api_ver} not supported, trying next…")
        else:  # no break
            raise RuntimeError("Unable to establish Shopify session with any API version")

        self.stats = {
            "created": 0,
            "updated": 0,
            "failed":  0,
        }

    # ────────────────────────────────────────────────────────────
    #  FIND EXISTING PRODUCT
    # ────────────────────────────────────────────────────────────
    @staticmethod
    def _find_existing(title: str):
        try:
            products = shopify.Product.find(title=title, limit=1)
            return products[0] if products else None
        except Exception as exc:
            logger.error(f"❌ find_existing failed for “{title}”: {exc}")
            return None

    # ────────────────────────────────────────────────────────────
    #  CREATE OR UPDATE ONE PRODUCT
    # ────────────────────────────────────────────────────────────
    def create_or_update(self, product_data: dict, src_file: str, delay: float = None):
        title = product_data["title"]
        existing = self._find_existing(title)
        action   = "updated" if existing else "created"
        product  = existing or shopify.Product()

        # ─── basic fields ───────────────────────────────────────
        for field in ("title", "body_html", "vendor", "product_type", "tags"):
            setattr(product, field, product_data.get(field, ""))

        # draft status always
        product.status = "draft"

        # ─── variants (overwrite) ───────────────────────────────
        product.variants = []  # clear
        for v_src in product_data["variants"]:
            v = shopify.Variant()
            # price as string “100.00”
            v.price = f"{float(v_src['price']):.2f}"
            for key in (
                "title", "sku", "inventory_quantity", "weight",
                "weight_unit", "inventory_management", "inventory_policy",
                "requires_shipping", "taxable"
            ):
                if key in v_src:
                    setattr(v, key, v_src[key])
            product.variants.append(v)

        # ─── images (optional) ─────────────────────────────────
        product.images = []
        for img in product_data.get("images", []):
            image = shopify.Image()
            image.src = img["src"]
            product.images.append(image)

        # ─── save ───────────────────────────────────────────────
        success = product.save()
        time.sleep(delay or Config.DEFAULT_DELAY)

        if success:
            self.stats[action] += 1
            logger.info(
                f"✅ {action.capitalize()} product: {title} "
                f"(ID {product.id}) from {src_file}"
            )
            return True
        else:
            self.stats["failed"] += 1
            logger.error(
                f"❌ Failed to {action} {title}: {product.errors.full_messages()}"
            )
            return False

    # ────────────────────────────────────────────────────────────
    #  IMPORT WHOLE CSV (processed)
    # ────────────────────────────────────────────────────────────
    def import_products(self, processed_data: dict):
        filename = processed_data["filename"]
        logger.info(f"🚀 Importing {len(processed_data['products'])} products from {filename}")

        for pdata in processed_data["products"]:
            self.create_or_update(pdata, filename)

    # ────────────────────────────────────────────────────────────
    #  SUMMARY & CLEAN-UP
    # ────────────────────────────────────────────────────────────
    def summary(self):
        logger.info("────────────────────────────────────")
        logger.info("SHOPIFY IMPORT SUMMARY")
        for key, val in self.stats.items():
            logger.info(f"{key.capitalize():>8}: {val}")
        logger.info("────────────────────────────────────")

    def cleanup(self):
        shopify.ShopifyResource.clear_session()
        logger.info("✅ Shopify session closed")
