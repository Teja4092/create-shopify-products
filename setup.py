from setuptools import setup, find_packages

setup(
    name="shopify-csv-importer",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "ShopifyAPI==12.0.0",
        "pandas==2.0.3", 
        "python-dotenv==1.0.0",
        "pathlib2==2.3.7",
        "requests==2.31.0"
    ],
    python_requires=">=3.8",
    author="Your Team",
    description="Modular Shopify CSV Product Import System",
    entry_points={
        'console_scripts': [
            'shopify-import=main:main',
        ],
    },
)
