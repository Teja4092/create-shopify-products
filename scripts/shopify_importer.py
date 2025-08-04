import logging
import time
from typing import List

import shopify
from config.settings import Config

logger = logging.getLogger(__name__)


class ShopifyImporter:
    """Create or update Shopify products produced by the CSV processor."""

    # ─────────────────────────────  INIT  ──────────────────────────────
    def __init__(self):
        # make sure required env-vars exist
        Config.validate_required_settings()

        # stats used by summary & overall_results
        self.stats = {"created": 0, "updated": 0, "failed": 0}

        # open a session – try a few API versions until one works
        tried: List[str] = []
        for ver in [Config.SHOPIFY_API_VERSION, "2024-01", "2023-07", "2023-04"]:
            if not ver or ver in tried:
                continue
            tried.append(ver)
            try:
                self.session = shopify.Session(
                    Config.SHOPIFY_SHOP_DOMAIN,
                    ver,
                    Config.SHOPIFY_ACCESS_TOKEN,
                )
                shopify.ShopifyResource.activate_session(self.session)
                logger.info(
                    f"✅ Connected to Shopify store {Config.SHOPIFY_SHOP_DOMAIN} "
                    f"(API {ver})"
                )
                break
            except shopify.api_version.VersionNotFoundError:
                logger.warning(f"⚠️  API version {ver} not supported – trying next…")
        else:  # no break
            raise RuntimeError("Unable to establish Shopify API session")

    # ───────────────────────  compatibility for main.py  ──────────────
    @property
    def overall_results(self):
        """Expose the counters in the shape main.py already expects."""
        return {
            "successful": self.stats["created"] + self.stats["updated"],
            "failed": self.stats["failed"],
        }

    # ─────────────────────────  helpers  ───────────────────────────────
    @staticmethod
    def _find_existing(title: str):
        """Return first product whose title matches, else None."""
        try:
            found = shopify.Product.find(title=title, limit=1)
            return found[0] if found else None
        except Exception as exc:
            logger.error(f"❌ search failure for “{title}”: {exc}")
            return None

    # ───────────────────────  create or update  ────────────────────────
    def create_or_update(self, pdata: dict, src_file: str, delay: float = None):
        title = pdata["title"]
        product = self._find_existing(title)
        action = "updated" if product else "created"
        if not product:
            product = shopify.Product()

        # basic fields
        for fld in ("title", "body_html", "vendor", "product_type", "tags"):
            setattr(product, fld, pdata.get(fld, ""))

        # always leave in Draft
        product.status = "draft"

        # variants – overwrite everything
        product.variants = []
        for v_src in pdata["variants"]:
            v = shopify.Variant()
            v.price = f"{float(v_src['price']):.2f}"          # two-decimal price
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

        # save to Shopify
        if product.save():
            self.stats[action] += 1
            logger.info(
                f"✅ {action.capitalize()} product: {title} (ID {product.id}) "
                f"from {src_file}"
            )
        else:
            self.stats["failed"] += 1
            logger.error(
                f"❌ Failed to {action} {title}: {product.errors.full_messages()}"
            )

        time.sleep(delay or Config.DEFAULT_DELAY)   # respect rate limits

    # ─────────────────────────  batch import  ──────────────────────────
    def import_products(self, processed: dict):
        fn = processed["filename"]
        logger.info(f"🚀 Importing {len(processed['products'])} products from {fn}")
        for pdata in processed["products"]:
            self.create_or_update(pdata, fn)

    # ─────────────────────────  summary  ───────────────────────────────
    def print_summary(self):
        logger.info("────────────────────────────────")
        logger.info("SHOPIFY IMPORT SUMMARY")
        for key in ("created", "updated", "failed"):
            logger.info(f"{key.capitalize():>10}: {self.stats[key]}")
        logger.info("────────────────────────────────") 

    # ─────────────────────────  cleanup  ───────────────────────────────
    def cleanup(self):
        shopify.ShopifyResource.clear_session()
        logger.info("✅ Shopify session closed")
