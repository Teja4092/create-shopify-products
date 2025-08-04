"""
Configuration package for Shopify CSV Import

Contains settings and configuration management.
"""

from .settings import Config

__all__ = ['Config']

# Configuration validation on package import
try:
    Config.validate_required_settings()
    print("✅ Configuration validated successfully")
except ValueError as e:
    print(f"⚠️  Configuration warning: {e}")
    print("Make sure to set required environment variables before running the import.")
