import json
import xml.etree.ElementTree as ET
import urllib.parse
import urllib.request
from datetime import datetime

DATA_FILE = "data.json"

try:
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        db = json.load(f)
except Exception:
    db = {"ministers": [], "signals": []}

REGULATORY_TAGS = {
    "inaugurat": ("Visit / Inauguration", "STAGE 1", "badge-stage1"),
    "bhoomi pujan": ("Plant Foundation", "STAGE 1", "badge-stage1"),
    "qco": ("QCO Order", "STAGE 4", "badge-stage4"),
    "quality control": ("Quality Norms", "STAGE 2", "badge-stage2"),
    "bis": ("BIS Standard", "STAGE 2", "badge-stage2"),
    "pli": ("PLI Allocation", "STAGE 3", "badge-amber"),
    "almm": ("ALMM Inclusion", "STAGE 4", "badge-stage4"),
    "anti-dumping": ("Tariff Protection", "STAGE 3", "badge-cyan"),
    "procurement": ("Tender / Procurement", "STAGE 3", "badge-cyan")
}

new_signals = []
existing_titles = {s.get("title", "").strip().lower() for s in db.get("signals", [])}

for minister in db.get("ministers", []):
    name = minister["name"]
    query = f'"{name}" (inaugurates OR plant OR "quality control" OR BIS OR PLI OR tender)'
    url = f"https://news.google.com/rss/search?q={urllib.parse.quote(query)}&hl=en-IN&gl=IN&ceid=IN:en"
    
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=12) as resp:
            root = ET.fromstring(resp.read())
            
            for item in root.findall(".//item")[:3]:
                title = item.find("title").text if item.find("title") is not None else ""
                clean_title = title.strip()
                if not clean_title or clean_title.lower() in existing_titles:
                    continue
                
                link = item.find("link").text if item.find("link") is not None else "#"
                title_lower = clean_title.lower()
                
                matched = ("General Policy", "STAGE 1", "badge-cyan")
                for key, val in REGULATORY_TAGS.items():
                    if key in title_lower:
                        matched = val
                        break
                
                tickers_str = ", ".join(minister.get("tickers", []))
                new_signals.append({
                    "date": datetime.now().strftime("%d %b %Y"),
                    "category": matched[0],
                    "title": clean_title,
                    "minister": name,
                    "impact": f"Automated scrape. Assess sensitivity across: {tickers_str}",
                    "stage": matched[1],
                    "badge": matched[2],
                    "url": link
                })
                existing_titles.add(clean_title.lower())
    except Exception as e:
        print(f"Skipping query for {name}: {e}")

# Prepend new signals and cap database at latest 100 entries
db["signals"] = (new_signals + db.get("signals", []))[:100]

with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump(db, f, indent=2, ensure_ascii=False)

print(f"Scrape completed: Added {len(new_signals)} new signal(s).")