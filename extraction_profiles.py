"""
Define different extraction rules for different industries
"""

PROFILES = {
    "ecommerce": {
        "name": "E-commerce",
        "description": "Extracts product prices, SKUs, inventory, reviews",
        "selectors": {
            "price": [
                '[class*="price"]',
                '[id*="price"]',
                '[data-testid*="price"]',
                '.product-price',
                'span[itemprop="price"]'
            ],
            "product_name": [
                'h1[class*="product"]',
                '[itemprop="name"]',
                '.product-title'
            ],
            "sku": [
                '[class*="sku"]',
                '[data-sku]',
                'span[itemprop="sku"]'
            ],
            "availability": [
                '[class*="stock"]',
                '[itemprop="availability"]',
                '.availability'
            ],
            "reviews": [
                '[class*="review"]',
                '[itemprop="ratingValue"]',
                '.rating'
            ],
            "images": {
                "product_images": '[class*="product"] img, .gallery img',
                "check_alt": True,
                "check_size": True
            }
        },
        "schema_types": ["Product", "Offer", "AggregateRating"]
    },
    
    "b2b": {
        "name": "B2B / SaaS",
        "description": "Extracts CTAs, forms, case studies, features",
        "selectors": {
            "cta_buttons": [
                'a[href*="contact"]',
                'a[href*="demo"]',
                'button[class*="cta"]',
                '.btn-primary'
            ],
            "forms": [
                'form[class*="contact"]',
                'form[class*="lead"]',
                'input[type="email"]'
            ],
            "case_studies": [
                '[class*="case-study"]',
                '[class*="testimonial"]',
                '.customer-story'
            ],
            "features": [
                '[class*="feature"]',
                '.benefits li',
                '[class*="capability"]'
            ],
            "pricing": [
                '[class*="price"]',
                '[class*="plan"]',
                '.pricing-tier'
            ]
        },
        "schema_types": ["Organization", "Service", "FAQPage"]
    },
    
    "blog_content": {
        "name": "Blog / Content Site",
        "description": "Extracts articles, authors, dates, categories",
        "selectors": {
            "article_body": [
                'article',
                '[class*="content"]',
                '.post-content',
                'main'
            ],
            "author": [
                '[class*="author"]',
                '[rel="author"]',
                'span[itemprop="author"]'
            ],
            "publish_date": [
                'time[datetime]',
                '[class*="date"]',
                'meta[property="article:published_time"]'
            ],
            "categories": [
                '[class*="category"]',
                '[class*="tag"]',
                '.taxonomy'
            ],
            "reading_time": [
                '[class*="reading-time"]',
                '[class*="read-time"]'
            ]
        },
        "schema_types": ["Article", "BlogPosting", "NewsArticle"]
    },
    
    "local_business": {
        "name": "Local Business",
        "description": "Extracts NAP, hours, services, locations",
        "selectors": {
            "business_name": [
                'h1',
                '[itemprop="name"]',
                '.business-name'
            ],
            "address": [
                '[class*="address"]',
                '[itemprop="address"]',
                '.location'
            ],
            "phone": [
                'a[href^="tel:"]',
                '[class*="phone"]',
                '[itemprop="telephone"]'
            ],
            "hours": [
                '[class*="hours"]',
                '[itemprop="openingHours"]',
                '.business-hours'
            ],
            "services": [
                '[class*="service"]',
                'ul.services li',
                '.offerings'
            ]
        },
        "schema_types": ["LocalBusiness", "Service", "OpeningHoursSpecification"]
    },
    
    "general": {
        "name": "General SEO Audit",
        "description": "Standard SEO elements only",
        "selectors": {
            "basic_content": True
        },
        "schema_types": []
    }
}

def get_profile_choices():
    """Return list of profile names for dropdown"""
    return {key: profile["name"] for key, profile in PROFILES.items()}
