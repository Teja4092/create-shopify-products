import logging
import time
from typing import List

import shopify
from config.settings import Config

logger = logging.getLogger(__name__)


class ShopifyImporter:
    """Create or update Shopify products from processed CSV data."""

    # ────────────────────  INIT  ───────────────────────────────
    def __init__(self):
        Config.validate_required_settings()

        # stats
        self.stats = {"created": 0, "updated": 0, "failed": 0}

        # open a session, trying a few API versions
        for api_ver in [Config.SHOPIFY_API_VERSION, "2024-01", "2023-07", "2023-04"]:
            try:
                self.session = shopify.Session(
                    Config.SHOPIFY_SHOP_DOMAIN, api_ver, Config.SHOPIFY_ACCESS_TOKEN
                )
                shopify.ShopifyResource.activate_session(self.session)
                logger.info(
                    f"✅ Connected to Shopify store: {Config.SHOPIFY_SHOP_DOMAIN} (API {api_ver})"
                )
                break
            except shopify.api_version.VersionNotFoundError:
                logger.warning(f"⚠️  API version {api_ver} not supported, trying next…")
        else:
            raise RuntimeError("Unable to establish Shopify API session")

    # ────────────────────  HELPERS  ────────────────────────────
    @staticmethod
    def _find_existing(title: str):
        try:
            products = shopify.Product.find(title=title, limit=1)
            return products[0] if products else None
        except Exception as exc:
            logger.error(f"❌ find_existing failed for “{title}”: {exc}")
            return None

    # ────────────────────  CREATE / UPDATE  ────────────────────
    def create_or_update(self, pdata: dict, src_file: str, delay: float = None):
        title = pdata["title"]
        existing = self._find_existing(title)
        action   = "updated" if existing else "created"
        product  = existing or shopify.Product()

        # basic fields
        for fld in ("title", "body_html", "vendor", "product_type", "tags"):
            setattr(product, fld, pdata.get(fld, ""))

        product.status = "draft"           # always draft

        # variants – overwrite
        product.variants = []
        for v_src in pdata["variants"]:
            v = shopify.Variant()
            v.price = f"{float(v_src['price']):.2f}"      # 2-decimal price
            for k in (
                "title", "sku", "inventory_quantity", "weight",
                "weight_unit", "inventory_management", "inventory_policy",
                "requires_shipping", "taxable"
            ):
                if k in v_src:
                    setattr(v, k, v_src[k])
            product.variants.append(v)

        # images – optional
        product.images = []
        for img_src in pdata.get("images", []):
            img = shopify.Image()
            img.src = img_src["src"]
            product.images.append(img)

        # save
        ok = product.save()
        time.sleep(delay or Config.DEFAULT_DELAY)

        if ok:
            self.stats[action] += 1
            logger.info(f"✅ {action.capitalize()} product: {title} (ID {product.id})")
        else:
            self.stats["failed"] += 1
            logger.error(f"❌ Failed to {action} {title}: {product.errors.full_messages()}")

    # ────────────────────  IMPORT LIST  ────────────────────────
    def import_products(self, processed: dict):
        fn = processed["filename"]
        logger.info(f"🚀 Importing {len(processed['products'])} products from {fn}")
        for pdata in processed["products"]:
            self.create_or_update(pdata, fn)

    # ────────────────────  SUMMARY  (NEW)  ─────────────────────
    def print_summary(self):
        logger.info("────────────────────────────────")
        logger.info("SHOPIFY IMPORT SUMMARY")
        for k in ("created", "updated", "failed"):
            logger.info(f"{k.capitalize():>8}: {self.stats[k]}")
        logger.info("────────────────────────────────")

    # ────────────────────  CLEAN-UP  ───────────────────────────
    def cleanup(self):
        shopify.ShopifyResource.clear_session()
        logger.info("✅ Shopify session closed")
