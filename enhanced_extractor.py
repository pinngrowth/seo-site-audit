"""
Robust content extraction using Selenium with system Chrome
"""

import json
import time
import random
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup

class RobustExtractor:
    """Extract content from HTML"""
    
    def __init__(self, html, url):
        self.soup = BeautifulSoup(html, 'lxml')
        self.url = url
    
    def extract_all_content(self, profile_key="general"):
        """Main extraction method"""
        
        data = {
            "url": self.url,
            "title": self._get_title(),
            "meta_description": self._get_meta("description"),
            "meta_keywords": self._get_meta("keywords"),
            "canonical_url": self._get_canonical(),
            "h1_tags": self._get_headings("h1"),
            "h2_tags": self._get_headings("h2"),
            "h3_tags": self._get_headings("h3"),
            "word_count": len(self._get_text().split()),
            "total_images": len(self.soup.find_all("img")),
            "images_without_alt": self._count_no_alt(),
        }
        
        return data
    
    def _get_title(self):
        tag = self.soup.find("title")
        return tag.get_text().strip() if tag else ""
    
    def _get_meta(self, name):
        tag = self.soup.find("meta", attrs={"name": name})
        return tag.get("content", "") if tag else ""
    
    def _get_canonical(self):
        tag = self.soup.find("link", attrs={"rel": "canonical"})
        return tag.get("href", "") if tag else ""
    
    def _get_headings(self, tag_name):
        tags = self.soup.find_all(tag_name)
        return [tag.get_text().strip() for tag in tags if tag.get_text().strip()]
    
    def _get_text(self):
        return self.soup.get_text()
    
    def _count_no_alt(self):
        imgs = self.soup.find_all("img")
        return sum(1 for img in imgs if not img.get("alt"))


def enhanced_crawl_with_extraction(start_url, max_pages, profile_key, delay_min, delay_max, progress_bar, status_text):
    """Crawl using Selenium with system Chrome"""
    
    results = []
    visited = set()
    to_visit = [start_url]
    
    # Chrome options
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.binary_location = '/usr/bin/chromium'
    
    service = Service('/usr/bin/chromedriver')
    driver = webdriver.Chrome(service=service, options=options)
    
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
                time.sleep(2)
                
                visited.add(url)
                
                # Extract data
                html = driver.page_source
                extractor = RobustExtractor(html, url)
                data = extractor.extract_all_content(profile_key)
                results.append(data)
                
                # Find links
                try:
                    links = driver.find_elements(By.TAG_NAME, "a")
                    for link in links[:30]:
                        href = link.get_attribute("href")
                        if href and start_url.split('/')[2] in href and href not in visited:
                            to_visit.append(href)
                except:
                    pass
                
            except Exception as e:
                print(f"Error: {e}")
                continue
    
    finally:
        driver.quit()
    
    return results
