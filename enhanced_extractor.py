"""
Robust content extraction with Selenium (Streamlit Cloud compatible)
Doesn't rely on proper HTML structure or semantic tags
"""

import re
import json
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

class RobustExtractor:
    """Extract content even from poorly structured sites"""
    
    def __init__(self, driver):
        self.driver = driver
        self.url = driver.current_url
    
    def extract_all_content(self, profile_key="general"):
        """Main extraction method with comprehensive fallbacks"""
        
        data = {
            "url": self.url,
            "title": self.driver.title,
            "meta_description": self._get_meta_content("description"),
            "meta_keywords": self._get_meta_content("keywords"),
            "canonical_url": self._get_link_href("canonical"),
            "og_title": self._get_meta_property("og:title"),
            "og_description": self._get_meta_property("og:description"),
            "h1_tags": self._get_headings("h1"),
            "h2_tags": self._get_headings("h2"),
            "h3_tags": self._get_headings("h3"),
            "word_count": len(self._get_body_text().split()),
            "total_images": len(self.driver.find_elements(By.TAG_NAME, "img")),
            "images_without_alt": self._count_images_without_alt(),
            "internal_links": self._count_internal_links(),
            "external_links": self._count_external_links(),
        }
        
        # Profile-specific extraction
        if profile_key != "general":
            data.update(self._extract_profile_specific(profile_key))
        
        return data
    
    def _get_meta_content(self, name):
        """Get meta tag content by name"""
        try:
            element = self.driver.find_element(By.CSS_SELECTOR, f'meta[name="{name}"]')
            return element.get_attribute("content") or ""
        except:
            return ""
    
    def _get_meta_property(self, property_name):
        """Get meta tag content by property"""
        try:
            element = self.driver.find_element(By.CSS_SELECTOR, f'meta[property="{property_name}"]')
            return element.get_attribute("content") or ""
        except:
            return ""
    
    def _get_link_href(self, rel):
        """Get link href by rel attribute"""
        try:
            element = self.driver.find_element(By.CSS_SELECTOR, f'link[rel="{rel}"]')
            return element.get_attribute("href") or ""
        except:
            return ""
    
    def _get_headings(self, tag):
        """Get all headings of specified tag"""
        try:
            elements = self.driver.find_elements(By.TAG_NAME, tag)
            return [el.text.strip() for el in elements if el.text.strip()]
        except:
            return []
    
    def _get_body_text(self):
        """Get all body text"""
        try:
            body = self.driver.find_element(By.TAG_NAME, "body")
            return body.text
        except:
            return ""
    
    def _count_images_without_alt(self):
        """Count images without alt text"""
        try:
            images = self.driver.find_elements(By.TAG_NAME, "img")
            count = 0
            for img in images:
                alt = img.get_attribute("alt")
                if not alt:
                    count += 1
            return count
        except:
            return 0
    
    def _count_internal_links(self):
        """Count internal links"""
        try:
            domain = urlparse(self.url).netloc
            links = self.driver.find_elements(By.TAG_NAME, "a")
            count = 0
            for link in links:
                href = link.get_attribute("href")
                if href and (href.startswith("/") or domain in href):
                    count += 1
            return count
        except:
            return 0
    
    def _count_external_links(self):
        """Count external links"""
        try:
            domain = urlparse(self.url).netloc
            links = self.driver.find_elements(By.TAG_NAME, "a")
            count = 0
            for link in links:
                href = link.get_attribute("href")
                if href and href.startswith("http") and domain not in href:
                    count += 1
            return count
        except:
            return 0
    
    def _extract_profile_specific(self, profile_key):
        """Extract profile-specific data"""
        from extraction_profiles import PROFILES
        
        if profile_key not in PROFILES:
            return {}
        
        profile = PROFILES[profile_key]
        extracted = {}
        
        for field, selectors in profile.get("selectors", {}).items():
            if isinstance(selectors, list):
                values = []
                for selector in selectors:
                    try:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for el in elements[:5]:  # Limit to 5
                            text = el.text.strip()
                            if text and text not in values:
                                values.append(text)
                    except:
                        continue
                extracted[f"profile_{field}"] = values
        
        return extracted


def enhanced_crawl_with_extraction(start_url, max_pages, profile_key, delay_min, delay_max, progress_bar, status_text):
    """Crawl using Selenium"""
    import time
    import random
    import undetected_chromedriver as uc
    
    results = []
    visited = set()
    to_visit = [start_url]
    
    # Setup Chrome options
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-blink-features=AutomationControlled')
    
    # Use undetected chromedriver
    driver = uc.Chrome(options=options, version_main=None, use_subprocess=False)
    
    try:
        while to_visit and len(visited) < max_pages:
            url = to_visit.pop(0)
            
            if url in visited:
                continue
            
            try:
                status_text.text(f"Crawling {len(visited)+1}/{max_pages}: {url[:50]}...")
                progress_bar.progress(len(visited) / max_pages)
                
                time.sleep(random.uniform(delay_min, delay_max))
                
                driver.get(url)
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # Scroll page
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2)")
                time.sleep(random.uniform(0.5, 1))
                
                visited.add(url)
                
                # Extract data
                extractor = RobustExtractor(driver)
                data = extractor.extract_all_content(profile_key)
                results.append(data)
                
                # Find more links
                try:
                    links = driver.find_elements(By.TAG_NAME, "a")
                    for link in links[:30]:
                        href = link.get_attribute("href")
                        if href and start_url.split('/')[2] in href and href not in visited:
                            to_visit.append(href)
                except:
                    pass
                
            except Exception as e:
                print(f"Error on {url}: {e}")
                continue
    
    finally:
        driver.quit()
    
    return results
