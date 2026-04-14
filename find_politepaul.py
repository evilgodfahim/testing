import requests
import xml.etree.ElementTree as ET
from urllib.parse import urlparse

FEEDS = [
    "https://evilgodfahim.github.io/edit/daily_feed.xml",
    "https://evilgodfahim.github.io/bdit/daily_feed.xml",
    "https://evilgodfahim.github.io/bdit/daily_feed_2.xml",
]

KEYWORD = "politepaul"

def fetch_feed(url):
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"[WARN] Failed to fetch {url}: {e}")
        return None

def extract_text(element):
    """Get all text recursively, handles HTML nested inside description."""
    parts = []
    for node in element.iter():
        if node.text:
            parts.append(node.text)
        if node.tail:
            parts.append(node.tail)
    return " ".join(parts).strip()

def base_link(url):
    """Return scheme + netloc only, e.g. https://example.com"""
    p = urlparse(url)
    if not p.scheme or not p.netloc:
        return None
    return f"{p.scheme}://{p.netloc}"

def parse_items(xml_text, feed_url):
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        print(f"[WARN] XML parse error for {feed_url}: {e}")
        return []

    ns = {"atom": "http://www.w3.org/2005/Atom"}
    items = root.findall(".//item")
    if not items:
        items = root.findall(".//atom:entry", ns)

    results = []
    for item in items:
        desc_el = item.find("description")
        if desc_el is None:
            desc_el = item.find("atom:summary", ns)
        if desc_el is None:
            desc_el = item.find("atom:content", ns)
        desc = extract_text(desc_el) if desc_el is not None else ""

        link_el = item.find("link")
        if link_el is not None:
            link = extract_text(link_el) or link_el.get("href", "")
        else:
            atom_link = item.find("atom:link", ns)
            link = atom_link.get("href", "") if atom_link is not None else ""

        results.append({"link": link.strip(), "description": desc})

    return results

def main():
    seen_bases = set()
    matches = []

    for feed_url in FEEDS:
        print(f"Fetching: {feed_url}")
        xml_text = fetch_feed(feed_url)
        if not xml_text:
            continue

        items = parse_items(xml_text, feed_url)
        print(f"  → {len(items)} items found")

        for item in items:
            link = item["link"]
            desc = item["description"]

            base = base_link(link)
            if not base:
                continue

            # Deduplication by base link
            if base in seen_bases:
                continue
            seen_bases.add(base)

            if KEYWORD.lower() in desc.lower():
                matches.append(base)

    print(f"\n{'='*60}")
    if matches:
        print(f"Found {len(matches)} unique source(s) mentioning '{KEYWORD}':\n")
        for link in matches:
            print(f"  {link}")
    else:
        print(f"No sources found mentioning '{KEYWORD}'.")

if __name__ == "__main__":
    main()
