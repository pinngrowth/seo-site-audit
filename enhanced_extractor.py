"""
Robust content extraction with multiple fallback strategies
Doesn't rely on proper HTML structure or semantic tags
"""

import re
import json
from urllib.parse import urlparse

class RobustExtractor:
    """Extract content even from poorly structured sites"""
    
    def __init__(self, page):
        self.page = page
        self.url = page.url
    
    def extract_all_content(self, profile_key="general"):
        """Main extraction method with comprehensive fallbacks"""
        
        data = {
            "url": self.url,
            
            # Basic metadata
            **self._extract_metadata(),
            
            # Title extraction (multiple strategies)
            **self._extract_titles(),
            
            # Description extraction
            **self._extract_descriptions(),
            
            # Heading extraction (all levels)
            **self._extract_headings(),
            
            # Content extraction
            **self._extract_main_content(),
            
            # Images (comprehensive)
            **self._extract_images(),
            
            # Links analysis
            **self._extract_links(),
            
            # Structured data
            **self._extract_structured_data(),
            
            # SEO-specific elements
            **self._extract_seo_elements(),
            
            # Profile-specific extraction
            **self._extract_profile_specific(profile_key),
        }
        
        return data
    
    def _extract_metadata(self):
        """Extract all meta tags"""
        meta_tags = {}
        
        try:
            metas = self.page.locator('meta').all()
            
            for meta in metas:
                name = meta.get_attribute('name') or meta.get_attribute('property') or meta.get_attribute('http-equiv')
                content = meta.get_attribute('content')
                
                if name and content:
                    meta_tags[f"meta_{name}"] = content
        except:
            pass
        
        return meta_tags
    
    def _extract_titles(self):
        """Extract title with multiple fallback strategies"""
        titles = {
            "title_tag": "",
            "og_title": "",
            "twitter_title": "",
            "h1_as_title": "",
            "largest_text_as_title": ""
        }
        
        try:
            titles["title_tag"] = self.page.title()
        except:
            pass
        
        try:
            titles["og_title"] = self.page.locator('meta[property="og:title"]').get_attribute('content') or ""
        except:
            pass
        
        try:
            titles["twitter_title"] = self.page.locator('meta[name="twitter:title"]').get_attribute('content') or ""
        except:
            pass
        
        try:
            h1s = self.page.locator('h1').all()
            if h1s:
                titles["h1_as_title"] = h1s[0].inner_text().strip()
        except:
            pass
        
        try:
            large_texts = self.page.evaluate('''() => {
                const elements = Array.from(document.querySelectorAll('header *, .header *, [class*="banner"] *'));
                return elements
                    .filter(el => el.textContent.trim().length > 10 && el.textContent.trim().length < 200)
                    .map(el => ({
                        text: el.textContent.trim(),
                        fontSize: window.getComputedStyle(el).fontSize
                    }))
                    .sort((a, b) => parseFloat(b.fontSize) - parseFloat(a.fontSize))
                    .slice(0, 1)
                    .map(item => item.text);
            }''')
            if large_texts:
                titles["largest_text_as_title"] = large_texts[0]
        except:
            pass
        
        titles["best_title"] = (
            titles["title_tag"] or 
            titles["og_title"] or 
            titles["h1_as_title"] or 
            titles["twitter_title"] or 
            titles["largest_text_as_title"] or 
            "NO TITLE FOUND"
        )
        
        return titles
    
    def _extract_descriptions(self):
        """Extract description with fallbacks"""
        descriptions = {
            "meta_description": "",
            "og_description": "",
            "first_paragraph": "",
            "twitter_description": ""
        }
        
        try:
            descriptions["meta_description"] = self.page.locator('meta[name="description"]').get_attribute('content') or ""
        except:
            pass
        
        try:
            descriptions["og_description"] = self.page.locator('meta[property="og:description"]').get_attribute('content') or ""
        except:
            pass
        
        try:
            descriptions["twitter_description"] = self.page.locator('meta[name="twitter:description"]').get_attribute('content') or ""
        except:
            pass
        
        try:
            paragraphs = self.page.locator('p').all()
            for p in paragraphs:
                text = p.inner_text().strip()
                if len(text) > 50 and len(text) < 500:
                    descriptions["first_paragraph"] = text
                    break
        except:
            pass
        
        descriptions["best_description"] = (
            descriptions["meta_description"] or 
            descriptions["og_description"] or 
            descriptions["first_paragraph"] or 
            descriptions["twitter_description"] or 
            "NO DESCRIPTION FOUND"
        )
        
        return descriptions
    
    def _extract_headings(self):
        """Extract ALL headings regardless of proper structure"""
        headings = {
            "h1_tags": [],
            "h2_tags": [],
            "h3_tags": [],
            "h4_tags": [],
            "h5_tags": [],
            "h6_tags": [],
            "heading_structure_issues": []
        }
        
        for level in range(1, 7):
            try:
                tags = self.page.locator(f'h{level}').all()
                headings[f"h{level}_tags"] = [h.inner_text().strip() for h in tags if h.inner_text().strip()]
            except:
                pass
        
        try:
            visual_headings = self.page.evaluate('''() => {
                const allElements = Array.from(document.querySelectorAll('*'));
                return allElements
                    .filter(el => {
                        const style = window.getComputedStyle(el);
                        const fontSize = parseFloat(style.fontSize);
                        const fontWeight = style.fontWeight;
                        const text = el.textContent.trim();
                        
                        return (
                            fontSize > 18 && 
                            (fontWeight === 'bold' || fontWeight === '700' || parseInt(fontWeight) >= 700) &&
                            text.length > 5 && 
                            text.length < 200 &&
                            !el.querySelector('*')
                        );
                    })
                    .map(el => el.textContent.trim())
                    .filter((v, i, a) => a.indexOf(v) === i);
            }''')
            headings["visual_headings"] = visual_headings
        except:
            headings["visual_headings"] = []
        
        if len(headings["h1_tags"]) == 0:
            headings["heading_structure_issues"].append("NO_H1")
        elif len(headings["h1_tags"]) > 1:
            headings["heading_structure_issues"].append("MULTIPLE_H1")
        
        return headings
    
    def _extract_main_content(self):
        """Extract main content using multiple strategies"""
        content = {
            "main_text": "",
            "word_count": 0,
            "paragraph_count": 0,
            "all_text_blocks": [],
            "content_location": ""
        }
        
        try:
            main = self.page.locator('main, article, [role="main"]').first
            content["main_text"] = main.inner_text().strip()
            content["content_location"] = "semantic_main"
        except:
            pass
        
        if not content["main_text"]:
            selectors = [
                '.content', '#content', '[class*="content"]',
                '.post', '[class*="post"]',
                '.entry', '[class*="entry"]',
                '.article', '[class*="article"]',
                'body'
            ]
            
            for selector in selectors:
                try:
                    element = self.page.locator(selector).first
                    text = element.inner_text().strip()
                    if len(text) > 100:
                        content["main_text"] = text
                        content["content_location"] = selector
                        break
                except:
                    continue
        
        if not content["main_text"]:
            try:
                text_blocks = self.page.evaluate('''() => {
                    const blocks = Array.from(document.querySelectorAll('div, section, article'));
                    return blocks
                        .map(block => ({
                            text: block.innerText || '',
                            length: (block.innerText || '').length,
                            selector: block.className || block.id || block.tagName
                        }))
                        .filter(b => b.length > 200)
                        .sort((a, b) => b.length - a.length)
                        .slice(0, 5);
                }''')
                
                if text_blocks:
                    content["main_text"] = text_blocks[0]["text"]
                    content["content_location"] = "largest_block"
            except:
                pass
        
        try:
            paragraphs = self.page.locator('p').all()
            content["paragraph_count"] = len(paragraphs)
            content["all_text_blocks"] = [p.inner_text().strip() for p in paragraphs if len(p.inner_text().strip()) > 20]
        except:
            pass
        
        if content["main_text"]:
            content["word_count"] = len(content["main_text"].split())
        
        content["has_thin_content"] = content["word_count"] < 300
        content["has_good_content"] = 300 <= content["word_count"] < 2000
        content["has_long_content"] = content["word_count"] >= 2000
        
        return content
    
    def _extract_images(self):
        """Comprehensive image extraction and analysis"""
        images_data = {
            "total_images": 0,
            "images_without_alt": 0,
            "images_with_empty_alt": 0,
            "images_with_good_alt": 0,
            "images_details": [],
            "background_images": []
        }
        
        try:
            imgs = self.page.locator('img').all()
            images_data["total_images"] = len(imgs)
            
            for img in imgs:
                src = img.get_attribute('src') or img.get_attribute('data-src') or img.get_attribute('data-lazy-src')
                alt = img.get_attribute('alt')
                title = img.get_attribute('title')
                width = img.get_attribute('width')
                height = img.get_attribute('height')
                
                img_info = {
                    "src": src,
                    "alt": alt or "",
                    "title": title or "",
                    "width": width,
                    "height": height,
                    "has_alt": alt is not None,
                    "alt_quality": "good" if (alt and len(alt) > 5) else ("empty" if alt == "" else "missing")
                }
                
                images_data["images_details"].append(img_info)
                
                if alt is None:
                    images_data["images_without_alt"] += 1
                elif alt == "":
                    images_data["images_with_empty_alt"] += 1
                elif len(alt) > 5:
                    images_data["images_with_good_alt"] += 1
        except:
            pass
        
        try:
            bg_images = self.page.evaluate('''() => {
                const elements = Array.from(document.querySelectorAll('*'));
                return elements
                    .map(el => {
                        const style = window.getComputedStyle(el);
                        const bgImage = style.backgroundImage;
                        if (bgImage && bgImage !== 'none') {
                            return bgImage;
                        }
                        return null;
                    })
                    .filter(bg => bg !== null);
            }''')
            images_data["background_images"] = bg_images
        except:
            pass
        
        return images_data
    
    def _extract_links(self):
        """Analyze all links"""
        links_data = {
            "total_links": 0,
            "internal_links": 0,
            "external_links": 0,
            "broken_anchor_links": 0,
            "links_without_text": 0,
            "nofollow_links": 0
        }
        
        try:
            domain = urlparse(self.url).netloc
            links = self.page.locator('a').all()
            links_data["total_links"] = len(links)
            
            for link in links:
                href = link.get_attribute('href')
                text = link.inner_text().strip()
                rel = link.get_attribute('rel') or ""
                
                if not href:
                    continue
                
                if href.startswith('/') or domain in href:
                    links_data["internal_links"] += 1
                elif href.startswith('http'):
                    links_data["external_links"] += 1
                
                if href == '#' or href.startswith('#'):
                    links_data["broken_anchor_links"] += 1
                
                if not text:
                    links_data["links_without_text"] += 1
                
                if 'nofollow' in rel:
                    links_data["nofollow_links"] += 1
        except:
            pass
        
        return links_data
    
    def _extract_structured_data(self):
        """Extract all schema.org and structured data"""
        structured = {
            "has_schema": False,
            "schema_types": [],
            "schema_data": [],
            "json_ld_count": 0
        }
        
        try:
            scripts = self.page.locator('script[type="application/ld+json"]').all()
            structured["json_ld_count"] = len(scripts)
            
            for script in scripts:
                try:
                    text = script.inner_text()
                    data = json.loads(text) if text else {}
                    
                    schemas = data if isinstance(data, list) else [data]
                    
                    for schema in schemas:
                        if isinstance(schema, dict) and '@type' in schema:
                            schema_type = schema['@type']
                            structured["schema_types"].append(schema_type)
                            structured["schema_data"].append(schema)
                except:
                    continue
            
            structured["has_schema"] = len(structured["schema_types"]) > 0
        except:
            pass
        
        try:
            microdata = self.page.locator('[itemscope]').count()
            structured["microdata_count"] = microdata
        except:
            structured["microdata_count"] = 0
        
        return structured
    
    def _extract_seo_elements(self):
        """Extract SEO-specific elements"""
        seo = {
            "canonical_url": "",
            "robots_meta": "",
            "has_sitemap_link": False,
            "has_robots_txt": False,
            "hreflang_tags": [],
            "og_tags": {},
            "twitter_tags": {}
        }
        
        try:
            canonical = self.page.locator('link[rel="canonical"]').get_attribute('href')
            seo["canonical_url"] = canonical or ""
        except:
            pass
        
        try:
            robots = self.page.locator('meta[name="robots"]').get_attribute('content')
            seo["robots_meta"] = robots or ""
        except:
            pass
        
        try:
            hreflangs = self.page.locator('link[rel="alternate"][hreflang]').all()
            seo["hreflang_tags"] = [
                {
                    "hreflang": link.get_attribute('hreflang'),
                    "href": link.get_attribute('href')
                }
                for link in hreflangs
            ]
        except:
            pass
        
        try:
            og_tags = self.page.locator('meta[property^="og:"]').all()
            for tag in og_tags:
                prop = tag.get_attribute('property')
                content = tag.get_attribute('content')
                if prop and content:
                    seo["og_tags"][prop] = content
        except:
            pass
        
        try:
            twitter_tags = self.page.locator('meta[name^="twitter:"]').all()
            for tag in twitter_tags:
                name = tag.get_attribute('name')
                content = tag.get_attribute('content')
                if name and content:
                    seo["twitter_tags"][name] = content
        except:
            pass
        
        return seo
    
    def _extract_profile_specific(self, profile_key):
        """Extract profile-specific data"""
        from extraction_profiles import PROFILES
        
        if profile_key not in PROFILES or profile_key == "general":
            return {}
        
        profile = PROFILES[profile_key]
        extracted = {}
        
        for field, selectors in profile.get("selectors", {}).items():
            if isinstance(selectors, list):
                values = []
                for selector in selectors:
                    try:
                        elements = self.page.locator(selector).all()
                        for el in elements:
                            text = el.inner_text().strip()
                            if text and text not in values:
                                values.append(text)
                    except:
                        continue
                extracted[f"profile_{field}"] = values[:10]
            elif isinstance(selectors, dict):
                extracted[f"profile_{field}"] = {}
        
        return extracted


def enhanced_crawl_with_extraction(start_url, max_pages, profile_key, delay_min, delay_max, progress_bar, status_text):
    """Crawl using enhanced extractor"""
    from playwright.sync_api import sync_playwright
    from playwright_stealth import stealth_sync
    import random
    import time
    
    results = []
    visited = set()
    to_visit = [start_url]
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled', '--no-sandbox']
        )
        
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        
        page = context.new_page()
        stealth_sync(page)
        
        while to_visit and len(visited) < max_pages:
            url = to_visit.pop(0)
            
            if url in visited:
                continue
            
            try:
                status_text.text(f"Crawling {len(visited)+1}/{max_pages}: {url[:50]}...")
                progress_bar.progress(len(visited) / max_pages)
                
                time.sleep(random.uniform(delay_min, delay_max))
                
                page.goto(url, wait_until='networkidle', timeout=30000)
                page.evaluate('window.scrollTo(0, document.body.scrollHeight/2)')
                time.sleep(random.uniform(0.5, 1))
                
                visited.add(url)
                
                extractor = RobustExtractor(page)
                data = extractor.extract_all_content(profile_key)
                
                results.append(data)
                
                links = page.locator('a[href]').all()
                for link in links[:30]:
                    href = link.get_attribute('href')
                    if href:
                        try:
                            full_url = page.evaluate(f'new URL("{href}", "{url}").href')
                            if start_url.split('/')[2] in full_url and full_url not in visited:
                                to_visit.append(full_url)
                        except:
                            pass
                
            except Exception as e:
                print(f"Error on {url}: {e}")
                continue
        
        browser.close()
    
    return results
