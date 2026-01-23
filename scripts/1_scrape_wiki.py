"""Скрипт 1: Парсинг South Park Wiki"""

from bs4 import BeautifulSoup
import requests
import time
import re
import json
from html import unescape
from pathlib import Path
from urllib.parse import unquote

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}
DELAY_SECONDS = 3.5
DATA_DIR = Path(__file__).parent.parent / 'data'
RAW_DIR = DATA_DIR / 'raw'


def clean_text(text):
    if not text:
        return ""
    text = unescape(text)
    text = re.sub(r'\[\d+\]', '', text)
    text = re.sub(r'\[edit\]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def determine_category(url):
    slug = url.split('/')[-1].lower()

    character_patterns = [
        '_marsh', '_cartman', '_mccormick', '_broflovski', '_stotch',
        '_stevens', '_thompson', '_tucker', '_turner', '_garrison',
        '_jenner', '_clinton', '_kern', '_schwartz', '_meyers',
        '_black', '_kim', '_testaburger', '_tweak', '_barbrady',
        '_hilton', '_victoria', 'buddha', 'god', 'jesus', 'santa',
        'mickey_mouse', 'indiana_jones', 'bart_simpson', 'michael',
        'jambu', 'chef', 'mr._hat', 'mr._slave', 'pc_principal',
        'captain_hindsight'
    ]

    for pattern in character_patterns:
        if pattern in slug:
            return 'character'

    location_patterns = [
        'location', 'residence', 'elementary', 'stark', 'bus_stop',
        'main_street', 'playground', 'hospital', 'community_center',
        'church', 'city_wok', 'tegridy_farms'
    ]

    for pattern in location_patterns:
        if pattern in slug:
            return 'location'

    return 'event'


def scrape_page(url):
    print(f"Scraping: {url}")

    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"  [ERROR] {e}")
        return None

    soup = BeautifulSoup(response.content, 'lxml')

    title_elem = soup.select_one('h1.page-header__title') or soup.select_one('h1')
    title = clean_text(title_elem.get_text(strip=True)) if title_elem else "Unknown"

    content = (soup.select_one('.mw-parser-output') or
               soup.select_one('#mw-content-text .mw-parser-output') or
               soup.select_one('#mw-content-text') or
               soup.select_one('.page-content') or
               soup.select_one('article'))

    if not content:
        print(f"  [ERROR] No content found")
        return None

    infobox = {}
    infobox_elem = content.select_one('.portable-infobox')
    if infobox_elem:
        for dt, dd in zip(infobox_elem.select('dt'), infobox_elem.select('dd')):
            key = clean_text(dt.get_text(strip=True))
            value = clean_text(dd.get_text(strip=True))
            if key and value:
                infobox[key] = value

    sections = {}
    current_section = None

    for elem in content.find_all(['h2', 'h3', 'p', 'ul', 'ol']):
        if elem.name in ['h2', 'h3']:
            text = clean_text(elem.get_text(strip=True))
            if text.lower() in ['references', 'external links', 'see also', 'navigation', 'gallery', 'videos']:
                current_section = None
                continue
            current_section = text
            if current_section not in sections:
                sections[current_section] = []
        elif current_section and elem.name in ['p', 'ul', 'ol']:
            para_text = clean_text(elem.get_text(strip=True))
            if para_text and len(para_text) > 10:
                sections[current_section].append(para_text)

    full_text_parts = []
    for section, paragraphs in sections.items():
        full_text_parts.append(f"## {section}\n")
        full_text_parts.append('\n\n'.join(paragraphs))
        full_text_parts.append('\n\n')

    full_text = ''.join(full_text_parts).strip()
    category = determine_category(url)

    print(f"  [OK] {title} ({category}), {len(full_text)} chars")

    return {
        'url': url,
        'title': title,
        'category': category,
        'infobox': infobox,
        'sections': sections,
        'full_text': full_text
    }


def main():
    urls_file = DATA_DIR / 'urls.txt'
    if not urls_file.exists():
        print(f"[ERROR] File not found: {urls_file}")
        return

    with open(urls_file, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip()]

    print(f"[*] Found {len(urls)} URLs\n")

    for category in ['character', 'location', 'event']:
        (RAW_DIR / category).mkdir(parents=True, exist_ok=True)

    success_count = 0
    failed_urls = []

    for i, url in enumerate(urls, 1):
        print(f"\n[{i}/{len(urls)}]")
        result = scrape_page(url)

        if result:
            slug = url.split('/')[-1]
            safe_slug = unquote(slug).replace('%', '_').replace('?', '_').replace('"', '').replace('<', '').replace('>', '').replace('|', '').replace('*', '').replace(':', '')
            output_path = RAW_DIR / result['category'] / f"{safe_slug}.json"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            success_count += 1
        else:
            failed_urls.append(url)

        if i < len(urls):
            print(f"  [WAIT] {DELAY_SECONDS}s...")
            time.sleep(DELAY_SECONDS)

    print(f"\n[SUCCESS] Scraped: {success_count}/{len(urls)}")
    if failed_urls:
        print(f"[ERROR] Failed: {len(failed_urls)}")
    print(f"[*] Results: {RAW_DIR}")


if __name__ == "__main__":
    main()
